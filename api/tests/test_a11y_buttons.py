import re
from pathlib import Path

HTML = Path(__file__).resolve().parents[2] / "web" / "index.html"


def test_every_button_has_text_or_aria_label():
    html = HTML.read_text(encoding="utf-8")
    for m in re.finditer(r"<button([^>]*)>(.*?)</button>", html, re.S):
        attrs, inner = m.groups()
        text = re.sub(r"<[^>]+>", "", inner).strip()
        assert text or "aria-label" in attrs, attrs
