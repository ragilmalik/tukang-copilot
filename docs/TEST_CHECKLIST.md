# Test checklist

What I check before every release, in the order I run it. The automated part is one command each; the manual part is what a person does on a phone. Results for the current release are in [TEST_REPORT.md](TEST_REPORT.md) and [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md).

**Why a checklist:** the app has three languages, two modes (offline and live), a recorded demo, a WhatsApp channel and a static build. Each one can break on its own, so each gets its own line.

## A. Automated (run from the repo folder)

Set `export NO_PROXY=127.0.0.1,localhost` if a proxy is configured, and put Chromium on `PATH` for the browser tests.

- [ ] `python -m ruff check api scripts` is clean.
- [ ] `python -m mypy api --strict` reports no issues.
- [ ] `python -m pytest api/tests -q` has 0 failed. On a small machine run the non-browser files in groups and each `test_playwright_*.py` on its own.
- [ ] Offline smoke: `OFFLINE=1 PORT=8765 python app.py`, then `python scripts/smoke_e2e.py http://127.0.0.1:8765` ends with all checks passed.
- [ ] Live smoke (key set): the same smoke with the live server.
- [ ] `python scripts/record_replay.py --check` says the recorded demo is up to date.
- [ ] `python scripts/build_static.py --check` passes.
- [ ] Layout and motion: `test_playwright_layout.py` (nothing sticks out of its card at 360, 390, 430 and the laptop frame) and `test_playwright_motion.py` pass.
- [ ] `python scripts/check_keys.py` (key set) passes every required model.
- [ ] `python scripts/run_eval.py --from-json docs/eval/live-2026-11-05.json` renders [EVAL.md](EVAL.md) without model calls.
- [ ] No secret in the tree: `git grep -nE "sk-[A-Za-z0-9]{16}|ghp_[A-Za-z0-9]{20}"` finds nothing, and `.env` is not tracked (`test_env_not_tracked.py`).

## B. Manual, on a phone (390 x 844) in each language (id, jv, en)

- [ ] Home screen loads, language switch changes every label.
- [ ] 1-tap demo: question appears, answer No, result with numbered parts.
- [ ] Numbers on the photo don't overlap and point at the right parts.
- [ ] Safety level, causes with percentages, tools and parts with estimated prices.
- [ ] Steps: one per screen, 🔊 reads the step, hands-free mode reads each step.
- [ ] Camera check: dark sample photo gives ⚠️ with a clear retake hint; the plug-cap sample passes on the step it shows.
- [ ] Still broken: re-plan moves to the next cause and says so.
- [ ] Red stop: type "rem blong" (brake failure). A STOP card appears at once with who to call, and no steps.
- [ ] PDF report opens and matches the screen; workshop PDF prints one step per page.
- [ ] Share report gives a read-only link; the shared page has no erase or outcome buttons.
- [ ] My garage lists the repair after "It works now".
- [ ] Erase now removes the repair.
- [ ] Back button and refresh in the middle of a repair don't lose it.
- [ ] Airplane mode: the recorded demo plays and is labelled as a recording.
- [ ] Screen changes slide briefly; with "reduce motion" on in the phone settings they switch at once. A tap during a slide still works.
- [ ] Hands-free mode on a 360 px phone: Back and Listen are square icon buttons, Next fits inside the step card.
- [ ] On a phone under 400 px wide the header shows "ID / JV / EN" next to the full app name, and the pill opens the language list.
- [ ] Pull down during a repair: the page does not reload. On the first screen pull-to-refresh still works.

## C. Manual, on a laptop (1280 x 800)

- [ ] The app sits in a phone frame with the side panel, QR code and demo button.
- [ ] `/wa` simulator: with `WA_SIM=1` a full chat repair works; without it the page says the simulator is off.
- [ ] `/health` shows the right mode (`offline` or `live`).

## D. Media, before publishing

- [ ] Demo video is under 3:00, captions readable, no stale offline badge, voice clear.
- [ ] Vertical clip plays on a phone, captions inside the safe area.
- [ ] Screenshots are sharp (2x), current version, from live answers.
- [ ] Sample photos show the "Sample photo (AI-generated)" tag.
