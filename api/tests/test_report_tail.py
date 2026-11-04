"""The PDF report never prints a page that holds only the end of the disclaimer.

Seen on 1.29.6: the Basa Jawa report after "Still broken" had a page 3 of 4 with one line on it
("tegangan dhuwur, celuk teknisi."), the rest of the page blank, then the mechanic brief.
"""
import time

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from api.main import app
from api.pipeline import engine
from api.render import report_pdf

client = TestClient(app)


def _wait(sid, want=("ready", "needs_answer", "stopped", "error")):
    for _ in range(300):
        s = client.get(f"/api/sessions/{sid}").json()
        if s["status"] in want:
            return s
        time.sleep(0.05)
    raise AssertionError("timeout")


def _pages(monkeypatch, tmp_path, sid):
    seen: list[list[Image.Image]] = []
    real = report_pdf._Doc.finish

    def keep(self):
        pages = real(self)
        seen.append(list(pages))
        return pages
    monkeypatch.setattr(report_pdf._Doc, "finish", keep)
    session = engine.load(sid)
    # tests run without narration; on the server the voice stage is done too, which is one more "under the hood" line
    session.setdefault("stages", {}).setdefault("narrate", {})["status"] = "done"
    report_pdf.build(engine.report(sid), session, engine.session_dir(sid), tmp_path / "r.pdf")
    return seen[0]


def _inked_rows(page: Image.Image) -> int:
    """Rows with any dark pixel between the top strip and the footer rule."""
    body = page.convert("L").crop((0, 40, page.width, report_pdf.H - report_pdf.M - 30))
    dark = body.point(lambda v: 255 if v < 200 else 0)
    return sum(1 for y in range(body.height) if dark.crop((0, y, body.width, y + 1)).getbbox())


@pytest.mark.parametrize("lang,report", [("jv", "Wis tak coba, isih mati"), ("id", "Sudah dicoba, tetap mati"),
                                         ("en", "Tried it, still dead")])
def test_no_page_holds_only_the_disclaimer_tail(monkeypatch, tmp_path, lang, report):
    sid = client.post("/api/sessions", data={"sample": "motor", "language": lang}).json()["id"]
    if _wait(sid)["status"] == "needs_answer":
        client.post(f"/api/sessions/{sid}/answer", data={"text": "ya"})
        _wait(sid, ("ready",))
    assert client.post(f"/api/sessions/{sid}/replan", data={"report": report}).json()["status"] == "ready"
    pages = _pages(monkeypatch, tmp_path, sid)
    for i, page in enumerate(pages, 1):
        assert _inked_rows(page) > 200, f"page {i} of {len(pages)} is nearly empty"


def _filled_doc(lines_used: int):
    doc = report_pdf._Doc("footer", "Kaca")
    doc.y = report_pdf.H - report_pdf.M - 40 - lines_used
    return doc


def test_disclaimer_moves_with_the_last_list_lines_when_two_columns_do_not_fit():
    L = report_pdf.LABELS["jv"]
    hood = [f"- Tahap {i}: muse-spark-1.3" for i in range(9)]
    doc = _filled_doc(150)  # room for the heading and a line or two, not for nine lines in two columns
    report_pdf._hood_and_disclaimer(doc, L, hood)
    assert len(doc.pages) == 2
    last = doc.pages[-1]
    assert _inked_rows(last) > 60  # list lines and the disclaimer together, not the disclaimer alone


def test_short_room_puts_the_list_in_two_columns_on_the_same_page():
    L = report_pdf.LABELS["id"]
    hood = [f"- Tahap {i}: muse-spark-1.3" for i in range(9)]
    doc = _filled_doc(330)  # one column needs ~ 52 + 9*28 + disclaimer; two columns fit
    report_pdf._hood_and_disclaimer(doc, L, hood)
    assert len(doc.pages) == 1


def test_plenty_of_room_keeps_one_column():
    L = report_pdf.LABELS["en"]
    hood = [f"- Stage {i}: muse-spark-1.3" for i in range(9)]
    doc = report_pdf._Doc("footer", "Page")
    start = doc.y
    report_pdf._hood_and_disclaimer(doc, L, hood)
    assert doc.y - start > 9 * 28  # nine rows stacked
    ImageDraw.Draw(doc.pages[0])  # still drawable, no stray page
    assert len(doc.pages) == 1
