"""Content-Security-Policy on every HTML page, HSTS only behind https, no inline script anywhere,
and the page landmarks axe-core asked for (status notes in an aside, disclaimer in the footer, /wa has a main and an h1)."""
import re

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.settings import ROOT

client = TestClient(app)
WEB = ROOT / "web"


@pytest.mark.parametrize("path", ["/", "/wa", "/guide/0123456789abcdef0123"])
def test_html_pages_carry_a_strict_csp(path: str):
    r = client.get(path)
    assert r.headers["content-type"].startswith("text/html"), path
    csp = r.headers.get("content-security-policy", "")
    script = re.search(r"script-src ([^;]+)", csp)
    assert script, csp
    assert script.group(1).strip() == "'self'", csp  # no 'unsafe-inline', no 'unsafe-eval', no outside hosts
    assert "object-src 'none'" in csp and "frame-ancestors 'self'" in csp and "base-uri 'self'" in csp


def test_json_answers_have_no_csp():
    r = client.get("/api/health")
    assert r.status_code == 200 and "content-security-policy" not in r.headers


def test_hsts_only_when_the_proxy_says_https():
    assert "strict-transport-security" not in client.get("/").headers
    r = client.get("/", headers={"x-forwarded-proto": "https"})
    assert r.headers["strict-transport-security"].startswith("max-age=")


@pytest.mark.parametrize("name", ["index.html", "guide.html", "gone.html", "wa.html"])
def test_no_inline_script_or_event_handler(name: str):
    html = (WEB / name).read_text(encoding="utf-8")
    for tag in re.findall(r"<script\b[^>]*>", html, re.I):
        assert "src=" in tag, (name, tag)
    assert all(not body.strip() for body in re.findall(r"<script\b[^>]*>(.*?)</script>", html, re.S | re.I)), name
    assert not re.search(r"\son[a-z]+\s*=", html, re.I), name


def test_wa_script_is_served_as_a_file():
    r = client.get("/static/wa.js")
    assert r.status_code == 200 and "javascript" in r.headers["content-type"]
    assert "wa-sim/send" in r.text


@pytest.mark.parametrize("name", ["index.html", "guide.html"])
def test_status_notes_and_disclaimer_sit_inside_landmarks(name: str):
    html = (WEB / name).read_text(encoding="utf-8")
    aside = re.search(r"<aside\b[^>]*>(.*?)</aside>", html, re.S)
    assert aside and 'id="offlineBar"' in aside.group(1) and 'id="modeBadge"' in aside.group(1)
    footer = re.search(r"<footer\b[^>]*>(.*?)</footer>", html, re.S)
    assert footer and 'id="disclaimer"' in footer.group(1)
    if name == "index.html":
        assert 'id="waSim"' in footer.group(1) and 'id="owBadge"' in aside.group(1)


def test_wa_page_has_a_main_and_one_h1():
    html = client.get("/wa").text
    assert len(re.findall(r"<main\b", html)) == 1
    assert len(re.findall(r"<h1\b", html)) == 1
