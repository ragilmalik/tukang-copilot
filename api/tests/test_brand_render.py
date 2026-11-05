"""The PDF report, the workshop sheet and the share cards wear the app's look (Barlow, safety colours with the right
text colour on them), never draw empty boxes for a character Barlow lacks, and stay small enough for a WhatsApp preview."""
import io
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from api.main import app
from api.render import brand, report_pdf, share_card

client = TestClient(app)
WEB = Path(__file__).resolve().parents[2] / "web"


WAIT_S = 60  # seconds a repair may take: generous, CI runners are slow and earlier repairs can still hold the worker pool


def _done(sample: str, lang: str = "en") -> str:
    sid = str(client.post("/api/sessions", data={"sample": sample, "language": lang}).json()["id"])
    deadline = time.monotonic() + WAIT_S
    while time.monotonic() < deadline:
        if client.get(f"/api/sessions/{sid}").json()["status"] not in {"created", "running"}:
            return sid
        time.sleep(0.05)
    raise AssertionError("timeout")


def _near(px: object, rgb: tuple[int, int, int], tol: int = 18) -> bool:
    assert isinstance(px, tuple)
    return all(abs(int(a) - b) <= tol for a, b in zip(px[:3], rgb))


def test_bundled_fonts_are_barlow() -> None:
    assert brand.font("display", 40).getname()[0] == "Barlow Condensed ExtraBold"
    assert brand.font("body", 20).getname()[0] == "Barlow"
    assert (brand.FONTS / "OFL.txt").exists()


def test_missing_glyphs_fall_back_instead_of_empty_boxes() -> None:
    im = Image.new("RGB", (400, 60), "white")
    d = ImageDraw.Draw(im)
    assert brand.covered("a") and brand.covered("…") and not brand.covered("≥") and not brand.covered("✓")
    w = brand.draw(d, (5, 5), "≥ 2 ✓ →", "semi", 30, brand.INK)
    assert w == pytest.approx(brand.length(d, "≥ 2 ✓ →", "semi", 30)) and w > 40
    assert brand.wrap(d, "a " * 200, "body", 20, 300, 2)[-1].endswith("…")


def test_safety_plate_text_colour_follows_ansi() -> None:
    assert brand.LEVEL["amber"] == (brand.YELLOW, brand.INK)  # black on yellow, never white
    assert brand.LEVEL["red"][1] == brand.LEVEL["green"][1] == brand.WHITE


def test_report_has_the_dark_header_and_a_yellow_caution_plate(samples, tmp_path) -> None:
    sid = _done("motor")
    from api.pipeline import engine

    s = engine.load(sid)
    s["diagnosis"]["safety_level"] = "amber"
    out = report_pdf.build({**engine.report(sid), "safety_level": "amber"}, s, engine.session_dir(sid), tmp_path / "r.pdf")
    assert out.read_bytes().startswith(b"%PDF")
    doc = report_pdf._Doc("f", "p")
    doc.band("Repair report", "#x")
    assert _near(doc.im.getpixel((report_pdf.W // 2, 60)), brand.DARK)
    y0 = doc.y
    report_pdf._safety_plate(doc, "amber", report_pdf.LABELS["en"], "Fuel nearby")
    assert _near(doc.im.getpixel((report_pdf.W - report_pdf.M - 30, y0 + 20)), brand.YELLOW)


def test_report_steps_use_drawn_number_plates_not_bracket_text(monkeypatch, samples, tmp_path) -> None:
    seen: list[str] = []
    orig = report_pdf._Doc.text

    def spy(self, txt, *a, **k):
        seen.append(str(txt))
        return orig(self, txt, *a, **k)

    monkeypatch.setattr(report_pdf._Doc, "text", spy)
    sid = _done("faucet")
    assert client.get(f"/api/sessions/{sid}/report.pdf").status_code == 200
    assert not any(t.startswith(("[OK]", "[  ]")) for t in seen), [t for t in seen if t.startswith("[")]
    assert any(t == "Likely causes" for t in seen)


@pytest.mark.parametrize("lang", ["id", "jv", "en"])
def test_share_card_is_on_brand_and_light(samples, lang) -> None:
    sid = _done("pump", lang)
    r = client.get(f"/api/sessions/{sid}/card.png")
    assert r.status_code == 200 and len(r.content) < 300_000, len(r.content)
    im = Image.open(io.BytesIO(r.content)).convert("RGB")
    assert im.size == (1200, 630)
    assert _near(im.getpixel((1180, 140)), brand.BETON)  # concrete, not the old cream paper
    assert not _near(im.getpixel((1180, 140)), (255, 250, 244), 3)


def test_front_page_preview_is_the_new_look_and_light() -> None:
    data = (WEB / "og.png").read_bytes()
    assert len(data) < 300_000
    im = Image.open(io.BytesIO(data)).convert("RGB")
    assert im.size == (1200, 630) and _near(im.getpixel((1180, 140)), brand.BETON)
    assert all(not share_card.HOME_LINES[i].count("→") for i in range(len(share_card.HOME_LINES)))
