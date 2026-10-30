"""Shopping links and WhatsApp share (api/shop.py + public session JSON)."""
from __future__ import annotations

import time
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from fastapi.testclient import TestClient

from api import shop
from api.main import app


def test_urls_are_encoded_and_bounded() -> None:
    u = shop.tokopedia_url("Busi NGK C7HSA & kabel <script>")
    assert u.startswith("https://www.tokopedia.com/search?q=")
    assert "<" not in u and " " not in u
    assert parse_qs(urlparse(u).query)["q"][0] == "Busi NGK C7HSA & kabel <script>"
    assert shop.shopee_url("x" * 500).count("x") == shop.MAX_NAME


def test_with_links_skips_blank_names_and_keeps_price() -> None:
    out = shop.with_links([{"name": "  Busi  ", "est_price_idr": 25000}, {"name": "   "}])
    assert len(out) == 1 and out[0]["name"] == "Busi" and out[0]["est_price_idr"] == 25000
    assert out[0]["shop_url"].endswith("q=Busi") and out[0]["shop_alt_url"].endswith("keyword=Busi")


def test_share_text_languages() -> None:
    t = shop.share_text("Motor susah hidup", [{"name": "Kunci busi"}], [{"name": "Busi", "est_price_idr": 25000}], "id")
    assert "Daftar belanja" in t and "- Busi (~Rp25.000)" in t and "Alat:" in t
    assert "Tools:" in shop.share_text("x", [{"name": "a"}], [], "en")
    assert unquote(shop.whatsapp_url("a b\nc")).endswith("a b\nc")


def test_session_json_carries_links() -> None:
    import io

    from PIL import Image

    c = TestClient(app)
    b = io.BytesIO()
    Image.new("RGB", (800, 600), (200, 200, 200)).save(b, "JPEG")
    r = c.post("/api/sessions", data={"text": "kran wastafel menetes", "language": "id", "category": "plumbing"},
               files=[("photos", ("a.jpg", b.getvalue(), "image/jpeg"))])
    assert r.status_code == 200, r.text
    sid = r.json()["id"]
    s: dict[str, Any] = {}
    for _ in range(200):
        s = c.get(f"/api/sessions/{sid}").json()
        if s["status"] in {"ready", "error", "stopped"}:
            break
        time.sleep(0.05)
    assert s["status"] == "ready", s["status"]
    items = s["diagnosis"]["tools"] + s["diagnosis"]["parts"]
    assert items and all(p["shop_url"].startswith("https://www.tokopedia.com/search?q=") for p in items)
    assert s["whatsapp_url"].startswith("https://wa.me/?text=")
