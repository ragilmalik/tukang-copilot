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
    monkeypatch.setattr(settings, "mock_pace_s", 0.0)  # no demo pacing in tests; test_streaming.py turns it on
    monkeypatch.setattr(settings, "demo_fallback", False)  # outage tests expect real errors; test_demo_fallback.py turns it on
    yield
    # a pipeline thread started by this test must not outlive its temp data folder (it would write into the next test's)
    import threading
    import time

    deadline = time.time() + 20
    for t in threading.enumerate():
        if t.name.startswith("session-"):
            t.join(max(0.0, deadline - time.time()))


@pytest.fixture
def samples(tmp_path):
    from api.pipeline import mock

    return mock.make_sample_photos(tmp_path / "samples")


# Browser-level tests (jsdom, real Chromium) take most of the suite's time. They carry the `slow` marker so the
# fast chunk runs with `-m "not slow"` and the slow chunk with `-m slow` (scripts/check_all.sh runs both).
SLOW_FILES = {"test_dom_jsdom.py", "test_playwright_smoke.py", "test_playwright_live.py", "test_playwright_replay.py", "test_playwright_audit5.py", "test_playwright_desk.py"}


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: browser-level test (jsdom or Chromium); run with -m slow")


def pytest_collection_modifyitems(config, items):
    for item in items:
        if item.path.name in SLOW_FILES:
            item.add_marker(pytest.mark.slow)
