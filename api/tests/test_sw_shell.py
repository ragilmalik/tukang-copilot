from pathlib import Path

WEB = Path(__file__).resolve().parents[2] / "web"


def test_service_worker_exists_and_has_no_em_dash():
    text = (WEB / "sw.js").read_text(encoding="utf-8")
    assert "fetch" in text
    assert "\u2014" not in text
