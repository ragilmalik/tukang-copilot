"""A repair whose picture files went missing on the server (disk trouble, a partial restore, a hand clean-up)
still opens everywhere: session, PDFs, share card, hand-off, report and the shared guide answer 200, never 500."""
import time

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.pipeline import engine

c = TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize("victim", ["parts.jpg", "photo1.jpg", "part_*.jpg", "diagram_*.png"])
def test_missing_pictures_never_break_a_page(victim: str) -> None:
    sid = c.post("/api/sessions", data={"sample": "faucet", "language": "en"}).json()["id"]
    deadline = time.monotonic() + 60
    while engine.load(sid)["status"] in ("created", "running") and time.monotonic() < deadline:
        time.sleep(0.02)
    for f in engine.session_dir(sid).glob(victim):
        f.unlink()
    for path in ("", "/report.pdf", "/workshop.pdf", "/card.png", "/handoff", "/report"):
        assert c.get(f"/api/sessions/{sid}{path}").status_code == 200, (victim, path)
    assert c.get(f"/guide/{sid}").status_code == 200


def test_a_corrupt_session_file_is_a_404_and_a_gone_page() -> None:
    sid = c.post("/api/sessions", data={"sample": "faucet", "language": "en"}).json()["id"]
    deadline = time.monotonic() + 60
    while engine.load(sid)["status"] in ("created", "running") and time.monotonic() < deadline:
        time.sleep(0.02)
    (engine.session_dir(sid) / "session.json").write_text('{"id": "', encoding="utf-8")
    assert c.get(f"/api/sessions/{sid}").status_code == 404
    assert c.get(f"/guide/{sid}").status_code == 404  # the friendly "this guide is gone" page
