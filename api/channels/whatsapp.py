"""WhatsApp channel: the same repair engine, reached from a WhatsApp chat (WhatsApp Cloud API, Graph API).

    GET  /webhooks/whatsapp   Meta's webhook check (hub.mode / hub.verify_token / hub.challenge)
    POST /webhooks/whatsapp   messages from WhatsApp users (X-Hub-Signature-256 checked with WA_APP_SECRET)

Off (404) unless WA_TOKEN, WA_PHONE_NUMBER_ID, WA_VERIFY_TOKEN and WA_APP_SECRET are all set. Endpoints and
payload shapes follow developers.facebook.com (Graph API v26.0); the URLs are listed in docs/WHATSAPP.md.

The chat, one owner per phone number:
  photo(s) + text or voice note  -> engine.create + engine.run (same safety gate, same models, same rules)
  red stop                       -> safety message + nearest-workshop Maps link, never any steps
  needs_answer                   -> the follow-up question; the next text or voice note is the answer
  ready                          -> SAM-marked photo with the diagnosis and cost/saving, then step 1 with
                                    reply buttons Done / Problem / Stop
  photo during a step            -> the step camera check (engine.check_step)
  Problem (or "masih rusak")     -> re-plan to the next cause (engine.replan)
  last step done or Stop         -> the PDF repair report as a document
  HAPUS / BUSAK / DELETE         -> erase this repair now (same as the app's "Delete my photos now")

Webhook deliveries are acknowledged at once and handled on a worker thread, one queue per owner so their
messages keep their order. A delivery Meta retries (same message id) is handled once. The chat state lives in
memory and is dropped after RETENTION_HOURS of silence, like the sessions on disk. Logs never carry a token or
a full phone number (mask()).

`/api/wa-sim/*` (api/channels/wa_sim.py) drives this same code with an in-process transport, so the channel can
be shown without a WhatsApp number.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import secrets
import shutil
import threading
import time
from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from PIL import Image

from .. import errors, guard, handoff
from ..pipeline import engine, safety, track
from ..settings import settings
from ..voice import parse_command
from .wa_text import command, detect, rupiah, t

log = logging.getLogger("tukang.whatsapp")
router = APIRouter()

MAX_TEXT = 2000
MAX_PHOTO = 15 * 1024 * 1024  # same limits as the web app (api/main.py)
MAX_AUDIO = 20 * 1024 * 1024
MAX_BODY = 1024 * 1024  # webhook POST body
MAX_PHOTOS = 3
BODY_MAX, CAPTION_MAX, BUTTON_TITLE_MAX, FOOTER_MAX = 1024, 1024, 20, 60  # Cloud API limits (docs/WHATSAPP.md)
IMAGE_EXT = {"image/jpeg": ".jpg", "image/jpg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
AUDIO_EXT = {"audio/ogg": ".ogg", "audio/mpeg": ".mp3", "audio/mp4": ".m4a", "audio/aac": ".aac", "audio/amr": ".amr",
             "audio/opus": ".opus", "audio/webm": ".webm", "audio/wav": ".wav", "audio/x-wav": ".wav"}


# --- small helpers
def enabled() -> bool:
    return all((settings.wa_token, settings.wa_phone_number_id, settings.wa_verify_token, settings.wa_app_secret))


def mask(phone: str) -> str:
    """For logs only: never the full number."""
    p = re.sub(r"\D", "", phone or "")
    return f"***{p[-3:]}" if p else "sim" if (phone or "").startswith("sim:") else "?"


def user_key(sender: str) -> str:
    return hashlib.sha256(("wa|" + (sender or "")).encode()).hexdigest()[:20]


def signature_ok(body: bytes, header: str | None, secret: str) -> bool:
    if not header or not header.startswith("sha256=") or not secret:
        return False
    want = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(want, header[7:].strip().lower())


def _cut(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def _base_mime(mime: str) -> str:
    return (mime or "").split(";")[0].strip().lower()


# --- inbound
@dataclass
class Inbound:
    sender: str          # WhatsApp user id / phone ("sim:<chat>" for the simulator)
    msg_id: str
    kind: str            # text | image | audio | button | other
    text: str = ""
    media_id: str = ""
    mime: str = ""
    button_id: str = ""
    raw_type: str = ""


def parse_webhook(body: dict[str, Any], phone_number_id: str | None = None) -> list[Inbound]:
    """Messages from a `whatsapp_business_account` webhook. Status updates (sent, delivered, read) carry no
    `messages` and are skipped; so are entries for another business number than ours."""
    out: list[Inbound] = []
    if not isinstance(body, dict) or body.get("object") != "whatsapp_business_account":
        return out
    for entry in body.get("entry") or []:
        for ch in (entry or {}).get("changes") or []:
            if (ch or {}).get("field") != "messages":
                continue
            val = ch.get("value") or {}
            pid = str((val.get("metadata") or {}).get("phone_number_id") or "")
            if phone_number_id and pid and pid != phone_number_id:
                continue
            for m in val.get("messages") or []:
                ev = parse_message(m)
                if ev is not None:
                    out.append(ev)
    return out


def parse_message(m: dict[str, Any]) -> Inbound | None:
    if not isinstance(m, dict) or not m.get("from") or not m.get("id"):
        return None
    typ = str(m.get("type") or "")
    ev = Inbound(sender=str(m["from"])[:40], msg_id=str(m["id"])[:200], kind="other", raw_type=typ)
    if typ == "text":
        ev.kind, ev.text = "text", str((m.get("text") or {}).get("body") or "")
    elif typ == "image":
        img = m.get("image") or {}
        ev.kind, ev.media_id, ev.mime, ev.text = "image", str(img.get("id") or ""), str(img.get("mime_type") or ""), str(img.get("caption") or "")
    elif typ == "audio":
        a = m.get("audio") or {}
        ev.kind, ev.media_id, ev.mime = "audio", str(a.get("id") or ""), str(a.get("mime_type") or "")
    elif typ == "interactive":
        it = m.get("interactive") or {}
        rep = it.get("button_reply") or it.get("list_reply") or {}
        ev.kind, ev.button_id, ev.text = "button", str(rep.get("id") or ""), str(rep.get("title") or "")
    elif typ == "button":  # quick-reply button on a template message
        ev.kind, ev.text = "text", str((m.get("button") or {}).get("text") or "")
    elif typ in {"reaction", "unsupported", "system", "request_welcome"}:
        ev.kind = "ignore"
    if ev.kind in {"image", "audio"} and not ev.media_id:
        ev.kind = "other"
    return ev


# --- transports
class MediaTooBig(Exception):
    pass


class Transport(Protocol):
    """Where replies go and where media comes from: the Graph API, or the simulator."""

    demo: bool

    def post(self, content: dict[str, Any]) -> None: ...

    def upload(self, path: Path, mime: str) -> str: ...

    def fetch(self, media_id: str, limit: int, dest: Path) -> Path: ...


class GraphTransport:
    """WhatsApp Cloud API over HTTPS (graph.facebook.com/<version>). One owner per instance."""

    def __init__(self, to: str):
        self.to = to
        self.demo = settings.offline

    def _url(self, path: str) -> str:
        return f"{settings.wa_graph_base.rstrip('/')}/{settings.wa_graph_version}/{path.lstrip('/')}"

    def _auth(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {settings.wa_token}"}

    def _call(self, method: str, url: str, **kw: Any) -> httpx.Response:
        last: Exception | None = None
        for attempt in range(2):
            try:
                r = httpx.request(method, url, headers=self._auth(), timeout=30, **kw)
            except httpx.HTTPError as e:
                last = e
            else:
                if r.status_code < 400:
                    return r
                last = RuntimeError(f"{r.status_code} from Graph API")
                if r.status_code not in (429, 500, 502, 503, 504):
                    break
            time.sleep(0.5 * (attempt + 1))
        raise RuntimeError(errors.detail(last or RuntimeError("Graph API call failed")))

    def post(self, content: dict[str, Any]) -> None:
        payload = {"messaging_product": "whatsapp", "recipient_type": "individual", "to": self.to, **content}
        try:
            self._call("POST", self._url(f"{settings.wa_phone_number_id}/messages"), json=payload)
        except Exception as e:  # one lost reply must not stop the chat
            log.warning("whatsapp send to %s failed: %s", mask(self.to), errors.detail(e))

    def upload(self, path: Path, mime: str) -> str:
        with path.open("rb") as f:
            r = self._call("POST", self._url(f"{settings.wa_phone_number_id}/media"),
                           data={"messaging_product": "whatsapp", "type": mime}, files={"file": (path.name, f, mime)})
        return str(r.json()["id"])

    def fetch(self, media_id: str, limit: int, dest: Path) -> Path:
        """GET /<media_id> for a short-lived URL, then download it with the same token (both steps per the docs)."""
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", media_id):
            raise OSError("bad media id")
        meta = self._call("GET", self._url(media_id), params={"phone_number_id": settings.wa_phone_number_id}).json()
        try:
            size = int(meta.get("file_size") or 0)
        except (TypeError, ValueError):
            size = 0
        if size > limit:
            raise MediaTooBig()
        url = str(meta.get("url") or "")
        if not url.startswith(("https://", "http://")):
            raise OSError("no media url")
        n = 0
        with httpx.stream("GET", url, headers=self._auth(), timeout=60, follow_redirects=True) as r:
            if r.status_code >= 400:
                raise OSError(f"{r.status_code} downloading media")
            with dest.open("wb") as f:
                for chunk in r.iter_bytes(256 * 1024):
                    n += len(chunk)
                    if n > limit:
                        raise MediaTooBig()
                    f.write(chunk)
        if n == 0:
            raise OSError("empty media")
        return dest


# --- conversation state
@dataclass
class Conv:
    key: str
    sender: str
    lang: str = "id"
    texts: list[str] = field(default_factory=list)
    photos: list[Path] = field(default_factory=list)
    audio: Path | None = None
    sid: str | None = None        # the repair being guided
    last_sid: str | None = None   # for HAPUS after the guide ended
    phase: str = "idle"           # idle | needs_answer | guiding | error
    step: int = 0
    last: float = field(default_factory=time.time)
    ready_at: float = 0.0
    timer: bool = False
    transport: Transport | None = None


_convs: dict[str, Conv] = {}
_queues: dict[str, deque[Callable[[], None]]] = {}
_running: set[str] = set()
_timers = 0
_seen: OrderedDict[str, float] = OrderedDict()
_glock = threading.Lock()
SEEN_MAX = 5000
forget_hooks: list[Callable[[str], None]] = []  # called with a chat key when cleanup() drops it (the simulator's log)


def conv_dir(key: str) -> Path:
    return settings.data_dir / "whatsapp" / key


def reset() -> None:
    """Tests: forget every chat."""
    global _timers
    wait_idle(10)
    with _glock:
        _convs.clear()
        _queues.clear()
        _seen.clear()
        _timers = 0


def busy(key: str) -> bool:
    with _glock:
        return key in _running or bool(_queues.get(key)) or bool((_convs.get(key) or Conv("", "")).timer)


def wait_idle(timeout: float = 30.0) -> bool:
    """Tests and the simulator: wait until every queued message has been handled."""
    end = time.time() + timeout
    while time.time() < end:
        with _glock:
            idle = not _running and not any(_queues.values()) and _timers == 0
        if idle:
            return True
        time.sleep(0.02)
    return False


def cleanup(now: float | None = None) -> int:
    """Drop chats silent for RETENTION_HOURS (their pending photos and voice notes go too)."""
    t0 = time.time() if now is None else now
    cutoff = t0 - 3600 * settings.retention_hours
    with _glock:
        old = [k for k, c in _convs.items() if c.last < cutoff and k not in _running]
        for k in old:
            _convs.pop(k, None)
            _queues.pop(k, None)
    for k in old:
        shutil.rmtree(conv_dir(k), ignore_errors=True)
        for hook in forget_hooks:
            hook(k)
    return len(old)


def _get_conv(sender: str) -> Conv:
    key = user_key(sender)
    with _glock:
        c = _convs.get(key)
        if c is None:
            c = _convs[key] = Conv(key=key, sender=sender)
        return c


def _seen_before(msg_id: str) -> bool:
    with _glock:
        if msg_id in _seen:
            return True
        _seen[msg_id] = time.time()
        while len(_seen) > SEEN_MAX:
            _seen.popitem(last=False)
        return False


def _enqueue(key: str, job: Callable[[], None]) -> None:
    with _glock:
        _queues.setdefault(key, deque()).append(job)
        if key in _running:
            return
        _running.add(key)
    threading.Thread(target=_drain, args=(key,), daemon=True, name=f"wa-{key[:6]}").start()


def _drain(key: str) -> None:
    while True:
        with _glock:
            q = _queues.get(key)
            if not q:
                _running.discard(key)
                return
            job = q.popleft()
        try:
            job()
        except Exception:
            log.exception("whatsapp handler failed")


def _job(conv: Conv, ev: Inbound, tr: Transport) -> Callable[[], None]:
    return lambda: handle(conv, ev, tr)


def dispatch(events: list[Inbound], transport_for: Callable[[str], Transport]) -> int:
    """Queue each new message for its owner; returns how many were queued (duplicates are skipped)."""
    cleanup()
    n = 0
    for ev in events:
        if ev.kind == "ignore" or _seen_before(ev.msg_id):
            continue
        conv = _get_conv(ev.sender)
        tr = transport_for(ev.sender)
        log.info("whatsapp in from %s: %s", mask(ev.sender), ev.kind)
        _enqueue(conv.key, _job(conv, ev, tr))
        n += 1
    return n


# --- sending
def _footer(tr: Transport) -> str:
    return t("footer_demo" if tr.demo else "footer", "en")[:FOOTER_MAX]


def send_text(tr: Transport, body: str) -> None:
    tr.post({"type": "text", "text": {"preview_url": False, "body": _cut(body, 4096)}})


def send_image(tr: Transport, path: Path, caption: str) -> None:
    try:
        mid = tr.upload(path, "image/png" if path.suffix == ".png" else "image/jpeg")
    except Exception as e:
        log.warning("whatsapp image upload failed: %s", errors.detail(e))
        send_text(tr, caption)
        return
    tr.post({"type": "image", "image": {"id": mid, "caption": _cut(caption, CAPTION_MAX)}})


def send_document(tr: Transport, path: Path, filename: str, caption: str) -> None:
    try:
        mid = tr.upload(path, "application/pdf")
    except Exception as e:
        log.warning("whatsapp document upload failed: %s", errors.detail(e))
        return
    tr.post({"type": "document", "document": {"id": mid, "filename": filename, "caption": _cut(caption, CAPTION_MAX)}})


def send_buttons(tr: Transport, body: str, buttons: list[tuple[str, str]], header_image: Path | None = None) -> None:
    inter: dict[str, Any] = {
        "type": "button",
        "body": {"text": _cut(body, BODY_MAX)},
        "footer": {"text": _footer(tr)},
        "action": {"buttons": [{"type": "reply", "reply": {"id": bid[:256], "title": _cut(title, BUTTON_TITLE_MAX)}}
                               for bid, title in buttons[:3]]},
    }
    if header_image is not None and header_image.exists():
        try:
            inter["header"] = {"type": "image", "image": {"id": tr.upload(header_image, "image/jpeg")}}
        except Exception as e:
            log.warning("whatsapp header upload failed: %s", errors.detail(e))
    tr.post({"type": "interactive", "interactive": inter})


# --- the chat
def handle(conv: Conv, ev: Inbound, tr: Transport) -> None:
    conv.last = time.time()
    conv.transport = tr
    if ev.text:
        if len(ev.text) > MAX_TEXT:
            send_text(tr, t("too_long", conv.lang))
            return
        lang = detect(ev.text)
        if lang:
            conv.lang = lang
    if ev.kind == "other":
        send_text(tr, t("unsupported", conv.lang))
        return
    if conv.sid:
        try:
            engine.load(conv.sid)
        except (FileNotFoundError, ValueError):  # erased in the app, or past RETENTION_HOURS
            conv.sid, conv.phase, conv.step = None, "idle", 0
    cmd = command(ev.text) if ev.kind == "text" else None
    if cmd == "erase":
        erase(conv, tr)
        return
    if cmd == "reset":
        _clear_pending(conv)
        conv.sid, conv.phase, conv.step = None, "idle", 0
        send_text(tr, t("reset", conv.lang))
        return
    if ev.kind == "button":
        on_button(conv, ev, tr)
        return
    if conv.phase == "guiding" and conv.sid:
        on_guiding(conv, ev, tr)
        return
    if conv.phase == "needs_answer" and conv.sid:
        on_answer(conv, ev, tr)
        return
    if conv.phase == "error" and conv.sid:
        _send_error(conv, tr, engine.load(conv.sid))
        return
    on_idle(conv, ev, tr, cmd)


def on_idle(conv: Conv, ev: Inbound, tr: Transport, cmd: str | None) -> None:
    if ev.kind == "text":
        if cmd == "hello" and not conv.photos:
            send_text(tr, t("welcome", conv.lang))
            return
        gate = safety.check_text(ev.text, conv.lang)
        if not gate.allowed:  # the same gate the engine runs first: a red stop never waits for a photo
            _clear_pending(conv)
            _send_red(conv, tr, gate.reason, {"text": ev.text, "object_report": None, "category": ""})
            return
        conv.texts.append(ev.text.strip())
    elif ev.kind == "image":
        if len(conv.photos) < MAX_PHOTOS:
            p = _fetch(conv, ev, tr, MAX_PHOTO, f"photo{len(conv.photos) + 1}", IMAGE_EXT)
            if p is None:
                return
            if not _readable_image(p):
                p.unlink(missing_ok=True)
                send_text(tr, t("bad_photo", conv.lang))
                return
            conv.photos.append(p)
        if ev.text.strip():
            gate = safety.check_text(ev.text, conv.lang)
            if not gate.allowed:
                _clear_pending(conv)
                _send_red(conv, tr, gate.reason, {"text": ev.text, "object_report": None, "category": ""})
                return
            conv.texts.append(ev.text.strip())
    elif ev.kind == "audio":
        p = _fetch(conv, ev, tr, MAX_AUDIO, "voice", AUDIO_EXT)
        if p is None:
            return
        if conv.audio is not None and conv.audio != p:
            conv.audio.unlink(missing_ok=True)
        conv.audio = p
    has_words = bool(conv.texts) or conv.audio is not None
    if conv.photos and has_words:
        _schedule_start(conv)
    elif conv.photos:
        if ev.kind == "image" and len(conv.photos) == 1:
            send_text(tr, t("ask_text", conv.lang))
    else:
        send_text(tr, t("ask_photo", conv.lang))


def _schedule_start(conv: Conv) -> None:
    """Photos of one album arrive as separate messages: wait WA_DEBOUNCE_S after the last one before starting."""
    global _timers
    if settings.wa_debounce_s <= 0:
        start_repair(conv)
        return
    conv.ready_at = time.time() + settings.wa_debounce_s
    if conv.timer:
        return
    conv.timer = True
    with _glock:
        _timers += 1

    def wait_then_fire() -> None:
        global _timers
        try:
            while True:
                left = conv.ready_at - time.time()
                if left <= 0:
                    break
                time.sleep(min(left, 0.5))
            _enqueue(conv.key, lambda: _fire(conv))
        finally:
            with _glock:
                _timers -= 1

    threading.Thread(target=wait_then_fire, daemon=True, name=f"wa-timer-{conv.key[:6]}").start()


def _fire(conv: Conv) -> None:
    conv.timer = False
    if conv.phase == "idle" and conv.photos and (conv.texts or conv.audio is not None):
        if time.time() < conv.ready_at:
            _schedule_start(conv)
            return
        start_repair(conv)


def start_repair(conv: Conv) -> None:
    tr = conv.transport
    if tr is None:
        return
    if _blocked(conv, tr, "new"):
        _clear_pending(conv)
        return
    send_text(tr, t("working", conv.lang))
    text = "\n".join(conv.texts)[:MAX_TEXT]
    try:
        s = engine.create(list(conv.photos), conv.lang, text, conv.audio, "", owner_token=secrets.token_urlsafe(18))  # never sent: the chat is the owner
    except RuntimeError as e:
        send_text(tr, t("bad_audio" if "recording" in str(e).lower() else "bad_photo", conv.lang))
        _clear_pending(conv)
        return
    _clear_pending(conv)
    conv.sid = conv.last_sid = s["id"]
    conv.phase, conv.step = "running", 0
    engine.run(s["id"])
    present(conv, tr)


def present(conv: Conv, tr: Transport) -> None:
    """Say what the engine decided: stop, a question, an error, or the diagnosis and step 1."""
    if not conv.sid:
        return
    s = engine.load(conv.sid)
    st = s["status"]
    if st == "stopped":
        _send_red(conv, tr, str(s.get("stop_reason") or ""), s)
    elif st == "needs_answer":
        conv.phase = "needs_answer"
        send_text(tr, "❓ " + str(s.get("question") or ""))
    elif st == "error":
        conv.phase = "error"
        _send_error(conv, tr, s)
    elif st == "exhausted":
        _send_exhausted(conv, tr, s)
    elif st == "ready":
        conv.phase, conv.step = "guiding", 1
        send_image(tr, _result_photo(s), result_caption(s, conv.lang))
        send_step(conv, tr, s)


def _result_photo(s: dict[str, Any]) -> Path:
    d = engine.session_dir(s["id"])
    return d / str(s.get("parts_image") or s["photos"][0])


def result_caption(s: dict[str, Any], lang: str) -> str:
    rep, dx = s.get("object_report") or {}, s.get("diagnosis") or {}
    lines = []
    if rep.get("object"):
        lines.append(f"🔧 {rep['object']}")
    causes = dx.get("causes") or []
    if causes:
        top = causes[min(int(s.get("cause_index") or 0), len(causes) - 1)]
        lines.append(f"🩺 {top.get('title', '')} ({int(top.get('confidence') or 0)}%)")
    level = str((s.get("safety") or {}).get("level") or dx.get("safety_level") or "")
    if level in {"green", "amber", "red"}:
        icon = {"green": "🟢", "amber": "🟡", "red": "🔴"}[level]
        lines.append(f"{icon} {t('safety', lang)}: {t('level_' + level, lang)}")
    parts, shop, save = int(dx.get("cost_estimate_idr") or 0), int(dx.get("shop_cost_estimate_idr") or 0), int(dx.get("diy_saving_idr") or 0)
    if parts or shop:
        line = t("cost_parts", lang, parts=rupiah(parts))
        if shop:
            line += t("cost_save", lang, shop=rupiah(shop), save=rupiah(save))
        lines.append(line)
    if dx.get("minutes_estimate"):
        lines.append(t("minutes", lang, m=int(dx["minutes_estimate"])))
    if s.get("mode") == "offline":
        lines.append(t("demo", lang))
    if s.get("fallback"):
        lines.append("⚠️ " + t("fallback", lang))
    return "\n".join(lines)


def _buttons(conv: Conv, s: dict[str, Any]) -> list[tuple[str, str]]:
    tag = f"{s['id']}:{int(s.get('cause_index') or 0)}:{conv.step}"
    return [(f"done:{tag}", t("btn_done", conv.lang)), (f"problem:{tag}", t("btn_problem", conv.lang)),
            (f"stop:{tag}", t("btn_stop", conv.lang))]


def step_body(conv: Conv, s: dict[str, Any], prefix: str = "") -> str:
    steps = (s.get("plan") or {}).get("steps") or []
    st = steps[conv.step - 1]
    lines = [prefix, ""] if prefix else []
    before = (s.get("diagnosis") or {}).get("before_you_start") or []
    if conv.step == 1 and before and not prefix:
        lines += [t("before", conv.lang)] + [f"☐ {b}" for b in before] + [""]
    lines.append(f"*{t('step', conv.lang, n=conv.step, total=len(steps))}*")
    lines.append(str(st.get("instruction") or ""))
    lines += [f"⚠️ {w}" for w in (st.get("warnings") or [])][:3]
    if int(st.get("wait_minutes") or 0):
        lines.append(t("wait", conv.lang, m=int(st["wait_minutes"])))
    lines.append(t("send_check", conv.lang))
    return "\n".join(lines)


def send_step(conv: Conv, tr: Transport, s: dict[str, Any], prefix: str = "") -> None:
    steps = (s.get("plan") or {}).get("steps") or []
    if not steps or not 1 <= conv.step <= len(steps):
        return
    st = steps[conv.step - 1]
    part = (s.get("parts") or {}).get(st.get("component_id") or "", {}) or {}
    header = engine.session_dir(s["id"]) / part["image"] if part.get("image") and not prefix else None
    send_buttons(tr, step_body(conv, s, prefix), _buttons(conv, s), header)


def _send_red(conv: Conv, tr: Transport, reason: str, s: dict[str, Any]) -> None:
    """Red stop: the safety message and where to find a workshop. No steps, ever."""
    q = handoff.maps_query(s)
    lines = [f"*{t('stop_title', conv.lang)}*", reason.strip(), "", t("workshop", conv.lang, url=handoff.maps_url(q)),
             t("emergency", conv.lang)]
    if conv.last_sid and s.get("id"):
        lines += ["", t("erase_hint", conv.lang)]
    send_text(tr, "\n".join(x for x in lines if x is not None))
    conv.sid, conv.phase, conv.step = None, "idle", 0


def _send_error(conv: Conv, tr: Transport, s: dict[str, Any]) -> None:
    tag = f"{s['id']}:0:0"
    send_buttons(tr, str(s.get("error") or errors.MESSAGES["generic"][conv.lang]),
                 [(f"retry:{tag}", t("btn_retry", conv.lang)), (f"stop:{tag}", t("btn_stop", conv.lang))])


def _send_report(conv: Conv, tr: Transport, s: dict[str, Any]) -> None:
    if not s.get("diagnosis"):
        return
    try:
        from ..render import report_pdf

        d = engine.session_dir(s["id"])
        out = report_pdf.build(engine.report(s["id"]), s, d, d / "report.pdf")
    except Exception as e:
        log.warning("whatsapp report failed: %s", errors.detail(e))
        return
    send_document(tr, out, f"tukang-copilot-{s['id']}.pdf", t("report_caption", conv.lang))


def _send_exhausted(conv: Conv, tr: Transport, s: dict[str, Any]) -> None:
    url = handoff.maps_url(handoff.maps_query(s))
    send_text(tr, "\n".join([str(s.get("stop_reason") or ""), "", t("workshop", conv.lang, url=url)]))
    _send_report(conv, tr, s)
    send_text(tr, t("erase_hint", conv.lang))
    conv.sid, conv.phase, conv.step = None, "idle", 0


def finish(conv: Conv, tr: Transport, s: dict[str, Any]) -> None:
    lines = [t("done", conv.lang)]
    done = str((s.get("plan") or {}).get("done_check") or "")
    if done:
        lines.append(f"{t('final_check', conv.lang)} {done}")
    lines += ["", t("new_hint", conv.lang), t("erase_hint", conv.lang)]
    send_text(tr, "\n".join(lines))
    _send_report(conv, tr, s)  # the last message: the PDF report
    conv.sid, conv.phase, conv.step = None, "idle", 0


def stop_guide(conv: Conv, tr: Transport, s: dict[str, Any]) -> None:
    url = handoff.maps_url(handoff.maps_query(s))
    send_text(tr, "\n".join([t("stopped", conv.lang), t("workshop", conv.lang, url=url), "", t("erase_hint", conv.lang)]))
    _send_report(conv, tr, s)
    conv.sid, conv.phase, conv.step = None, "idle", 0


def advance(conv: Conv, tr: Transport, s: dict[str, Any], prefix: str = "") -> None:
    steps = (s.get("plan") or {}).get("steps") or []
    conv.step += 1
    if conv.step > len(steps):
        if prefix:
            send_text(tr, prefix)
        finish(conv, tr, s)
    else:
        send_step(conv, tr, s, prefix)


def replan(conv: Conv, tr: Transport, report: str) -> None:
    sid = conv.sid or ""
    if _blocked(conv, tr, "followup"):
        return
    try:
        s = engine.replan(sid, report)
    except ValueError:
        send_step(conv, tr, engine.load(sid))
        return
    except Exception as e:  # Meta busy: the plan is unchanged, the owner can tap Problem again
        log.warning("whatsapp replan failed: %s", errors.detail(e))
        send_step(conv, tr, engine.load(sid), prefix=errors.friendly(e, conv.lang))
        return
    if s["status"] == "stopped":
        _send_red(conv, tr, str(s.get("stop_reason") or ""), s)
    elif s["status"] == "exhausted":
        _send_exhausted(conv, tr, s)
    elif s["status"] == "ready":
        conv.step = 1
        cause = str((s.get("plan") or {}).get("cause_title") or "")
        send_text(tr, t("replan", conv.lang, k=int(s.get("cause_index") or 0) + 1, cause=cause))
        send_step(conv, tr, s)


def on_button(conv: Conv, ev: Inbound, tr: Transport) -> None:
    parts = ev.button_id.split(":")
    action = parts[0] if parts else ""
    sid = parts[1] if len(parts) > 1 else ""
    if action == "retry" and conv.sid == sid and conv.phase == "error":
        if _blocked(conv, tr, "followup"):
            return
        try:
            engine.retry(sid)
        except ValueError:
            pass
        send_text(tr, t("working", conv.lang))
        engine.run(sid)
        present(conv, tr)
        return
    if action == "stop" and conv.sid == sid and conv.phase == "error":
        stop_guide(conv, tr, engine.load(sid))
        return
    if conv.phase != "guiding" or not conv.sid:
        send_text(tr, t("new_hint", conv.lang))
        return
    s = engine.load(conv.sid)
    current = f"{conv.sid}:{int(s.get('cause_index') or 0)}:{conv.step}"
    if ":".join(parts[1:]) != current:
        send_step(conv, tr, s, prefix=t("stale", conv.lang))
        return
    if action == "done":
        advance(conv, tr, s)
    elif action == "problem":
        replan(conv, tr, "")
    elif action == "stop":
        stop_guide(conv, tr, s)


def on_guiding(conv: Conv, ev: Inbound, tr: Transport) -> None:
    sid = conv.sid or ""
    s = engine.load(sid)
    if ev.kind == "image":
        if _blocked(conv, tr, "followup"):
            return
        p = _fetch(conv, ev, tr, MAX_PHOTO, "check", IMAGE_EXT)
        if p is None:
            return
        try:
            res = engine.check_step(sid, conv.step, p)
        except engine.LimitReached:
            send_step(conv, tr, s, prefix=t("limit", conv.lang))
            return
        except ValueError:
            send_step(conv, tr, s)
            return
        except OSError:
            send_text(tr, t("bad_photo", conv.lang))
            return
        except Exception as e:
            log.warning("whatsapp step check failed: %s", errors.detail(e))
            send_step(conv, tr, s, prefix=errors.friendly(e, conv.lang))
            return
        finally:
            p.unlink(missing_ok=True)
        s = engine.load(sid)
        if res.get("passed"):
            advance(conv, tr, s, prefix="✅ " + str(res.get("observation") or ""))
        else:
            msg = ["❌ " + str(res.get("observation") or "")]
            if res.get("correction"):
                msg.append("👉 " + str(res["correction"]))
            msg.append(str(res.get("escalate_hint") or t("check_fail_hint", conv.lang)))
            send_step(conv, tr, s, prefix="\n".join(msg))
        return
    if ev.kind == "audio":
        if _blocked(conv, tr, "followup"):
            return
        p = _fetch(conv, ev, tr, 2 * 1024 * 1024, "cmd", AUDIO_EXT)
        if p is None:
            return
        try:
            heard = engine.voice_command(sid, "", p)
        except ValueError:
            send_text(tr, t("bad_audio", conv.lang))
            return
        except Exception as e:
            send_step(conv, tr, s, prefix=errors.friendly(e, conv.lang))
            return
        finally:
            p.unlink(missing_ok=True)
        _command(conv, tr, s, heard.get("command"), str(heard.get("text") or ""), voice=True)
        return
    text = ev.text.strip()
    cmd = parse_command(text, conv.lang)
    if cmd is None and not safety.check_text(text, s["lang"]).allowed:
        cmd = "broken"  # engine.replan runs the same text gate first and stops the guide
    _command(conv, tr, s, cmd, text)


def _command(conv: Conv, tr: Transport, s: dict[str, Any], cmd: str | None, text: str, voice: bool = False) -> None:
    if cmd == "next":
        advance(conv, tr, s)
    elif cmd == "back":
        conv.step = max(1, conv.step - 1)
        send_step(conv, tr, s)
    elif cmd == "repeat":
        send_step(conv, tr, s)
    elif cmd == "check":
        send_text(tr, t("ask_photo_check", conv.lang))
    elif cmd == "broken":
        replan(conv, tr, "" if voice else text)
    elif cmd == "stop":
        stop_guide(conv, tr, s)
    else:
        send_step(conv, tr, s, prefix=t("voice_unknown" if voice else "not_understood", conv.lang))


def on_answer(conv: Conv, ev: Inbound, tr: Transport) -> None:
    sid = conv.sid or ""
    s = engine.load(sid)
    text = ev.text.strip() if ev.kind == "text" else ""
    if ev.kind == "audio":
        if _blocked(conv, tr, "followup"):
            return
        p = _fetch(conv, ev, tr, MAX_AUDIO, "answer", AUDIO_EXT)
        if p is None:
            return
        try:
            text = str(engine.voice_command(sid, "", p).get("text") or "")
        except Exception:
            text = ""
        finally:
            p.unlink(missing_ok=True)
    if not text:
        send_text(tr, t("answer_first", conv.lang) + "\n❓ " + str(s.get("question") or ""))
        return
    if _blocked(conv, tr, "followup"):
        return
    try:
        engine.answer(sid, text)
    except ValueError:
        present(conv, tr)
        return
    send_text(tr, t("working", conv.lang))
    engine.run(sid)
    present(conv, tr)


def erase(conv: Conv, tr: Transport) -> None:
    """Same as the app's "Delete my photos now": the repair folder and any pending media go at once."""
    for sid in {x for x in (conv.sid, conv.last_sid) if x}:
        track.forget(sid)
        engine.delete(sid)
    _clear_pending(conv)
    shutil.rmtree(conv_dir(conv.key), ignore_errors=True)  # pending media and anything the simulator kept
    conv.sid = conv.last_sid = None
    conv.phase, conv.step = "idle", 0
    send_text(tr, t("erased", conv.lang))


# --- plumbing
def _blocked(conv: Conv, tr: Transport, bucket: str) -> bool:
    """Live mode: the web app's abuse guard, keyed on the phone number (hashed) instead of the IP."""
    if not guard.active():
        return False
    try:
        guard.check_budget()
        guard.check_rate(f"wa:{conv.key}", bucket=bucket)
    except guard.Blocked as b:
        send_text(tr, guard.message(b.kind, conv.lang))
        return True
    return False


def _clear_pending(conv: Conv) -> None:
    for p in conv.photos:
        p.unlink(missing_ok=True)
    if conv.audio is not None:
        conv.audio.unlink(missing_ok=True)
    conv.photos, conv.audio, conv.texts = [], None, []
    conv.ready_at = 0.0


def _fetch(conv: Conv, ev: Inbound, tr: Transport, limit: int, stem: str, exts: dict[str, str]) -> Path | None:
    ext = exts.get(_base_mime(ev.mime))
    if ext is None:
        send_text(tr, t("unsupported", conv.lang))
        return None
    d = conv_dir(conv.key) / "pending"
    d.mkdir(parents=True, exist_ok=True)
    dest = d / f"{stem}_{int(time.time() * 1000) % 10**9}{ext}"
    try:
        return tr.fetch(ev.media_id, limit, dest)
    except MediaTooBig:
        dest.unlink(missing_ok=True)
        send_text(tr, t("too_big", conv.lang))
    except Exception as e:
        dest.unlink(missing_ok=True)
        log.warning("whatsapp media download for %s failed: %s", mask(conv.sender), errors.detail(e))
        send_text(tr, t("media_failed", conv.lang))
    return None


def _readable_image(p: Path) -> bool:
    try:
        with Image.open(p) as im:
            im.verify()
        return True
    except Exception:
        return False


# --- HTTP
@router.get("/webhooks/whatsapp")
def verify(request: Request) -> PlainTextResponse:
    """Meta calls this once when the Callback URL is saved: echo hub.challenge when the verify token matches."""
    if not enabled():
        raise HTTPException(404)
    q = request.query_params
    token = q.get("hub.verify_token") or ""
    if q.get("hub.mode") == "subscribe" and hmac.compare_digest(token.encode(), settings.wa_verify_token.encode()):
        return PlainTextResponse(q.get("hub.challenge") or "")
    raise HTTPException(403, "verification failed")


@router.post("/webhooks/whatsapp")
async def receive(request: Request) -> dict[str, Any]:
    """One webhook delivery. Answer 200 fast (Meta retries slow or failed deliveries); the work runs on a queue."""
    if not enabled():
        raise HTTPException(404)
    body = await request.body()
    if len(body) > MAX_BODY:
        raise HTTPException(413, "payload too large")
    if not signature_ok(body, request.headers.get("x-hub-signature-256"), settings.wa_app_secret):
        raise HTTPException(403, "bad signature")
    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise HTTPException(400, "not json")
    events = parse_webhook(data, settings.wa_phone_number_id)
    n = dispatch(events, GraphTransport)
    return {"ok": True, "queued": n}
