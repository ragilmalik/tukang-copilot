"""Static judge build in real Chromium, served by a plain file server under a sub-path (like GitHub Pages).

No backend runs: the test fails if the page asks the network for any /api/ URL or anything outside its folder.
"""
import functools
import http.server
import os
import sys
import threading
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
from api.tests.test_playwright_smoke import _chromium_path  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build_static  # type: ignore[import-not-found]  # noqa: E402


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):  # keep pytest output clean
        pass


@pytest.fixture
def site(tmp_path):
    build_static.build(tmp_path / "tukang-copilot")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(tmp_path)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    yield f"http://127.0.0.1:{srv.server_address[1]}/tukang-copilot/"
    srv.shutdown()


@pytest.mark.parametrize("size", [(390, 844), (1280, 800)])
def test_static_build_plays_recorded_demo_without_a_server(site, size):
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch(executable_path=_chromium_path(), args=["--no-proxy-server"])
        except Exception as e:  # no browser available in this environment
            pytest.skip(f"Chromium not available: {str(e).splitlines()[0]}")
        pg = b.new_page(viewport={"width": size[0], "height": size[1]})
        urls: list[str] = []
        errors: list[str] = []
        pg.on("request", lambda r: urls.append(r.url))
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(site)
        pg.select_option("#lang", "en")
        pg.wait_for_selector("#modeBadge:not(.hidden)", timeout=5000)
        assert "Recorded demo" in pg.inner_text("#modeBadge")               # labelled from the first second
        assert not pg.is_visible("#wakeNote")
        pg.click("#demoBtn")
        pg.wait_for_selector("#question:not(.hidden)", timeout=20000)
        pg.click("#quickAns button >> nth=0")
        pg.wait_for_selector("#result:not(.hidden)", timeout=20000)
        assert pg.inner_text("#dxObject").strip()
        assert pg.evaluate("document.getElementById('partsImg').naturalWidth") > 0
        for b2 in pg.locator("#preList input").all():
            b2.check()
        pg.click("#sampleGood")
        pg.wait_for_selector("#checkResult:not(.hidden)", timeout=10000)
        assert "Looks right" in pg.inner_text("#checkResult")
        assert "static/replay/report-en.pdf" in pg.get_attribute("#pdfBtn", "href")
        if size[0] >= 1024:
            pg.wait_for_selector("#qrBox svg", timeout=5000)
            assert "/tukang-copilot/" in pg.get_attribute("#qrBox", "aria-label")
        b.close()
    assert not [u for u in urls if "/api/" in u], "the static build called the API"
    assert not [u for u in urls if u.startswith("http") and not u.startswith(site)], [u for u in urls if not u.startswith(site)]
    assert not errors, errors
