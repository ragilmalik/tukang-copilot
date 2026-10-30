"""A stand-in Meta Model API server built from the official request/response shapes (docs/META_API_NOTES.md)
and our recorded fixtures. It lets the REAL `meta_client` code path (HTTP, multipart, SSE streaming, SAM
mask parsing, base64 images) run end to end without a key or any spend.

    python -m api.testing.fake_meta            # serves http://127.0.0.1:8765/v1, key "test-key"
    META_API_BASE=http://127.0.0.1:8765/v1 MODEL_API_KEY=test-key python app.py

It checks the Authorization header (401 on a wrong key), validates the request shapes the docs require
(400 on a malformed SAM prompt or a missing schema), and answers each structured-output request with the
fixture for the schema name it asks for.
"""
from __future__ import annotations

import base64
import io
import json
import re
import time
from typing import Any

import numpy as np
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image

from ..pipeline import mock

TEST_KEY = "test-key"
MODELS = ["muse-wonder-1.0", "muse-spark-1.3", "muse-spark-1.2", "muse-spark-1.1", "muse-image-1.0",
          "muse-voice-transcribe-1.0", "sam-3.1"]
app = FastAPI(title="Fake Meta Model API (tests only)")
CALLS: list[dict[str, Any]] = []  # tests inspect what the client sent


def _err(status: int, code: str, msg: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": msg, "param": None, "type": "invalid_request_error"}}, status)


def _auth(req: Request) -> JSONResponse | None:
    if req.headers.get("authorization") != f"Bearer {TEST_KEY}":
        return _err(401, "invalid_api_key", "Incorrect API key provided.")
    return None


def _decode_data_url(url: str) -> Image.Image:
    b64 = url.split(",", 1)[1]
    return Image.open(io.BytesIO(base64.b64decode(b64)))


def _owner_text(messages: list[dict[str, Any]]) -> str:
    """The owner's own words (what a real model would key on), not our system prompt."""
    text = _all_text([m for m in messages if m.get("role") == "user"])
    return text.split("Owner's description:", 1)[1] if "Owner's description:" in text else text


def _all_text(messages: list[dict[str, Any]]) -> str:
    out = []
    for m in messages:
        c = m.get("content")
        if isinstance(c, str):
            out.append(c)
        elif isinstance(c, list):
            out += [p.get("text", "") for p in c if p.get("type") == "text"]
    return "\n".join(out)


@app.get("/v1/models")
async def models(req: Request):
    if (e := _auth(req)):
        return e
    return {"object": "list", "data": [{"id": m, "object": "model", "created": 1793000000 - i, "owned_by": "meta"} for i, m in enumerate(MODELS)]}


@app.post("/v1/asr/transcribe")
async def transcribe(req: Request):
    if (e := _auth(req)):
        return e
    form = await req.form()
    try:
        spec = json.loads(form["request"])
    except Exception:
        return _err(400, "invalid_request", "request part must be JSON")
    audio = form.get("audio")
    if audio is None or spec.get("audioEncoding") != "WAV":
        return _err(400, "invalid_request", "The audio is not a supported WAV file")
    data = await audio.read()
    if not data.startswith(b"RIFF"):
        return _err(400, "invalid_request", "The audio is not a supported WAV file")
    CALLS.append({"endpoint": "asr", "request": spec})
    lang = "en" if "English" in (spec.get("languageBias") or []) else "id"
    return {"sessionId": req.query_params.get("sessionId", "x"), "transcript": mock.TRANSCRIPTS[lang], "audioDurationMs": 3000, "turns": []}


@app.post("/v1/chat/completions")
async def chat(req: Request):
    if (e := _auth(req)):
        return e
    body = await req.json()
    model = body.get("model")
    if model not in MODELS:
        return _err(404, "model_not_found", "The requested model was not found.")
    msgs = body.get("messages") or []
    CALLS.append({"endpoint": "chat", "model": model, "schema": ((body.get("response_format") or {}).get("json_schema") or {}).get("name")})
    has_audio = any(isinstance(m.get("content"), list) and any(p.get("type") == "input_audio" for p in m["content"]) for m in msgs)
    usage = {"prompt_tokens": 1200, "completion_tokens": 300, "total_tokens": 1500}
    if has_audio:
        content = mock.TRANSCRIPTS["jv"]
    else:
        rf = body.get("response_format") or {}
        if rf.get("type") != "json_schema" or "schema" not in (rf.get("json_schema") or {}):
            return _err(400, "invalid_request", "response_format json_schema with a schema is required by this fixture server")
        name = rf["json_schema"].get("name")
        text = _all_text(msgs)
        lang = "en" if "in English" in text else "id"
        sc = mock.scenario(_owner_text(msgs))
        idx = 1 if "Earlier attempt" in text else 0
        fixtures = {"object_report": lambda: mock.object_report(sc, lang), "diagnosis": lambda: mock.diagnosis(sc, lang),
                    "repair_plan": lambda: mock.plan(sc, lang, idx), "diagram_review": lambda: {"ok": True, "problems": [], "fix_prompt": ""},
                    "step_check": lambda: {"passed": True, "observation": "Looks right.", "correction": ""}}
        if name not in fixtures:
            return _err(400, "invalid_request", f"no fixture for schema {name}")
        content = json.dumps(fixtures[name](), ensure_ascii=False)
    return {"id": "chatcmpl-fake", "object": "chat.completion", "created": int(time.time()), "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}], "usage": usage}


def _png(w: int = 512, h: int = 512) -> str:
    im = Image.new("RGB", (w, h), (250, 246, 238))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


@app.post("/v1/images/generations")
@app.post("/v1/images/edits")
async def images(req: Request):
    if (e := _auth(req)):
        return e
    body = await req.json()
    if body.get("model") != "muse-image-1.0" or not body.get("prompt"):
        return _err(400, "invalid_request", "model and prompt are required")
    if req.url.path.endswith("edits") and not body.get("images"):
        return _err(400, "invalid_request", "images are required for edits")
    CALLS.append({"endpoint": "images", "path": req.url.path})
    return {"created": int(time.time()), "data": [{"b64_json": _png()}], "output_format": body.get("output_format", "webp")}


def _sam_record(oid: int, l: int, t: int, r: int, b: int, w: int, h: int) -> str:
    from meta_sam_parser._mask_codec import _encode_raster  # Meta's own encoder: the bytes match the real wire format

    mh, mw = max(1, b - t), max(1, r - l)
    yy, xx = np.mgrid[0:mh, 0:mw]
    m = ((((xx - mw / 2) / (mw / 2)) ** 2 + ((yy - mh / 2) / (mh / 2)) ** 2) <= 1).astype(int).ravel().tolist()
    payload = _encode_raster(m, mw, mh)
    return (f"{oid}<|box;x1={l};y1={t};x2={r - 1};y2={b - 1};w={w};h={h};c=0.93|>"
            f"<|mask;x=0;y=0;c=0.93;data={mh},{mw},{payload}|>")


@app.post("/v1/responses")
async def responses(req: Request):
    if (e := _auth(req)):
        return e
    body = await req.json()
    if body.get("model") != "sam-3.1":
        return _err(404, "model_not_found", "The requested model was not found.")
    meta = body.get("metadata") or {}
    if any(not isinstance(v, str) for v in meta.values()):
        return _err(400, "invalid_request", "metadata values must be strings")
    parts = body["input"][0]["content"]
    prompt = next(p["text"] for p in parts if p["type"] == "input_text")
    img = _decode_data_url(next(p["image_url"] for p in parts if p["type"] == "input_image"))
    w, h = img.size
    CALLS.append({"endpoint": "sam", "prompt": prompt})
    recs = []
    if prompt.startswith("<0f>"):  # box/point object prompt
        for m in re.finditer(r"(\d+)<\|box;x1=(\d+);y1=(\d+);x2=(\d+);y2=(\d+);w=(\d+);h=(\d+)\|>", prompt):
            oid, l, t, r, b, pw, ph = map(int, m.groups())
            if (pw, ph) != (w, h):
                return _err(400, "invalid_request", f"prompt coordinates are given in a {pw}x{ph} frame, whose aspect ratio does not match the {w}x{h} media")
            recs.append(_sam_record(oid, l, t, r + 1, b + 1, w, h))
    else:
        if re.search(r"[,;+]", prompt):
            pass  # lists return zero matches, like the real model
        else:
            box = mock._BOXES.get(prompt.strip().lower())
            if box:
                recs.append(_sam_record(0, int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h), w, h))
    text = ("<0f>" + ",".join(recs)) if recs else ""
    lane = {"item_id": "msg_fake", "output_index": 0, "content_index": 0}

    def gen():
        events = [{"type": "response.created", "response": {"id": "resp_fake", "status": "in_progress"}}]
        if text:
            half = len(text) // 2
            events += [{"type": "response.output_text.delta", "delta": text[:half], **lane},
                       {"type": "response.output_text.delta", "delta": text[half:], **lane}]
        else:
            events += [{"type": "response.output_text.delta", "delta": "", **lane}]
        events += [{"type": "response.output_text.done", "text": text, **lane},
                   {"type": "response.completed", "response": {"id": "resp_fake", "status": "completed"}}]
        for ev in events:
            yield f"event: {ev['type']}\ndata: {json.dumps(ev)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


# OpenAI-compatible Baseten stand-in for the open-weights path (same handler, different base URL)
@app.post("/baseten/v1/chat/completions")
async def baseten(req: Request):
    if req.headers.get("authorization") != "Bearer test-baseten-key":
        return _err(401, "unauthorized", "bad key")
    body = await req.json()
    if body.get("model") != "meta-models/muse-spark-open":
        return _err(404, "model_not_found", "unknown model")
    CALLS.append({"endpoint": "baseten", "model": body.get("model")})
    req.scope["headers"] = [(k, v) for k, v in req.scope["headers"] if k != b"authorization"] + [(b"authorization", f"Bearer {TEST_KEY}".encode())]
    body["model"] = "muse-spark-1.3"
    rf = body.get("response_format") or {}
    text = _all_text(body.get("messages") or [])
    sc, lang = mock.scenario(_owner_text(body.get("messages") or [])), ("en" if "in English" in text else "id")
    name = (rf.get("json_schema") or {}).get("name")
    data = {"diagnosis": mock.diagnosis(sc, lang), "repair_plan": mock.plan(sc, lang)}.get(name, {})
    return {"id": "x", "object": "chat.completion", "model": "meta-models/muse-spark-open",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": json.dumps(data), "reasoning_content": "..."}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10}}


def serve_in_thread(port: int = 0) -> str:
    """Start this fake server on a background thread; returns its base URL (e.g. http://127.0.0.1:51234/v1).
    Also adds 127.0.0.1 to NO_PROXY so a corporate/sandbox proxy can't swallow local calls."""
    import os
    import socket
    import threading

    import uvicorn

    for var in ("NO_PROXY", "no_proxy"):
        os.environ[var] = ",".join(filter(None, [os.environ.get(var, ""), "127.0.0.1", "localhost"]))
    if not port:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True, name="fake-meta").start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    return f"http://127.0.0.1:{port}/v1"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8765)
