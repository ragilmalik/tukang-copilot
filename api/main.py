"""Tukang Copilot HTTP API + static phone web app (one process, see docs/API.md)."""
from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import re
import shutil
import tempfile
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import __version__, guard, shop
from .pipeline import engine, media, mock
from .settings import ROOT, settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
WEB = ROOT / "web"
SAMPLES = ROOT / "samples"
if not all((SAMPLES / f"{k}.jpg").exists() for k in ("motor", "pump", "faucet", "rice")):
    mock.make_sample_photos(SAMPLES)
SAMPLE_TEXT = {
    "motor": mock.TRANSCRIPTS,
    "pump": {"id": "Pompa air Shimizu saya bunyi dan muter, tapi airnya nggak keluar sama sekali.",
             "jv": "Pompa banyu Shimizuku muni lan muter, nanging banyune ora metu babar pisan.",
             "en": "My Shimizu water pump hums and spins, but no water comes out at all."},
    "faucet": {"id": "Kran wastafel dapur netes terus walaupun sudah ditutup kencang.", "jv": "Kran wastafel pawon netes terus senajan wis ditutup kenceng.",
               "en": "The kitchen faucet keeps dripping even when closed tight."},
    "rice": {"id": "Rice cooker saya nggak panas, lampunya mati padahal sudah dicolok.", "jv": "Rice cookerku ora panas, lampune mati senajan wis dicolok.",
             "en": "My rice cooker won't heat, the light is off even though it's plugged in."},
}
CATEGORIES = {"", "motor", "pump", "appliance", "plumbing", "other"}
IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_TYPES = {".webm", ".ogg", ".wav", ".mp3", ".m4a", ".mp4", ".aac", ".opus"}
VIDEO_TYPES = {".mp4", ".mov", ".webm", ".3gp", ".mkv", ".m4v"}
MAX_PHOTO, MAX_AUDIO, MAX_VIDEO = 15 * 1024 * 1024, 20 * 1024 * 1024, 40 * 1024 * 1024
FILE_RE = re.compile(r"^(photo\d|parts|part_[A-Za-z0-9_-]+|check_\d+_\d+_\d+|diagram_\d+|voice_\d+_\d+)\.(jpg|png|mp3)$")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    n = engine.cleanup()  # privacy: drop sessions older than RETENTION_HOURS
    if n:
        logging.getLogger("tukang").info("deleted %d sessions older than %sh", n, settings.retention_hours)
    yield


app = FastAPI(title="Tukang Copilot", version=__version__, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",")], allow_methods=["*"], allow_headers=["*"])
@app.middleware("http")
async def security_headers(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Cheap hardening: no MIME sniffing, no framing, no referrer leaks, camera and mic only for this origin."""
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    resp.headers.setdefault("Permissions-Policy", "camera=(self), microphone=(self), geolocation=(self)")
    return resp


app.mount("/static", StaticFiles(directory=WEB), name="static")


async def _save_upload(up: UploadFile, allowed: set[str], limit: int, default_ext: str) -> Path:
    ext = (Path(up.filename or "").suffix or default_ext).lower()
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported file type {ext}")
    fd, name = tempfile.mkstemp(suffix=ext)
    size = 0
    try:
        with os.fdopen(fd, "wb") as f:
            while chunk := await up.read(1024 * 1024):  # stream to disk, stop early on oversize uploads
                size += len(chunk)
                if size > limit:
                    raise HTTPException(413, "File too large")
                f.write(chunk)
        if size == 0:
            raise HTTPException(400, "Empty file")
    except BaseException:
        Path(name).unlink(missing_ok=True)
        raise
    return Path(name)


def _load(sid: str) -> dict[str, Any]:
    try:
        return engine.load(sid)
    except (FileNotFoundError, ValueError):
        raise HTTPException(404, "Session not found")


def public(s: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in s.items() if k not in {"text", "history"}}
    out["files_base"] = f"/files/{s['id']}/"
    dx = out.get("diagnosis")
    if isinstance(dx, dict):
        out["diagnosis"] = {**dx, "tools": shop.with_links(dx.get("tools") or []), "parts": shop.with_links(dx.get("parts") or [])}
        text = shop.share_text(dx.get("problem_summary", ""), dx.get("tools") or [], dx.get("parts") or [], str(out.get("lang", "id")))
        out["whatsapp_url"] = shop.whatsapp_url(text)
    return out


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (WEB / "index.html").read_text(encoding="utf-8")


@app.get("/manifest.webmanifest")
def manifest() -> FileResponse:
    """PWA manifest (install to home screen). Served from the root so its scope covers the whole app."""
    p = WEB / "manifest.webmanifest"
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p, media_type="application/manifest+json")


@app.get("/sw.js")
def service_worker() -> FileResponse:
    p = WEB / "sw.js"
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p, media_type="text/javascript", headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"})


@app.get("/guide/{sid}", response_class=HTMLResponse)
def guide_page(sid: str) -> str:
    s = _load(sid)
    title = html.escape((s.get("object_report") or {}).get("object") or "Tukang Copilot")
    return (WEB / "guide.html").read_text(encoding="utf-8").replace("{{TITLE}}", title).replace("{{SID}}", sid)


@app.get("/health")
@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "version": __version__, "mode": settings.mode, "meta_api_key": bool(settings.meta_api_key),
            "open_weights": settings.open_weights_active, "models": engine.models_used()}


@app.post("/api/sessions")
async def create_session(request: Request, photos: list[UploadFile] | None = File(default=None), audio: UploadFile | None = File(default=None),
                         video: UploadFile | None = File(default=None),
                         text: str = Form(default=""), language: str = Form(default="id"), category: str = Form(default=""),
                         sample: str = Form(default="")) -> dict[str, Any]:
    if language not in {"id", "jv", "en"}:
        raise HTTPException(400, "language must be id, jv or en")
    if category not in CATEGORIES:
        raise HTTPException(400, "unknown category")
    if len(text) > 2000:
        raise HTTPException(400, "Description is too long (max 2000 characters)")
    if guard.active():
        try:
            guard.check_budget()
            guard.check_rate(guard.client_key(request.headers.get("x-forwarded-for"), request.client.host if request.client else None))
        except guard.Blocked as b:
            raise HTTPException(b.status, guard.message(b.kind, language), headers={"Retry-After": str(b.retry_after)})
    tmp: list[Path] = []
    tmp_dirs: list[Path] = []
    video_sound: Path | None = None
    try:
        if sample:
            if sample not in SAMPLE_TEXT:
                raise HTTPException(400, "unknown sample")
            photo_paths = [SAMPLES / f"{sample}.jpg"]
            text = text or SAMPLE_TEXT[sample][language]
        else:
            ups = [p for p in (photos or []) if p.filename][:3]
            has_video = video is not None and bool(video.filename)
            if not ups and not has_video:
                raise HTTPException(400, "Take or upload a photo of the broken thing")
            for up in ups:
                tmp.append(await _save_upload(up, IMAGE_TYPES, MAX_PHOTO, ".jpg"))
            photo_paths = list(tmp)
            if has_video and video is not None and len(photo_paths) < 3:
                # 5-10 s clip -> sharpest frame from each third, appended after any photos (max 3 in total)
                vid = await _save_upload(video, VIDEO_TYPES, MAX_VIDEO, ".mp4")
                tmp.append(vid)
                frames_dir = Path(tempfile.mkdtemp(prefix="tc-frames-"))
                try:
                    frames = media.extract_frames(vid, frames_dir)
                except RuntimeError as e:
                    raise HTTPException(400, str(e))
                tmp.extend(frames)
                photo_paths += frames[:3 - len(photo_paths)]
                tmp_dirs.append(frames_dir)
                video_sound = vid  # used as the voice description if nothing else was given
        audio_path = None
        if audio is not None and audio.filename:
            audio_path = await _save_upload(audio, AUDIO_TYPES, MAX_AUDIO, ".webm")
            tmp.append(audio_path)
        if audio_path is None and not text.strip() and video_sound is not None:
            audio_path = video_sound
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
        for d in tmp_dirs:
            shutil.rmtree(d, ignore_errors=True)
    engine.start(s["id"])
    return {"id": s["id"]}


@app.get("/api/sessions/{sid}")
def get_session(sid: str) -> dict[str, Any]:
    return public(_load(sid))


@app.get("/api/sessions/{sid}/events")
async def events(sid: str) -> StreamingResponse:
    """Server-Sent Events: one `data:` line per change until the session settles."""
    _load(sid)

    async def gen() -> AsyncIterator[str]:
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
def post_answer(sid: str, text: str = Form(...)) -> dict[str, Any]:
    _load(sid)
    try:
        engine.answer(sid, text)
    except ValueError as e:
        raise HTTPException(409, str(e))
    engine.start(sid)
    return {"ok": True}


@app.post("/api/sessions/{sid}/steps/{n}/check")
async def post_check(sid: str, n: int, photo: UploadFile = File(...)) -> dict[str, Any]:
    _load(sid)
    p = await _save_upload(photo, IMAGE_TYPES, MAX_PHOTO, ".jpg")
    try:
        return engine.check_step(sid, n, p)
    except ValueError as e:
        raise HTTPException(409, str(e))
    finally:
        p.unlink(missing_ok=True)


@app.post("/api/sessions/{sid}/replan")
def post_replan(sid: str, report: str = Form(default="")) -> dict[str, Any]:
    _load(sid)
    try:
        return public(engine.replan(sid, report))
    except ValueError as e:
        raise HTTPException(409, str(e))


@app.get("/api/sessions/{sid}/report")
def get_report(sid: str) -> dict[str, Any]:
    _load(sid)
    return engine.report(sid)


@app.get("/api/sessions/{sid}/report.pdf")
def get_report_pdf(sid: str) -> FileResponse:
    """Printable repair report (A4 PDF): safety level, marked photo, steps with camera checks, tools, cost."""
    s = _load(sid)
    if not s.get("diagnosis"):
        raise HTTPException(409, "The diagnosis is not ready yet")
    from .render import report_pdf

    out = report_pdf.build(engine.report(sid), s, engine.session_dir(sid), engine.session_dir(sid) / "report.pdf")
    return FileResponse(out, media_type="application/pdf", filename=f"tukang-copilot-{sid}.pdf")


@app.get("/files/{sid}/{name}")
def files(sid: str, name: str) -> FileResponse:
    if not FILE_RE.match(name):
        raise HTTPException(404)
    try:
        p = engine.session_dir(sid) / name
    except ValueError:
        raise HTTPException(404)
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p)
