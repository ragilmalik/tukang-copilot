"""Record the 1-tap judge demo (motorbike, demo mode) into a static fixture the front end can replay.

Why: a free Render service sleeps and needs ~50 s to wake. When the server is slow or unreachable, web/replay.js plays
this RECORDED run instead (clearly labelled "Recorded demo" on screen): same screens, same agent log, same marked photo,
no server and no model calls. Nothing here is a live answer; it is the demo-mode (MOCK) pipeline, recorded once.

Output (all under web/replay/, served at /static/replay/):
  demo.json          per language (id, jv, en): progress snapshots, the follow-up question, the ready session, and one
                     "delta" per action (step check with each stand-in photo, re-plan, outcome) so actions can be
                     replayed in any order
  files/*.jpg        the photos the sessions show (sample photo, SAM-marked photo, part crops)
  check_ok.jpg, check_dark.jpg   the two labelled stand-in "check my step" photos
  card-<lang>.png, report-<lang>.pdf   share card and PDF report

Regenerate after changing the mock answers, the session shape or the UI flow:
    python scripts/record_replay.py            # writes web/replay/
    python scripts/record_replay.py --check    # exit 1 if the committed fixture is out of date (shape only)
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["MOCK"] = "1"
os.environ.setdefault("NARRATION_VOICE", "0")

OUT = ROOT / "web" / "replay"
FILES_BASE = "/static/replay/files/"
LANGS = ("id", "jv", "en")
FORMAT = 1
PACE_S = 0.6
ANSWER = {"id": "Ya, starter berbunyi tapi mesin tidak hidup", "jv": "Nggih, starter muni nanging mesin mboten urip",
          "en": "Yes, the starter turns but the engine won't fire"}
REPLAN = {"id": "Sudah dicoba, masih tidak mau hidup", "jv": "Sampun dijajal, taksih mboten purun urip", "en": "Tried it, still won't start"}
# keys whose new value is merged into the current one (dict) or appended (list) when an action is replayed
MERGE_KEYS = {"checks"}
APPEND_KEYS = {"agent_log"}
SKIP_KEYS = {"updated", "created"}


def _setup(tmp: Path) -> Any:
    from api.settings import settings

    settings.data_dir = tmp
    settings.mock = True
    settings.narration_voice = False
    settings.mock_pace_s = 0.0
    settings.demo_fallback = False
    from fastapi.testclient import TestClient

    from api.main import app

    return TestClient(app)


def _snaps(c: Any, sid: str) -> list[dict[str, Any]]:
    with c.stream("GET", f"/api/sessions/{sid}/events") as r:
        body = "".join(r.iter_text())
    return [json.loads(line[6:]) for line in body.splitlines() if line.startswith("data: ")]


def _settled(c: Any, sid: str) -> dict[str, Any]:
    snaps = _snaps(c, sid)
    assert snaps, "no progress snapshots"
    return {"snaps": snaps, "session": c.get(f"/api/sessions/{sid}").json()}


def _scrub(obj: Any, sid: str, rid: str) -> Any:
    """Point every session URL at the recorded copy: /files/<sid>/ -> /static/replay/files/, <sid> -> replay id."""
    s = json.dumps(obj, ensure_ascii=False)
    s = s.replace(f"/files/{sid}/", FILES_BASE).replace(sid, rid)
    return json.loads(s)


def _delta(before: dict[str, Any], after: dict[str, Any], merge: set[str]) -> dict[str, Any]:
    out: dict[str, Any] = {"set": {}, "merge": {}, "append": {}}
    for k, v in after.items():
        if k in SKIP_KEYS or before.get(k) == v:
            continue
        if k in APPEND_KEYS and isinstance(v, list) and isinstance(before.get(k), list) and v[:len(before[k])] == before[k]:
            out["append"][k] = v[len(before[k]):]
        elif k in merge and isinstance(v, dict) and isinstance(before.get(k), dict):
            out["merge"][k] = {kk: vv for kk, vv in v.items() if before[k].get(kk) != vv}
        else:
            out["set"][k] = v
    return out


def _check(c: Any, sid: str, n: int, photo: bytes) -> tuple[int, dict[str, Any]]:
    r = c.post(f"/api/sessions/{sid}/steps/{n}/check", files={"photo": ("check.jpg", photo, "image/jpeg")})
    return r.status_code, r.json()


def _record_checks(c: Any, sid: str, photos: dict[str, bytes], files_dir: Path) -> dict[str, Any]:
    """For the current plan: each step x each stand-in photo, recorded against the same starting state (fresh copy),
    so the replay can apply them in whatever order the visitor taps."""
    from api.pipeline import engine

    base = engine.load(sid)
    base_pub = c.get(f"/api/sessions/{sid}").json()
    out: dict[str, Any] = {}
    for st in (base.get("plan") or {}).get("steps") or []:
        n = int(st["n"])
        for kind, data in photos.items():
            engine.save(copy.deepcopy(base))
            code, resp = _check(c, sid, n, data)
            after = c.get(f"/api/sessions/{sid}").json()
            for tr in ((after.get("checks") or {}).get(str(n)) or {}).get("tries") or []:
                src = engine.session_dir(sid) / str(tr.get("photo", ""))
                if tr.get("photo") and src.is_file():  # both stand-in photos get the same name on the server: keep both
                    name = f"{src.stem}_{kind}{src.suffix}"
                    shutil.copyfile(src, files_dir / name)
                    tr["photo"] = name
            out.setdefault(str(n), {})[kind] = {"status": code, "response": resp, "delta": _delta(base_pub, after, MERGE_KEYS)}
    engine.save(copy.deepcopy(base))
    return out


def record_lang(c: Any, lang: str, photos: dict[str, bytes], files_dir: Path, out_dir: Path, pace: float = PACE_S) -> dict[str, Any]:
    from api.pipeline import engine

    from api.settings import settings

    settings.mock_pace_s = pace  # demo pacing so the stream has one snapshot per stage, like the real demo
    sid = c.post("/api/sessions", data={"sample": "motor", "language": lang}).json()["id"]
    rid = f"replay-motor-{lang}"
    ask = _settled(c, sid)
    assert ask["session"]["status"] == "needs_answer", ask["session"]["status"]
    assert c.post(f"/api/sessions/{sid}/answer", data={"text": ANSWER[lang]}).status_code == 200
    ready = _settled(c, sid)
    settings.mock_pace_s = 0.0
    assert ready["session"]["status"] == "ready", ready["session"]["status"]
    checks0 = _record_checks(c, sid, photos, files_dir)
    handoff = c.get(f"/api/sessions/{sid}/handoff").json()
    card = c.get(f"/api/sessions/{sid}/card.png")
    pdf = c.get(f"/api/sessions/{sid}/report.pdf")
    assert card.status_code == 200 and pdf.status_code == 200
    (out_dir / f"card-{lang}.png").write_bytes(card.content)
    (out_dir / f"report-{lang}.pdf").write_bytes(pdf.content)
    outcome: dict[str, Any] = {}
    base = engine.load(sid)
    for res in ("fixed", "pro"):
        engine.save(copy.deepcopy(base))
        before = c.get(f"/api/sessions/{sid}").json()
        after = c.post(f"/api/sessions/{sid}/outcome", data={"result": res},
                       headers={"X-Owner-Token": str(base.get("owner_token") or "")}).json()
        outcome[res] = _delta(before, after, set())
    engine.save(copy.deepcopy(base))
    before = c.get(f"/api/sessions/{sid}").json()
    replanned = c.post(f"/api/sessions/{sid}/replan", data={"report": REPLAN[lang]}).json()
    replan = _delta(before, replanned, set())
    checks1 = _record_checks(c, sid, photos, files_dir) if replanned.get("status") == "ready" else {}
    for f in engine.session_dir(sid).iterdir():  # photos the screens show (same for every language)
        if f.suffix.lower() in {".jpg", ".png"} and f.name != "card.png" and not f.name.startswith("check_"):
            shutil.copyfile(f, files_dir / f.name)
    rec = {"sid": rid, "ask": ask, "ready": ready, "answer": ANSWER[lang], "checks": {"0": checks0, "1": checks1},
           "handoff": handoff, "outcome": outcome, "replan": replan, "replan_report": REPLAN[lang]}
    return _scrub(rec, sid, rid)


def build(out_dir: Path, pace: float = PACE_S) -> dict[str, Any]:
    from api.main import _dark_photo, __version__

    samples = ROOT / "samples"
    ok_path = samples / "check_motor.jpg"
    photos = {"ok": (ok_path if ok_path.exists() else samples / "motor.jpg").read_bytes(), "dark": _dark_photo()}
    tmp = Path(tempfile.mkdtemp(prefix="tc-replay-"))
    try:
        c = _setup(tmp)
        if out_dir.exists():
            shutil.rmtree(out_dir)
        files_dir = out_dir / "files"
        files_dir.mkdir(parents=True)
        (out_dir / "check_ok.jpg").write_bytes(photos["ok"])
        (out_dir / "check_dark.jpg").write_bytes(photos["dark"])
        langs = {lang: record_lang(c, lang, photos, files_dir, out_dir, pace) for lang in LANGS}
        health = c.get("/api/health").json()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    from api.settings import settings

    assets = sorted(f"/static/replay/{f.relative_to(out_dir).as_posix()}" for f in out_dir.rglob("*")
                    if f.is_file() and f.suffix in {".jpg", ".png"})  # the service worker keeps these for offline use (no PDFs)
    data = {"format": FORMAT, "kind": "recorded-demo", "recorded_with": __version__, "sample": "motor",
            "max_check_fails": settings.max_check_fails, "assets": assets,
            "note": "RECORDED demo-mode run (MOCK answers, labelled stand-in photos). Not a live model answer.",
            "models": health.get("models"), "langs": langs}
    (out_dir / "demo.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return data


def shape(data: dict[str, Any]) -> str:
    """A fingerprint of the fixture's structure: keys, value types and step counts, not timestamps, ids or how many
    progress snapshots the stream happened to produce (only the last one, the settled state, counts)."""
    def walk(o: Any) -> Any:
        if isinstance(o, dict):
            return {k: (walk(v[-1:]) if k == "snaps" and isinstance(v, list) else walk(v)) for k, v in sorted(o.items())
                    if k not in {"recorded_with", "ms", "updated", "created", "elapsed_ms", "t", "at"}}
        if isinstance(o, list):
            return [walk(v) for v in o]
        return type(o).__name__
    return hashlib.sha256(json.dumps(walk(data), sort_keys=True).encode()).hexdigest()[:16]


def is_current() -> bool:
    """True when web/replay/demo.json still has the shape the app produces today (used by the tests)."""
    cur = json.loads((OUT / "demo.json").read_text(encoding="utf-8"))
    tmp = Path(tempfile.mkdtemp(prefix="tc-replay-check-"))
    try:
        return shape(cur) == shape(build(tmp / "replay", pace=0.0))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if web/replay/demo.json no longer matches the app's shape")
    a = ap.parse_args()
    if a.check:
        same = is_current()
        print("replay fixture up to date" if same else "replay fixture OUT OF DATE: run python scripts/record_replay.py")
        return 0 if same else 1
    data = build(OUT)
    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"wrote {OUT.relative_to(ROOT)}/ ({size // 1024} KB) for {', '.join(data['langs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
