"""v1.23: link previews (Open Graph card) for shared guides and the front page, gzip, favicon."""
import io
import time

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api.main import app
from api.pipeline import engine
from api.render import share_card
from api.tests.owner_auth import owner

client = TestClient(app)


def _done(sample, lang="en"):
    sid = client.post("/api/sessions", data={"sample": sample, "language": lang}).json()["id"]
    for _ in range(200):
        s = client.get(f"/api/sessions/{sid}").json()
        if s["status"] not in {"created", "running"}:
            return sid
        time.sleep(0.05)
    raise AssertionError("timeout")


@pytest.mark.parametrize("sample,lang", [("faucet", "en"), ("pump", "jv"), ("rice", "id"), ("motor", "id")])
def test_card_is_an_og_sized_png_for_every_scenario(sample, lang):
    sid = _done(sample, lang)
    r = client.get(f"/api/sessions/{sid}/card.png")
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    im = Image.open(io.BytesIO(r.content))
    assert im.size == (1200, 630) and len(r.content) < 600_000


def test_guide_page_carries_link_preview_tags():
    sid = _done("faucet")
    page = client.get(f"/guide/{sid}").text
    assert f'property="og:image" content="http://testserver/api/sessions/{sid}/card.png"' in page
    assert 'name="twitter:card" content="summary_large_image"' in page and 'property="og:title"' in page
    assert page.index("og:image") < page.index("</head>")


def test_card_never_uses_the_owners_words(tmp_path):
    sid = _done("faucet")
    s = engine.load(sid)
    a = share_card.build(dict(s, text="", transcript=""), engine.session_dir(sid), tmp_path / "a.png").read_bytes()
    b = share_card.build(dict(s, text="MY PRIVATE WORDS " * 20, transcript="secret"), engine.session_dir(sid), tmp_path / "b.png").read_bytes()
    assert a == b


def test_card_gone_after_erase():
    sid = _done("faucet")
    assert client.delete(f"/api/sessions/{sid}", headers=owner(sid)).status_code == 200
    assert client.get(f"/api/sessions/{sid}/card.png").status_code == 404


def test_front_page_preview_and_favicon():
    page = client.get("/").text
    assert 'property="og:image" content="http://testserver/og.png"' in page and 'rel="icon"' in page
    r = client.get("/og.png")
    assert r.status_code == 200 and Image.open(io.BytesIO(r.content)).size == (1200, 630)
    assert client.get("/static/icons/icon-192.png").status_code == 200


def test_static_files_are_gzipped_but_sse_is_not():
    r = client.get("/static/app.js", headers={"Accept-Encoding": "gzip"})
    assert r.headers.get("content-encoding") == "gzip"
    sid = _done("faucet")
    with client.stream("GET", f"/api/sessions/{sid}/events", headers={"Accept-Encoding": "gzip"}) as ev:
        assert ev.headers.get("content-encoding") is None and ev.headers["content-type"].startswith("text/event-stream")
