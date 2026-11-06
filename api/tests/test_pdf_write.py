"""The report and workshop PDFs are written next to the repair and served from there (1.33.1 audit).

Up to 1.33.0 every GET of report.pdf rewrote the file in place: a second download that started while the first
was being sent (two people opening the guide's PDF link, a double tap) could be sent a half-written file. The
build also made the session folder again when it was missing, so an erase that landed while a PDF was being
drawn left a folder with the owner's report (and marked photo in it) on the server until the janitor's next
pass, 24 hours later. Now the PDF goes to a temp file that replaces the old one in one step, and a missing
folder means the repair is gone (404)."""
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from api.main import app
from api.pipeline import engine
from api.tests.owner_auth import OwnerClient

client = OwnerClient(app)


def _ready() -> str:
    import time

    sid: str = client.post("/api/sessions", data={"sample": "faucet", "language": "en"}).json()["id"]
    deadline = time.monotonic() + 60
    while engine.load(sid)["status"] not in ("ready", "error"):
        assert time.monotonic() < deadline
        time.sleep(0.02)
    return sid


def _whole_pdf(p: Path) -> bool:
    b = p.read_bytes()
    return b.startswith(b"%PDF") and b.rstrip().endswith(b"%%EOF")


@pytest.mark.parametrize("name", ["report.pdf", "workshop.pdf"])
def test_a_reader_during_a_rebuild_sees_the_whole_earlier_pdf(name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    sid = _ready()
    final = engine.session_dir(sid) / name
    assert client.get(f"/api/sessions/{sid}/{name}").status_code == 200 and _whole_pdf(final)
    real = Image.Image.save
    seen: list[bool] = []

    def save(self: Image.Image, fp: Any, *a: Any, **kw: Any) -> None:
        if str(a[0] if a else kw.get("format", "")).upper() == "PDF":
            Path(fp).write_bytes(b"%PDF-1.4\n% half written")  # the writer is part way through its file
            seen.append(_whole_pdf(final))  # what a second download would send right now
        real(self, fp, *a, **kw)

    monkeypatch.setattr(Image.Image, "save", save)
    r = client.get(f"/api/sessions/{sid}/{name}")
    assert r.status_code == 200 and r.content.startswith(b"%PDF")
    assert seen == [True]
    assert _whole_pdf(final)
    assert sorted(p.name for p in final.parent.glob("*.tmp*")) == []  # no temp file left behind


def test_an_erase_while_the_pdf_is_drawn_leaves_no_folder(monkeypatch: pytest.MonkeyPatch) -> None:
    from api.render import report_pdf

    sid = _ready()
    d = engine.session_dir(sid)
    real = report_pdf._Doc.finish

    def finish(self: Any) -> Any:
        pages = real(self)
        assert engine.delete(sid)  # the owner taps "Erase my photos now" while the pages are being drawn
        return pages

    monkeypatch.setattr(report_pdf._Doc, "finish", finish)
    r = client.get(f"/api/sessions/{sid}/report.pdf")
    assert r.status_code == 404
    assert not d.exists()
