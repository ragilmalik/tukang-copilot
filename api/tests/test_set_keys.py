"""scripts/set_keys.py: the one-step key swap writes .env correctly and never touches it without a key."""
import importlib.util
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(monkeypatch, env_file):
    monkeypatch.setenv("TC_ENV_FILE", str(env_file))
    spec = importlib.util.spec_from_file_location("set_keys", ROOT / "scripts" / "set_keys.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    calls: list[list[str]] = []

    def fake_call(cmd, cwd=None):
        calls.append(cmd)
        return 0

    monkeypatch.setattr(mod.subprocess, "call", fake_call)
    return mod, calls


def test_piped_keys_written_and_checked(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    mod, calls = _load(monkeypatch, env)
    monkeypatch.setattr(sys, "stdin", io.StringIO("meta-key-123\nbaseten-456\n"))
    assert mod.main(["--stdin"]) == 0
    text = env.read_text()
    for line in ("MODEL_API_KEY=meta-key-123", "MOCK=0", "BASETEN_API_KEY=baseten-456", "USE_OPEN_WEIGHTS=1"):
        assert line in text.splitlines(), line
    assert calls and calls[0][-1].endswith("check_keys.py")       # checks run straight after


def test_no_key_leaves_env_untouched(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    mod, calls = _load(monkeypatch, env)
    monkeypatch.setattr(sys, "stdin", io.StringIO("\n"))
    assert mod.main(["--stdin"]) == 1
    assert not env.exists() and not calls


def test_help_writes_nothing(monkeypatch, tmp_path, capsys):
    env = tmp_path / ".env"
    mod, calls = _load(monkeypatch, env)
    assert mod.main(["--help"]) == 0
    assert "one step to go live" in capsys.readouterr().out and not env.exists()
