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

from . import __version__, errors, guard, handoff, impact, shop
from .trace import build_trace
from .pipeline import engine, media, mock, photos, track
from .settings import ROOT, settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
WEB = ROOT / "web"
SAMPLES = ROOT / "samples"
if not all((SAMPLES / f"{k}.jpg").exists() for k in ("motor", "pump", "faucet", "rice", "tire")):
    mock.make_sample_photos(SAMPLES)
SAMPLE_TEXT = {
    "motor": mock.TRANSCRIPTS,
    "pump": {"id": "Pompa air Shimizu saya bunyi dan muter, tapi airnya nggak keluar sama sekali.",
             "jv": "Pompa banyu Shimizuku muni lan muter, nanging banyune ora metu babar pisan.",
             "en": "My Shimizu water pump hums and spins, but no water comes out at all."},
    "tire": {"id": "Ban belakang motor saya kempes pelan-pelan dan sepertinya ada paku di tapaknya.",
             "jv": "Ban mburi motorku kempes alon-alon lan kayane ana paku ing tapake.",
             "en": "My scooter's rear tyre is slowly going flat and there seems to be a nail in the tread."},
    "faucet": {"id": "Kran wastafel dapur netes terus walaupun sudah ditutup kencang.", "jv": "Kran wastafel pawon netes terus senajan wis ditutup kenceng.",
               "en": "The kitchen faucet keeps dripping even when closed tight."},
    "rice": {"id": "Rice cooker saya nggak panas, lampunya mati padahal sudah dicolok.", "jv": "Rice cookerku ora panas, lampune mati senajan wis dicolok.",
             "en": "My rice cooker won't heat, the light is off even though it's plugged in."},
}
CATEGORIES = {"", "motor", "pump", "appliance", "plumbing", "other"}
IMAGE_TYPES = photos.allowed_exts()
AUDIO_TYPES = {".webm", ".ogg", ".wav", ".mp3", ".m4a", ".mp4", ".aac", ".opus"}
VIDEO_TYPES = {".mp4", ".mov", ".webm", ".3gp", ".mkv", ".m4v"}
MAX_PHOTO, MAX_AUDIO, MAX_VIDEO = 15 * 1024 * 1024, 20 * 1024 * 1024, 40 * 1024 * 1024
FILE_RE = re.compile(r"^(photo\d|parts|part_[A-Za-z0-9_-]+|check_\d+_\d+_\d+|diagram_\d+|voice_\d+_\d+)\.(jpg|png|mp3)$")


CLEANUP_EVERY_S = 3600.0


async def _janitor(interval: float) -> None:
    """Keep the privacy promise on a server that stays up for days: purge expired sessions every `interval` seconds."""
    while True:
        try:
            n = await asyncio.to_thread(engine.cleanup)
            if n:
                logging.getLogger("tukang").info("deleted %d sessions older than %sh", n, settings.retention_hours)
        except Exception:  # never let the janitor die
            logging.getLogger("tukang").exception("cleanup failed")
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    task = asyncio.create_task(_janitor(CLEANUP_EVERY_S))  # first pass runs at startup, then hourly
    try:
        yield
    finally:
        task.cancel()


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
    path = Path(name)
    if allowed is IMAGE_TYPES and photos.is_heif(path):
        try:  # iPhone HEIC -> JPEG so every later stage sees a normal photo
            return photos.heif_to_jpeg(path)
        except OSError as e:
            raise HTTPException(400, str(e) if not photos.HEIF_OK else "Could not read that photo. Try a JPG or PNG.")
        finally:
            path.unlink(missing_ok=True)
    return path


def _load(sid: str) -> dict[str, Any]:
    try:
        return engine.load(sid)
    except (FileNotFoundError, ValueError):
        raise HTTPException(404, "Session not found")


def _guard_followup(request: Request, sid: str) -> None:
    """Live mode: a model call inside a repair counts toward FOLLOWUP_RATE_PER_HOUR and the daily budget."""
    if not guard.active():
        return
    try:
        guard.check_budget()
        guard.check_rate(guard.client_key(request.headers.get("x-forwarded-for"), request.client.host if request.client else None),
                         bucket="followup")
    except guard.Blocked as b:
        raise HTTPException(b.status, guard.message(b.kind, str(_load(sid).get("lang", "id"))), headers={"Retry-After": str(b.retry_after)})


def public(s: dict[str, Any]) -> dict[str, Any]:
    # never on the wire: the owner's own words (text, history, phrases the injection guard caught) and raw errors
    out = {k: v for k, v in s.items() if k not in {"text", "history", "error_detail", "input_flags"}}
    out["input_guard"] = len(s.get("input_flags") or [])
    out["files_base"] = f"/files/{s['id']}/"
    out["trace"] = build_trace(s)
    dx = out.get("diagnosis")
    if isinstance(dx, dict):
        out["diagnosis"] = {**dx, "tools": shop.with_links(dx.get("tools") or []), "parts": shop.with_links(dx.get("parts") or [])}
        text = shop.share_text(dx.get("problem_summary", ""), dx.get("tools") or [], dx.get("parts") or [], str(out.get("lang", "id")))
        out["whatsapp_url"] = shop.whatsapp_url(text)
    return out


def progress_view(s: dict[str, Any]) -> dict[str, Any]:
    """What the progress screen streams (SSE) while the agent works: stage states plus each stage's result as soon
    as it exists, so the viewer sees the object report, the SAM-marked photo and the top cause arrive one by one.
    Built from public() so nothing private (owner's words, raw errors) can leak; trimmed to stay small."""
    p = public(s)
    out: dict[str, Any] = {k: p.get(k) for k in ("id", "lang", "status", "stages", "question", "error", "error_kind",
                                                  "agent_log", "models", "files_base", "input_guard")}
    rep = p.get("object_report")
    if isinstance(rep, dict):
        out["object_report"] = {"object": rep.get("object", ""), "brand_model_guess": rep.get("brand_model_guess", ""),
                                "components": [{"id": c.get("id"), "name": c.get("name", "")} for c in rep.get("components") or []
                                               if isinstance(c, dict)][:8],
                                "visible_issues": list(rep.get("visible_issues") or [])[:3]}
    if p.get("parts_image") and (s.get("stages", {}).get("segment", {}).get("status") == "done"):
        found = [v for v in (p.get("parts") or {}).values() if isinstance(v, dict)]
        out["parts_image"] = p["parts_image"]
        out["parts_found"] = [{"label": v.get("label"), "name": v.get("name", ""), "found": bool(v.get("found"))} for v in found][:8]
    dx = p.get("diagnosis")
    if isinstance(dx, dict) and dx.get("causes"):
        out["diagnosis"] = {"problem_summary": dx.get("problem_summary", ""), "safety_level": dx.get("safety_level", ""),
                            "causes": [{"title": c.get("title", ""), "confidence": c.get("confidence", 0)}
                                       for c in dx["causes"][:3] if isinstance(c, dict)]}
    plan = p.get("plan")
    if isinstance(plan, dict):
        out["plan_steps"] = len(plan.get("steps") or [])
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
            "open_weights": settings.open_weights_active, "demo_fallback": settings.demo_fallback, "models": engine.models_used()}


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
            s = engine.create(photo_paths, language, text, audio_path, category, sample=sample)
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


@app.get("/api/demo/check-photo/{kind}")
def demo_check_photo(kind: str, sample: str = "motor") -> Response:
    """1-tap demo: a labelled STAND-IN 'after' photo so a visitor with no broken object can try "Check my step".
    kind=ok: the scenario's after-photo (or its sample photo); kind=dark: a too-dark shot that the check rejects."""
    if kind not in {"ok", "dark"} or sample not in SAMPLE_TEXT:
        raise HTTPException(404)
    if kind == "ok":
        p = SAMPLES / f"check_{sample}.jpg"
        return FileResponse(p if p.exists() else SAMPLES / f"{sample}.jpg", media_type="image/jpeg")
    return Response(_dark_photo(), media_type="image/jpeg", headers={"Cache-Control": "max-age=3600"})


def _dark_photo() -> bytes:
    import io

    from PIL import Image, ImageDraw

    im = Image.new("RGB", (800, 600), (8, 8, 10))
    ImageDraw.Draw(im).text((16, 12), "STAND-IN - too dark (demo)", fill=(70, 70, 76))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    return buf.getvalue()


@app.get("/api/sessions/{sid}")
def get_session(sid: str) -> dict[str, Any]:
    return public(_load(sid))


@app.delete("/api/sessions/{sid}")
def delete_session(sid: str) -> dict[str, Any]:
    """Erase this repair (photos, voice, PDFs) from the server now, instead of waiting for RETENTION_HOURS."""
    _load(sid)
    track.forget(sid)
    return {"id": sid, "deleted": engine.delete(sid)}


@app.get("/api/sessions/{sid}/events")
async def events(sid: str) -> StreamingResponse:
    """Server-Sent Events: one `data:` line per change until the session settles."""
    _load(sid)

    async def gen() -> AsyncIterator[str]:
        last = None
        for _ in range(900):  # ~7.5 min max
            s = engine.load(sid)
            snap = json.dumps(progress_view(s), ensure_ascii=False)
            if snap != last:
                yield f"data: {snap}\n\n"
                last = snap
            if s["status"] not in {"created", "running"}:
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@app.post("/api/sessions/{sid}/answer")
def post_answer(sid: str, request: Request, text: str = Form(...)) -> dict[str, Any]:
    _load(sid)
    if len(text) > 2000:
        raise HTTPException(400, "Answer is too long")
    _guard_followup(request, sid)
    try:
        engine.answer(sid, text)
    except ValueError as e:
        raise HTTPException(409, str(e))
    engine.start(sid)
    return {"ok": True}


@app.post("/api/sessions/{sid}/retry")
def post_retry(sid: str, request: Request) -> dict[str, Any]:
    """Run again a session that stopped on an error (busy AI service, dropped signal ...)."""
    _load(sid)
    _guard_followup(request, sid)
    try:
        engine.retry(sid)
    except ValueError as e:
        raise HTTPException(409, str(e))
    engine.start(sid)
    return {"ok": True}


@app.post("/api/sessions/{sid}/steps/{n}/check")
async def post_check(sid: str, n: int, request: Request, photo: UploadFile = File(...)) -> dict[str, Any]:
    _load(sid)
    _guard_followup(request, sid)
    p = await _save_upload(photo, IMAGE_TYPES, MAX_PHOTO, ".jpg")
    try:
        return engine.check_step(sid, n, p)
    except engine.LimitReached as e:
        raise HTTPException(429, str(e))
    except ValueError as e:
        raise HTTPException(409, str(e))
    except OSError:  # not a readable picture: the owner should retake it, the service is fine
        raise HTTPException(400, "Could not read that photo. Try a JPG or PNG.")
    except Exception as e:  # Meta API busy or offline: the photo is not lost, the person can simply retake it
        logging.getLogger("tukang").error("step check failed: %s", errors.detail(e))
        raise HTTPException(503, errors.friendly(e, _load(sid)["lang"]), headers={"Retry-After": "10"})
    finally:
        p.unlink(missing_ok=True)


MAX_FRAME = 3 * 1024 * 1024


@app.post("/api/sessions/{sid}/steps/{n}/track")
async def post_track(sid: str, n: int, frame: UploadFile = File(...)) -> dict[str, Any]:
    """Live guide: one small camera frame -> SAM 3.1 boxes and outline of this step's part (normalised 0..1).
    About one frame per second; too fast gives 429, and after MAX_TRACK_FRAMES the answer has limit_reached."""
    _load(sid)
    p = await _save_upload(frame, IMAGE_TYPES, MAX_FRAME, ".jpg")
    try:
        return await asyncio.to_thread(track.track_step, sid, n, p)
    except track.TooFast:
        raise HTTPException(429, "Too many frames, slow down", headers={"Retry-After": "1"})
    except ValueError as e:
        raise HTTPException(409, str(e))
    except OSError:
        raise HTTPException(400, "Could not read that frame")
    except Exception as e:  # SAM busy: the live view keeps running, the next frame tries again
        logging.getLogger("tukang").error("track failed: %s", errors.detail(e))
        raise HTTPException(503, errors.friendly(e, _load(sid)["lang"]), headers={"Retry-After": "3"})
    finally:
        p.unlink(missing_ok=True)


@app.post("/api/sessions/{sid}/command")
async def post_command(sid: str, request: Request, text: str = Form(default=""), audio: UploadFile | None = File(default=None)) -> dict[str, Any]:
    """Hands-free fallback for phones without SpeechRecognition: a push-to-talk clip (or text) -> one command
    (next, back, repeat, check, broken, stop) or null. The clip is transcribed and deleted at once."""
    _load(sid)
    if len(text) > 200:
        raise HTTPException(400, "Command text is too long")
    if audio is not None and audio.filename:  # typed commands never reach a model
        _guard_followup(request, sid)
    p = await _save_upload(audio, AUDIO_TYPES, 2 * 1024 * 1024, ".webm") if audio is not None and audio.filename else None
    if p is None and not text.strip():
        raise HTTPException(400, "Say or type a command")
    try:
        return await asyncio.to_thread(engine.voice_command, sid, text, p)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logging.getLogger("tukang").error("voice command failed: %s", errors.detail(e))
        raise HTTPException(503, errors.friendly(e, _load(sid)["lang"]), headers={"Retry-After": "5"})
    finally:
        if p is not None:
            p.unlink(missing_ok=True)


@app.post("/api/sessions/{sid}/replan")
def post_replan(sid: str, request: Request, report: str = Form(default="")) -> dict[str, Any]:
    _load(sid)
    if len(report) > 2000:
        raise HTTPException(400, "Report is too long")
    _guard_followup(request, sid)
    try:
        return public(engine.replan(sid, report))
    except ValueError as e:
        raise HTTPException(409, str(e))
    except Exception as e:
        logging.getLogger("tukang").error("replan failed: %s", errors.detail(e))
        raise HTTPException(503, errors.friendly(e, _load(sid)["lang"]), headers={"Retry-After": "10"})


@app.post("/api/sessions/{sid}/outcome")
def post_outcome(sid: str, result: str = Form(...), minutes: int | None = Form(default=None),
                 tester: str = Form(default="")) -> dict[str, Any]:
    """The owner closes the loop: result is "fixed" (it works now) or "pro" (a mechanic took over).
    Optional for trials: minutes the fix took, and a tester label (e.g. "T1"). Each call is appended to the impact log."""
    _load(sid)
    try:
        return public(engine.set_outcome(sid, result.strip().lower(), minutes, tester))
    except ValueError as e:
        raise HTTPException(409 if "plan" in str(e) else 422, str(e))


@app.get("/api/sessions/{sid}/handoff")
def get_handoff(sid: str, request: Request) -> dict[str, Any]:
    """Bengkel hand-off card: WhatsApp summary (guide + PDF links), Google Maps search for the right workshop."""
    s = _load(sid)
    base = settings.public_base_url or str(request.base_url)
    return handoff.build(s, base)


@app.get("/api/sessions/{sid}/report")
def get_report(sid: str) -> dict[str, Any]:
    _load(sid)
    return engine.report(sid)


@app.get("/api/sessions/{sid}/report.pdf")
def get_report_pdf(sid: str) -> FileResponse:
    """Printable repair report (A4 PDF): safety level, marked photo, steps with camera checks, tools, cost."""
    s = _load(sid)
    if not s.get("diagnosis") and s.get("status") != "stopped":  # a safety stop before diagnosis still gets a stop report
        raise HTTPException(409, "The diagnosis is not ready yet")
    from .render import report_pdf

    out = report_pdf.build(engine.report(sid), s, engine.session_dir(sid), engine.session_dir(sid) / "report.pdf")
    return FileResponse(out, media_type="application/pdf", filename=f"tukang-copilot-{sid}.pdf")


@app.get("/api/sessions/{sid}/workshop.pdf")
def get_workshop_pdf(sid: str) -> FileResponse:
    """Large-print workshop sheets (A4, one step per page) to pin up next to the job."""
    s = _load(sid)
    if not s.get("plan"):
        raise HTTPException(409, "The plan is not ready yet")
    from .render import workshop_pdf

    out = workshop_pdf.build(engine.report(sid), s, engine.session_dir(sid), engine.session_dir(sid) / "workshop.pdf")
    return FileResponse(out, media_type="application/pdf", filename=f"tukang-copilot-workshop-{sid}.pdf")


@app.get("/api/impact/outcomes.jsonl")
def impact_log(request: Request) -> Response:
    """The trial outcome log (numbers only), for scripts/impact_report.py --data. Off unless IMPACT_TOKEN is set;
    send it as the X-Impact-Token header. A server disk can be wiped on redeploy, so download after the trials."""
    import hmac

    tok = request.headers.get("x-impact-token", "")
    if not settings.impact_token or not hmac.compare_digest(tok, settings.impact_token):
        raise HTTPException(404)
    p = impact.log_path()
    return Response(p.read_bytes() if p.exists() else b"", media_type="application/x-ndjson")


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
