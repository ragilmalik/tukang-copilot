"""A stand-in WhatsApp Cloud API (Graph API) server, built from the request and response shapes on
developers.facebook.com (docs/WHATSAPP.md lists the pages). It lets the REAL channel code (api/channels/whatsapp.py:
httpx calls, multipart upload, two-step media download, payload limits) run end to end with no WhatsApp number.

    POST /<ver>/<PHONE_NUMBER_ID>/messages   send a message (checked: messaging_product, to, type, per-type shape,
                                             reply buttons <= 3, titles <= 20, body <= 1024, caption <= 1024)
    POST /<ver>/<PHONE_NUMBER_ID>/media      upload (multipart: messaging_product=whatsapp, file) -> {"id"}
    GET  /<ver>/<MEDIA_ID>                   media URL + mime_type + file_size + sha256
    GET  /download/<MEDIA_ID>                the bytes (Bearer token required, like lookaside.fbsbx.com)

Every call needs `Authorization: Bearer <TOKEN>` (401 otherwise). Also: webhook payload builders and sign()
for tests, shaped like the examples on the webhook reference pages.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import threading
import time
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

TOKEN = "test-wa-token"
PHONE_ID = "106540352242922"
VERSION = "v26.0"
WABA_ID = "102290129340398"

app = FastAPI(title="fake Graph API")
_lock = threading.Lock()
sent: list[dict[str, Any]] = []
uploads: dict[str, dict[str, Any]] = {}
media: dict[str, dict[str, Any]] = {}  # inbound media (what WhatsApp users "sent")
calls: list[str] = []
base_url = ""


def reset() -> None:
    with _lock:
        sent.clear()
        uploads.clear()
        media.clear()
        calls.clear()


def add_media(data: bytes, mime: str) -> str:
    """Register a file a WhatsApp user sent; returns its media id for the webhook payload."""
    mid = str(10**15 + len(media) + int(uuid.uuid4().int % 10**9))
    with _lock:
        media[mid] = {"data": data, "mime": mime}
    return mid


def _auth_ok(request: Request) -> bool:
    return request.headers.get("authorization") == f"Bearer {TOKEN}"


def _err(status: int, msg: str, code: int = 100) -> JSONResponse:
    return JSONResponse({"error": {"message": msg, "type": "OAuthException", "code": code, "fbtrace_id": "fake"}}, status_code=status)


def _check_message(p: dict[str, Any]) -> str | None:
    if p.get("messaging_product") != "whatsapp":
        return "messaging_product must be whatsapp"
    if not p.get("to"):
        return "to is required"
    typ = p.get("type")
    body = p.get(str(typ))
    if not isinstance(body, dict):
        return f"missing {typ} object"
    if typ == "text":
        if not body.get("body") or len(body["body"]) > 4096:
            return "text.body required, max 4096"
    elif typ in {"image", "document", "audio", "video"}:
        if not (body.get("id") or body.get("link")):
            return f"{typ}.id or link required"
        if body.get("id") and body["id"] not in uploads:
            return "unknown media id"
        if len(body.get("caption") or "") > 1024:
            return "caption max 1024"
    elif typ == "interactive":
        if body.get("type") != "button":
            return "only button interactive messages are faked"
        if not (body.get("body") or {}).get("text") or len(body["body"]["text"]) > 1024:
            return "interactive body.text required, max 1024"
        if len((body.get("footer") or {}).get("text") or "") > 60:
            return "footer max 60"
        btns = (body.get("action") or {}).get("buttons") or []
        if not 1 <= len(btns) <= 3:
            return "1 to 3 reply buttons"
        titles = [((b.get("reply") or {}).get("title") or "") for b in btns]
        ids = [((b.get("reply") or {}).get("id") or "") for b in btns]
        if any(not x or len(x) > 20 for x in titles) or len(set(titles)) != len(titles):
            return "button titles required, unique, max 20"
        if any(not x or len(x) > 256 for x in ids):
            return "button ids required, max 256"
        hdr = body.get("header")
        if hdr and hdr.get("type") == "image" and (hdr.get("image") or {}).get("id") not in uploads:
            return "unknown header media id"
    else:
        return f"type {typ} not faked"
    return None


@app.post("/{ver}/{phone_id}/messages")
async def messages(ver: str, phone_id: str, request: Request) -> Response:
    calls.append(f"POST messages {ver}")
    if not _auth_ok(request):
        return _err(401, "Invalid OAuth access token.", 190)
    if phone_id != PHONE_ID:
        return _err(400, "Unsupported post request.")
    p = await request.json()
    problem = _check_message(p)
    if problem:
        return _err(400, problem)
    wamid = "wamid.fake" + uuid.uuid4().hex[:16]
    with _lock:
        sent.append(p)
    return JSONResponse({"messaging_product": "whatsapp", "contacts": [{"input": p["to"], "wa_id": p["to"]}], "messages": [{"id": wamid}]})


@app.post("/{ver}/{phone_id}/media")
async def upload(ver: str, phone_id: str, request: Request) -> Response:
    calls.append(f"POST media {ver}")
    if not _auth_ok(request):
        return _err(401, "Invalid OAuth access token.", 190)
    form = await request.form()
    f = form.get("file")
    if form.get("messaging_product") != "whatsapp" or f is None or isinstance(f, str):
        return _err(400, "messaging_product=whatsapp and file are required")
    data = await f.read()
    mid = str(2 * 10**15 + len(uploads))
    with _lock:
        uploads[mid] = {"data": data, "mime": f.content_type or "", "filename": f.filename or ""}
    return JSONResponse({"id": mid})


@app.get("/download/{mid}")
def download(mid: str, request: Request) -> Response:
    calls.append("GET download")
    if not _auth_ok(request):
        return _err(401, "Invalid OAuth access token.", 190)
    m = media.get(mid)
    if m is None:
        return Response(status_code=404)
    return Response(m["data"], media_type=m["mime"].split(";")[0])


@app.get("/{ver}/{mid}")
def media_url(ver: str, mid: str, request: Request) -> Response:
    calls.append(f"GET media {ver}")
    if not _auth_ok(request):
        return _err(401, "Invalid OAuth access token.", 190)
    m = media.get(mid)
    if m is None:
        return _err(404, "media not found")
    return JSONResponse({"messaging_product": "whatsapp", "url": f"{base_url}/download/{mid}", "mime_type": m["mime"],
                         "sha256": base64.b64encode(hashlib.sha256(m["data"]).digest()).decode(),
                         "file_size": str(len(m["data"])), "id": mid})


def serve_in_thread(port: int = 0) -> str:
    """Start on a background thread; returns the base URL (no version). Adds 127.0.0.1 to NO_PROXY."""
    global base_url
    import os
    import socket

    import uvicorn

    for var in ("NO_PROXY", "no_proxy"):
        os.environ[var] = ",".join(filter(None, [os.environ.get(var, ""), "127.0.0.1", "localhost"]))
    if not port:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True, name="fake-graph").start()
    for _ in range(200):
        if server.started:
            break
        time.sleep(0.05)
    base_url = f"http://127.0.0.1:{port}"
    return base_url


# --- webhook payloads (for tests)
def webhook(messages: list[dict[str, Any]], phone_number_id: str = PHONE_ID) -> dict[str, Any]:
    return {"object": "whatsapp_business_account", "entry": [{"id": WABA_ID, "changes": [{"value": {
        "messaging_product": "whatsapp", "metadata": {"display_phone_number": "15550783881", "phone_number_id": phone_number_id},
        "contacts": [{"profile": {"name": "Test Owner"}, "wa_id": messages[0]["from"] if messages else ""}],
        "messages": messages}, "field": "messages"}]}]}


def _msg(sender: str, typ: str, body: dict[str, Any], wamid: str | None = None) -> dict[str, Any]:
    return {"from": sender, "id": wamid or "wamid." + uuid.uuid4().hex, "timestamp": str(int(time.time())), "type": typ, typ: body}


def text_msg(sender: str, text: str, wamid: str | None = None) -> dict[str, Any]:
    return _msg(sender, "text", {"body": text}, wamid)


def image_msg(sender: str, media_id: str, caption: str = "", wamid: str | None = None, mime: str = "image/jpeg") -> dict[str, Any]:
    return _msg(sender, "image", {"mime_type": mime, "sha256": "x", "id": media_id, **({"caption": caption} if caption else {})}, wamid)


def audio_msg(sender: str, media_id: str, wamid: str | None = None) -> dict[str, Any]:
    return _msg(sender, "audio", {"mime_type": "audio/ogg; codecs=opus", "sha256": "x", "id": media_id, "voice": True}, wamid)


def button_msg(sender: str, button_id: str, title: str = "", wamid: str | None = None) -> dict[str, Any]:
    return _msg(sender, "interactive", {"type": "button_reply", "button_reply": {"id": button_id, "title": title}}, wamid)


def status_update(recipient: str) -> dict[str, Any]:
    """A delivery status webhook (no messages): the channel must ignore it."""
    return {"object": "whatsapp_business_account", "entry": [{"id": WABA_ID, "changes": [{"value": {
        "messaging_product": "whatsapp", "metadata": {"display_phone_number": "15550783881", "phone_number_id": PHONE_ID},
        "statuses": [{"id": "wamid.x", "status": "delivered", "timestamp": "1", "recipient_id": recipient}]}, "field": "messages"}]}]}


def sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def encode(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload).encode()
