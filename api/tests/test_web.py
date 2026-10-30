"""Static checks on the phone web app (no browser needed)."""
import re
import shutil
import subprocess

import pytest

from api.settings import ROOT

WEB = ROOT / "web"
JS = (WEB / "app.js").read_text(encoding="utf-8")
INDEX = (WEB / "index.html").read_text(encoding="utf-8")


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_app_js_parses():
    assert subprocess.run(["node", "--check", str(WEB / "app.js")], capture_output=True).returncode == 0


def test_every_id_used_in_js_exists_in_index():
    used = set(re.findall(r'\$\("([A-Za-z]+)"\)', JS)) | set(re.findall(r'on\("([A-Za-z]+)"', JS))
    have = set(re.findall(r'id="([A-Za-z]+)"', INDEX))
    assert not (used - have), f"missing in index.html: {used - have}"


def test_every_ui_string_key_exists_in_all_languages():
    keys = set(re.findall(r'data-tp?="([A-Za-z]+)"', INDEX))
    for lang in ("id", "en"):
        m = re.search(lang + r": \{(.*?)\n  \},?\n", JS, re.S)
        assert m, lang
        block = m.group(1)
        missing = [k for k in keys if not re.search(r"\b" + k + r":", block)]
        assert not missing, (lang, missing)


def test_guide_page_is_read_only():
    g = (WEB / "guide.html").read_text(encoding="utf-8")
    assert "{{SID}}" in g and "stepPhoto" not in g and "stuckBtn" not in g


def test_no_inline_secrets():
    texts = [f for f in WEB.rglob("*") if f.is_file() and f.suffix in {".js", ".html", ".css", ".webmanifest"}]
    assert texts
    for f in texts:
        assert "MODEL_API_KEY" not in f.read_text(encoding="utf-8"), f


def test_accessibility_hooks_present():
    css = (WEB / "style.css").read_text(encoding="utf-8")
    assert "focus-visible" in css and "prefers-reduced-motion" in css and ".sr-only" in css
    for needle in ('id="progressStatus"', 'aria-live="polite"', 'role="alert"', 'aria-pressed="false"', 'id="stepPhotoLabel"'):
        assert needle in INDEX, needle
    assert 'lang === "jv" ? "jv"' in JS  # Javanese UI must not be tagged as Indonesian for screen readers
    assert "setAttribute(\"aria-pressed\"" in JS
