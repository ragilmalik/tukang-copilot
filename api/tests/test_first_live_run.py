"""scripts/first_live_run.py against the fake Meta server: report written, no key in it, plain exit codes."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import first_live_run as flr  # type: ignore[import-not-found]  # noqa: E402

from api.settings import settings  # noqa: E402
from api.testing import fake_meta  # noqa: E402


@pytest.fixture(autouse=True)
def _keep_settings(monkeypatch):
    for k in ("meta_api_key", "meta_api_base", "mock", "narration_voice", "demo_fallback", "data_dir"):
        monkeypatch.setattr(settings, k, getattr(settings, k))


def test_fake_rehearsal_writes_report_without_the_key(tmp_path, capsys):
    out = tmp_path / "LIVE_RUN.md"
    assert flr.main(["--fake", "--out", str(out)]) == 0
    md = out.read_text(encoding="utf-8")
    assert "REHEARSAL" in md and "not a real model" in md and "Status: **ready**" in md
    assert fake_meta.TEST_KEY not in md and fake_meta.TEST_KEY not in capsys.readouterr().out
    assert "fallback: none" in md and "| segment | done |" in md and "$0.0" in md
    assert "The AI asked" in md                                            # the motor sample asks first, the script answers


def test_faucet_draws_a_muse_image_diagram(tmp_path):
    out = tmp_path / "f.md"
    assert flr.main(["--fake", "--sample", "faucet", "--lang", "en", "--out", str(out)]) == 0
    assert "Diagrams drawn (Muse Image): 0" not in out.read_text(encoding="utf-8")


def test_no_key_says_run_set_keys_and_exits_2(tmp_path, capsys):
    settings.meta_api_key, settings.mock = "", False
    assert flr.main(["--out", str(tmp_path / "x.md")]) == 2
    assert "python scripts/set_keys.py" in capsys.readouterr().out and not (tmp_path / "x.md").exists()


def test_mock_on_says_so_and_exits_2(tmp_path, capsys):
    settings.meta_api_key, settings.mock = "sk-secret-123", True
    assert flr.main(["--out", str(tmp_path / "x.md")]) == 2
    out = capsys.readouterr().out
    assert "MOCK=1" in out and "sk-secret" not in out


def test_wrong_key_fails_in_plain_english(tmp_path, capsys, monkeypatch):
    base = fake_meta.serve_in_thread()
    settings.meta_api_base, settings.meta_api_key, settings.mock = base, "wrong-key-xyz", False
    assert flr.main(["--out", str(tmp_path / "x.md")]) == 1
    out = capsys.readouterr().out
    assert "did not accept the key" in out and "set_keys.py" in out and "wrong-key-xyz" not in out
