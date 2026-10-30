"""Runs the real web/app.js in jsdom against a live mock server (no browser needed).

Needs `node` and the `jsdom` npm package. Found via JSDOM_DIR (a folder holding node_modules/jsdom),
./node_modules, or /tmp/jd. Install once: `mkdir /tmp/jd && cd /tmp/jd && npm install jsdom`.
Skips cleanly when either is missing.
"""
import json
import os
import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).parent / "dom" / "dom_flow.mjs"


def _jsdom_dir() -> str | None:
    for d in (os.environ.get("JSDOM_DIR"), str(ROOT), "/tmp/jd"):
        if d and (Path(d) / "node_modules" / "jsdom").is_dir():
            return d
    return None


@pytest.fixture
def server():
    import uvicorn

    from api.main import app

    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    t = threading.Thread(target=srv.run, daemon=True); t.start()
    for _ in range(100):
        if srv.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    srv.should_exit = True; t.join(5)


def test_phone_ui_in_jsdom(server: str) -> None:
    jd = _jsdom_dir()
    if not shutil.which("node") or not jd:
        pytest.skip("node or jsdom not installed")
    env = {**os.environ, "JSDOM_DIR": jd, "NO_PROXY": "127.0.0.1,localhost"}
    p = subprocess.run(["node", str(SCRIPT), server], capture_output=True, text=True, timeout=110, env=env)
    out = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else "{}"
    res = json.loads(out)
    failed = [c for c in res.get("checks", []) if not c["ok"]]
    assert p.returncode == 0 and res.get("ok"), f"failed checks: {failed} stderr={p.stderr[:300]}"
    assert len(res["checks"]) >= 30
