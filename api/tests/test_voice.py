"""Hands-free voice commands: parse_command in id / jv / en, the JavaScript mirror gives the same answers,
POST /api/sessions/{id}/command (text and push-to-talk audio, mock and the real ASR path), and the web wiring."""
import io
import json
import re
import shutil
import subprocess
import time
import wave
from pathlib import Path
from typing import Any

import pytest

from api.main import app
from api.settings import settings
from api.voice import COMMANDS, WORDS, parse_command
from api.tests.owner_auth import OwnerClient

client = OwnerClient(app)
WEB = Path(__file__).resolve().parents[2] / "web"
JS = (WEB / "app.js").read_text(encoding="utf-8")

CASES = [
    # Bahasa Indonesia
    ("lanjut", "id", "next"), ("oke, terus", "id", "next"), ("langkah berikutnya", "id", "next"), ("Sudah!", "id", "next"),
    ("kembali", "id", "back"), ("mundur satu", "id", "back"), ("ulangi dong", "id", "repeat"), ("sekali lagi", "id", "repeat"),
    ("cek", "id", "check"), ("tolong periksa", "id", "check"), ("masih rusak", "id", "broken"), ("tetap mati nih", "id", "broken"),
    ("berhenti", "id", "stop"), ("jangan lanjut", "id", None), ("halo apa kabar", "id", None),
    # Basa Jawa
    ("terus", "jv", "next"), ("wis, sabanjure", "jv", "next"), ("bali", "jv", "back"), ("baleni", "jv", "repeat"),
    ("sepisan maneh", "jv", "repeat"), ("priksa", "jv", "check"), ("isih rusak", "jv", "broken"), ("isih netes lho", "jv", "broken"),
    ("mandheg", "jv", "stop"), ("wis cukup", "jv", "stop"), ("ojo terus", "jv", None), ("masih rusak", "jv", "broken"),
    # English
    ("next", "en", "next"), ("Next step please.", "en", "next"), ("go back", "en", "back"), ("previous", "en", "back"),
    ("repeat that", "en", "repeat"), ("say that again", "en", "repeat"), ("check", "en", "check"), ("take a photo", "en", "check"),
    ("it's still broken", "en", "broken"), ("didn't work", "en", "broken"), ("stop", "en", "stop"), ("don't stop", "en", None),
    ("what a nice day", "en", None), ("lanjut", "en", "next"),
    # edge cases
    ("", "id", None), ("   ", "en", None), ("!!!", "jv", None), ("LANJUT", "xx", "next"),
]


WAIT_S = 60  # seconds a repair may take: generous, CI runners are slow and earlier repairs can still hold the worker pool


@pytest.mark.parametrize("text,lang,want", CASES)
def test_parse_command(text, lang, want):
    assert parse_command(text, lang) == want


def test_every_language_has_every_command():
    for lg in ("id", "jv", "en"):
        assert set(WORDS[lg]) == set(COMMANDS)
        for words in WORDS[lg].values():
            assert words and all(w == w.lower().strip() for w in words)


def test_js_word_lists_match_python():
    m = re.search(r"/\* VOICE_WORDS:start \*/const VOICE_WORDS = (.*?);/\* VOICE_WORDS:end \*/", JS)
    assert m
    assert json.loads(m.group(1)) == WORDS


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_js_parse_command_matches_python():
    start = JS.index("/* VOICE_WORDS:start */")
    end = JS.index("\n}\n", JS.index("function parseCommand")) + 3
    src = JS[start:end] + "\nconst cases = " + json.dumps([[t, lg] for t, lg, _ in CASES]) + ";\n" \
        + "console.log(JSON.stringify(cases.map(([t, l]) => parseCommand(t, l))));\n"
    out = subprocess.run(["node", "-e", src], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout) == [w for _, _, w in CASES]


def _ready(sample: str = "pump", lang: str = "id") -> dict[str, Any]:
    sid = client.post("/api/sessions", data={"sample": sample, "language": lang}).json()["id"]
    deadline = time.monotonic() + WAIT_S
    while time.monotonic() < deadline:
        s: dict[str, Any] = client.get(f"/api/sessions/{sid}").json()
        if s["status"] not in ("created", "running"):
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def _wav(seconds: float = 1.0) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
        w.writeframes(b"\0\0" * int(16000 * seconds))
    return buf.getvalue()


def test_command_endpoint_text():
    s = _ready("pump", "jv")
    j = client.post(f"/api/sessions/{s['id']}/command", data={"text": "isih rusak"}).json()
    assert j == {"text": "isih rusak", "command": "broken", "lang": "jv"}
    assert client.post(f"/api/sessions/{s['id']}/command", data={"text": "piye kabare"}).json()["command"] is None


@pytest.mark.parametrize("lang,word", [("id", "lanjut"), ("jv", "terus"), ("en", "next")])
def test_command_endpoint_audio_mock(lang, word):
    s = _ready("faucet", lang)
    r = client.post(f"/api/sessions/{s['id']}/command", files={"audio": ("c.wav", _wav(), "audio/wav")})
    assert r.status_code == 200, r.text
    assert r.json() == {"text": word, "command": "next", "lang": lang}


def test_command_endpoint_errors():
    s = _ready("faucet")
    assert client.post("/api/sessions/nope/command", data={"text": "lanjut"}).status_code == 404
    assert client.post(f"/api/sessions/{s['id']}/command").status_code == 400
    assert client.post(f"/api/sessions/{s['id']}/command", data={"text": "x" * 300}).status_code == 400
    assert client.post(f"/api/sessions/{s['id']}/command", files={"audio": ("c.wav", b"not audio", "audio/wav")}).status_code == 400
    assert client.post(f"/api/sessions/{s['id']}/command", files={"audio": ("c.exe", _wav(), "audio/wav")}).status_code == 400
    long = client.post(f"/api/sessions/{s['id']}/command", files={"audio": ("c.wav", _wav(16), "audio/wav")})
    assert long.status_code == 400 and "15" in long.json()["detail"]


def test_command_audio_live_path(monkeypatch):
    from api.pipeline import mock
    from api.tests.doubles import fake_meta

    base = fake_meta.serve_in_thread()
    s = _ready("faucet", "id")
    monkeypatch.setattr(settings, "mock", False)
    monkeypatch.setattr(settings, "meta_api_key", fake_meta.TEST_KEY)
    monkeypatch.setattr(settings, "meta_api_base", base)
    fake_meta.CALLS.clear()
    j = client.post(f"/api/sessions/{s['id']}/command", files={"audio": ("c.wav", _wav(), "audio/wav")}).json()
    assert j["text"] == mock.TRANSCRIPTS["id"] and j["command"] == parse_command(mock.TRANSCRIPTS["id"], "id")
    assert any(c["endpoint"] == "asr" for c in fake_meta.CALLS)


def test_web_voice_wiring():
    for page in ("index.html", "guide.html"):
        html = (WEB / page).read_text(encoding="utf-8")
        assert 'id="voiceBar"' in html and 'id="voiceDot"' in html and 'id="pttBtn"' in html
    assert "webkitSpeechRecognition" in JS and '"jv-ID"' in JS and "/command`" in JS
    jv = JS[JS.index("T.jv = Object.assign"):]
    assert "Prentah swara" in jv and "isih rusak" in jv
