"""Demo assets from the real app running in demo (mock) mode: screenshots, captions, voice-over, a 2-3 min video.

    python scripts/make_demo_assets.py shots     # Playwright drives the phone UI -> docs/demo/screenshots/*.png (+ wa)
    python scripts/make_demo_assets.py wa        # only the WhatsApp simulator shots -> docs/demo/screenshots/30_whatsapp_*.png
    python scripts/make_demo_assets.py diagram   # docs/img/architecture.png (also used in the video)
    python scripts/make_demo_assets.py voice     # edge-tts voice-over per scene -> docs/demo/voice/*.mp3 (needs internet)
    python scripts/make_demo_assets.py video     # docs/demo/tukang-copilot-demo.mp4 (16:9) + captions .srt + vertical X clip
    python scripts/make_demo_assets.py all

Everything shown is the app built during the hackathon answering live from the Meta Model API, with labelled
AI-generated sample photos. The video says so on screen, and the waits for the models are cut (the real wait is noted). My own real-phone video (docs/DEMO_SCRIPT.md) replaces it once I record it.
Chromium: PLAYWRIGHT_CHROMIUM, system chromium, or `python -m playwright install chromium`.

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

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
DEMO = ROOT / "docs" / "demo"
SHOTS = DEMO / "screenshots"
VOICE = DEMO / "voice"
FIX = ROOT / "api" / "tests" / "fixtures"
ARCH = ROOT / "docs" / "img" / "architecture.png"
W, H = 1920, 1080
ORANGE, INK, BG, MUTED = (255, 122, 0), (29, 35, 43), (246, 243, 238), (107, 116, 128)
VOICE_NAME = "en-US-AndrewMultilingualNeural"  # the most natural-sounding English narrator edge-tts has
VOICE_RATE = "-4%"                              # a touch slower than default, like someone explaining, not reading
PAUSE_S = 0.45                                  # gap between an owner's line and the narrator


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in (("DejaVuSans-Bold.ttf",) if bold else ("DejaVuSans.ttf",)):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


# --- scenes (the script)
@dataclass
class Scene:
    key: str
    image: str            # screenshot name (also the fallback still), "title:<text>", "wa:<shots>" or "arch"
    caption: str          # on-screen caption (what the viewer reads)
    say: str              # voice-over (English)
    min_s: float = 5.0
    head: str = ""        # short headline over the caption, in the video's side panel
    tone: str = "act"     # safety colour of the panel accent: act (orange), check (yellow), ok (green), stop (red), info (blue)
    pre: tuple[str, str] = ("", "")   # (edge-tts voice, line) spoken first by an owner, in Bahasa or Basa Jawa


WA_LABELS = ["Cause on your photo", "Tap a step button", "Gas leak: red stop"]
HACKATHON_LINE = "Built during the Meta AI Developer Hackathon, Oct 26 to Nov 4, 2026 (first commit Oct 30)"

SCENES: list[Scene] = [
    # 3-second silent title card, then the story. The voice-over captions are burned in (English).
    # a short spoken line on the title card too, so the film never opens on dead air
    Scene("title", "title:Fix it yourself, safely. In Javanese.|" + HACKATHON_LINE,
          "Tukang Copilot · Muse Spark + SAM 3.1 + Muse Image", "This is Tukang Copilot. Fix it yourself, safely, even in Javanese.", 3),
    Scene("hook", "title:Motor mogok. Bengkelnya tutup.|Bike won't start. The repair shop is closed.",
          "139 million motorbikes in Indonesia (BPS 2024), plus water pumps.",
          "In Indonesia, a small fault on a motorbike or a water pump can cost a day's wage. "
          "Repair videos can't see your problem, and most aren't in your language.", 7,
          pre=("id-ID-ArdiNeural", "Aduh motorku mogok, bengkelnya tutup lagi.")),
    Scene("intro", "01_home", "Photo + voice in Bahasa, Javanese or English. No photo? 1-tap demo.",
          "Take a photo and say what's wrong. Every answer here is live from Meta's models. The photos are AI-generated samples.", 5,
          "Snap it, say it"),
    Scene("progress", "02_progress", "Results stream in as each Meta model finishes: what it saw, SAM 3.1's outlines, the likely cause.",
          "Each result shows up as soon as it's ready: what Muse Spark saw, the parts SAM outlined, then the likely cause.", 6, "Watch it work", "info"),
    Scene("question", "03_question", "Unsure? It asks one question instead of guessing.",
          "If it isn't sure, it asks one short question instead of guessing.", 4, "One question"),
    Scene("diagnosis", "04_diagnosis", "Likely causes with confidence, safety level, tools, time, cost vs bengkel price.",
          "Then the diagnosis. Likely causes with confidence, a safety level, tools and time, and the parts cost next to the bengkel price.", 6,
          "The likely cause", "check"),
    Scene("parts", "05_parts", "SAM 3.1 masks the real parts on your own photo, numbered.",
          "SAM 3.1 marks the parts on your own photo, not on some generic diagram.", 5, "Parts on your photo"),
    Scene("preflight", "15_preflight", "Safety first: the steps stay locked until every check is ticked.",
          "Before step one, there's a short safety checklist. The steps stay locked until it's done.", 5,
          "Safety first", "check"),
    Scene("live", "16_live_guide", "Live camera guide: SAM 3.1 outlines the part to touch, on the live camera.",
          "Point the camera, and SAM 3.1 outlines the part to touch, about once a second. "
          "Here it's Chromium's test camera playing a sample photo.", 8, "Live camera guide"),
    Scene("check_fail", "07_check_fail", "Check my step: the photo is verified. A correction when it's wrong.",
          "After each step, you send a photo, and Muse Spark compares it with what it should look like. "
          "This one's too dark, so it asks for a retake.", 7, "Check my step", "check"),
    Scene("check_pass", "08_check_pass", "A clear photo of the finished step passes.",
          "A clear photo of the plug cap back on passes, and it moves on.", 4, "Verified", "ok"),
    Scene("handsfree", "17_hands_free", "Hands-free: steps read aloud, voice commands like “lanjut”, “ulang”, “cek”.",
          "Hands dirty? Turn on hands-free. It reads each step out loud and listens for simple voice commands.", 6, "Hands-free"),
    Scene("replan", "09_replan", "Still broken? The agent re-plans to the next likely cause.",
          "Still broken? Tell it what happened, and it moves on to the next likely cause. Plan, act, check, re-plan.", 6, "Re-plan"),
    Scene("diagram", "28_diagram_step", "No photo can show it? Muse Image draws a diagram for the step, reviewed by Muse Spark.",
          "When a photo can't show a step, like the washer inside a tap, Muse Image draws a diagram, and Muse Spark checks it.", 5,
          "A diagram for the step", "info"),
    Scene("agent", "23_agent_log", "“What the AI did”: every decision, the model that made it, and why it asked.",
          "Every decision stays on screen: what it saw, why it asked, each photo check, and which model did it.", 6,
          "What the AI did", "info"),
    Scene("handoff", "18_handoff", "Hand-off to a bengkel: WhatsApp summary, nearest workshop, PDF with a mechanic brief.",
          "When it's a job for a pro, one tap hands it over: a WhatsApp summary, the nearest bengkel, and a PDF brief for the mechanic.", 7, "Hand-off to a bengkel"),
    Scene("rice", "11_rice_stop", "Red stop: opening 220 V internals → take it to a service centre.",
          "And it knows when to say no. A rice cooker that won't heat means opening 220 volt parts, "
          "so it stops and sends you to a service centre.", 7, "Red stop", "stop"),
    # no share, language or stop-PDF scenes: the cut has to stay under 3:00, and WhatsApp shows the Javanese
    Scene("wa", "wa:30_whatsapp_jv_diagnosis,30_whatsapp_jv_steps,30_whatsapp_jv_redstop",
          "Also works in WhatsApp, in Basa Jawa. Same agent, same safety gate.",
          "It works in WhatsApp too, in Javanese. Send a photo, and the same agent replies with the marked photo, "
          "the diagnosis, and a button for each step. A gas leak still gets a red stop.", 6, "WhatsApp, in Basa Jawa",
          pre=("jv-ID-SitiNeural", "Kran pawonku netes terus, piye iki?")),
    Scene("arch", "arch", "Meta models: Voice Transcribe · Muse Spark · SAM 3.1 · Muse Image (Muse Spark Open optional).",
          "Under the hood: Voice Transcribe, Muse Spark to see, reason and check, SAM 3.1 for masks and live tracking, "
          "and Muse Image for diagrams. The safety rules live in code.", 9, "Meta models"),
    Scene("close", "title:Tukang Copilot|Every phone becomes a mechanic's apprentice.",
          "Open source, MIT licence, built during the Meta AI Developer Hackathon.",
          "Tukang Copilot. Every phone becomes a mechanic's apprentice.", 5),
]


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
    settings.demo_fallback = False
    settings.rate_limit_per_hour = 1000
    if not settings.offline:
        settings.wa_sim = True
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
# camera frames at once (about 0.66 confidence, tested 6 Nov 2026), while the small brass priming plug is often missed
LIVE_PART = ("motor", "pump")


def live_step_n(pg: Any) -> int:
    """The step of the live pump plan whose part is the first LIVE_PART word found in the parts' SAM phrases
    (the blue electric motor of the pump, else the pump body). 0 when no step names one."""
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
    from api.main import _dark_photo

    dark = Path(tempfile.mkdtemp()) / "dark.jpg"
    dark.write_bytes(_dark_photo("motor"))  # the after-photo shot in a dark corner: the check asks for the torch
    cam = _fake_camera_y4m(FIX / "sample_pump_overview.jpg")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=_chromium(), args=[
            "--no-proxy-server", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream",
            f"--use-file-for-fake-video-capture={cam}"])
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True, locale="id-ID",
                            timezone_id=TZ)
        ctx.grant_permissions(["camera", "microphone"], origin=base)
        ctx.add_init_script(SR_STUB)
        public_links(ctx, base)
        pg = ctx.new_page()
        page_errors: list[str] = []
        _console_watch(pg, page_errors)

        def snap(name: str, full: bool = False) -> None:
            pg.wait_for_timeout(350)
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
        mpdf.write_bytes(pg.request.get(f"{base}/api/sessions/{msid}/report.pdf").body())
        # the PDF pages are drawn as images (no text layer); in this motorbike report the agent log is on page 2
        info = subprocess.run(["pdfinfo", str(mpdf)], capture_output=True, text=True).stdout
        page_no = 2 if any(ln.startswith("Pages:") and int(ln.split()[1]) >= 2 for ln in info.splitlines()) else 1
        subprocess.run(["pdftoppm", "-png", "-r", "110", "-f", str(page_no), "-l", str(page_no), "-singlefile", str(mpdf),
                        str(SHOTS / "25_pdf_agent")], check=True)
        print("shot 25_pdf_agent (page", page_no, ")", flush=True)
        (SHOTS / "26_share_card.png").write_bytes(pg.request.get(f"{base}/api/sessions/{msid}/card.png").body())
        print("shot 26_share_card", flush=True)
        top_at("#result .actions", 72); snap("12_report")  # the share and report buttons, starting under the header
        pg.click("#mechBtn"); pg.wait_for_selector("#handoff:not(.hidden)", timeout=10000)
        pg.evaluate("document.querySelector('#handoff details') && (document.querySelector('#handoff details').open = true)")
        top_at("#mechBtn"); snap("18_handoff")
        # live camera guide on the pump repair (Chromium fake camera playing a labelled sample photo)
        go_sample("pump"); pg.wait_for_selector("#result:not(.hidden)", timeout=LIVE_MS)
        pg.evaluate("window.scrollTo(0,0)"); snap("10_pump")
        tick_preflight()
        go_to_step(live_step_n(pg))
        pg.click("#liveBtn"); pg.wait_for_selector("#live:not(.hidden)")
        top_at("#liveBtn")
        locked = "() => /^🎯/.test(document.querySelector('#liveState').textContent)"
        for _ in range(4):  # the fake camera drifts, so the outline comes and goes: shoot while it is on screen
            try:  # SAM 3.1 on the fake camera frames finds the part within a few frames (each frame is a paid SAM call)
                pg.wait_for_function(locked, timeout=20000)
            except Exception:  # noqa: BLE001
                print("live guide: no lock-on within 20 s", flush=True)
                continue
            pg.screenshot(path=str(SHOTS / "16_live_guide.png"))
            if pg.evaluate(locked):
                break
        print("shot 16_live_guide", flush=True)
        pg.click("#liveClose")
        # safety stop with PDF + hand-off
        go_sample("rice"); pg.wait_for_selector("#stopBox:not(.hidden)", timeout=LIVE_MS)
        pg.wait_for_selector("#stopHandoff:not(.hidden)", timeout=10000)
        pg.evaluate("window.scrollTo(0, 0)"); snap("11_rice_stop")  # the STOP card sits under the "Stopped for your safety" heading
        top_at("#stopBox > p:nth-of-type(3)"); snap("22_stop_handoff")  # "Do this now", the service buttons, the hand-off
        sid = pg.evaluate("S && S.id")
        pdf = Path(tempfile.mkdtemp()) / "stop.pdf"
        pdf.write_bytes(pg.request.get(f"{base}/api/sessions/{sid}/report.pdf").body())
        subprocess.run(["pdftoppm", "-png", "-r", "110", "-f", "1", "-l", "1", "-singlefile", str(pdf), str(SHOTS / "19_stop_pdf")], check=True)
        print("shot 19_stop_pdf", flush=True)
        faucet_with_diagram(pg, base)
        pg.evaluate("window.scrollTo(0,0)"); snap("13_english")
        # the step Muse Image drew a diagram for (the washer inside the tap)
        for _ in range(10):
            if "diagram" in (pg.get_attribute("#stepImg", "src") or "") and pg.is_visible("#stepImg"):
                break
            pg.click("#nextBtn"); pg.wait_for_timeout(300)
        top_at("#stepCard", 72); snap("28_diagram_step")
        go_sample("tire", "jv"); pg.wait_for_selector("#result:not(.hidden)", timeout=LIVE_MS)
        pg.evaluate("window.scrollTo(0,0)"); snap("20_javanese_result")
        pg.goto(base + "/"); pg.select_option("#lang", "jv"); pg.wait_for_timeout(300); snap("14_garage_jv", full=True)
        # recorded demo: what a visitor sees when the server sleeps (forced here with ?replay=1)
        pg.goto(base + "/?replay=1"); pg.select_option("#lang", "en"); pg.click("#demoBtn")
        pg.wait_for_selector("#question:not(.hidden)", timeout=20000); pg.click('#quickAns button[data-q="qNo"]')
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

    SHOTS.mkdir(parents=True, exist_ok=True)
    base, srv = _server()
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=_chromium(), args=["--no-sandbox", "--no-proxy-server"])
        for lang in ("jv", "en"):
            pg = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, timezone_id=TZ)
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
TIMING = VOICE / "timing.json"   # where each owner's line ends in its scene clip (the caption switches to the narrator there)


def _loudnorm(src: Path, out: Path) -> None:
    """Two-pass EBU R128 loudness normalisation (linear, so short clips are not pumped) to LUFS / TRUE_PEAK."""
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-af",
                            f"loudnorm=I={LUFS}:TP={TRUE_PEAK}:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True, check=True).stderr
    m = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
    af = (f"loudnorm=I={LUFS}:TP={TRUE_PEAK}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-af", f"{af},aresample=24000",
                    "-ac", "1", "-c:a", "libmp3lame", "-b:a", "96k", str(out)], check=True)


def voice() -> None:
    """edge-tts (Microsoft neural voices, free, needs internet). Set EDGE_TTS_PROXY if the network needs a proxy.

    One mp3 per scene in docs/demo/voice: the owner's line (Bahasa or Basa Jawa) when the scene has one, a short
    pause, then the narrator, joined and loudness-normalised. Only the finished clips stay in the folder: the
    owner's part is a temporary file, and where it ends is kept in timing.json for the captions."""
    import edge_tts

    VOICE.mkdir(parents=True, exist_ok=True)
    proxy = os.environ.get("EDGE_TTS_PROXY")
    if not proxy:  # aiohttp chokes on some proxy URLs in the environment; edge-tts goes direct unless EDGE_TTS_PROXY is set
        for k in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy", "ALL_PROXY", "all_proxy"):
            os.environ.pop(k, None)

    said_file = VOICE / "script.json"  # the text each mp3 was made from: a changed line is re-recorded
    said: dict[str, str] = json.loads(said_file.read_text()) if said_file.exists() else {}
    timing: dict[str, float] = json.loads(TIMING.read_text()) if TIMING.exists() else {}
    import demo_video as dv

    tmp = dv.WORK / "voice-parts"  # the owner's and narrator's parts before joining: build folder, outside the repo
    tmp.mkdir(parents=True, exist_ok=True)

    async def tts(text: str, name: str, out: Path) -> None:
        """One line as a wav, with the dead air edge-tts leaves at each end cut off (the scene adds its own beat).
        The cut keeps 80 ms before the first sound and after the last, so no word loses its first or last sound."""
        raw = tmp / (out.stem + ".raw.mp3")
        for attempt in range(4):  # the free service sometimes answers with no audio: wait a little and ask again
            try:
                await edge_tts.Communicate(text, name, rate=VOICE_RATE, proxy=proxy).save(str(raw))
                break
            except edge_tts.exceptions.NoAudioReceived:
                if attempt == 3:
                    raise
                print(f"edge-tts sent no audio for {out.stem}, trying again", flush=True)
                await asyncio.sleep(2 + 3 * attempt)
        trim = "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.08"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", f"{trim},areverse,{trim},areverse,aresample=24000",
                        "-ac", "1", str(out)], check=True)

    async def run() -> None:
        for sc in SCENES:
            out = VOICE / f"{sc.key}.mp3"
            said_as = json.dumps([VOICE_NAME, VOICE_RATE, "trimmed", LUFS, sc.pre, sc.say], ensure_ascii=False)
            if out.exists() and out.stat().st_size > 1000 and said.get(sc.key) == said_as and (sc.key in timing or not sc.pre[1]):
                continue
            if not sc.say:  # silent card: a quiet track keeps every segment's audio the same shape
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-t", f"{sc.min_s - 0.7:.2f}", "-i",
                                "anullsrc=r=24000:cl=mono", "-c:a", "libmp3lame", "-b:a", "48k", str(out)], check=True)
                timing.pop(sc.key, None)
            elif not sc.pre[1]:
                body = tmp / f"{sc.key}.body.wav"
                await tts(sc.say, VOICE_NAME, body)
                _loudnorm(body, out)
                timing.pop(sc.key, None)
            else:  # owner's line, a short pause, then the narrator, joined into one clip
                pre, body, joined = tmp / f"{sc.key}.pre.wav", tmp / f"{sc.key}.body.wav", tmp / f"{sc.key}.joined.wav"
                await tts(sc.pre[1], sc.pre[0], pre)
                await tts(sc.say, VOICE_NAME, body)
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(pre), "-f", "lavfi", "-t", f"{PAUSE_S}",
                                "-i", "anullsrc=r=24000:cl=mono", "-i", str(body), "-filter_complex",
                                "[0:a]aformat=sample_rates=24000:channel_layouts=mono[a];[2:a]aformat=sample_rates=24000:channel_layouts=mono[c];"
                                "[a][1:a][c]concat=n=3:v=0:a=1[o]", "-map", "[o]", str(joined)], check=True)
                _loudnorm(joined, out)
                timing[sc.key] = round(_dur(pre) + PAUSE_S, 3)
            said[sc.key] = said_as
            said_file.write_text(json.dumps(said, indent=1, ensure_ascii=False) + "\n")
            TIMING.write_text(json.dumps(timing, indent=1, sort_keys=True) + "\n")
            print("voice", sc.key, out.stat().st_size, flush=True)

    asyncio.run(run())
    keys = {sc.key for sc in SCENES}
    said = {k: v for k, v in said.items() if k in keys}
    said_file.write_text(json.dumps(said, indent=1, ensure_ascii=False) + "\n")
    TIMING.write_text(json.dumps({k: v for k, v in timing.items() if k in keys}, indent=1, sort_keys=True) + "\n")
    for old in VOICE.glob("*.mp3"):  # clips of scenes that were cut, and parts left by older versions of this script
        if old.stem not in keys:
            _to_trash(old)


def _to_trash(p: Path) -> None:
    """Never delete for good: unwanted generated files go to the trash folder (AI_TRASH, default /workspace/.ai-trash)."""
    trash = Path(os.environ.get("AI_TRASH", "/workspace/.ai-trash")) / "tukang-copilot" / time.strftime("%Y%m%d-%H%M%S")
    trash.mkdir(parents=True, exist_ok=True)
    shutil.move(str(p), str(trash / p.name))
    print("moved to trash:", p.name, "->", trash, flush=True)


def _dur(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(p)], capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])


# --- frames + video
def _wrap(d: ImageDraw.ImageDraw, text: str, f: Any, width: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split():
            t = (cur + " " + word).strip()
            if d.textlength(t, font=f) <= width:
                cur = t
            else:
                lines.append(cur); cur = word
        lines.append(cur)
    return lines


def _frame(sc: Scene, vertical: bool = False, subtitle: str = "") -> Image.Image:
    fw, fh = (1080, 1920) if vertical else (W, H)
    im = Image.new("RGB", (fw, fh), BG); d = ImageDraw.Draw(im)
    cap_x = 900  # caption column for screenshot scenes; moved right for the wide share card
    if sc.image.startswith("title:"):
        big, small = sc.image[6:].split("|")
        im.paste(ORANGE, [0, 0, fw, fh]); d = ImageDraw.Draw(im)
        y = fh // 2 - 160
        for ln in _wrap(d, big, font(84), fw - 200):
            d.text((100, y), ln, fill="white", font=font(84)); y += 104
        for ln in _wrap(d, small, font(44, False), fw - 200):
            d.text((100, y + 20), ln, fill="white", font=font(44, False)); y += 60
    elif sc.image == "arch":
        a = Image.open(ARCH).convert("RGB")
        if vertical:
            a = a.resize((fw, int(a.height * fw / a.width))); im.paste(a, (0, 420))
        elif subtitle:  # leave room under the diagram for the caption bar and the burned-in subtitle
            aw = int(fw * 0.68)
            im.paste(a.resize((aw, int(a.height * aw / a.width)), Image.Resampling.LANCZOS), ((fw - aw) // 2, 0))
        else:
            im.paste(a.resize((fw, int(a.height * fw / a.width))), (0, 0))
    elif sc.image.startswith("wa:"):  # three WhatsApp simulator screens side by side, each with a short label
        names = sc.image[3:].split(",")
        ph = 692 if vertical else 640
        pw_ = int(780 * ph / 1688)
        gap = 30 if vertical else 60
        x = (fw - len(names) * pw_ - (len(names) - 1) * gap) // 2 if vertical else 100
        y = 260 if vertical else 250
        for k, name in enumerate(names):
            shot = Image.open(SHOTS / f"{name}.png").convert("RGB").resize((pw_, ph), Image.Resampling.LANCZOS)
            xx = x + k * (pw_ + gap)
            d.rounded_rectangle([xx - 10, y - 10, xx + pw_ + 10, y + ph + 10], radius=28, fill=INK)
            im.paste(shot, (xx, y))
            lab = WA_LABELS[k] if k < len(WA_LABELS) else ""
            lf = font(26 if vertical else 28)
            d.text((xx + (pw_ - d.textlength(lab, font=lf)) / 2, y - 62), lab, fill=INK, font=lf)
        if vertical:
            d.text((80, 60), "WhatsApp simulator · live Meta answers · AI-generated sample photos", fill=MUTED, font=font(30, False))
        else:
            cap_x = x + len(names) * (pw_ + gap) + 40
            d.text((cap_x, 120), "Tukang Copilot", fill=ORANGE, font=font(56))
            d.text((cap_x, 195), "WhatsApp simulator · live Meta answers", fill=MUTED, font=font(28, False))
    else:
        shot = Image.open(SHOTS / f"{sc.image}.png").convert("RGB")
        ph = fh - (560 if vertical else 120)
        pw_ = int(shot.width * ph / shot.height)
        wide = shot.width > shot.height
        if wide:  # landscape picture (the share card): fit it to the left 1/2 (or full width in the vertical clip)
            pw_ = fw - 160 if vertical else 780
            ph = int(shot.height * pw_ / shot.width)
        shot = shot.resize((pw_, ph), Image.Resampling.LANCZOS)
        x = (fw - pw_) // 2 if vertical else 140
        y = (fh - ph) // 2 - 200 if (vertical and wide) else (140 if vertical else ((fh - ph) // 2 if wide else 60))
        d.rounded_rectangle([x - 14, y - 14, x + pw_ + 14, y + ph + 14], radius=36, fill=INK)
        im.paste(shot, (x, y))
        cap_x = max(900, x + pw_ + 100)
        if vertical:
            d.text((80, 60), "live Meta answers · AI-generated sample photos", fill=MUTED, font=font(30, False))
        if not vertical:
            hx = cap_x if wide else x + pw_ + 120
            d.text((hx, 120), "Tukang Copilot", fill=ORANGE, font=font(56))
            d.text((hx, 195), "live Meta answers · AI-generated sample photos", fill=MUTED, font=font(28, False))
    if sc.image != "arch" or True:
        f = font(46 if not vertical else 44)
        cw = (fw - cap_x - 80) if (not vertical and not sc.image.startswith(("title:", "arch"))) else fw - 160
        cx = cap_x if (not vertical and not sc.image.startswith(("title:", "arch"))) else 80
        lines = _wrap(d, sc.caption, f, cw)
        lh = 60
        if vertical:
            cy = fh - 380 if not sc.image.startswith("title:") else fh - 520
            if sc.image == "arch":
                d.rectangle([0, cy - 30, fw, cy + lh * len(lines) + 30], fill=INK)
        elif sc.image == "arch":
            cy = fh - 30 - lh * len(lines)
            d.rectangle([0, cy - 20, fw, fh], fill=INK)
        elif sc.image.startswith("title:"):
            cy = fh - 200
        else:
            cy = 420
        if subtitle and sc.image == "arch" and not vertical:  # lift the caption bar above the subtitle box
            shift = 170
            d.rectangle([0, cy - 20 - shift, fw, fh], fill=INK); cy -= shift
        for ln in lines:
            d.text((cx, cy), ln, fill=("white" if sc.image == "arch" or sc.image.startswith("title:") else INK), font=f); cy += lh
    if subtitle:
        _subtitle(d, subtitle, fw, fh, vertical, cap_x if not (vertical or sc.image.startswith(("title:", "arch"))) else None)
    return im


def _subtitle(d: ImageDraw.ImageDraw, text: str, fw: int, fh: int, vertical: bool, col_x: int | None) -> None:
    """Burned-in caption of what the voice is saying right now: white on a dark box, bottom of the frame
    (bottom of the right-hand column next to a phone screenshot)."""
    f = font(40 if vertical else 36, False)
    x0, x1 = (col_x - 30, fw - 50) if col_x is not None else (60, fw - 60)
    lines = _wrap(d, text, f, x1 - x0 - 60)
    lh = 52 if vertical else 48
    y1 = fh - (90 if vertical else 50)
    y0 = y1 - lh * len(lines) - 36
    d.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=(15, 18, 23))
    y = y0 + 18
    for ln in lines:
        w = d.textlength(ln, font=f)
        d.text((x0 + (x1 - x0 - w) / 2, y), ln, fill="white", font=f); y += lh


def _sentences(text: str) -> list[str]:
    import re

    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p.strip()]
    out: list[str] = []
    for p in parts:  # very long sentences are split at a comma so a caption never runs past 3 lines
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


def scene_lengths() -> dict[str, float]:
    """Each scene lasts its voice-over plus 0.7 s (at least min_s); the close card gets half a second more to read
    (more would leave dead air at the end)."""
    out = {}
    for sc in SCENES:
        mp3 = VOICE / f"{sc.key}.mp3"
        spoken = _dur(mp3) if (sc.say and mp3.exists()) else 0.0
        out[sc.key] = round(max(sc.min_s, (spoken + 0.7) if spoken else sc.min_s) + (0.5 if sc.key == "close" else 0.0), 3)
    return out


def capture(groups: list[str]) -> None:
    """Screen recordings for the video (see scripts/demo_video.py); one group per call keeps each run near a minute."""
    import demo_video as dv

    lengths = scene_lengths()
    for g in groups or list(dv.GROUPS):
        dv.capture(g, lengths)


def _shot(sc: Scene, dur: float, spoken: float) -> Any:
    import demo_video as dv

    sents = _sentences(sc.say) if sc.say else []
    total = sum(len(x) for x in sents) or 1
    subs, acc = [], 0.0
    timing = json.loads(TIMING.read_text()) if TIMING.exists() else {}
    if sc.pre[1] and sc.key in timing:  # the owner's own words first, quoted, then the narrator's sentences
        lead = float(timing[sc.key])
        subs.append((0.0, lead, f"“{sc.pre[1]}”"))
        acc, spoken = lead, max(0.1, spoken - lead)
    for j, sent in enumerate(sents):  # one caption per spoken sentence, timed by its share of the characters
        sd = spoken * len(sent) / total
        end = dur if j == len(sents) - 1 else acc + sd
        subs.append((acc, end, sent))
        acc += sd
    return dv.Shot(sc, dur, subs)


def _join(lst: Path, out: Path, loudness: bool = False) -> None:
    """Join the cached segments. +faststart rewrites the file in place, which fails on some synced folders,
    so the join happens in the build folder and the finished file is moved over. With loudness=True the joined
    soundtrack gets one more two-pass loudnorm to LUFS (the picture is copied, not re-encoded)."""
    tmp = lst.with_suffix(".mp4")
    joined = lst.with_suffix(".joined.mp4") if loudness else tmp
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart",
                    str(joined)], check=True)
    if loudness:
        probe = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(joined), "-vn", "-af",
                                f"loudnorm=I={LUFS}:TP={TRUE_PEAK}:LRA=11:print_format=json", "-f", "null", "-"],
                               capture_output=True, text=True, check=True).stderr
        m = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
        af = (f"loudnorm=I={LUFS}:TP={TRUE_PEAK}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(joined), "-map", "0:v", "-map", "0:a", "-c:v", "copy",
                        "-af", af, "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(tmp)], check=True)
        # the un-normalised join stays in the build folder (a cache outside the repo, overwritten next time)
    shutil.move(str(tmp), str(out))


def video(only: list[str] | None = None) -> None:
    """Main 16:9 video at 60 fps: one cached segment per scene in $TMPDIR/tukang-video (delete a segment to re-render it),
    then joined. Run `capture` first. `video KEY ...` renders only those scenes (each call must finish in a few minutes)."""
    import demo_video as dv

    DEMO.mkdir(parents=True, exist_ok=True)
    work = dv.WORK / "segments"
    work.mkdir(parents=True, exist_ok=True)
    lengths = scene_lengths()
    srt: list[str] = []
    stamps: list[str] = []
    t, n_sub = 0.0, 0
    parts: list[Path] = []
    prev_last: Path | None = None
    for i, sc in enumerate(SCENES):
        mp3 = VOICE / f"{sc.key}.mp3"
        spoken = _dur(mp3) if (sc.say and mp3.exists()) else 0.0
        dur = lengths[sc.key]
        shot = _shot(sc, dur, spoken)
        for a, b_, sent in shot.subs:
            n_sub += 1
            srt.append(f"{n_sub}\n{_srt_time(t + a)} --> {_srt_time(t + b_)}\n{sent}\n")
        stamps.append(f"{_mmss(t)}  {sc.key:<11} {sc.caption}")
        t += dur
        seg, last = work / f"{i:02}_{sc.key}.mp4", work / f"{i:02}_{sc.key}.last.png"
        parts.append(seg)
        if (only is None or sc.key in only) and not (seg.exists() and last.exists() and only is None):
            t0 = time.time()
            dv.render_segment(shot, seg, (W, H), mp3 if spoken else None, prev_last, dv.Renderer(shot, (W, H)), last)
            print(f"segment {seg.name} {dur:.1f}s in {time.time() - t0:.0f}s", flush=True)
        prev_last = last
    if only is not None:
        return
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    out = DEMO / "tukang-copilot-demo.mp4"
    _join(lst, out, loudness=True)
    (DEMO / "tukang-copilot-demo.en.srt").write_text("\n".join(srt))
    real = _dur(out)
    (DEMO / "TIMESTAMPS.txt").write_text(
        "Tukang Copilot demo video: scene start times (mm:ss), made by scripts/make_demo_assets.py video\n"
        f"File: docs/demo/tukang-copilot-demo.mp4, length {_mmss(real)} ({real:.1f} s, ffprobe), 1920x1080 at 60 fps. "
        f"Live Meta API answers ({dv.recorded_on()}, model waits cut), AI-generated sample photos.\n"
        "English captions of the voice-over are burned in; the same text is in tukang-copilot-demo.en.srt.\n\n"
        + "\n".join(stamps) + "\n", encoding="utf-8")
    if real >= 180:
        raise SystemExit(f"video is {real:.1f} s: the hackathon limit is 3:00")
    print(f"video -> {out} ({real:.1f}s by ffprobe)")


VERTICAL = {  # key: (seconds, where in the recording to start, Bahasa line on top, English line at the bottom)
    "title": (3.0, 0.0, "Tukang Copilot", ""),
    "hook": (4.5, 0.0, "Motor mogok, bengkel tutup? Foto + ngomong.", "Bike won't start and the shop is closed? Snap it and say what's wrong."),
    "progress": (4.5, 2.2, "Lihat AI bekerja: hasil muncul tiap tahap.", "Watch the AI work: results appear stage by stage."),
    "parts": (4.5, 0.8, "SAM 3.1 menandai part di foto kamu.", "SAM 3.1 marks the parts on your photo."),
    "live": (4.5, 4.2, "Kamera langsung: part yang harus dipegang ditandai.", "Live camera: the part to touch is outlined (demo)."),
    "check_pass": (4.5, 0.0, "Tiap langkah dicek kamera.", "Every step is checked by the camera."),
    "rice": (4.5, 4.4, "Bahaya? Dia bilang STOP.", "Dangerous? It says STOP and hands you to a pro."),
    "wa": (4.5, 0.0, "Juga lewat WhatsApp, dalam Basa Jawa.", "Also works in WhatsApp (simulator, live answers)."),
    "arch": (4.5, 0.0, "Built with Meta Muse Spark + SAM 3.1 + Muse Image", "Voice Transcribe · Muse Spark · SAM 3.1 · Muse Image"),
    "close": (4.5, 0.0, "Tukang Copilot · open source · Meta AI", "Fix it yourself, safely. In Javanese."),
}
VERTICAL_ZOOMS = {"parts": [(0.0, 1.0, 300), (0.6, 1.0, 300), (2.0, 1.35, 300), (4.5, 1.35, 300)],
                  "check_pass": [(0.0, 1.0, 560), (0.8, 1.0, 560), (2.0, 1.3, 560), (4.5, 1.3, 560)],
                  "rice": [(0.0, 1.15, 330), (4.5, 1.3, 330)],
                  "live": [(0.0, 1.25, 400), (4.5, 1.3, 400)]}


def vertical() -> None:
    """~45 s 9:16 clip for X (silent): Bahasa line on top, English line at the bottom, the same recordings."""
    import demo_video as dv

    work = dv.WORK / "vsegments"
    work.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []
    prev_last: Path | None = None
    for k, (secs, offset, bahasa, english) in VERTICAL.items():
        sc = next(s for s in SCENES if s.key == k)
        v = Scene(sc.key, sc.image, bahasa, "", secs, sc.head, sc.tone)
        shot = dv.Shot(v, secs, [(0.0, secs, english)] if english else [])
        seg, last = work / f"v_{k}.mp4", work / f"v_{k}.last.png"
        if not (seg.exists() and last.exists()):
            dv.render_segment(shot, seg, (1080, 1920), None, prev_last, dv.Renderer(shot, (1080, 1920), vertical=True, clip_offset=offset,
                                                                                       zooms=VERTICAL_ZOOMS), last)
            print("vertical segment", k, flush=True)
        parts.append(seg)
        prev_last = last
    lst = work / "vlist.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    out = DEMO / "tukang-copilot-x-vertical.mp4"
    _join(lst, out)
    print("vertical ->", out, f"{_dur(out):.1f}s")


GIF_SHOTS = ["01_home", "02_progress", "03_question", "05_parts", "23_agent_log", "24_agent_jump", "15_preflight", "07_check_fail", "08_check_pass",
             "16_live_guide", "09_replan", "28_diagram_step", "11_rice_stop", "20_javanese_result", "30_whatsapp_jv_diagnosis"]


GIF_W, GIF_H = 640, 1200  # README shows it 320 px wide: 2x so it stays sharp on a phone or a retina screen
GIF_MAX_BYTES = 6 * 1024 * 1024


def gif() -> None:
    """README hero: the phone flow as a looping GIF (~1.6 s per screen) from the screenshots, at 2x the size the
    README shows it. One palette for the whole loop (no colour shimmer between screens); fewer colours if it is too big."""
    import demo_video as dv

    work = dv.WORK / "gif"  # frames in the build folder (outside the repo), overwritten each time
    work.mkdir(parents=True, exist_ok=True)
    for i, name in enumerate(GIF_SHOTS):
        im = Image.open(SHOTS / f"{name}.png").convert("RGB")
        im = im.resize((GIF_W, int(im.height * GIF_W / im.width)), Image.Resampling.LANCZOS).crop((0, 0, GIF_W, GIF_H))
        im.save(work / f"{i:02}.png")
    out = DEMO / "hero.gif"
    colors = 128
    for colors in (128, 96, 64):
        vf = (f"split[a][b];[a]palettegen=max_colors={colors}:stats_mode=full[p];"
              "[b][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "1/1.6", "-i", str(work / "%02d.png"),
                        "-frames:v", str(len(GIF_SHOTS)), "-vf", vf, "-loop", "0", str(out)], check=True)
        if out.stat().st_size <= GIF_MAX_BYTES:
            break
    print("gif ->", out, f"{out.stat().st_size // 1024} KB, {colors} colours")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    rest = sys.argv[2:]
    if cmd == "capture":
        capture(rest)
        return
    if cmd == "video":
        video(rest or None)
        return
    steps: dict[str, list[Callable[[], None]]] = {"shots": [shots, wa_shots], "wa": [wa_shots], "diagram": [diagram], "voice": [voice],
                                                  "vertical": [vertical], "gif": [gif],
                                                  "all": [shots, wa_shots, diagram, voice, lambda: capture([]), video, vertical, gif]}
    for fn in steps[cmd]:
        fn()


if __name__ == "__main__":
    main()
