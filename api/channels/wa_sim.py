"""WhatsApp simulator: the page /wa shows a WhatsApp-style chat that talks to the same handler as the real webhook
(api/channels/whatsapp.py: same parsing, same engine, same replies), with an in-process transport instead of the
Graph API. Each sent message is the exact Cloud API message object the real channel would POST.

On in demo mode (no Meta key or MOCK=1). With a live key it stays off unless WA_SIM=1, because then every chat
would spend real model calls (the live-mode guard limits still apply).

    POST /api/wa-sim/send               chat, text | photo | audio | button   (one inbound WhatsApp message)
    GET  /api/wa-sim/poll?chat=&after=  replies with seq > after, plus busy (a reply is still being worked on)
    GET  /api/wa-sim/media/{chat}/{id}  a photo or PDF the chat sent back
    GET  /api/wa-sim/sample/{name}.jpg  the labelled sample photos (AI-generated), so the page can send one
"""
from __future__ import annotations

import re
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from .. import guard
from ..settings import ROOT, settings
from . import whatsapp as wa

router = APIRouter()
CHAT_RE = re.compile(r"^[a-f0-9]{16,32}$")
MEDIA_RE = re.compile(r"^m[0-9a-f]{12}$")
SAMPLES = {"motor", "pump", "faucet", "rice", "tire"}
OUTBOX_MAX = 300
_outbox: dict[str, list[dict[str, Any]]] = {}
_seq: dict[str, int] = {}
_lock = threading.Lock()


def sim_enabled() -> bool:
    return settings.offline or settings.wa_sim


def _sender(chat: str) -> str:
    return f"sim:{chat}"


def _key(chat: str) -> str:
    return wa.user_key(_sender(chat))


def _media_dir(chat: str, sub: str) -> Path:
    return wa.conv_dir(_key(chat)) / sub


class SimTransport:
    """Keeps outgoing replies in memory for the page to poll; media files live in the chat's own folder,
    which goes with the chat (RETENTION_HOURS, or HAPUS)."""

    def __init__(self, chat: str):
        self.chat = chat
        self.demo = settings.offline

    def post(self, content: dict[str, Any]) -> None:
        key = _key(self.chat)
        with _lock:
            n = _seq.get(key, 0) + 1
            _seq[key] = n
            box = _outbox.setdefault(key, [])
            box.append({"seq": n, "at": time.time(), "message": content})
            del box[:-OUTBOX_MAX]

    def upload(self, path: Path, mime: str) -> str:
        mid = "m" + uuid.uuid4().hex[:12]
        d = _media_dir(self.chat, "out")
        d.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, d / f"{mid}{path.suffix.lower()}")
        return mid

    def fetch(self, media_id: str, limit: int, dest: Path) -> Path:
        if not MEDIA_RE.match(media_id):
            raise OSError("bad media id")
        src = next(iter(_media_dir(self.chat, "in").glob(f"{media_id}.*")), None)
        if src is None:
            raise OSError("no such media")
        if src.stat().st_size > limit:
            raise wa.MediaTooBig()
        shutil.copyfile(src, dest)
        return dest


def _check_chat(chat: str) -> None:
    if not sim_enabled():
        raise HTTPException(404)
    if not CHAT_RE.match(chat or ""):
        raise HTTPException(400, "bad chat id")


async def _save_in(chat: str, up: UploadFile, limit: int) -> tuple[str, str]:
    mime = wa._base_mime(up.content_type or "")
    d = _media_dir(chat, "in")
    d.mkdir(parents=True, exist_ok=True)
    mid = "m" + uuid.uuid4().hex[:12]
    ext = (Path(up.filename or "").suffix or ".bin").lower()[:6]
    p = d / f"{mid}{ext}"
    size = 0
    with p.open("wb") as f:
        while chunk := await up.read(1024 * 1024):
            size += len(chunk)
            if size > limit:
                f.close()
                p.unlink(missing_ok=True)
                raise HTTPException(413, "File too large")
            f.write(chunk)
    if size == 0:
        p.unlink(missing_ok=True)
        raise HTTPException(400, "Empty file")
    return mid, mime


@router.get("/api/wa-sim/info")
def info() -> dict[str, Any]:
    return {"enabled": sim_enabled(), "mode": settings.mode, "channel_live": wa.enabled()}


@router.post("/api/wa-sim/send")
async def send(request: Request, chat: str = Form(...), text: str = Form(default=""), button: str = Form(default=""),
               photo: UploadFile | None = File(default=None), audio: UploadFile | None = File(default=None)) -> dict[str, Any]:
    """One message from the simulated owner, shaped exactly like a Cloud API webhook message."""
    _check_chat(chat)
    try:  # costs nothing in demo mode, but keeps one visitor from filling the disk
        guard.check_rate("wasim:" + guard.client_key(request.headers.get("x-forwarded-for"), request.client.host if request.client else None),
                         bucket="wasim", limit=settings.wa_sim_rate_per_hour)
    except guard.Blocked as b:
        raise HTTPException(429, "Too many messages", headers={"Retry-After": str(b.retry_after)})
    if len(text) > 4096 or len(button) > 300:
        raise HTTPException(400, "too long")
    msg: dict[str, Any] = {"from": _sender(chat), "id": "sim." + uuid.uuid4().hex, "timestamp": str(int(time.time()))}
    if photo is not None and photo.filename:
        mid, mime = await _save_in(chat, photo, wa.MAX_PHOTO)
        msg |= {"type": "image", "image": {"id": mid, "mime_type": mime or "image/jpeg", **({"caption": text} if text else {})}}
    elif audio is not None and audio.filename:
        mid, mime = await _save_in(chat, audio, wa.MAX_AUDIO)
        msg |= {"type": "audio", "audio": {"id": mid, "mime_type": mime or "audio/ogg", "voice": True}}
    elif button:
        title = button.split("|", 1)[1] if "|" in button else ""
        msg |= {"type": "interactive", "interactive": {"type": "button_reply", "button_reply": {"id": button.split("|", 1)[0], "title": title}}}
    elif text.strip():
        msg |= {"type": "text", "text": {"body": text}}
    else:
        raise HTTPException(400, "Send text, a photo, a voice note or a button")
    ev = wa.parse_message(msg)
    if ev is None:
        raise HTTPException(400, "bad message")
    wa.dispatch([ev], lambda _s: SimTransport(chat))
    return {"ok": True, "id": msg["id"]}


@router.get("/api/wa-sim/poll")
def poll(chat: str, after: int = 0) -> dict[str, Any]:
    _check_chat(chat)
    with _lock:
        msgs = [m for m in _outbox.get(_key(chat), []) if m["seq"] > after]
    return {"messages": msgs, "busy": wa.busy(_key(chat)), "mode": settings.mode}


@router.get("/api/wa-sim/media/{chat}/{mid}")
def media(chat: str, mid: str) -> FileResponse:
    _check_chat(chat)
    if not MEDIA_RE.match(mid):
        raise HTTPException(404)
    p = next(iter(_media_dir(chat, "out").glob(f"{mid}.*")), None)
    if p is None:
        raise HTTPException(404)
    types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".pdf": "application/pdf"}
    return FileResponse(p, media_type=types.get(p.suffix, "application/octet-stream"))


@router.get("/api/wa-sim/sample/{name}.jpg")
def sample(name: str) -> FileResponse:
    if not sim_enabled() or name not in SAMPLES:
        raise HTTPException(404)
    p = ROOT / "samples" / f"{name}.jpg"
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p, media_type="image/jpeg")


@router.get("/wa")
def page() -> FileResponse:
    return FileResponse(ROOT / "web" / "wa.html", media_type="text/html")


def forget(key: str) -> None:
    with _lock:
        _outbox.pop(key, None)
        _seq.pop(key, None)


wa.forget_hooks.append(forget)


def reset() -> None:
    with _lock:
        _outbox.clear()
        _seq.clear()
