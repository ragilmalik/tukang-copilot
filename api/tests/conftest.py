"""Every test runs offline in MOCK mode with its own temp data folder. No key, no network, no cost."""
import os
import sys
from pathlib import Path

os.environ.setdefault("MOCK", "1")
os.environ.setdefault("NARRATION_VOICE", "0")  # no network TTS in tests
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _tmp_data(tmp_path, monkeypatch):
    from api.settings import settings

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "mock", True)
    monkeypatch.setattr(settings, "narration_voice", False)
    yield


@pytest.fixture
def samples(tmp_path):
    from api.pipeline import mock

    return mock.make_sample_photos(tmp_path / "samples")
