"""First live run: one real repair through the real Meta models, written up in docs/LIVE_RUN.md.

Run it once, right after `python scripts/set_keys.py` says ALL GOOD:

    python scripts/first_live_run.py                  # motorbike sample, Indonesian, writes docs/LIVE_RUN.md
    python scripts/first_live_run.py --sample faucet --lang en   # this sample also draws a Muse Image diagram
    python scripts/first_live_run.py --fake           # rehearsal against the built-in stand-in Meta server (free)

What it does, in order:
  1. Checks a Meta key is set (it never prints the key or any part of it) and that demo mode is off.
  2. Asks Meta which models the key can use (free) and says which ones the app needs are missing.
  3. Runs ONE sample repair through the whole pipeline (look, SAM 3.1 outline, diagnose, plan, safety check,
     Muse Image diagram, voice), answers the follow-up question if the AI asks one, and checks one step photo.
     DEMO_FALLBACK is switched off, so a stage that fails is reported, never silently replaced by demo answers.
  4. Writes docs/LIVE_RUN.md: what the AI said, how long each stage took, and what it cost.

Cost: one repair is a few US cents; the app's per-repair cap (MAX_COST_USD, default $0.50) still applies.
Exit codes: 0 = it worked, 1 = the run failed (the message says what to do), 2 = no key / demo mode is on.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("NARRATION_VOICE", "1")

from api import __version__, errors  # noqa: E402
from api.settings import settings  # noqa: E402

WIB = timezone(timedelta(hours=7))
NEEDED = ("vision_model", "reason_model", "sam_model", "image_model")
ANSWERS = {"id": "Tidak", "jv": "Ora", "en": "No"}
FIXES = {
    "auth": "Meta did not accept the key. Make a new key on dev.meta.ai and run: python scripts/set_keys.py",
    "busy": "Meta is busy or rate-limiting. Wait a minute and run this again.",
    "network": "Could not reach Meta. Check the internet connection (and any proxy), then run this again.",
    "budget": "The per-repair cost cap was hit. Raise MAX_COST_USD in .env a little, or try the faucet sample.",
    "invalid": "The model answered in a shape the app could not use. Run once more; if it repeats, docs/LIVE_RUN.md shows the error, and docs/META_API_NOTES.md has the shapes the app expects.",
    "generic": "Something unexpected failed. The error is in docs/LIVE_RUN.md (it has no key in it, so it is safe to share); docs/TROUBLESHOOTING.md has the usual fixes.",
}


def say(msg: str) -> None:
    print(msg, flush=True)


def _host(url: str) -> str:
    return url.split("//", 1)[-1].split("/", 1)[0]


def preflight() -> int:
    if not settings.meta_api_key:
        say("No Meta key found. Run this first:  python scripts/set_keys.py   (paste the key, press Enter)")
        return 2
    if settings.mock:
        say("MOCK=1 is set, so the app is in free demo mode. Remove MOCK=1 from .env (set_keys.py does this) and run again.")
        return 2
    say(f"Meta key: found (not shown). Server: {_host(settings.meta_api_base)}")
    return 0


def model_check() -> tuple[list[str], str]:
    """Models the app needs that this key cannot see ([] = all there). Second value: an error kind, or ''."""
    from api import meta_client

    try:
        have = set(meta_client.list_models())
    except Exception as e:  # noqa: BLE001
        return [], errors.classify(e)
    return [getattr(settings, k) for k in NEEDED if getattr(settings, k) not in have], ""


def run_repair(sample: str, lang: str) -> dict[str, Any]:
    from api.main import SAMPLE_TEXT, SAMPLES
    from api.pipeline import engine

    text = SAMPLE_TEXT[sample][lang]
    t0 = time.perf_counter()
    s = engine.create([SAMPLES / f"{sample}.jpg"], lang, text, None, "", sample=sample)
    s = engine.run(s["id"])
    asked = s.get("question")
    if s["status"] == "needs_answer":
        engine.answer(s["id"], ANSWERS[lang])
        s = engine.run(s["id"])
    total = time.perf_counter() - t0
    check: dict[str, Any] = {}
    if s["status"] == "ready":
        photo = SAMPLES / f"check_{sample}.jpg"
        t1 = time.perf_counter()
        try:
            check = engine.check_step(s["id"], 1, photo if photo.exists() else SAMPLES / f"{sample}.jpg")
        except Exception as e:  # noqa: BLE001
            check = {"error": errors.friendly(e, "en")}
        check["seconds"] = round(time.perf_counter() - t1, 1)
        s = engine.load(s["id"])
    return {"session": s, "question": asked, "answer": ANSWERS[lang] if asked else "", "seconds": round(total, 1),
            "check": check, "text": text}


def render(r: dict[str, Any], sample: str, lang: str, fake: bool, missing: list[str]) -> str:
    s = r["session"]
    dx, plan = s.get("diagnosis") or {}, s.get("plan") or {}
    when = datetime.now(WIB).strftime("%Y-%m-%d %H:%M WIB")
    title = ("# First live run: REHEARSAL against the stand-in Meta server (not a real model)" if fake
             else "# First live run: real Meta models")
    L = [title, "",
         f"Made by `python scripts/first_live_run.py{' --fake' if fake else ''}` on {when} (app {__version__}), "
         f"sample `{sample}`, language `{lang}`, server `{_host(settings.meta_api_base)}`. No key is stored in this file.", ""]
    if fake:
        L += ["> This is a rehearsal: `api/testing/fake_meta.py` answered with recorded demo fixtures, so the words",
              "> below are the demo answers and the timings are local. Run it again without `--fake` after set_keys.py.", ""]
    fb = s.get("fallback") or []
    L += ["## Result", "",
          f"- Status: **{s['status']}**" + (f" ({s.get('error')})" if s.get("error") else ""),
          f"- Demo answers used as a fallback: {', '.join(fb) if fb else 'none (every stage answered by the model)'}",
          f"- Models: {', '.join(f'{k} = {v}' for k, v in (s.get('models') or {}).items())}",
          f"- Models this key could not see: {', '.join(missing) if missing else 'none'}",
          f"- Total time (photo in to plan ready, incl. the follow-up answer): **{r['seconds']} s**",
          f"- Cost of the repair: **${(s.get('cost') or {}).get('spent_usd', 0):.4f}** "
          f"(cap ${(s.get('cost') or {}).get('budget_usd', settings.max_cost_usd)}); by model: "
          + ", ".join(f"{k} ${v:.4f}" for k, v in ((s.get('cost') or {}).get('by_model') or {}).items()), ""]
    L += ["## What went in", "", f"- Photo: `samples/{sample}.jpg` (labelled AI-generated sample photo)", f"- Owner text: {r['text']}"]
    if r["question"]:
        L.append(f"- The AI asked: \"{r['question']}\" and the script answered \"{r['answer']}\"")
    L += ["", "## What the AI said", ""]
    rep = s.get("object_report") or {}
    L.append(f"- Object: {rep.get('object', '-')}")
    for c in (dx.get("causes") or [])[:3]:
        L.append(f"- Cause: {c.get('title')} ({c.get('confidence')} %)")
    L.append(f"- Safety level: {dx.get('safety_level', s.get('safety', {}).get('level'))}; {dx.get('safety_reason', '')}")
    found = sum(1 for p in (s.get("parts") or {}).values() if p.get("found"))
    L.append(f"- SAM 3.1 outlined {found} of {len(s.get('parts') or {})} parts")
    if s.get("stop_reason"):
        L.append(f"- Stopped for safety: {s['stop_reason']}")
    for st in (plan.get("steps") or []):
        L.append(f"  {st.get('n')}. {st.get('instruction')}" + (" (diagram)" if st.get("needs_diagram") else ""))
    L.append(f"- Diagrams drawn (Muse Image): {sum(1 for d in (s.get('diagrams') or {}).values() if d.get('file'))}")
    L.append(f"- Voice clips: {len(s.get('audio') or {})}")
    if r["check"]:
        c = r["check"]
        L.append(f"- Step 1 camera check ({c.get('seconds')} s): " + (c.get("error") or f"{'passed' if c.get('passed') else 'not passed'}: {c.get('observation', '')}"))
    L += ["", "## Time per stage", "", "| Stage | Status | ms |", "|---|---|---|"]
    for k, v in (s.get("stages") or {}).items():
        L.append(f"| {k} | {v.get('status')} | {v.get('ms', '-')} |")
    L += ["", "## Next", "",
          "- If everything above is fine: `python scripts/run_eval.py` and `python scripts/smoke_e2e.py http://127.0.0.1:8000` in live mode.",
          "- Once checked, copy the total time and cost into WRITEUP and SUBMISSION.", ""]
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", default="motor", choices=["motor", "faucet", "pump", "tire"])
    ap.add_argument("--lang", default="id", choices=["id", "jv", "en"])
    ap.add_argument("--out", default=str(ROOT / "docs" / "LIVE_RUN.md"))
    ap.add_argument("--fake", action="store_true", help="rehearse against the built-in stand-in Meta server (free)")
    a = ap.parse_args(argv)
    if a.fake:
        from api.testing import fake_meta

        settings.meta_api_base, settings.meta_api_key, settings.mock = fake_meta.serve_in_thread(), fake_meta.TEST_KEY, False
        settings.narration_voice = False
        say("Rehearsal mode: using the built-in stand-in Meta server. Nothing here is a real model answer.")
    rc = preflight()
    if rc:
        return rc
    settings.demo_fallback = False  # a live check must never be papered over with demo answers
    tmp = Path(tempfile.mkdtemp(prefix="tc-live-"))
    settings.data_dir = tmp
    try:
        say("Checking which models the key can use (free)...")
        missing, err = model_check()
        if err:
            say(f"FAILED at the model list: {FIXES[err]}")
            return 1
        if missing:
            say(f"Note: this key cannot see {', '.join(missing)}. The run will probably fail at that stage.")
        say(f"Running one {a.sample} repair through the real pipeline (about a minute)...")
        r = run_repair(a.sample, a.lang)
        md = render(r, a.sample, a.lang, a.fake, missing)
        if settings.meta_api_key and settings.meta_api_key in md:  # belt and braces: never write a key
            raise SystemExit("Refusing to write the report: it would contain the key.")
        Path(a.out).write_text(md, encoding="utf-8")
        s = r["session"]
        if s["status"] not in {"ready", "stopped"}:
            say(f"FAILED: {FIXES.get(s.get('error_kind') or 'generic', FIXES['generic'])}")
            say(f"Details are in {Path(a.out).name} (no key in it).")
            return 1
        cost = (s.get("cost") or {}).get("spent_usd", 0)
        say(f"DONE: status {s['status']}, {r['seconds']} s, ${cost:.4f}. Report: {Path(a.out).name}")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
