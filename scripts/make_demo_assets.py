"""Demo assets from the real app: screenshots, voice-over, the demo film, the vertical clip and the README GIF.

    python scripts/make_demo_assets.py shots          # Playwright drives the phone UI -> docs/demo/screenshots/*.png (+ wa)
    python scripts/make_demo_assets.py wa             # only the WhatsApp simulator shots (needs live answers)
    python scripts/make_demo_assets.py diagram        # docs/img/architecture.png
    python scripts/make_demo_assets.py voice          # edge-tts voice-over, one take per sentence -> docs/demo/voice (internet)
    python scripts/make_demo_assets.py capture GROUP  # screen recordings: motor, steps, other (no GROUP: all three)
    python scripts/make_demo_assets.py video [KEY..]  # docs/demo/tukang-copilot-demo.mp4 + .en.srt + TIMESTAMPS.txt
    python scripts/make_demo_assets.py vertical       # docs/demo/tukang-copilot-x-vertical.mp4 (9:16, voice + music)
    python scripts/make_demo_assets.py gif            # docs/demo/hero.gif from the recordings

The film (SCENES) opens on a real problem at home, shows the app working on real recorded screens, then the measured
numbers and the repo link. The people-and-home stills are AI-generated scenes and say so while on screen; the app
screens are real Meta API output recorded on a live run on 6 Nov 2026 and played back; the photos in the app are
labelled AI-generated sample photos. DEMO_MUSIC points at the music bed ("Lucky Acoustic", Jesse Keller, CC BY 3.0).
Chromium: PLAYWRIGHT_CHROMIUM, system chromium, or `python -m playwright install chromium`.

Two sources of answers for the screenshots and recordings:

  live (default)      every answer is a new call to the Meta Model API (needs the key, about $0.60 for the shots).
  recorded            DEMO_RECORDED_DATA=<folder> plays answers that already came from the live API, so nothing new is
                      paid for: the motorbike repair is the app's own recorded 1-tap demo (web/replay/demo.json, the
                      "Recorded demo" badge is on screen), and the pump, rice cooker, faucet and Basa Jawa tyre repairs
                      are live sessions recorded by an earlier live run (a copy of its DATA_DIR). Pages are opened at
                      the public address (DEMO_PUBLIC_BASE), answered by the local server, so links and QR codes read
                      like the deployed site. Any request that would start new model work is refused and fails the run;
                      in `shots` only the live camera guide still calls SAM 3.1 live. The film and the vertical clip
                      are made from recorded clips only, because the narration says so.

DEMO_BASE_URL=http://127.0.0.1:8765 uses a server I already started (`PORT=8765 python app.py` with the key, plus
WA_SIM=1 DEMO_FALLBACK=0 NARRATION_VOICE=0) instead of starting one in this process on a free port. The script checks
that its /health says live (and the current version) before it spends anything.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable
from typing import Any

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
DEMO = ROOT / "docs" / "demo"
SHOTS = DEMO / "screenshots"
VOICE = DEMO / "voice"
FIX = ROOT / "api" / "tests" / "fixtures"
ARCH = ROOT / "docs" / "img" / "architecture.png"
W, H = 1920, 1080
VOICE_NAME = "en-US-AndrewMultilingualNeural"  # the most natural-sounding free English narrator (VOICE_PICK A/B, 6 Nov 2026)
VOICE_RATE = "-8%"                              # about 150 words a minute: someone explaining, not reading
OWNER_RATE = "-4%"                              # the owners' Bahasa and Basa Jawa lines, a little slower than default


# --- scenes (the script)
@dataclass
class Scene:
    key: str
    image: str            # "broll:<repo path>" or "still:<scene>" (AI-generated scene), "proof", "title:<big>|<small>",
                          # or a screenshot name (the fallback still of a recorded scene)
    caption: str          # on-screen line under the headline (what the viewer reads)
    say: str              # voice-over (English); one caption per sentence
    min_s: float = 4.0
    head: str = ""        # short headline (7 words or fewer)
    tone: str = "act"     # safety colour of the accent: act (orange), check (yellow), ok (green), stop (red), info (blue)
    pre: tuple[str, str] = ("", "")   # (edge-tts voice, line) spoken first by an owner, in Bahasa or Basa Jawa
    pre_en: str = ""      # the owner's line in English: the burned-in caption while the owner speaks
    move: str = "br"      # Ken Burns anchor of a still: br, bl, c, tr, r (the point that stays put while it pushes in)
    hold: float = 0.6     # silence after the voice before the next scene


REPO_URL = "github.com/ragilmalik/tukang-copilot"
MUSIC_CREDIT = 'Music: "Lucky Acoustic" by Jesse Keller (jamendo.com/track/1540859), licensed under CC BY 3.0'
OWNER_PAUSE_S = 0.45   # gap between an owner's line and the narrator
SENTENCE_GAP_S = 0.32  # gap between two narrator sentences (each sentence is its own take, so the read can breathe)

# The film: hook (a real problem at home) -> what the app does -> the app in action (real recorded screens) -> proof
# (numbers from the repo's reports only) -> one action (the repo). About two minutes.
SCENES: list[Scene] = [
    Scene("hook", "broll:docs/launch/broll/broll_pump.jpg", "The pump hums, but no water comes out.",
          "When the water pump stops, the whole house waits.", 4, "Pompa mati.", "act",
          pre=("id-ID-GadisNeural", "Aduh, pompa airnya mati lagi. Bak mandi kosong."),
          pre_en="Oh no, the water pump died again. The tub is empty."),
    Scene("problem", "broll:docs/launch/broll/broll_motor_start.jpg", "The bike won't start, and the shop is closed.",
          "Or the motorbike won't start, and the bengkel down the road is closed.", 4,
          "Motor mogok.", "act"),
    Scene("promise", "still:cover", "Photo in. The broken part marked. Steps out.",
          "So I built Tukang Copilot. Take a photo, say what's wrong, and it finds the part "
          "and walks you through the fix.", 4, "Tukang Copilot", "act", move="c"),
    Scene("home", "01_home", "Real Meta API output, recorded on a live run on 6 Nov 2026.",
          "From here on, every phone screen is real output from Meta's models, recorded on a live run on November sixth.", 4, "Real app, real answers", "info"),
    Scene("capture", "01_home", "A photo and a few words, in Bahasa, Basa Jawa or English.",
          "Pick a photo and say the problem, in Bahasa, Javanese or English.", 4, "Snap it, say it"),
    Scene("progress", "02_progress", "1-tap demo: the recorded live run on this same photo.",
          "The one-tap demo replays that run on this same photo. Results show up as each model finishes.", 4, "Watch it work", "info"),
    Scene("diagnosis", "04_diagnosis", "Causes with confidence, safety level, tools, time, and cost next to the bengkel price.",
          "Then the likely cause, how sure it is, and the parts cost next to the bengkel price.", 4, "The likely cause", "check"),
    Scene("parts", "05_parts", "SAM 3.1 outlines and numbers the real parts.",
          "SAM 3.1 outlines the real parts on your own photo and numbers them.", 4, "Parts on your photo"),
    Scene("preflight", "15_preflight", "The steps stay locked until every box is ticked.",
          "A short safety list comes first. The steps stay locked until every box is ticked.", 4,
          "Safety first", "check"),
    Scene("steps", "06_step", "What to do, which part, and what done looks like.",
          "Then it goes one step at a time.", 6,
          "One step at a time"),
    Scene("check_fail", "07_check_fail", "Send a photo after the step. Too dark? Retake.",
          "After a step, I send a photo and Muse Spark checks it. Too dark, so it asks for another.", 4,
          "Check my step", "check"),
    Scene("check_pass", "08_check_pass", "A clear photo of the plug cap back on passes.",
          "A clear photo of the plug cap back on passes.", 4, "Verified", "ok"),
    Scene("replan", "09_replan", "It moves on to the next likely cause.",
          "Still broken? It plans again around the next likely cause.", 4, "Still broken?"),
    Scene("handoff", "18_handoff", "WhatsApp summary, the nearest workshop, a PDF brief for the mechanic.",
          "A job for a pro? One tap hands it to a bengkel, with a WhatsApp summary and a PDF.", 4, "Hand it to a bengkel"),
    Scene("diagram", "28_diagram_step", "Muse Image draws the hidden step; Muse Spark reviews it.",
          "When a photo can't show a step, Muse Image draws a diagram.", 4,
          "A diagram for the hidden step", "info"),
    Scene("rice_broll", "broll:docs/launch/broll/broll_rice.jpg", "220 V inside. This one is not a home job.",
          "It also knows when to say no.", 3, "Bahaya? Stop.", "stop"),
    Scene("rice", "11_rice_stop", "Opening 220 V parts: it stops and sends you to a service centre.",
          "A rice cooker that won't heat means 220-volt parts inside, so it stops and sends you to a service centre.", 4,
          "Red stop", "stop"),
    Scene("tyre_broll", "still:poster-vertical", "", "", 3, "Basa Jawa", "act",
          pre=("jv-ID-DimasNeural", "Ban motorku kempes, ana paku nancep."),
          pre_en="My bike tyre is flat, there's a nail stuck in it.", move="c", hold=0.5),
    Scene("tyre", "20_javanese_result", "The same repair, from cause to steps, in Basa Jawa.",
          "It answers in Javanese too.", 5, "Basa Jawa"),
    Scene("proof", "proof", "", "On the live API, with my earlier sample photos, a repair took a median of 83 seconds and about 4 US cents. "
          "It stopped all 33 dangerous test cases, with no false stops on 17 everyday jobs.", 6, "What I measured", "info", hold=1.0),
    Scene("close", "title:Fix it yourself, safely.|Open source, MIT licence. Bahasa Indonesia, Basa Jawa and English.",
          "", "Tukang Copilot is open source. The code is on GitHub, at the link below.", 6, hold=3.2),
]

# The proof card: only numbers from the repo's reports (each one checked in docs/launch/ASSETS.md's claims table).
PROOF: list[tuple[str, str]] = [
    ("83 s", "median time per repair on the live Meta API, photo in to plan ready"),
    ("$0.044", "median cost per repair on the live API (about 4 US cents)"),
    ("33 / 33", "dangerous red-team cases stopped (23 owner texts + 10 plan steps)"),
    ("0 / 17", "everyday jobs stopped by mistake"),
    ("1,096", "automated tests passed, 0 failed, 0 skipped (last full run, v1.32.0)"),
]
PROOF_NOTE = ("Live eval of 5 Nov 2026 (docs/EVAL.md), run on the earlier set of AI-generated sample photos, "
              "before the photos in this video. Tests: docs/TEST_REPORT.md.")


def scenes(recorded_mode: bool | None = None) -> list[Scene]:
    """The scenes of the main film. The narration says the answers were recorded on a live run, so the film is only
    made from recorded clips (video() checks); recorded_mode is kept for callers of the older signature."""
    del recorded_mode
    return list(SCENES)


# The vertical cut (9:16, about 35 s, voice and music): its own short lines over the same recordings.
# key: (scene, recording to show, where in it to start)
VSCENES: list[Scene] = [
    Scene("v_hook", "broll:docs/launch/broll/broll_pump.jpg", "", "Pump dead? Bike won't start? Take a photo and say what's wrong.", 3,
          "Pompa mati?", "act", pre=("id-ID-GadisNeural", "Aduh, pompa airnya mati lagi."), pre_en="Oh no, the water pump died again.",
          hold=0.35),
    Scene("v_parts", "05_parts", "", "Tukang Copilot finds the likely cause and outlines the parts on your photo.", 3,
          "Parts on your photo", hold=0.35),
    Scene("v_check", "08_check_pass", "", "Then it checks every step from a new photo.", 3, "Every step checked", "ok", hold=0.35),
    Scene("v_stop", "11_rice_stop", "", "If the job is dangerous, it stops.", 3, "It says stop", "stop", hold=0.35),
    Scene("v_tyre", "20_javanese_result", "", "In Bahasa, Javanese or English.", 3, "Basa Jawa too", hold=0.35),
    Scene("v_close", "title:Fix it yourself, safely.|Open source, MIT licence.", "",
          "Real recorded output from Meta's models. The code is on GitHub.", 4, hold=2.6),
]
VCLIPS = {"v_parts": ("parts", 0.8), "v_check": ("check_pass", 0.0), "v_stop": ("rice", 2.0), "v_tyre": ("tyre", 0.0)}
VERTICAL_ZOOMS: dict[str, list[tuple[float, float, float]]] = {"parts": [(0.0, 1.0, 300), (0.6, 1.0, 300), (2.0, 1.3, 300), (6.0, 1.3, 300)],
                  "check_pass": [(0.0, 1.0, 560), (0.8, 1.0, 560), (2.0, 1.25, 560), (6.0, 1.25, 560)],
                  "rice": [(0.0, 1.1, 330), (6.0, 1.25, 330)]}


LIVE_MS = 240_000  # live Meta answers take up to a couple of minutes
ANSWER = "Ya"      # the owner's answer to the follow-up (one yes/no question since 1.30.0)


# --- screenshots
class _External:
    """Stand-in for the uvicorn server when DEMO_BASE_URL points at one I started myself (nothing to stop here)."""
    should_exit = False


def _check_external(base: str) -> None:
    """The external server must answer live (no offline badge in any frame) on the version in this checkout."""
    import httpx

    from api import __version__

    h = httpx.get(base.rstrip("/") + "/health", timeout=10, trust_env=False).json()
    want_offline = os.environ.get("DEMO_ASSETS_OFFLINE") == "1"
    if (h.get("mode") == "offline") != want_offline or h.get("version") != __version__:
        raise SystemExit(f"{base}/health says mode={h.get('mode')} version={h.get('version')}: start the server live on {__version__}")
    if h.get("demo_fallback"):
        raise SystemExit(f"{base} has DEMO_FALLBACK on: a failed live call would show a demo answer. Start it with DEMO_FALLBACK=0")


def _server() -> tuple[str, Any]:
    # Live by default: every answer in the screenshots and the video comes from the real Meta Model API (needs the key).
    # DEMO_ASSETS_OFFLINE=1 runs the same flow on the offline canned answers, only for trying the script for free.
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    if os.environ.get("DEMO_BASE_URL"):
        base = os.environ["DEMO_BASE_URL"].rstrip("/")
        _check_external(base)
        return base, _External()
    if os.environ.get("DEMO_ASSETS_OFFLINE") == "1":
        os.environ["OFFLINE"] = "1"
    os.environ.setdefault("NARRATION_VOICE", "0")
    os.environ.setdefault("WA_SIM", "1")  # the /wa simulator answers live too
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    import uvicorn

    from api.main import app
    from api.settings import settings

    settings.data_dir = Path(tempfile.mkdtemp(prefix="tukang-demo-"))
    if recorded():  # a copy, so the recording itself never changes
        shutil.copytree(Path(os.environ["DEMO_RECORDED_DATA"]) / "sessions", settings.data_dir / "sessions")
        for f in (settings.data_dir / "sessions").glob("*/session.json"):
            os.utime(f)  # the hourly janitor purges by file age: the copies count from now, the privacy setting stays as it is
    settings.demo_fallback = False
    settings.rate_limit_per_hour = 1000
    if not settings.offline:
        settings.wa_sim = True
    # DEMO_PORT=8765 pins the port (a shared machine where only one port is ours); default: any free port
    port = int(os.environ.get("DEMO_PORT") or 0)
    if not port:
        s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=srv.run, daemon=True).start()
    while not srv.started:
        time.sleep(0.05)
    return f"http://127.0.0.1:{port}", srv


def _chromium() -> str | None:
    for p in (os.environ.get("PLAYWRIGHT_CHROMIUM"), shutil.which("chromium"), shutil.which("chromium-browser"), shutil.which("google-chrome")):
        if p and Path(p).exists():
            return p
    return None


SR_STUB = """(() => {  // headless Chromium has no working speech service: a silent stand-in so the hands-free UI can be shown
  class SR { constructor() { this.lang = ''; this.continuous = true; this.interimResults = false; }
    start() { setTimeout(() => this.onstart && this.onstart(), 30); } stop() {} abort() {} }
  window.SpeechRecognition = SR; window.webkitSpeechRecognition = SR; })();"""


def _fake_camera_y4m(photo: Path) -> Path:
    """Chromium's fake camera plays a .y4m file: a few seconds of a labelled sample photo with a slow drift."""
    out = Path(tempfile.mkdtemp()) / "cam.y4m"
    # the drift stays within 10 px of the top-left corner, so the "Sample photo (AI-generated)" tag is never cut off
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(photo), "-t", "4", "-r", "10",
                    "-vf", "scale=1024:768,crop=1000:750:5+5*sin(t):4+4*cos(t),scale=640:480,format=yuv420p",
                    "-f", "yuv4mpegpipe", str(out)], check=True)
    return out


def sample_step_n(pg: Any, sample: str) -> int:
    """The step the labelled sample after-photo shows in the live plan on screen, picked by the app's own rule
    (api/sample_step.py, the same pick the "Sample photo" button uses). 0 when the plan has no steps."""
    from api import sample_step

    pick = sample_step.pick(sample, pg.evaluate("(S && S.plan && S.plan.steps) || []"))
    if pick and not pick["shows"]:
        print(f"sample step: no step of this live plan names what the {sample} after-photo shows, using the last step", flush=True)
    return int(pick["n"]) if pick else 0


# the live camera guide aims at a big, plain part of the pump photo: SAM 3.1 finds "electric pump motor" on the fake
# camera frames at once (about 0.66 confidence, tested 6 Nov 2026), while the small brass priming plug is often missed.
# Plans that never name the motor get a pipe (the white suction or discharge pipe is just as easy), then the pump.
LIVE_PART = ("motor", "pipe", "pump")


def live_step_n(pg: Any) -> int:
    """The step of the live pump plan whose part is the first LIVE_PART word found in the parts' SAM phrases
    (the blue electric motor of the pump, else a pipe, else the pump body). 0 when no step names one."""
    comps = pg.evaluate("((S && S.object_report && S.object_report.components) || []).map((c) => [c.id, c.sam_phrase || ''])")
    steps = pg.evaluate("((S && S.plan && S.plan.steps) || []).map((x) => [x.n, x.component_id || ''])")
    phrase = {str(cid): str(ph).lower() for cid, ph in comps}
    for word in LIVE_PART:
        for n, cid in steps:
            if word in phrase.get(str(cid), ""):
                return int(n)
    return 0


PUBLIC_BASE = os.environ.get("DEMO_PUBLIC_BASE", "https://tukang-copilot.onrender.com").rstrip("/")


def public_links(ctx: Any, base: str) -> None:
    """Links in the hand-off message read like the public site's, never like this machine's address.

    The app builds them from PUBLIC_BASE_URL, else from the request host, so a server on this machine writes
    "http://127.0.0.1:8765/guide/..." into the WhatsApp summary. Here the hand-off answer is passed through and only
    that host is swapped for PUBLIC_BASE: the same text the deployed site (PUBLIC_BASE_URL set) sends. The model
    answers in it are untouched."""
    local = base.rstrip("/")

    def swap(route: Any) -> None:
        resp = route.fetch()
        route.fulfill(response=resp, body=resp.text().replace(local, PUBLIC_BASE))

    ctx.route("**/api/sessions/*/handoff*", swap)


TZ = "Asia/Jakarta"  # the browser clock of every shot and clip: WIB, where the app's owners are (chat times, garage dates)


# --- recorded answers (DEMO_RECORDED_DATA): no new model work except the live camera guide
REPLAY_JSON = ROOT / "web" / "replay" / "demo.json"
TRACK_RE = r"/api/sessions/[^/]+/steps/\d+/track$"  # the live camera guide: the one request allowed to call a model


def recorded() -> bool:
    return bool(os.environ.get("DEMO_RECORDED_DATA"))


def site(base: str) -> str:
    """Where pages are opened: the public address in recorded mode (relayed to `base`), else the local server."""
    return PUBLIC_BASE if recorded() else base


def recorded_session(sample: str, lang: str, diagram: bool = False) -> str:
    """The newest recorded live session of a sample repair in a language (with a Muse Image diagram when asked)."""
    from api.settings import settings

    best: tuple[float, str] | None = None
    for f in (settings.data_dir / "sessions").glob("*/session.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("sample") != sample or d.get("lang") != lang or d.get("mode") != "live" or d.get("status") not in ("ready", "stopped"):
            continue
        if diagram and not any((v or {}).get("file") for v in (d.get("diagrams") or {}).values()):
            continue
        if best is None or float(d.get("created") or 0) > best[0]:
            best = (float(d.get("created") or 0), str(d["id"]))
    if best is None:
        raise SystemExit(f"no recorded live {sample} session in {lang} under {settings.data_dir}: record one with a live run first")
    return best[1]


def spent_total() -> float:
    """Every recorded session's cost on this server (the app's own meter, api/guard.py adds it up the same way)."""
    from api.settings import settings

    total = 0.0
    for f in (settings.data_dir / "sessions").glob("*/session.json"):
        total += float((json.loads(f.read_text(encoding="utf-8")).get("cost") or {}).get("spent_usd") or 0.0)
    return total


def no_new_runs(ctx: Any, errors: list[str]) -> None:
    """Recorded mode: a request that would start new model work (a new repair, an answer, a photo check, a re-plan,
    a voice command, a WhatsApp message) is refused and fails the run. The recording answers those inside the page
    (web/replay.js), so one reaching the network means the page left the recording."""
    import re

    def check(route: Any) -> None:
        r = route.request
        if r.method == "POST" and not re.search(TRACK_RE, r.url.split("?")[0]):
            errors.append(f"refused a new model call in recorded mode: POST {r.url}")
            route.abort()
            return
        route.fallback()

    ctx.route("**/api/**", check)


def owner_token(sid: str) -> str:
    """The owner token stored with a recorded session (the server gave it to the phone that made the repair)."""
    from api.settings import settings

    d = json.loads((settings.data_dir / "sessions" / sid / "session.json").read_text(encoding="utf-8"))
    return str(d.get("owner_token") or "")


def open_recorded(pg: Any, origin: str, sid: str, lang: str) -> None:
    """Open a recorded session the way the app reopens one after a reload (/#id), in the given UI language, as the
    phone that made it: its owner token goes into the page's store first (web/app.js ownerSet, key tc_owner), since
    the live camera guide, step checks and "Still broken" answer 403 without it (1.32.0)."""
    pg.goto(f"{origin}/")
    pg.evaluate("([id, tok]) => { let m = {}; try { m = JSON.parse(localStorage.getItem('tc_owner') || '{}') || {}; } catch (_) {}"
                " m[id] = tok; localStorage.setItem('tc_owner', JSON.stringify(m)); }", [sid, owner_token(sid)])
    pg.goto(f"{origin}/#{sid}")
    pg.reload()
    pg.wait_for_selector("#result:not(.hidden), #stopBox:not(.hidden)", timeout=30000)
    if pg.input_value("#lang") != lang:  # the picker remembers the last language of this browser: switch like an owner would
        pg.select_option("#lang", lang)
        pg.wait_for_timeout(400)


def serve_as_public(ctx: Any, base: str) -> None:
    """Requests to PUBLIC_BASE are answered by the server at `base`, so a page can be opened at the public address."""
    local = base.rstrip("/")

    def relay(route: Any) -> None:
        route.fulfill(response=route.fetch(url=route.request.url.replace(PUBLIC_BASE, local, 1)))

    ctx.route(PUBLIC_BASE + "/**", relay)


DIAGRAM_TRIES = 3  # live plans differ run to run: the faucet plan asks Muse Image for a diagram most times, not every time


def faucet_with_diagram(pg: Any, base: str) -> None:
    """Open the English faucet sample until its live plan has a step with a Muse Image diagram (at most DIAGRAM_TRIES
    live runs), so the diagram shot and scene always have one to show. Ticks the safety list on the way."""
    for attempt in range(DIAGRAM_TRIES):
        pg.goto(base + "/")
        pg.select_option("#lang", "en")
        pg.wait_for_timeout(300)
        pg.click('button.sample[data-sample="faucet"]')
        pg.wait_for_selector("#result:not(.hidden)", timeout=LIVE_MS)
        has = pg.evaluate("Object.values((S && S.diagrams) || {}).some((d) => d && d.file)")  # the app's own stepImage() rule
        if has:
            break
        print(f"faucet plan {attempt + 1} has no diagram step, asking again", flush=True)
    else:
        raise SystemExit(f"no Muse Image diagram in {DIAGRAM_TRIES} live faucet plans")
    for box in pg.locator("#preList input").all():
        box.check()
    pg.wait_for_timeout(200)


def _console_watch(pg: Any, errors: list[str]) -> None:
    """Collect JS errors and console errors: the finished shots and clips must not come from a page that broke."""
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)


def shots() -> None:
    from playwright.sync_api import sync_playwright

    SHOTS.mkdir(parents=True, exist_ok=True)
    base, srv = _server()
    rec, origin = recorded(), site(base)
    spent_before = spent_total() if rec else 0.0
    from api.main import _dark_photo

    dark = Path(tempfile.mkdtemp()) / "dark.jpg"
    dark.write_bytes(_dark_photo("motor"))  # the after-photo shot in a dark corner: the check asks for the torch
    cam = _fake_camera_y4m(FIX / "sample_pump_overview.jpg")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=_chromium(), args=[
            "--no-proxy-server", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream",
            f"--use-file-for-fake-video-capture={cam}"])
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True, locale="id-ID",
                            timezone_id=TZ)
        ctx.grant_permissions(["camera", "microphone"], origin=origin)
        ctx.add_init_script(SR_STUB)
        page_errors: list[str] = []
        if rec:
            serve_as_public(ctx, base)    # pages at the public address, answered by this server
            no_new_runs(ctx, page_errors)  # registered last, so it sees every /api request first
        else:
            public_links(ctx, base)
        pg = ctx.new_page()
        _console_watch(pg, page_errors)

        def snap(name: str, full: bool = False) -> None:
            pg.wait_for_timeout(350)
            if pg.is_visible("#tourClose"):  # the 1-tap demo's tip bar would cover the bottom of the still
                pg.click("#tourClose"); pg.wait_for_timeout(250)
            # never mid screen change: a view transition paints old and new screen shifted over each other
            pg.wait_for_function("() => !document.documentElement.matches(':active-view-transition')", timeout=5000)
            pg.screenshot(path=str(SHOTS / f"{name}.png"), full_page=full)
            print("shot", name, flush=True)

        def top_at(sel: str, y: int = 80) -> None:
            """Scroll so `sel` starts just under the sticky header (65 px): no half-hidden line at the top of a shot.
            Measured again after each scroll until it holds, since a late image or a re-render above can shift it."""
            for _ in range(5):
                pg.evaluate("([s, y]) => { const el = document.querySelector(s);"
                            " window.scrollTo({top: Math.max(0, el.getBoundingClientRect().top + scrollY - y), behavior: 'instant'}); }", [sel, y])
                pg.wait_for_timeout(250)
                off = pg.evaluate("([s, y]) => document.querySelector(s).getBoundingClientRect().top - y", [sel, y])
                at_end = pg.evaluate("scrollY <= 0 || innerHeight + scrollY >= document.documentElement.scrollHeight - 1")
                if abs(off) < 2 or at_end:
                    break

        def go_sample(sample: str, lang: str = "id") -> None:
            pg.goto(base + "/"); pg.select_option("#lang", lang); pg.wait_for_timeout(200)
            pg.click(f'button.sample[data-sample="{sample}"]')

        def go_to_step(n: int) -> None:
            """Walk the step card to step n of the plan on screen (0 = stay)."""
            for _ in range(12):
                cur = pg.inner_text("#stepNo").strip()
                if not n or cur == str(n):
                    break
                pg.click("#nextBtn" if int(cur or 1) < n else "#prevBtn"); pg.wait_for_timeout(350)

        def tick_preflight() -> None:
            for box in pg.locator("#preList input").all():
                box.check()
            pg.wait_for_timeout(200)

        def no_tour() -> None:
            """The 1-tap demo's tip bar would cover the bottom of a still: close it (it stays closed for the tab)."""
            if pg.is_visible("#tourClose"):
                pg.click("#tourClose")
                pg.wait_for_timeout(200)

        def check_done() -> None:
            """A step check has answered: the result line has its pass or fail class and no "Checking…" left."""
            pg.wait_for_function("() => { const el = document.querySelector('#checkResult');"
                                 " return (el.classList.contains('isPass') || el.classList.contains('isFail'))"
                                 " && !el.textContent.includes('…'); }", timeout=LIVE_MS)

        if rec:
            # the motorbike repair from the recorded 1-tap demo (real live answers, "Recorded demo" badge on screen)
            pg.goto(origin + "/"); pg.wait_for_selector("#goBtn")
            pg.set_input_files("#photo", str(FIX / "sample_motor_plug_area.jpg"))
            pg.fill("#text", "Motor saya Honda Beat susah hidup, distarter cuma bunyi tapi mesin nggak nyala.")
            pg.evaluate("document.activeElement && document.activeElement.blur(); window.scrollTo(0, 0)")
            snap("01_home")  # nothing is sent: the first screen with a photo picked and the problem typed
            pg.goto(origin + "/?replay=1"); pg.select_option("#lang", "id"); pg.wait_for_timeout(300)
            # the recording plays one stage a tick (0.9 s); a slower tick leaves time to shoot the progress screen
            # before the question arrives (same recorded snapshots, only spaced out)
            pg.evaluate("window.TCReplay._state.tick = 3000")
            pg.click("#demoBtn"); pg.wait_for_selector("#progress:not(.hidden)")
            no_tour()
            pg.wait_for_selector("#lf-segment img", timeout=30000)
            pg.wait_for_function("() => document.querySelector('#lf-segment img').naturalWidth > 0", timeout=10000)
            top_at("#progress", 72)
            snap("02_progress")
            pg.evaluate("window.TCReplay._state.tick = 900")
            pg.wait_for_selector("#question:not(.hidden), #result:not(.hidden)", timeout=30000)
            no_tour()
            if pg.is_visible("#question"):  # only when the recorded run asked its follow-up (demo.json "asked")
                pg.fill("#answerText", ANSWER)  # the "Ya" quick answer; the recorded answer starts with it and is in the log
                pg.evaluate("document.activeElement && document.activeElement.blur()")
                top_at("#question"); snap("03_question")
                pg.click("#answerBtn")
            else:
                print("recorded run asked no follow-up question (top cause sure enough): no 03_question", flush=True)
            pg.wait_for_selector("#result:not(.hidden)", timeout=30000)
            no_tour()
            top_at("#dxSummary"); snap("04_diagnosis")
            top_at("#partsWrap", 72); snap("05_parts")
            top_at("#result .safety", 84); snap("15_preflight")
            tick_preflight()
            top_at("#stepCard", 72); snap("06_step")
            pg.click("#sampleBad"); check_done()  # the recorded check of the too-dark sample photo
            top_at("#stepPhotoLabel"); snap("07_check_fail")
            pg.click("#sampleGood"); check_done()  # the plug cap photo, checked on the step it shows
            top_at("#stepPhotoLabel"); snap("08_check_pass")
        else:
            for attempt in range(3):  # live: the model asks a follow-up only when unsure, and the screenshots need one
                pg.goto(base + "/"); pg.wait_for_selector("#goBtn")
                pg.set_input_files("#photo", str(FIX / "sample_motor_plug_area.jpg"))
                pg.fill("#text", "Motor saya Honda Beat susah hidup, distarter cuma bunyi tapi mesin nggak nyala.")
                pg.evaluate("document.activeElement && document.activeElement.blur(); window.scrollTo(0, 0)")
                snap("01_home")
                pg.click("#goBtn"); pg.wait_for_selector("#progress:not(.hidden)")
                # partial results stream in as each live stage finishes
                pg.wait_for_selector("#lf-segment img", timeout=LIVE_MS)
                pg.wait_for_function("() => document.querySelector('#lf-segment img').naturalWidth > 0", timeout=10000)
                top_at("#progress", 72)
                snap("02_progress")
                pg.wait_for_selector("#question:not(.hidden), #result:not(.hidden)", timeout=LIVE_MS)
                if pg.is_visible("#question"):
                    break
                print("no follow-up question this time, again", flush=True)
            pg.fill("#answerText", ANSWER)  # one yes/no question since 1.30.0: a plain yes, like the quick "Ya" chip
            pg.evaluate("document.activeElement && document.activeElement.blur()")
            top_at("#question"); snap("03_question")
            pg.click("#answerBtn"); pg.wait_for_selector("#result:not(.hidden)", timeout=LIVE_MS)
            top_at("#dxSummary"); snap("04_diagnosis")       # the likely causes with their confidence
            top_at("#partsWrap", 72); snap("05_parts")       # the SAM 3.1 masks on the photo, numbered
            top_at("#result .safety", 84); snap("15_preflight")
            tick_preflight()
            top_at("#stepCard", 72); snap("06_step")
            pg.set_input_files("#stepPhoto", str(dark))
            pg.wait_for_function("() => !document.querySelector('#checkResult').textContent.includes('…')", timeout=LIVE_MS)
            top_at("#stepPhotoLabel"); snap("07_check_fail")
            go_to_step(sample_step_n(pg, "motor"))  # the sample after-photo shows the plug cap pushed back on
            pg.set_input_files("#stepPhoto", str(FIX / "sample_motor_step_cap_on.jpg"))
            pg.wait_for_timeout(600)
            pg.wait_for_function("() => !document.querySelector('#checkResult').textContent.includes('…')", timeout=LIVE_MS)
            top_at("#stepPhotoLabel"); snap("08_check_pass")
        pg.wait_for_timeout(2000)
        pg.locator("#agent .agGo", has_text="Langkah 1 dicek").first.click()          # tap a log line → back to that step
        pg.wait_for_selector("#stepCard.flash"); pg.wait_for_timeout(900)
        pg.evaluate("window.scrollBy(0, -40)"); snap("24_agent_jump")
        pg.check("#handsFree"); pg.wait_for_selector("#voiceBar:not(.hidden)", timeout=5000); pg.wait_for_timeout(600)
        top_at("#prevBtn"); snap("17_hands_free")
        pg.uncheck("#handsFree")
        pg.fill("#stuckText", "Sudah dicoba, mesin tetap tidak nyala."); pg.click("#stuckBtn")
        pg.wait_for_function("() => document.querySelector('#stuckMsg').textContent.length > 3 && !document.querySelector('#stuckBtn').disabled",
                             timeout=LIVE_MS); pg.wait_for_timeout(600)
        pg.wait_for_selector("#planBanner:not(.hidden)"); pg.evaluate("window.scrollTo(0, 0)"); snap("09_replan")  # re-plan banner + tried cause
        pg.evaluate("document.querySelector('#agent').scrollIntoView({block: 'start'}); window.scrollBy(0, -70)"); snap("23_agent_log")
        tick_preflight()
        for _ in range(6):  # back to step 1 so the hand-off and PDF shots below match earlier takes
            if pg.is_disabled("#prevBtn"):
                break
            pg.click("#prevBtn"); pg.wait_for_timeout(150)
        msid = pg.evaluate("S && S.id")
        mpdf = Path(tempfile.mkdtemp()) / "motor.pdf"
        # recorded: the report and share card recorded with the demo (the replay serves these same files)
        mpdf.write_bytes(pg.request.get(f"{base}/static/replay/report-id.pdf" if rec else f"{base}/api/sessions/{msid}/report.pdf").body())
        # the PDF pages are drawn as images (no text layer); in this motorbike report the agent log is on page 2
        info = subprocess.run(["pdfinfo", str(mpdf)], capture_output=True, text=True).stdout
        page_no = 2 if any(ln.startswith("Pages:") and int(ln.split()[1]) >= 2 for ln in info.splitlines()) else 1
        subprocess.run(["pdftoppm", "-png", "-r", "110", "-f", str(page_no), "-l", str(page_no), "-singlefile", str(mpdf),
                        str(SHOTS / "25_pdf_agent")], check=True)
        print("shot 25_pdf_agent (page", page_no, ")", flush=True)
        (SHOTS / "26_share_card.png").write_bytes(pg.request.get(f"{base}/static/replay/card-id.png" if rec else f"{base}/api/sessions/{msid}/card.png").body())
        print("shot 26_share_card", flush=True)
        top_at("#result .actions", 72); snap("12_report")  # the share and report buttons, starting under the header
        pg.click("#mechBtn"); pg.wait_for_selector("#handoff:not(.hidden)", timeout=10000)
        pg.evaluate("document.querySelector('#handoff details') && (document.querySelector('#handoff details').open = true)")
        top_at("#mechBtn"); snap("18_handoff")
        # live camera guide on the pump repair (Chromium fake camera playing a labelled sample photo)
        if rec:
            open_recorded(pg, origin, recorded_session("pump", "id"), "id")
        else:
            go_sample("pump"); pg.wait_for_selector("#result:not(.hidden)", timeout=LIVE_MS)
        pg.evaluate("window.scrollTo(0,0)"); snap("10_pump")
        tick_preflight()
        go_to_step(live_step_n(pg))
        pg.click("#liveBtn"); pg.wait_for_selector("#live:not(.hidden)")
        top_at("#liveBtn")
        # the live line says "Found <part>" in the page's language (the 🎯 can be drawn as an icon, so match the words)
        locked = ("() => document.querySelector('#liveState').textContent"
                  ".includes(t('liveFound').replace('{name}', '').replace('🎯', '').trim())")
        # Polled from here (every 250 ms, at most 30 s) instead of a page-side wait: each frame the page sends is a paid
        # SAM 3.1 call, so the camera closes as soon as the shot is in. The outline comes and goes with the drift of the
        # fake camera, so the shot is taken only while the line says the part is found.
        shot_ok = False
        for _ in range(120):
            if pg.evaluate(locked):
                pg.wait_for_timeout(300)  # let the outline paint
                if pg.evaluate(locked):
                    pg.screenshot(path=str(SHOTS / "16_live_guide.png"))
                    shot_ok = True
                    break
            pg.wait_for_timeout(250)
        if not shot_ok:
            page_errors.append("live guide: SAM 3.1 did not find the part within 30 s (16_live_guide not taken)")
        print("shot 16_live_guide", flush=True)
        pg.click("#liveClose")
        # safety stop with PDF + hand-off
        if rec:
            open_recorded(pg, origin, recorded_session("rice", "id"), "id")
        else:
            go_sample("rice")
        pg.wait_for_selector("#stopBox:not(.hidden)", timeout=LIVE_MS)
        pg.wait_for_selector("#stopHandoff:not(.hidden)", timeout=10000)
        pg.evaluate("window.scrollTo(0, 0)"); snap("11_rice_stop")  # the STOP card sits under the "Stopped for your safety" heading
        top_at("#stopBox > p:nth-of-type(3)"); snap("22_stop_handoff")  # "Do this now", the service buttons, the hand-off
        sid = pg.evaluate("S && S.id")
        pdf = Path(tempfile.mkdtemp()) / "stop.pdf"
        pdf.write_bytes(pg.request.get(f"{base}/api/sessions/{sid}/report.pdf").body())
        subprocess.run(["pdftoppm", "-png", "-r", "110", "-f", "1", "-l", "1", "-singlefile", str(pdf), str(SHOTS / "19_stop_pdf")], check=True)
        print("shot 19_stop_pdf", flush=True)
        if rec:
            open_recorded(pg, origin, recorded_session("faucet", "en", diagram=True), "en")
            tick_preflight()
        else:
            faucet_with_diagram(pg, base)
        pg.evaluate("window.scrollTo(0,0)"); snap("13_english")
        # the step Muse Image drew a diagram for (the washer inside the tap)
        for _ in range(10):
            if "diagram" in (pg.get_attribute("#stepImg", "src") or "") and pg.is_visible("#stepImg"):
                break
            pg.click("#nextBtn"); pg.wait_for_timeout(300)
        top_at("#stepCard", 72); snap("28_diagram_step")
        if rec:
            open_recorded(pg, origin, recorded_session("tire", "jv"), "jv")
        else:
            go_sample("tire", "jv"); pg.wait_for_selector("#result:not(.hidden)", timeout=LIVE_MS)
        pg.evaluate("window.scrollTo(0,0)"); snap("20_javanese_result")
        pg.goto(origin + "/"); pg.select_option("#lang", "jv"); pg.wait_for_timeout(300); snap("14_garage_jv", full=True)
        # recorded demo: what a visitor sees when the server sleeps (forced here with ?replay=1)
        pg.goto(origin + "/?replay=1"); pg.select_option("#lang", "en"); pg.click("#demoBtn")
        pg.wait_for_selector("#question:not(.hidden), #result:not(.hidden)", timeout=20000)
        if pg.is_visible("#question"):
            pg.click('#quickAns button[data-q="qNo"]')
        pg.wait_for_selector("#result:not(.hidden)", timeout=20000)
        if pg.is_visible("#tourClose"):
            pg.click("#tourClose")  # the tip bar would sit over the diagnosis in a still
        pg.evaluate("window.scrollTo(0, 0)"); snap("27_recorded_demo")
        # laptop view: phone frame + side panel (QR code, 1-tap demo, language switch)
        # opened at the public address (served by this server), so the QR code and its caption show what a visitor of
        # the deployed site sees, not this machine's "127.0.0.1 only works on this computer"
        lap_ctx = b.new_context(viewport={"width": 1280, "height": 800}, timezone_id=TZ)
        serve_as_public(lap_ctx, base)
        lap = lap_ctx.new_page()
        lap.goto(PUBLIC_BASE + "/"); lap.select_option("#lang", "en"); lap.wait_for_selector("#qrBox svg", timeout=5000); lap.wait_for_timeout(400)
        lap.screenshot(path=str(SHOTS / "29_laptop.png")); print("shot 29_laptop", flush=True)
        b.close()
    srv.should_exit = True
    if rec:
        print(f"live spend of this run (app cost meter, live camera guide only): ${spent_total() - spent_before:.4f}", flush=True)
    if page_errors:
        raise SystemExit("page errors while shooting:\n" + "\n".join(page_errors))
    print("screenshots ->", SHOTS, sorted(p.name for p in SHOTS.glob("*.png")))


# --- WhatsApp simulator
WA_SHOTS = ["30_whatsapp_jv_diagnosis", "30_whatsapp_jv_steps", "30_whatsapp_jv_redstop", "30_whatsapp_en_check", "30_whatsapp_en_pdf"]


def wa_shots() -> None:
    """The WhatsApp simulator page (/wa, live Meta answers with WA_SIM=1): the same handler as the real Cloud API webhook, so these show what a
    WhatsApp chat gets. Javanese: photo in, marked photo + diagnosis, step buttons, red stop; English: a step check and
    the PDF report. Not a real WhatsApp number (that waits on my Meta setup, docs/WHATSAPP.md)."""
    from playwright.sync_api import sync_playwright

    if recorded():
        # the simulator keeps its chat in server memory only, so there is no recording to play back: these shots
        # need live answers (`wa` without DEMO_RECORDED_DATA, about $0.15). The ones in the folder are kept.
        print("recorded mode: WhatsApp shots kept as they are (re-make them with a live `wa` run)", flush=True)
        return
    SHOTS.mkdir(parents=True, exist_ok=True)
    base, srv = _server()
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=_chromium(), args=["--no-sandbox", "--no-proxy-server"])
        for lang in ("jv", "en"):
            pg = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3, timezone_id=TZ)
            errors: list[str] = []
            _console_watch(pg, errors)

            def snap(name: str) -> None:
                pg.wait_for_timeout(800)
                pg.screenshot(path=str(SHOTS / f"{name}.png")); print("shot", name, flush=True)

            pg.goto(base + f"/wa?lang={lang}"); pg.wait_for_selector("#chips button")
            pg.locator("#chips button").nth(0).click()                       # sample: dripping kitchen tap
            pg.wait_for_selector(".btns button", timeout=LIVE_MS)
            if lang == "jv":
                pg.wait_for_timeout(800)
                # the diagnosis message (marked photo + likely cause) at the top of the chat
                pg.evaluate("""(() => { const log = document.getElementById('log');
                  const row = [...log.querySelectorAll('.row:not(.me)')].find((r) => r.textContent.includes('🩺'));
                  log.scrollTop += row.getBoundingClientRect().top - log.getBoundingClientRect().top - 8; })()""")
                snap("30_whatsapp_jv_diagnosis")
                pg.evaluate("document.getElementById('log').scrollTop = 1e9")
                snap("30_whatsapp_jv_steps")
                pg.goto(base + f"/wa?lang={lang}"); pg.evaluate("sessionStorage.clear()"); pg.reload()
                pg.wait_for_selector("#chips button")
                pg.locator("#chips button").nth(3).click()                   # sample: gas smell -> red stop
                pg.wait_for_function("() => document.querySelectorAll('.row:not(.me)').length >= 1", timeout=LIVE_MS)
                pg.wait_for_timeout(700)
                snap("30_whatsapp_jv_redstop")
            else:
                # the sample "after" photo (dry spout): checked on the step it shows, with a line saying which one.
                # A pass on the plan's last step ends the guide (PDF in the chat); on an earlier step the next step follows.
                pg.locator("#chips button").nth(4).click()
                pg.wait_for_function("() => [...document.querySelectorAll('.row:not(.me)')].some((r) => /sample photo/.test(r.textContent))"
                                     " && (document.querySelector('.doc') || document.querySelectorAll('.btns').length >= 2)", timeout=LIVE_MS)
                pg.wait_for_timeout(800)
                pg.evaluate("""(() => { const log = document.getElementById('log');
                  const row = [...log.querySelectorAll('.row:not(.me)')].reverse().find((r) => /sample photo/.test(r.textContent));
                  log.scrollTop += row.getBoundingClientRect().top - log.getBoundingClientRect().top - 120; })()""")
                snap("30_whatsapp_en_check")
                if not pg.locator(".doc").count():
                    pg.locator(".btns").last.locator("button").nth(2).click()  # Stop -> PDF report in the chat
                pg.wait_for_selector(".doc", timeout=LIVE_MS)
                pg.evaluate("document.getElementById('log').scrollTop = 1e9")
                snap("30_whatsapp_en_pdf")
            if errors:
                raise SystemExit(f"/wa page errors: {errors}")
            pg.close()
        b.close()
    srv.should_exit = True


# --- architecture diagram
def diagram() -> None:
    """docs/img/architecture.png in the app's look: concrete page, white plates, Barlow, safety colours by meaning."""
    import demo_video as dv

    f = dv.font
    im = dv.concrete(W, H).copy()
    d = ImageDraw.Draw(im)
    dv.brand_row(im, 80, 52, size=54)
    d.text((80, 118), "One agent loop, five Meta models", font=f("black", 76), fill=dv.INK)
    dv.draw_text(d, (82, 204), "plan → act → verify → re-plan, with a safety gate in code", f("body", 32), dv.MUTED)
    blue, red, green, ink = dv.TONE["info"], dv.TONE["stop"], dv.TONE["ok"], dv.INK
    boxes = [  # title, model chip, two lines, top-left, accent
        ("Phone (PWA)", "", "photo · voice · text\nid / jv / en", (80, 290), ink),
        ("Listen", "Voice Transcribe", "Javanese audio:\nMuse Spark 1.2", (440, 290), blue),
        ("Look", "Muse Spark 1.3", "vision → ObjectReport\nJSON", (800, 290), blue),
        ("Find parts", "SAM 3.1", "masks on the photo\nand the live camera", (1160, 290), blue),
        ("Diagnose", "Muse Spark 1.3", "or Muse Spark Open*\n(open weights)", (1520, 290), blue),
        ("Safety gate", "code", "3 layers, red = STOP\nand hand to a pro", (1520, 590), red),
        ("Plan", "Muse Spark", "steps with the\nexpected state", (1160, 590), blue),
        ("Illustrate", "Muse Image", "edit of your photo\nwhen a photo can't show it", (800, 590), blue),
        ("Verify step", "Muse Spark", "new photo → pass\nor a correction", (440, 590), green),
        ("Report", "", "PDF · bengkel hand-off\n· My garage", (80, 590), ink),
    ]
    bw, bh = 320, 210
    for title, chip, sub, (x, y), col in boxes:
        d.rounded_rectangle([x + 4, y + 8, x + bw + 4, y + bh + 8], radius=22, fill=(214, 216, 210))
        d.rounded_rectangle([x, y, x + bw, y + bh], radius=22, fill=dv.PLATE)
        d.rounded_rectangle([x, y, x + 10, y + bh], radius=5, fill=col)
        d.text((x + 30, y + 22), title, font=f("black", 44), fill=ink)
        if chip:
            dv.pill(im, (x + 30, y + 80), chip, f("semi", 22), (255, 255, 255), col, (12, 5))
        for j, line in enumerate(sub.split("\n")):
            dv.draw_text(d, (x + 30, y + 128 + j * 31), line, f("body", 25), dv.MUTED)

    def arrow(a: tuple[int, int], b: tuple[int, int]) -> None:
        d.line([a, b], fill=dv.TONE["act"], width=7)
        ax, ay = b
        dx, dy = (b[0] - a[0]), (b[1] - a[1])
        n = max(1.0, (dx * dx + dy * dy) ** 0.5)
        ux, uy = dx / n, dy / n
        d.polygon([(ax, ay), (ax - 24 * ux + 13 * uy, ay - 24 * uy - 13 * ux), (ax - 24 * ux - 13 * uy, ay - 24 * uy + 13 * ux)], fill=dv.TONE["act"])

    for x in (400, 760, 1120, 1480):
        arrow((x + 2, 395), (x + 38, 395))
    arrow((1680, 500), (1680, 590))
    for x in (1520, 1160, 800, 440):
        arrow((x - 2, 695), (x - 38, 695))
    d.line([(600, 800), (600, 840), (1320, 840), (1320, 800)], fill=dv.TONE["act"], width=5)
    dv.draw_text(d, (640, 850), "fails twice → re-plan to the next cause (or escalate to a professional)", f("body", 27), ink)
    d.text((80, 906), "* USE_OPEN_WEIGHTS=true runs Diagnose + Plan on Muse Spark Open (open weights) on Baseten.", font=f("body", 22), fill=dv.MUTED)
    d.text((80, 936), "All calls go through api/meta_client.py: auth, retries, timeouts, JSON-schema checks, a per-session cost cap.",
           font=f("body", 22), fill=dv.MUTED)
    ARCH.parent.mkdir(parents=True, exist_ok=True)
    im.save(ARCH)
    print("diagram ->", ARCH)


# --- voice-over
LUFS = -16.0      # loudness of every voice clip (and of the finished video), the usual target for online video
TRUE_PEAK = -1.5
TIMING = VOICE / "timing.json"   # each clip's captions: [start s, end s, text] in the clip, measured from the takes


def _loudnorm(src: Path, out: Path) -> None:
    """Two-pass EBU R128 loudness normalisation (linear, so short clips are not pumped) to LUFS / TRUE_PEAK."""
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-af",
                            f"loudnorm=I={LUFS}:TP={TRUE_PEAK}:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True, check=True).stderr
    m = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
    af = (f"loudnorm=I={LUFS}:TP={TRUE_PEAK}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-af", f"{af},aresample=24000",
                    "-ac", "1", "-c:a", "libmp3lame", "-b:a", "128k", str(out)], check=True)


def all_scenes() -> list[Scene]:
    """Every scene that has a voice clip: the main film and the vertical cut."""
    return scenes() + VSCENES


def voice() -> None:
    """edge-tts (Microsoft neural voices, free, needs internet). Set EDGE_TTS_PROXY if the network needs a proxy.

    One mp3 per scene in docs/demo/voice. Each sentence is its own take, so the narrator pauses between sentences the
    way a person reading a script does (SENTENCE_GAP_S), and the owner's line (Bahasa or Basa Jawa) comes first with
    its own pause. The joined clip is loudness-normalised. timing.json keeps where each caption starts and ends, so
    the burned-in captions and the .srt follow the real takes instead of a guess from the text length."""
    import edge_tts

    VOICE.mkdir(parents=True, exist_ok=True)
    proxy = os.environ.get("EDGE_TTS_PROXY")
    if not proxy:  # aiohttp chokes on some proxy URLs in the environment; edge-tts goes direct unless EDGE_TTS_PROXY is set
        for k in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy", "ALL_PROXY", "all_proxy"):
            os.environ.pop(k, None)

    said_file = VOICE / "script.json"  # the text each mp3 was made from: a changed line is re-recorded
    said: dict[str, str] = json.loads(said_file.read_text()) if said_file.exists() else {}
    timing: dict[str, list[list[Any]]] = json.loads(TIMING.read_text()) if TIMING.exists() else {}
    if any(not isinstance(v, list) for v in timing.values()):
        timing = {}  # the older format (one float per scene): every clip is made again
    import demo_video as dv

    tmp = dv.WORK / "voice-parts"  # the takes before joining: build folder, outside the repo
    tmp.mkdir(parents=True, exist_ok=True)

    async def tts(text: str, name: str, out: Path) -> float:
        """One take as a 24 kHz mono wav, with the dead air edge-tts leaves at each end cut off (80 ms kept, so no
        word loses its first or last sound). Returns its length."""
        raw = tmp / (out.stem + ".raw.mp3")
        rate = VOICE_RATE if name == VOICE_NAME else OWNER_RATE
        for attempt in range(4):  # the free service sometimes answers with no audio: wait a little and ask again
            try:
                await edge_tts.Communicate(text, name, rate=rate, proxy=proxy).save(str(raw))
                break
            except edge_tts.exceptions.NoAudioReceived:
                if attempt == 3:
                    raise
                print(f"edge-tts sent no audio for {out.stem}, trying again", flush=True)
                await asyncio.sleep(2 + 3 * attempt)
        trim = "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.08"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", f"{trim},areverse,{trim},areverse,aresample=24000",
                        "-ac", "1", "-c:a", "pcm_s16le", str(out)], check=True)
        return _dur(out)

    async def run() -> None:
        for sc in all_scenes():
            out = VOICE / f"{sc.key}.mp3"
            said_as = json.dumps([VOICE_NAME, VOICE_RATE, OWNER_RATE, "sentences", SENTENCE_GAP_S, OWNER_PAUSE_S, LUFS,
                                  sc.pre, sc.say], ensure_ascii=False)
            if out.exists() and out.stat().st_size > 1000 and said.get(sc.key) == said_as and sc.key in timing:
                continue
            parts: list[tuple[Path, float]] = []   # (take, silence after it)
            caps: list[list[Any]] = []
            t = 0.0
            if sc.pre[1]:
                p = tmp / f"{sc.key}.pre.wav"
                d = await tts(sc.pre[1], sc.pre[0], p)
                caps.append([0.0, round(d, 3), f"“{sc.pre_en}”"])
                gap = OWNER_PAUSE_S if sc.say else 0.0
                parts.append((p, gap))
                t = d + gap
            sents = _sentences(sc.say) if sc.say else []
            for j, sent in enumerate(sents):
                p = tmp / f"{sc.key}.s{j}.wav"
                d = await tts(_spoken(sent), VOICE_NAME, p)
                caps.append([round(t, 3), round(t + d, 3), sent])
                gap = SENTENCE_GAP_S if j < len(sents) - 1 else 0.0
                parts.append((p, gap))
                t += d + gap
            joined = tmp / f"{sc.key}.joined.wav"
            ins: list[str] = []
            chain = ""
            for i, (p, gap) in enumerate(parts):
                ins += ["-i", str(p)]
                chain += f"[{i}:a]aformat=sample_rates=24000:channel_layouts=mono,apad=pad_dur={gap:.3f}[p{i}];"
            chain += "".join(f"[p{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1[o]"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", chain, "-map", "[o]", str(joined)], check=True)
            _loudnorm(joined, out)
            timing[sc.key] = caps
            said[sc.key] = said_as
            said_file.write_text(json.dumps(said, indent=1, ensure_ascii=False) + "\n")
            TIMING.write_text(json.dumps(timing, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
            print("voice", sc.key, f"{_dur(out):.2f}s", flush=True)

    asyncio.run(run())
    keys = {sc.key for sc in all_scenes()}
    said = {k: v for k, v in said.items() if k in keys}
    said_file.write_text(json.dumps(said, indent=1, ensure_ascii=False) + "\n")
    TIMING.write_text(json.dumps({k: v for k, v in timing.items() if k in keys}, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    for old in VOICE.glob("*.mp3"):  # clips of scenes that were cut go to the trash folder
        if old.stem not in keys:
            _to_trash(old)


# How the narrator should say a few written forms (the captions keep the written form).
SPOKEN = {"$0.044": "four point four cents", "1,096": "one thousand and ninety-six", "220-volt": "two hundred and twenty volt",
          "SAM 3.1": "Sam three point one", "83 seconds": "eighty-three seconds", "4 US cents": "four US cents"}


def _spoken(text: str) -> str:
    for a, b in SPOKEN.items():
        text = text.replace(a, b)
    return text


def _to_trash(p: Path) -> None:
    """Never delete for good: unwanted generated files go to the trash folder (AI_TRASH, default /workspace/.ai-trash)."""
    trash = Path(os.environ.get("AI_TRASH", "/workspace/.ai-trash")) / "tukang-copilot" / time.strftime("%Y%m%d-%H%M%S")
    trash.mkdir(parents=True, exist_ok=True)
    shutil.move(str(p), str(trash / p.name))
    print("moved to trash:", p.name, "->", trash, flush=True)


def _dur(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(p)], capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])


# --- video
def _sentences(text: str) -> list[str]:
    """One caption (and one voice take) per sentence; a very long sentence is split at a comma so a caption never
    runs past 3 lines."""
    import re

    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p.strip()]
    out: list[str] = []
    for p in parts:
        if len(p) > 120 and ", " in p:
            mid = p.find(", ", len(p) // 3)
            if mid > 0:
                out += [p[:mid + 1], p[mid + 2:]]
                continue
        out.append(p)
    return out


def _mmss(t: float) -> str:
    return f"{int(t) // 60}:{int(t) % 60:02}"


def _srt_time(t: float) -> str:
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def _timing() -> dict[str, list[list[Any]]]:
    return json.loads(TIMING.read_text()) if TIMING.exists() else {}


def scene_length(sc: Scene) -> float:
    """A scene lasts its voice-over (which starts LEAD s after the cut) plus its hold, and at least min_s."""
    import demo_video as dv

    mp3 = VOICE / f"{sc.key}.mp3"
    spoken = _dur(mp3) if ((sc.say or sc.pre[1]) and mp3.exists()) else 0.0
    return round(max(sc.min_s, dv.LEAD + spoken + sc.hold if spoken else sc.min_s), 3)


def scene_lengths() -> dict[str, float]:
    return {sc.key: scene_length(sc) for sc in scenes()}


def capture(groups: list[str]) -> None:
    """Screen recordings for the video (see scripts/demo_video.py); one group per call."""
    import demo_video as dv

    lengths = scene_lengths()
    for g in groups or list(dv.GROUPS):
        dv.capture(g, lengths)


def _shot(sc: Scene, dur: float) -> Any:
    """The scene with its captions on the scene clock: the measured takes from timing.json, shifted by LEAD. A caption
    stays up until the next one starts (or half a second after its last word)."""
    import demo_video as dv

    caps = _timing().get(sc.key, []) if (sc.say or sc.pre[1]) else []
    subs = []
    for j, (a, b, text) in enumerate(caps):
        start = dv.LEAD + float(a)
        end = dv.LEAD + float(caps[j + 1][0]) if j + 1 < len(caps) else min(dur, dv.LEAD + float(b) + 0.5)
        subs.append((round(start, 3), round(end, 3), str(text)))
    return dv.Shot(sc, dur, subs)


def _check_voice_clips(scs: list[Scene]) -> None:
    """A voice clip made from an older line would say something the captions do not: refuse it."""
    said = json.loads((VOICE / "script.json").read_text()) if (VOICE / "script.json").exists() else {}
    timing = _timing()
    for sc in scs:
        if (sc.say or sc.pre[1]) and (sc.say not in said.get(sc.key, "") or sc.key not in timing):
            raise SystemExit(f"docs/demo/voice/{sc.key}.mp3 was not made from the current line: run `voice` first")


MUSIC_DB = -9.5    # track gain before ducking: with the duck the music sits a median 20.5 dB under the voice (measured, docs/demo/README)
MUSIC_DB_VERTICAL = -12.0  # the vertical cut talks with shorter pauses, so the same gain sat only 16.7 dB under: 19.2 dB with this


def music_file() -> Path:
    """The music bed: DEMO_MUSIC, "Lucky Acoustic" by Jesse Keller (CC BY 3.0, credit in MUSIC_CREDIT). Not kept in the repo."""
    p = Path(os.environ.get("DEMO_MUSIC", ""))
    if not os.environ.get("DEMO_MUSIC") or not p.is_file():
        raise SystemExit("set DEMO_MUSIC to the music file (Lucky Acoustic by Jesse Keller, jamendo.com/track/1540859)")
    return p


def mix_music(joined: Path, out: Path, music_db: float = MUSIC_DB) -> None:
    """Put the music under the voice and normalise the mix.

    Music: music_db, a 3 dB cut around 2.5 kHz (the voice's presence band), ducked by the voice with a sidechain
    compressor (threshold 0.03, ratio 5, attack 20 ms, release 450 ms), 1.5 s fade in, 3 s fade out to the end.
    Then a two-pass loudnorm of the whole mix to -16 LUFS integrated, true peak -1.5 dBTP. The picture is copied;
    audio is AAC 192 kbps; +faststart so it streams."""
    total = _dur(joined)
    # both stems are padded to the picture's length and the mix is cut to it, so the end card keeps its music
    # (amix and sidechaincompress otherwise stop with whichever input ends first)
    graph = (f"[1:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,volume={music_db}dB,"
             f"equalizer=f=2500:t=q:w=1:g=-3,afade=t=in:d=1.5,afade=t=out:st={max(0.0, total - 3):.3f}:d=3,apad=whole_dur={total:.3f}[m];"
             f"[0:a]aresample=48000,aformat=channel_layouts=stereo,apad=whole_dur={total:.3f},asplit=2[v1][v2];"
             "[m][v1]sidechaincompress=threshold=0.03:ratio=5:attack=20:release=450[duck];"
             f"[duck][v2]amix=inputs=2:normalize=0:duration=longest,atrim=0:{total:.3f}[mix]")
    pre = out.with_suffix(".premix.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(joined), "-i", str(music_file()), "-filter_complex", graph,
                    "-map", "[mix]", "-c:a", "pcm_s16le", str(pre)], check=True)
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(pre), "-af",
                            f"loudnorm=I={LUFS}:TP={TRUE_PEAK}:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True, check=True).stderr
    m = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
    af = (f"loudnorm=I={LUFS}:TP={TRUE_PEAK}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
    # +faststart rewrites the file at the end, which can fail with an I/O error on a synced folder: write it in the
    # machine's own temp folder and move the finished file over
    tmp = Path(tempfile.mkdtemp(prefix="tukang-mix-")) / out.name
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(joined), "-i", str(pre), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-t", f"{total:.3f}",
                    "-movflags", "+faststart", str(tmp)], check=True)
    shutil.move(str(tmp), str(out))


def _render_all(scs: list[Scene], folder: Path, size: tuple[int, int], only: list[str] | None, vertical: bool) -> list[Path]:
    """Render (or reuse) one segment per scene into `folder`; returns the segment paths in order."""
    import demo_video as dv

    folder.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []
    prev_last: Path | None = None
    for i, sc in enumerate(scs):
        dur = scene_length(sc)
        shot = _shot(sc, dur)
        mp3 = VOICE / f"{sc.key}.mp3"
        seg, last = folder / f"{i:02}_{sc.key}.mkv", folder / f"{i:02}_{sc.key}.last.png"
        parts.append(seg)
        want = (only is not None and sc.key in only) or (only is None and not (seg.exists() and last.exists()))
        if want:
            t0 = time.time()
            clip_key, offset = VCLIPS.get(sc.key, (sc.key, 0.0)) if vertical else (sc.key, 0.0)
            r = dv.Renderer(shot, size, vertical=vertical, clip_offset=offset, clip_key=clip_key,
                            zooms=VERTICAL_ZOOMS if vertical else None)
            dv.render_segment(shot, seg, size, mp3 if mp3.exists() and (sc.say or sc.pre[1]) else None, prev_last, r, last)
            print(f"segment {seg.name} {dur:.1f}s in {time.time() - t0:.0f}s", flush=True)
        prev_last = last
    return parts


def _concat(parts: list[Path], out: Path) -> None:
    lst = out.with_suffix(".txt")
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)], check=True)


def video(only: list[str] | None = None) -> None:
    """Main 16:9 film, 1920x1080 at 30 fps: one cached segment per scene in $TMPDIR/tukang-video/segments (move a
    segment away to re-render it), joined, then the music mix. Run `voice` and `capture` first, with recorded clips.
    `video KEY ...` renders only those scenes and stops there."""
    import demo_video as dv

    if not dv.played_back():
        raise SystemExit("the narration says the answers were recorded on a live run: capture with DEMO_RECORDED_DATA set")
    scs = scenes()
    _check_voice_clips(scs)
    parts = _render_all(scs, dv.WORK / "segments", (W, H), only, vertical=False)
    if only is not None:
        return
    joined = dv.WORK / "segments" / "joined.mkv"
    _concat(parts, joined)
    out = DEMO / "tukang-copilot-demo.mp4"
    mix_music(joined, dv.WORK / "segments" / "final.mp4")
    shutil.move(str(dv.WORK / "segments" / "final.mp4"), str(out))
    srt: list[str] = []
    stamps: list[str] = []
    t, n = 0.0, 0
    for sc in scs:
        dur = scene_length(sc)
        for a, b, sent in _shot(sc, dur).subs:
            n += 1
            srt.append(f"{n}\n{_srt_time(t + a)} --> {_srt_time(t + b)}\n{sent}\n")
        what = " · ".join(x for x in (sc.head.rstrip("."), sc.caption or sc.pre_en or sc.say.split(". ")[0].rstrip(".")) if x)
        stamps.append(f"{_mmss(t)}  {sc.key:<11} {what}")
        t += round(dur * dv.FPS) / dv.FPS  # each segment holds whole frames: count them, so the captions never drift
    (DEMO / "tukang-copilot-demo.en.srt").write_text("\n".join(srt), encoding="utf-8")
    real = _dur(out)
    (DEMO / "TIMESTAMPS.txt").write_text(
        "Tukang Copilot demo video: scene start times (mm:ss), made by scripts/make_demo_assets.py video\n"
        f"File: docs/demo/tukang-copilot-demo.mp4, length {_mmss(real)} ({real:.1f} s, ffprobe), 1920x1080 at {dv.FPS} fps.\n"
        f"App screens: real Meta API output recorded on a live run ({dv.recorded_on()}, from {dv.recorded_time()}) and played back. "
        "AI-generated sample photos; the people-and-home stills are labelled AI-generated scenes.\n"
        "English captions are burned in; the same text is in tukang-copilot-demo.en.srt.\n"
        f"{MUSIC_CREDIT}\n\n"
        + "\n".join(stamps) + "\n", encoding="utf-8")
    if not 90 <= real <= 150:
        raise SystemExit(f"video is {real:.1f} s: the cut should be 1:30 to 2:30")
    print(f"video -> {out} ({real:.1f}s by ffprobe)")


def vertical(only: list[str] | None = None) -> None:
    """9:16 cut for X, Reels and Shorts (1080x1920, 30 fps, about 35 s): its own short voice lines over the same
    recordings, phone-sized English captions inside the safe area, the same music mix."""
    import demo_video as dv

    if not dv.played_back():
        raise SystemExit("capture with DEMO_RECORDED_DATA set first (the clip says the output was recorded)")
    _check_voice_clips(VSCENES)
    folder = dv.WORK / "vsegments"
    parts = _render_all(VSCENES, folder, (1080, 1920), only, vertical=True)
    if only is not None:
        return
    joined = folder / "vjoined.mkv"
    _concat(parts, joined)
    out = DEMO / "tukang-copilot-x-vertical.mp4"
    mix_music(joined, folder / "vfinal.mp4", MUSIC_DB_VERTICAL)
    shutil.move(str(folder / "vfinal.mp4"), str(out))
    real = _dur(out)
    if not 30 <= real <= 45:
        raise SystemExit(f"vertical clip is {real:.1f} s: it should be 30 to 45 s")
    print("vertical ->", out, f"{real:.1f}s")


# The README GIF: moments of the recordings, (recording, from s, to s)
GIF_CLIPS = [("progress", 1.4, 4.4), ("diagnosis", 0.4, 2.4), ("parts", 0.6, 2.6), ("check_pass", 0.6, 2.6),
             ("rice", 2.0, 4.0), ("tyre", 0.0, 2.0)]  # progress from 1.4 s: the stage list, not the tap on the sample
GIF_W, GIF_H = 640, 1200  # README shows it 320 px wide: 2x so it stays sharp on a phone or a retina screen
GIF_FPS = 6
GIF_MAX_BYTES = 3 * 1024 * 1024


def gif() -> None:
    """README hero: the recorded phone screens as a looping GIF, 640 px wide, from the same recordings as the video.
    Two-pass palette (one palette for the whole loop, so no colour shimmer between screens); fewer colours or
    frames until it is under GIF_MAX_BYTES."""
    import demo_video as dv

    work = dv.WORK / "gif"
    if work.exists():
        shutil.rmtree(work)  # build folder outside the repo, made again each time
    work.mkdir(parents=True)
    n = 0
    for key, a, b in GIF_CLIPS:
        clip = dv.Clip(key)
        for k in range(int(round((b - a) * GIF_FPS))):
            _, im = clip.at(a + k / GIF_FPS)
            im = im.resize((GIF_W, round(im.height * GIF_W / im.width)), Image.Resampling.LANCZOS).crop((0, 0, GIF_W, GIF_H))
            im.save(work / f"{n:04}.png")
            n += 1
    out = DEMO / "hero.gif"
    tmp = work / "hero.gif"
    colors = 128
    for colors in (128, 96, 64, 48):
        pal = work / "palette.png"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(GIF_FPS), "-i", str(work / "%04d.png"),
                        "-vf", f"palettegen=max_colors={colors}:stats_mode=full", "-frames:v", "1", "-update", "1", str(pal)], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(GIF_FPS), "-i", str(work / "%04d.png"), "-i", str(pal),
                        "-lavfi", "paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle", "-loop", "0", str(tmp)], check=True)
        if tmp.stat().st_size <= GIF_MAX_BYTES:
            break
    if tmp.stat().st_size > GIF_MAX_BYTES:
        raise SystemExit(f"hero.gif is {tmp.stat().st_size} bytes even at {colors} colours")
    shutil.move(str(tmp), str(out))
    print("gif ->", out, f"{n} frames, {out.stat().st_size // 1024} KB, {colors} colours")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    rest = sys.argv[2:]
    if cmd == "capture":
        capture(rest)
        return
    if cmd == "video":
        video(rest or None)
        return
    if cmd == "vertical":
        vertical(rest or None)
        return
    steps: dict[str, list[Callable[[], None]]] = {"shots": [shots, wa_shots], "wa": [wa_shots], "diagram": [diagram], "voice": [voice],
                                                  "vertical": [vertical], "gif": [gif],
                                                  "all": [shots, wa_shots, diagram, voice, lambda: capture([]), video, vertical, gif]}
    for fn in steps[cmd]:
        fn()


if __name__ == "__main__":
    main()
