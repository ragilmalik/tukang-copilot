"""Record the 1-tap demo (motorbike sample photo) from the REAL Meta Model API into a fixture the front end can replay.

A free Render service sleeps and needs ~50 s to wake. When the server is slow or unreachable, web/replay.js plays
this RECORDED run instead (labelled "Recorded live run" on screen): same screens, same agent log, same marked photo,
no server and no model calls at replay time. Every answer in it came from the real models (Muse Spark 1.3, SAM 3.1,
Muse Image) on the date stored in demo.json; only the photo is a labelled AI-generated sample photo.

Output (all under web/replay/, served at /static/replay/):
  demo.json          per language (id, jv, en): progress snapshots, the follow-up question when the model asked one
                     ("asked"), the ready session, and one "delta" per action (step check with each sample photo,
                     re-plan, outcome) so actions can be replayed in any order
  files/*.jpg        the photos the sessions show (sample photo, SAM-marked photo, part crops)
  check_ok.jpg, check_dark.jpg   the two labelled sample "check my step" photos (check_ok shows one step, stored as
                     sample_step per plan; the dark one is checked on whatever step is on screen)
  card-<lang>.png, report-<lang>.pdf   share card and PDF report

Regenerate after changing the prompts, the session shape or the UI flow (needs the Meta key, costs about $0.60):
    python scripts/record_replay.py            # live run, writes web/replay/
    python scripts/record_replay.py --check    # exit 1 if the committed fixture no longer has the app's shape
                                               # (compares against an offline run, free, no key needed)
    python scripts/record_replay.py --resample # re-pick the sample photo's step after a change to api/sample_step.py
                                               # (uses the recorded plans and checks, free, no key needed)
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
os.environ.setdefault("NARRATION_VOICE", "0")

OUT = ROOT / "web" / "replay"
FILES_BASE = "/static/replay/files/"
LANGS = ("id", "jv", "en")
FORMAT = 1
PACE_S = 0.6
# The follow-up is one yes/no question since 1.30.0 (the live model picks what it asks), so the owner just answers
# yes, the same as the app's quick "Ya" button. Recordings made before this change carry the longer answer.
ANSWER = {"id": "Ya", "jv": "Nggih", "en": "Yes"}
REPLAN = {"id": "Sudah dicoba, masih tidak mau hidup", "jv": "Sampun dijajal, taksih mboten purun urip", "en": "Tried it, still won't start"}
# keys whose new value is merged into the current one (dict) or appended (list) when an action is replayed
MERGE_KEYS = {"checks"}
APPEND_KEYS = {"agent_log"}
SKIP_KEYS = {"updated", "created"}


def _setup(tmp: Path, live: bool = False) -> Any:
    from api.settings import settings

    settings.data_dir = tmp
    settings.mock = not live
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


def _scrub(obj: Any, sid: str, rid: str, lang: str) -> Any:
    """Point every session URL at the recorded copy: /files/<sid>/ -> /static/replay/files/<lang>/, <sid> -> replay id.
    Each language is its own live run, with its own marked photo and part pictures, so each gets its own folder."""
    s = json.dumps(obj, ensure_ascii=False)
    s = s.replace(f"/files/{sid}/", f"{FILES_BASE}{lang}/").replace(sid, rid)
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


def _own(sid: str) -> dict[str, str]:
    """The owner header the phone sends on every request that changes the repair (X-Owner-Token)."""
    from api.pipeline import engine

    return {"X-Owner-Token": str(engine.load(sid).get("owner_token") or "")}


def _check(c: Any, sid: str, n: int, photo: bytes) -> tuple[int, dict[str, Any]]:
    r = c.post(f"/api/sessions/{sid}/steps/{n}/check", files={"photo": ("check.jpg", photo, "image/jpeg")}, headers=_own(sid))
    return r.status_code, r.json()


def _record_checks(c: Any, sid: str, photos: dict[str, bytes], files_dir: Path) -> dict[str, Any]:
    """For the current plan: each step x each sample photo, recorded against the same starting state (fresh copy),
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
                if tr.get("photo") and src.is_file():
                    # Every step gets the same two sample photos, so one file per kind is enough. One copy per step
                    # and plan was 70 identical files (about 5 MB) that the service worker downloaded on install.
                    name = f"check_{kind}{src.suffix}"
                    if not (files_dir / name).exists():
                        shutil.copyfile(src, files_dir / name)
                    tr["photo"] = name
            out.setdefault(str(n), {})[kind] = {"status": code, "response": resp, "delta": _delta(base_pub, after, MERGE_KEYS)}
    engine.save(copy.deepcopy(base))
    return out


def _sample_step(server_pick: Any, checks: dict[str, Any], where: str) -> Any:
    """The step the "Sample photo" button checks in the replay. The server's pick (api/sample_step.py: the step whose
    expected state is what the sample after-photo shows) when the live model passed the photo there. If the model did
    not, the first step it did pass (marked shows=False, so the UI only says which step it checks); that answer is
    just as recorded."""
    if not isinstance(server_pick, dict) or not checks:
        return server_pick
    passed = sorted(int(n) for n, rec in checks.items() if (rec.get("ok") or {}).get("response", {}).get("passed"))
    if int(server_pick["n"]) in passed or not passed:
        if not passed:
            print(f"{where}: the live model passed the sample photo on no step; the replay shows that fail", flush=True)
        return server_pick
    print(f"{where}: the live model did not pass the sample photo on step {server_pick['n']}; using step {passed[0]}", flush=True)
    return {"n": passed[0], "shows": False}


def record_lang(c: Any, lang: str, photos: dict[str, bytes], files_dir: Path, out_dir: Path, pace: float = PACE_S) -> dict[str, Any]:
    from api.pipeline import engine

    from api.settings import settings

    files_dir = files_dir / lang
    files_dir.mkdir(parents=True, exist_ok=True)
    settings.mock_pace_s = pace  # offline only: pacing so the stream has one snapshot per stage (live has real timing)
    rid = f"replay-motor-{lang}"
    # One take, recorded as the model answered it. The live model asks its one yes/no follow-up only when its top cause
    # is under 60% sure (api/pipeline/engine.py); the clear motorbike sample photo (plug cap visibly off) usually makes
    # it sure, so the run goes straight to the plan. Retrying until it asks would pay for takes and show a flow the
    # photo does not produce, so the recording keeps whichever happened ("asked" says which). web/replay.js plays both.
    sid = c.post("/api/sessions", data={"sample": "motor", "language": lang}).json()["id"]
    ask = _settled(c, sid)
    asked = ask["session"]["status"] == "needs_answer"
    if asked:
        assert c.post(f"/api/sessions/{sid}/answer", data={"text": ANSWER[lang]}, headers=_own(sid)).status_code == 200
        ready = _settled(c, sid)
    else:  # already ready: the "ready" part is the same settled run (its last snapshot), never replayed on its own
        print(f"{lang}: no follow-up question (top cause sure enough), recording the run as it came", flush=True)
        ready = {"snaps": ask["snaps"][-1:], "session": ask["session"]}
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
    replanned = c.post(f"/api/sessions/{sid}/replan", data={"report": REPLAN[lang]}, headers=_own(sid)).json()
    replan = _delta(before, replanned, set())
    checks1 = _record_checks(c, sid, photos, files_dir) if replanned.get("status") == "ready" else {}
    for f in engine.session_dir(sid).iterdir():  # photos the screens show
        if f.suffix.lower() in {".jpg", ".png"} and f.name != "card.png" and not f.name.startswith("check_"):
            shutil.copyfile(f, files_dir / f.name)
    rec = {"sid": rid, "asked": asked, "ask": ask, "ready": ready, "answer": ANSWER[lang] if asked else "", "checks": {"0": checks0, "1": checks1},
           "handoff": handoff, "outcome": outcome, "replan": replan, "replan_report": REPLAN[lang],
           "sample_step": {}}
    _set_sample_steps(rec, lang)
    return _scrub(rec, sid, rid, lang)


def _set_sample_steps(L: dict[str, Any], lang: str) -> None:
    """Store the step each plan's sample photo is checked on (see _sample_step) where the replay reads the session:
    the ready session (plan 1), the re-plan delta (plan 2) and L["sample_step"]. Uses only the recorded plans and
    checks, so --resample can redo it without model calls when api/sample_step.py changes."""
    from api import sample_step

    sample = str(L["ready"]["session"].get("sample") or "motor")
    plan0 = L["ready"]["session"].get("plan") or {}
    step0 = _sample_step(sample_step.pick(sample, plan0.get("steps") or []), L["checks"].get("0") or {}, f"{lang} plan 1")
    L["ready"]["session"]["sample_step"] = step0
    L["sample_step"] = {"0": step0, "1": None}
    plan1 = (L.get("replan") or {}).get("set", {}).get("plan")
    if isinstance(plan1, dict):
        step1 = _sample_step(sample_step.pick(sample, plan1.get("steps") or []), L["checks"].get("1") or {}, f"{lang} plan 2")
        L["replan"]["set"]["sample_step"] = step1
        L["sample_step"]["1"] = step1


def resample() -> dict[str, Any]:
    """Re-derive sample_step in the committed recording from its own plans and checks (no model calls, no key)."""
    path = OUT / "demo.json"
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    for lang, L in data["langs"].items():
        _set_sample_steps(L, lang)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return data


def _shrink(out_dir: Path) -> None:
    """The sample photos are detailed (about 250 KB each) and the service worker keeps every picture here for offline
    use, so re-encode them smaller: JPEG at 960 px and quality 72, PNG down to 256 colours."""
    from PIL import Image

    for f in out_dir.rglob("*"):
        if f.suffix == ".jpg" and f.stat().st_size > 60_000:
            with Image.open(f) as im:
                rgb = im.convert("RGB")
            rgb.thumbnail((960, 960), Image.Resampling.LANCZOS)
            rgb.save(f, "JPEG", quality=72, optimize=True, progressive=True)
        elif f.suffix == ".png" and f.stat().st_size > 150_000:
            with Image.open(f) as im:
                q = im.convert("RGB").quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
            q.save(f, "PNG", optimize=True)


def build(out_dir: Path, pace: float = PACE_S, live: bool = False) -> dict[str, Any]:
    from api.main import _dark_photo, __version__

    samples = ROOT / "samples"
    ok_path = samples / "check_motor.jpg"
    photos = {"ok": (ok_path if ok_path.exists() else samples / "motor.jpg").read_bytes(), "dark": _dark_photo("motor")}
    tmp = Path(tempfile.mkdtemp(prefix="tc-replay-"))
    try:
        c = _setup(tmp, live)
        if out_dir.exists():
            shutil.rmtree(out_dir)
        files_dir = out_dir / "files"
        files_dir.mkdir(parents=True)
        (out_dir / "check_ok.jpg").write_bytes(photos["ok"])
        (out_dir / "check_dark.jpg").write_bytes(photos["dark"])
        langs = {}
        for lang in LANGS:
            langs[lang] = record_lang(c, lang, photos, files_dir, out_dir, pace)
            print(f"recorded {lang}", flush=True)
        health = c.get("/api/health").json()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    _shrink(out_dir)
    from api.settings import settings

    assets = sorted(f"/static/replay/{f.relative_to(out_dir).as_posix()}" for f in out_dir.rglob("*")
                    if f.is_file() and f.suffix in {".jpg", ".png"})  # the service worker keeps these for offline use (no PDFs)
    from datetime import datetime, timedelta, timezone

    when = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M WIB")
    cost = round(sum(float(((L["ready"]["session"].get("cost") or {}).get("spent_usd")) or 0) for L in langs.values()), 4)
    note = (f"RECORDED live run: every answer came from the real Meta Model API on {when}. Replaying it makes no model calls. "
            "The photos are labelled AI-generated sample photos." if live else
            "OFFLINE shape check (canned answers, no Meta key). Never shipped in the app.")
    data = {"format": FORMAT, "kind": "recorded-demo", "recorded_with": __version__, "sample": "motor",
            "source": "meta-api-live" if live else "offline", "recorded_at": when if live else "",
            "pipeline_cost_usd": cost if live else 0,
            "max_check_fails": settings.max_check_fails, "assets": assets,
            "note": note, "models": health.get("models"), "langs": langs}
    (out_dir / "demo.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return data


IGNORE = {"recorded_with", "recorded_at", "source", "note", "pipeline_cost_usd", "ms", "updated", "created",
          "elapsed_ms", "t", "at"}
SKIP_TREES = {"delta", "outcome", "replan"}  # what changes depends on the model's answer (a step can pass or fail)
_ID_KEY = __import__("re").compile(r"^[A-Za-z_]{0,8}\d+$")


def key_paths(data: Any) -> tuple[set[str], set[str]]:
    """Every key path in the fixture (list items and id-keyed maps such as steps "1", "2" or parts "c1" collapsed to
    one), plus the paths that hold an empty or null container. Values, list lengths and model wording do not count:
    a live recording and an offline run of the same app have the same paths."""
    paths: set[str] = set()
    empty: set[str] = set()

    def walk(o: Any, p: str) -> None:
        paths.add(p)
        if isinstance(o, dict):
            if not o:
                empty.add(p)
            idmap = bool(o) and all(_ID_KEY.match(str(k)) for k in o)
            for k, v in o.items():
                if k in IGNORE or k in SKIP_TREES:
                    continue
                if k == "snaps" and isinstance(v, list):
                    v = v[-1:]
                walk(v, f"{p}/*" if idmap else f"{p}/{k}")
        elif isinstance(o, list):
            if not o:
                empty.add(p)
            for v in o:
                walk(v, f"{p}/[]")
        elif o is None or o == "":
            empty.add(p)

    walk(data, "")
    return paths, empty


def _without_unmatched_ask(a: dict[str, Any], b: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """A language where only one side asked its follow-up question: its "ask" part is a paused session on one side and
    a finished one on the other, so it is left out of the comparison there (the "ready" part still carries the finished
    session's shape on both sides). Where both asked, the paused session is compared as before."""
    a, b = copy.deepcopy(a), copy.deepcopy(b)
    for lang in set(a.get("langs") or {}) & set(b.get("langs") or {}):
        La, Lb = a["langs"][lang], b["langs"][lang]
        if La.get("asked", True) != Lb.get("asked", True):
            for L in (La, Lb):
                L.pop("ask", None)
                # the agent log's "ask" and "answer" lines exist only on the side that asked
                for part in [L.get("ready") or {}, *((L.get("ready") or {}).get("snaps") or [])]:
                    sess = part.get("session", part)
                    if isinstance(sess, dict) and isinstance(sess.get("agent_log"), list):
                        sess["agent_log"] = [e for e in sess["agent_log"] if e.get("kind") not in ("ask", "answer")]
    return a, b


def shape_diff(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    """Key paths only one side has, ignoring anything under a container that is empty on the other side."""
    a, b = _without_unmatched_ask(a, b)
    pa, ea = key_paths(a)
    pb, eb = key_paths(b)

    def under(p: str, empties: set[str]) -> bool:
        return any(p.startswith(e + "/") for e in empties)

    return sorted([f"only in recording: {p}" for p in pa - pb if not under(p, eb)] +
                  [f"only in app today: {p}" for p in pb - pa if not under(p, ea)])


def shape(data: dict[str, Any]) -> str:
    """A fingerprint of the fixture's key paths (see key_paths)."""
    return hashlib.sha256(json.dumps(sorted(key_paths(data)[0])).encode()).hexdigest()[:16]


def is_current(verbose: bool = False) -> bool:
    """True when web/replay/demo.json still has the key paths the app produces today (used by the tests). The app side
    is an offline run (free, no key), so this works in CI."""
    cur = json.loads((OUT / "demo.json").read_text(encoding="utf-8"))
    tmp = Path(tempfile.mkdtemp(prefix="tc-replay-check-"))
    try:
        diff = shape_diff(cur, build(tmp / "replay", pace=0.0))
        if verbose:
            print("\n".join(diff[:40]))
        return not diff
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if web/replay/demo.json no longer matches the app's shape")
    ap.add_argument("--resample", action="store_true",
                    help="re-pick the step each sample photo is checked on (api/sample_step.py) in the committed recording; no model calls")
    a = ap.parse_args()
    if a.resample:
        data = resample()
        print("sample_step: " + ", ".join(f"{lang} {L['sample_step']}" for lang, L in data["langs"].items()))
        return 0
    if a.check:
        same = is_current(verbose=True)
        print("replay fixture up to date" if same else "replay fixture OUT OF DATE: run python scripts/record_replay.py")
        return 0 if same else 1
    from api.settings import settings

    if not settings.meta_api_key:
        print("No Meta key: the recording must come from the real API. Run python scripts/set_keys.py first.")
        return 2
    data = build(OUT, pace=0.0, live=True)
    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"wrote {OUT.relative_to(ROOT)}/ ({size // 1024} KB) for {', '.join(data['langs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
