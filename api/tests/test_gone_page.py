"""An expired or erased guide link opens a page in the reader's language, not raw JSON; pages answer HEAD."""
from fastapi.testclient import TestClient

from api.main import app

c = TestClient(app)


def test_unknown_guide_is_a_friendly_page_not_json() -> None:
    r = c.get("/guide/abcdef123456", headers={"Accept-Language": "id-ID,id;q=0.9"})
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("text/html")
    assert "Panduan ini sudah tidak ada" in r.text and "24 jam" in r.text
    assert "detail" not in r.text and 'href="/?lang=id"' in r.text
    assert r.headers.get("cache-control") == "no-store"


def test_gone_page_follows_the_language() -> None:
    assert "This guide is gone" in c.get("/guide/x1", headers={"Accept-Language": "en-US,en"}).text
    assert "Pandhuan iki wis ora ana" in c.get("/guide/x1", headers={"Accept-Language": "en-US,jv;q=0.5"}).text
    assert "Panduan ini sudah tidak ada" in c.get("/guide/x1", headers={"Accept-Language": "de-DE,id;q=0.4"}).text
    assert "This guide is gone" in c.get("/guide/x1?lang=en", headers={"Accept-Language": "id-ID"}).text
    page = c.get("/guide/x1?lang=jv").text
    assert '<html lang="jv">' in page and 'aria-current="true">JV<' in page


def test_gone_page_escapes_the_link_id() -> None:
    r = c.get('/guide/"><img src=x onerror=alert(1)>')
    assert r.status_code == 404 and "guide-gone" in r.text
    assert "<img src=x" not in r.text and "onerror=alert(1)>" not in r.text


def test_erased_repair_link_shows_the_gone_page(samples) -> None:
    r = c.post("/api/sessions", data={"language": "en", "sample": "faucet"})
    sid, tok = r.json()["id"], r.json()["owner_token"]
    assert c.get(f"/guide/{sid}").status_code == 200
    assert c.delete(f"/api/sessions/{sid}", headers={"X-Owner-Token": tok}).status_code == 200
    g = c.get(f"/guide/{sid}?lang=en")
    assert g.status_code == 404 and "This guide is gone" in g.text


def test_pages_answer_head() -> None:
    assert c.head("/").status_code == 200
    assert c.head("/guide/nothing-here").status_code == 404
