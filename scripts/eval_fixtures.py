"""Score the photo fixtures against what the manifest expects. Works against a RUNNING server, mock or live.

    python scripts/eval_fixtures.py                       # http://localhost:8000
    python scripts/eval_fixtures.py http://127.0.0.1:8031 --out docs/EVAL_REPORT.md
    python scripts/eval_fixtures.py URL --dir path/to/real/photos   # a folder with its own manifest.json

In mock mode this proves the pipeline and the safety routing. In LIVE mode, with real photos and a
manifest of the same shape, it gives honest numbers: how often the safety level, the object category and
the part masks came out right, how long a repair took and what it cost. Exits 0 only if every fixture met
its expectation (the unknown-object edge case must not produce a confident plan).

Manifest entry fields used: file, text, category, safety (green/amber/red), role (step_check / edge_case /
reference are handled separately), scenario.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIR = ROOT / "api" / "tests" / "fixtures"
DONE = ("ready", "stopped", "needs_answer", "error", "exhausted")


def wait(c: httpx.Client, sid: str, timeout: float = 240) -> dict[str, Any]:
    t0 = time.time()
    while time.time() - t0 < timeout:
        s: dict[str, Any] = c.get(f"/api/sessions/{sid}").json()
        if s["status"] in DONE:
            return s
        time.sleep(0.5)
    raise TimeoutError(sid)


def parts_rate(s: dict[str, Any]) -> tuple[int, int]:
    parts = s.get("parts") or {}
    return sum(1 for p in parts.values() if p.get("found")), len(parts)


OWNERS: dict[str, dict[str, str]] = {}  # session id -> owner header, as the phone keeps it


def run_item(c: httpx.Client, d: Path, item: dict[str, Any]) -> dict[str, Any]:
    lang = "en" if item["file"].endswith("_en.jpg") or item["text"].startswith(("My ", "The ", "Rice cooker not")) else "id"
    t0 = time.time()
    with open(d / item["file"], "rb") as f:
        r = c.post("/api/sessions", data={"text": item["text"], "language": lang, "category": item.get("category", "")},
                   files=[("photos", (item["file"], f, "image/jpeg"))])
    r.raise_for_status()
    sid = r.json()["id"]
    OWNERS[sid] = {"X-Owner-Token": str(r.json().get("owner_token") or "")}  # the answer and the step checks need it
    s = wait(c, sid)
    asked = False
    if s["status"] == "needs_answer":
        asked = True
        c.post(f"/api/sessions/{sid}/answer", data={"text": "Tidak tahu, tolong lanjut." if lang == "id" else "Not sure, please continue."},
               headers=OWNERS[sid])
        s = wait(c, sid)
    found, total = parts_rate(s)
    cat = ((s.get("object_report") or {}).get("category") or "")
    level = (s.get("safety") or {}).get("level", "")
    steps = len(((s.get("plan") or {}).get("steps")) or [])
    edge = item.get("role") == "edge_case"
    want = item.get("safety")
    checks: dict[str, bool] = {}
    if edge:
        # An unreadable request must end in a question, a stop or an honest "not sure", never a confident plan.
        checks["no confident plan"] = asked or s["status"] in ("stopped", "needs_answer") or steps == 0 or level != "green"
    else:
        checks["finished"] = s["status"] in ("ready", "stopped")
        if want:
            checks["safety level"] = level == want
            checks["status vs level"] = (s["status"] == "stopped") == (want == "red")
        if item.get("category") and item["category"] not in ("other",):
            checks["category"] = bool(cat) and (cat == item["category"] or item["category"] in cat or cat in item["category"])
        if s["status"] == "ready":
            checks["has steps"] = steps >= 3
            # a photo that shows only some of the scenario's parts says how many in "parts_in_photo"
            need = int(item["parts_in_photo"]) if item.get("parts_in_photo") else total / 2
            checks["parts found"] = total > 0 and found >= need
    return {"sid": sid, "file": item["file"], "scenario": item.get("scenario", ""), "status": s["status"], "level": level, "category": cat,
            "parts": f"{found}/{total}", "steps": steps, "asked": asked, "secs": round(time.time() - t0, 1),
            "cost": float((s.get("cost") or {}).get("spent_usd") or 0), "mode": s.get("mode", ""),
            "checks": checks, "pass": all(checks.values())}


def run_step_checks(c: httpx.Client, d: Path, manifest: list[dict[str, Any]], sessions: dict[str, str]) -> list[dict[str, Any]]:
    out = []
    for item in manifest:
        if item.get("role") != "step_check" or item["scenario"] not in sessions:
            continue
        with open(d / item["file"], "rb") as f:
            sid = sessions[item["scenario"]]
            r = c.post(f"/api/sessions/{sid}/steps/1/check", files={"photo": ("c.jpg", f, "image/jpeg")}, headers=OWNERS.get(sid, {}))
        j = r.json() if r.status_code == 200 else {}
        good = r.status_code == 200 and "passed" in j
        out.append({"file": item["file"], "scenario": item["scenario"], "http": r.status_code, "passed": j.get("passed"), "pass": good})
    return out


def markdown(rows: list[dict[str, Any]], steps: list[dict[str, Any]], base: str) -> str:
    mode = rows[0]["mode"] if rows else "?"
    n_ok = sum(1 for r in rows if r["pass"])
    cost = sum(r["cost"] for r in rows)
    lines = [
        "# Fixture evaluation", "",
        f"Server: `{base}`, mode **{mode}**, {time.strftime('%Y-%m-%d %H:%M', time.gmtime())} UTC.", "",
        "The fixtures are labelled AI-generated sample photos, not real repairs. In mock mode this shows the pipeline and safety routing work; "
        "only a LIVE run on real photos gives accuracy numbers.", "",
        f"**{n_ok}/{len(rows)} photos met every expectation.** Total model cost: ${cost:.3f}.", "",
        "| Photo | Status | Safety | Category | Parts found | Steps | Asked | Secs | Result |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        bad = ", ".join(k for k, v in r["checks"].items() if not v)
        lines.append(f"| {r['file']} | {r['status']} | {r['level']} | {r['category']} | {r['parts']} | {r['steps']} | "
                     f"{'yes' if r['asked'] else 'no'} | {r['secs']} | {'PASS' if r['pass'] else 'FAIL: ' + bad} |")
    if steps:
        lines += ["", "Camera step checks:", "", "| Photo | HTTP | Verdict returned | Result |", "|---|---|---|---|"]
        for s in steps:
            lines.append(f"| {s['file']} | {s['http']} | {s['passed']} | {'PASS' if s['pass'] else 'FAIL'} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base", nargs="?", default="http://localhost:8000")
    ap.add_argument("--dir", type=Path, default=DEFAULT_DIR, help="folder with photos and a manifest.json")
    ap.add_argument("--out", type=Path, help="write a markdown report here")
    args = ap.parse_args()
    base = args.base.rstrip("/")
    manifest: list[dict[str, Any]] = json.loads((args.dir / "manifest.json").read_text())["fixtures"]
    rows: list[dict[str, Any]] = []
    sessions: dict[str, str] = {}
    with httpx.Client(base_url=base, timeout=120, trust_env=not base.startswith(("http://localhost", "http://127."))) as c:
        for item in manifest:
            if item.get("role") in ("step_check", "reference") or not item.get("text"):
                continue
            row = run_item(c, args.dir, item)
            rows.append(row)
            if row["status"] == "ready" and not item.get("role"):
                sessions.setdefault(item["scenario"], row["sid"])
            print(("PASS " if row["pass"] else "FAIL ") + f"{row['file']:42s} {row['status']:8s} {row['level']:6s} parts {row['parts']} steps {row['steps']} {row['secs']}s")
        steps = run_step_checks(c, args.dir, manifest, sessions)
        for s in steps:
            print(("PASS " if s["pass"] else "FAIL ") + f"step check {s['file']} http {s['http']} passed={s['passed']}")
    report = markdown(rows, steps, base)
    if args.out:
        args.out.write_text(report)
        print(f"wrote {args.out}")
    good = all(r["pass"] for r in rows) and all(s["pass"] for s in steps)
    print("\nALL MET" if good else "\nSOME FIXTURES MISSED THEIR EXPECTATION")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
