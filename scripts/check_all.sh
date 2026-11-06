#!/usr/bin/env bash
# One command for every check CI runs: lint, strict types, all tests (incl. browser smoke if Chromium exists).
set -u
cd "$(dirname "$0")/.."
[ -f .venv/bin/activate ] && . .venv/bin/activate
export MOCK=1 NARRATION_VOICE=0
fail=0
echo "== ruff";   python -m ruff check . || fail=1
echo "== mypy";   python -m mypy api || fail=1
echo "== mypy (whole repo: scripts, tests, docs/launch)"; python -m mypy . || fail=1
# Two chunks so each stays short (and fits tools with a ~2 min command limit): fast unit/API tests, then the
# browser-level `slow` ones (jsdom + Chromium; they skip cleanly when node/jsdom/Chromium are missing).
echo "== pytest (fast)"; python -m pytest api/tests -q -p no:warnings -m "not slow" 2>&1 | tail -3; [ "${PIPESTATUS[0]}" -eq 0 ] || fail=1
echo "== pytest (slow: jsdom + browser)"; python -m pytest api/tests -q -p no:warnings -m slow 2>&1 | tail -3; [ "${PIPESTATUS[0]}" -eq 0 ] || fail=1
[ $fail -eq 0 ] && echo "ALL CHECKS PASSED" || echo "SOME CHECKS FAILED"
exit $fail
