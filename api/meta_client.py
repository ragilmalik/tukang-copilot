"""meta_client: the only module that talks to Meta models (SPEC §6). Auth, retries, timeouts, logging, cost.

Every endpoint and model id below was checked against Meta's public docs on 2026-10-30:
  * Muse Voice Transcribe  POST /v1/asr/transcribe (multipart)   https://dev.meta.ai/docs/speech-to-text
  * Muse Spark / Wonder    POST /v1/chat/completions             https://dev.meta.ai/docs/structured-output
                           image parts                            https://dev.meta.ai/docs/image-understanding
  * Muse Spark 1.2 audio   input_audio content part               https://dev.meta.ai/docs/video-understanding#audio
  * Muse Image             POST /v1/images/generations, /edits    https://dev.meta.ai/docs/image-generation
  * SAM 3.1                POST /v1/responses (stream=true)       https://dev.meta.ai/docs/media-segmentation
                           output grammar + meta-sam-parser       https://dev.meta.ai/docs/sam/client-libraries
  * Muse Spark Open        Baseten, OpenAI-compatible chat         https://dev.meta.ai/docs/muse-spark-open/deploy#baseten
Base URL https://api.meta.ai/v1, auth "Authorization: Bearer <key>".
"""
from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, AsyncIterator

import httpx

from . import cost
from .settings import settings

log = logging.getLogger("tukang.meta")
RETRY_STATUS = {429, 500, 502, 503, 504}


class MetaAPIError(RuntimeError):
    pass


def _headers(json_body: bool = True) -> dict[str, str]:
    h = {"Authorization": f"Bearer {settings.meta_api_key}"}
    if json_body:
        h["Content-Type"] = "application/json"
    return h


def _post(url: str, *, retries: int = 3, timeout: float = 300.0, **kw: Any) -> httpx.Response:
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            r = httpx.post(url, timeout=timeout, **kw)
            if r.status_code in RETRY_STATUS and attempt < retries:
                wait = 2 ** attempt * 2
                log.warning("HTTP %s from %s, retry in %ss", r.status_code, url, wait)
                time.sleep(wait)
                continue
            if r.status_code >= 400:
                raise MetaAPIError(f"{r.status_code} from {url}: {r.text[:600]}")
            return r
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last = e
            if attempt < retries:
                time.sleep(2 ** attempt * 2)
    raise MetaAPIError(f"Request to {url} failed: {last}")


def data_url(path: Path) -> str:
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    return f"data:{mime.get(path.suffix.lower(), 'image/png')};base64,{base64.b64encode(path.read_bytes()).decode()}"


def image_part(path: Path, max_side: int = 1024) -> dict[str, Any]:
    """Chat Completions image part (an image_url OBJECT on chat completions), downsized to save tokens."""
    from PIL import Image

    im = Image.open(path).convert("RGBA")
    im.thumbnail((max_side, max_side))
    bg = Image.new("RGB", im.size, (128, 128, 128))
    bg.paste(im, mask=im.split()[-1])
    buf = io.BytesIO()
    bg.save(buf, "JPEG", quality=85)
    return {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()}}


# --- 1. Listen
def transcribe(wav_path: Path, seconds: float, language_bias: list[str] | None = None,
               keywords: list[str] | None = None) -> str:
    """Muse Voice Transcribe file endpoint. WAV must be mono 16-bit PCM, 16 or 24 kHz, <= 10 min."""
    req: dict[str, Any] = {"mode": "PUSH_TO_TALK", "model": settings.asr_model, "audioEncoding": "WAV"}
    if language_bias:
        req["languageBias"] = language_bias
    if keywords:
        req["keywords"] = keywords
    with open(wav_path, "rb") as f:
        r = _post(
            f"{settings.meta_api_base}/asr/transcribe?sessionId=tukang-{uuid.uuid4().hex[:12]}",
            headers=_headers(json_body=False),
            files={"request": (None, json.dumps(req), "application/json"), "audio": (wav_path.name, f, "audio/wav")},
        )
    cost.charge(settings.asr_model, seconds / 3600 * cost.ASR_USD_PER_HOUR)
    return (r.json().get("transcript") or "").strip()


def transcribe_with_spark_audio(wav_path: Path, language_name: str) -> str:
    """Javanese is not among Muse Voice Transcribe's 25 languages, so Javanese voice notes go through
    Muse Spark 1.2 audio understanding (docs recommend 1.2 for audio; give >= 4000 output tokens)."""
    body = {
        "model": settings.audio_model,
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": f"Transcribe this audio. Someone is describing a broken object they want to repair, mostly in {language_name}. "
                                     "Keep the original language and words. Return only the transcript."},
            {"type": "input_audio", "input_audio": {"data": base64.b64encode(wav_path.read_bytes()).decode(), "format": "wav"}},
        ]}],
    }
    r = _post(f"{settings.meta_api_base}/chat/completions", headers=_headers(), json=body)
    j = r.json()
    cost.charge_tokens(settings.audio_model, j.get("usage"))
    return (j["choices"][0]["message"].get("content") or "").strip()


# --- 2. Text models, structured output
def _extract_json(text: str) -> Any:
    from .coerce import extract_json
    return extract_json(text)


def chat_json(messages: list[dict[str, Any]], schema: dict[str, Any], schema_name: str, *,
              model: str | None = None, reasoning_effort: str = "medium", open_weights: bool = False) -> Any:
    """Chat Completions with response_format json_schema. Returns the parsed JSON object."""
    rf = {"type": "json_schema", "json_schema": {"name": schema_name, "schema": schema}}
    if open_weights:
        url = f"{settings.open_api_base}/chat/completions"
        headers = {"Authorization": f"Bearer {settings.baseten_api_key}", "Content-Type": "application/json"}
        body: dict[str, Any] = {
            "model": settings.open_model, "messages": messages, "response_format": rf,
            "max_tokens": 16384,  # reasoning and answer share this budget on Muse Spark Open
            "reasoning_effort": reasoning_effort if reasoning_effort in {"low", "medium", "high", "xhigh"} else "medium",
        }
    else:
        model = model or settings.reason_model
        url = f"{settings.meta_api_base}/chat/completions"
        headers = _headers()
        body = {"model": model, "messages": messages, "reasoning_effort": reasoning_effort, "response_format": rf}
    try:
        r = _post(url, headers=headers, json=body, timeout=600)
    except MetaAPIError as e:
        if open_weights and "response_format" in str(e):  # provider only takes json_object
            body["response_format"] = {"type": "json_object"}
            r = _post(url, headers=headers, json=body, timeout=600)
        else:
            raise
    j = r.json()
    if not open_weights:
        cost.charge_tokens(model, j.get("usage"))
    return _extract_json(j["choices"][0]["message"].get("content") or "")


# --- 3/5. Muse Image
def _image_bytes(r: httpx.Response) -> bytes:
    data = r.json().get("data") or []
    if not data:
        raise MetaAPIError(f"Muse Image returned no image: {r.text[:300]}")
    if data[0].get("b64_json"):
        return base64.b64decode(data[0]["b64_json"])
    if data[0].get("url"):
        return httpx.get(data[0]["url"], timeout=120).content
    raise MetaAPIError("Muse Image response had neither b64_json nor url")


def generate_image(prompt: str, out: Path, size: str = "1536x1024", fast: bool = False) -> Path:
    cost.check(cost.IMAGE_USD)
    body = {
        "model": settings.image_model, "prompt": prompt, "n": 1, "size": size, "output_format": "png",
        "reasoning_strength": "low" if fast else "high",
        # Instruction cards: allow image search for tool/part references, no web search or shell.
        "tool_enablement": {"enable_web_search": False, "enable_shell": False, "enable_image_search": True},
    }
    r = _post(f"{settings.meta_api_base}/images/generations", headers=_headers(), json=body, timeout=600)
    out.write_bytes(_image_bytes(r))
    cost.charge(settings.image_model, cost.IMAGE_USD)
    return out


def edit_image(prompt: str, refs: list[Path], out: Path, fast: bool = False) -> Path:
    """Image-to-image with 1-10 reference images (Meta's JSON body for /v1/images/edits)."""
    cost.check(cost.IMAGE_USD)
    body = {
        "model": settings.image_model, "prompt": prompt, "n": 1, "output_format": "png",
        "images": [{"image_url": data_url(p)} for p in refs[:10]],
        "reasoning_strength": "low" if fast else "high",
        "tool_enablement": {"enable_web_search": False, "enable_shell": False},
    }
    r = _post(f"{settings.meta_api_base}/images/edits", headers=_headers(), json=body, timeout=600)
    out.write_bytes(_image_bytes(r))
    cost.charge(settings.image_model, cost.IMAGE_USD)
    return out


# --- 4. SAM 3.1
def segment(image_path: Path, prompt: str) -> list[dict[str, Any]]:
    """SAM 3.1 on one image. `prompt` is either a short noun phrase ("spark plug cap") or box/point
    object-prompt text built with meta_sam_parser.build_object_prompt (never both, per the docs).
    Returns [{object_id, left, top, right, bottom, mask (bytes 0/1, mh x mw), mw, mh, confidence}].
    Masks are box-local; parsed with Meta's own parser (pip install meta-sam-parser)."""
    cost.check(cost.SAM_IMAGE_USD)
    body = {
        "model": settings.sam_model,
        "input": [{"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": prompt},
            {"type": "input_image", "image_url": data_url(image_path)},
        ]}],
        "stream": True,
        "metadata": {"mask_encoding": "one_bit", "include_confidence": "true"},  # metadata values are strings
    }
    events: list[dict[str, Any]] = []
    headers = _headers() | {"Accept": "text/event-stream"}
    for attempt in range(3):
        events.clear()
        try:
            with httpx.stream("POST", f"{settings.meta_api_base}/responses", headers=headers, json=body, timeout=300) as r:
                if r.status_code in RETRY_STATUS and attempt < 2:
                    time.sleep(3 * (attempt + 1))
                    continue
                if r.status_code >= 400:
                    r.read()
                    raise MetaAPIError(f"SAM {r.status_code}: {r.text[:400]}")
                for line in r.iter_lines():
                    if line.startswith("data: "):
                        payload = line[6:].strip()
                        if payload == "[DONE]":
                            break
                        events.append(json.loads(payload))
            break
        except (httpx.TimeoutException, httpx.TransportError):
            if attempt == 2:
                raise
    cost.charge(settings.sam_model, cost.SAM_IMAGE_USD)
    return parse_sam_events(events)


def log_call(stage: str, model: str, started: float) -> None:
    """Structured per-call log line: stage, model, latency (SPEC §7 observability)."""
    log.info("call stage=%s model=%s latency_ms=%d", stage, model, int((time.time() - started) * 1000))


def list_models() -> list[str]:
    """GET /v1/models: the model ids enabled for this key (used by scripts/verify_meta_api.py)."""
    r = httpx.get(f"{settings.meta_api_base}/models", headers=_headers(json_body=False), timeout=30)
    if r.status_code >= 400:
        raise MetaAPIError(f"{r.status_code} from /models: {r.text[:300]}")
    return [m.get("id", "") for m in r.json().get("data", [])]


def parse_sam_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Responses stream events -> masks, using Meta's meta-sam-parser."""
    from meta_sam_parser import decode_mask_to_raster, image_segmentation_format, parse_responses_stream

    async def _source() -> AsyncIterator[dict[str, Any]]:
        for ev in events:
            yield ev

    async def _parse() -> Any:
        return await parse_responses_stream(_source(), image_segmentation_format()).final_result()

    result = asyncio.run(_parse())
    out: list[dict[str, Any]] = []
    for rec in result.records:
        if rec.kind != "mask":
            continue
        b = rec.bounds
        out.append({
            "object_id": rec.object_id, "left": int(b.left), "top": int(b.top), "right": int(b.right),
            "bottom": int(b.bottom), "mask": decode_mask_to_raster(rec.mask), "mw": rec.mask.width,
            "mh": rec.mask.height, "confidence": rec.confidence,
        })
    return out
