"""Tukang Copilot HTTP API + static phone web app (one process, see docs/API.md)."""
from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import re
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .pipeline import engine, mock
from .settings import ROOT, settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
WEB = ROOT / "web"
SAMPLES = ROOT / "samples"
if not all((SAMPLES / f"{k}.jpg").exists() for k in ("motor", "faucet", "rice")):
    mock.make_sample_photos(SAMPLES)
SAMPLE_TEXT = {
    "motor": mock.TRANSCRIPTS,
    "faucet": {"id": "Kran wastafel dapur netes terus walaupun sudah ditutup kencang.", "jv": "Kran wastafel pawon netes terus senajan wis ditutup kenceng.",
               "en": "The kitchen faucet keeps dripping even when closed tight."},
    "rice": {"id": "Rice cooker saya nggak panas, lampunya mati padahal sudah dicolok.", "jv": "Rice cookerku ora panas, lampune mati senajan wis dicolok.",
             "en": "My rice cooker won't heat, the light is off even though it's plugged in."},
}
CATEGORIES = {"", "motor", "pump", "appliance", "plumbing", "other"}
IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_TYPES = {".webm", ".ogg", ".wav", ".mp3", ".m4a", ".mp4", ".aac", ".opus"}
MAX_PHOTO, MAX_AUDIO = 15 * 1024 * 1024, 20 * 1024 * 1024
FILE_RE = re.compile(r"^(photo\d|parts|part_[A-Za-z0-9_-]+|check_\d+_\d+_\d+|diagram_\d+|voice_\d+_\d+)\.(jpg|png|mp3)$")


@asynccontextmanager
async def lifespan(_app):
    n = engine.cleanup()  # privacy: drop sessions older than RETENTION_HOURS
    if n:
        logging.getLogger("tukang").info("deleted %d sessions older than %sh", n, settings.retention_hours)
    yield


app = FastAPI(title="Tukang Copilot", version=__version__, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",")], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=WEB), name="static")


async def _save_upload(up: UploadFile, allowed: set[str], limit: int, default_ext: str) -> Path:
    ext = (Path(up.filename or "").suffix or default_ext).lower()
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported file type {ext}")
    data = await up.read()
    if not data:
        raise HTTPException(400, "Empty file")
    if len(data) > limit:
        raise HTTPException(413, "File too large")
    fd, name = tempfile.mkstemp(suffix=ext)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return Path(name)


def _load(sid: str) -> dict:
    try:
        return engine.load(sid)
    except (FileNotFoundError, ValueError):
        raise HTTPException(404, "Session not found")


def public(s: dict) -> dict:
    out = {k: v for k, v in s.items() if k not in {"text", "history"}}
    out["files_base"] = f"/files/{s['id']}/"
    return out


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (WEB / "index.html").read_text(encoding="utf-8")


@app.get("/guide/{sid}", response_class=HTMLResponse)
def guide_page(sid: str) -> str:
    s = _load(sid)
    title = html.escape((s.get("object_report") or {}).get("object") or "Tukang Copilot")
    return (WEB / "guide.html").read_text(encoding="utf-8").replace("{{TITLE}}", title).replace("{{SID}}", sid)


@app.get("/health")
@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "version": __version__, "mode": settings.mode, "meta_api_key": bool(settings.meta_api_key),
            "open_weights": settings.open_weights_active, "models": engine.models_used()}


@app.post("/api/sessions")
async def create_session(photos: list[UploadFile] | None = File(default=None), audio: UploadFile | None = File(default=None),
                         text: str = Form(default=""), language: str = Form(default="id"), category: str = Form(default=""),
                         sample: str = Form(default="")) -> dict:
    if language not in {"id", "jv", "en"}:
        raise HTTPException(400, "language must be id, jv or en")
    if category not in CATEGORIES:
        raise HTTPException(400, "unknown category")
    if len(text) > 2000:
        raise HTTPException(400, "Description is too long (max 2000 characters)")
    tmp: list[Path] = []
    try:
        if sample:
            if sample not in SAMPLE_TEXT:
                raise HTTPException(400, "unknown sample")
            photo_paths = [SAMPLES / f"{sample}.jpg"]
            text = text or SAMPLE_TEXT[sample][language]
        else:
            ups = [p for p in (photos or []) if p.filename][:3]
            if not ups:
                raise HTTPException(400, "Take or upload a photo of the broken thing")
            for up in ups:
                tmp.append(await _save_upload(up, IMAGE_TYPES, MAX_PHOTO, ".jpg"))
            photo_paths = list(tmp)
        audio_path = None
        if audio is not None and audio.filename:
            audio_path = await _save_upload(audio, AUDIO_TYPES, MAX_AUDIO, ".webm")
            tmp.append(audio_path)
        if not text.strip() and audio_path is None:
            raise HTTPException(400, "Describe the problem by voice or text")
        try:
            s = engine.create(photo_paths, language, text, audio_path, category)
        except RuntimeError as e:
            raise HTTPException(400, str(e))
        except OSError:
            raise HTTPException(400, "Could not read that photo. Try a JPG or PNG.")
    finally:
        for p in tmp:
            p.unlink(missing_ok=True)
    engine.start(s["id"])
    return {"id": s["id"]}


@app.get("/api/sessions/{sid}")
def get_session(sid: str) -> dict:
    return public(_load(sid))


@app.get("/api/sessions/{sid}/events")
async def events(sid: str):
    """Server-Sent Events: one `data:` line per change until the session settles."""
    _load(sid)

    async def gen():
        last = None
        for _ in range(900):  # ~7.5 min max
            s = engine.load(sid)
            snap = json.dumps({"status": s["status"], "stages": s["stages"], "question": s.get("question")}, ensure_ascii=False)
            if snap != last:
                yield f"data: {snap}\n\n"
                last = snap
            if s["status"] not in {"created", "running"}:
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@app.post("/api/sessions/{sid}/answer")
def post_answer(sid: str, text: str = Form(...)) -> dict:
    _load(sid)
    try:
        engine.answer(sid, text)
    except ValueError as e:
        raise HTTPException(409, str(e))
    engine.start(sid)
    return {"ok": True}


@app.post("/api/sessions/{sid}/steps/{n}/check")
async def post_check(sid: str, n: int, photo: UploadFile = File(...)) -> dict:
    _load(sid)
    p = await _save_upload(photo, IMAGE_TYPES, MAX_PHOTO, ".jpg")
    try:
        return engine.check_step(sid, n, p)
    except ValueError as e:
        raise HTTPException(409, str(e))
    finally:
        p.unlink(missing_ok=True)


@app.post("/api/sessions/{sid}/replan")
def post_replan(sid: str, report: str = Form(default="")) -> dict:
    _load(sid)
    try:
        return public(engine.replan(sid, report))
    except ValueError as e:
        raise HTTPException(409, str(e))


@app.get("/api/sessions/{sid}/report")
def get_report(sid: str) -> dict:
    _load(sid)
    return engine.report(sid)


@app.get("/files/{sid}/{name}")
def files(sid: str, name: str):
    if not FILE_RE.match(name):
        raise HTTPException(404)
    try:
        p = engine.session_dir(sid) / name
    except ValueError:
        raise HTTPException(404)
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p)
