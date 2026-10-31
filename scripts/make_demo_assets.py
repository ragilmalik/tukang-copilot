"""Demo assets from the REAL app running in demo (mock) mode: screenshots, captions, voice-over, a 2-3 min video.

    python scripts/make_demo_assets.py shots     # Playwright drives the phone UI -> docs/demo/screenshots/*.png
    python scripts/make_demo_assets.py diagram   # docs/img/architecture.png (also used in the video)
    python scripts/make_demo_assets.py voice     # edge-tts voice-over per scene -> docs/demo/voice/*.mp3 (needs internet)
    python scripts/make_demo_assets.py video     # docs/demo/tukang-copilot-demo.mp4 (16:9) + captions .srt + vertical X clip
    python scripts/make_demo_assets.py all

Everything shown is the app built during the hackathon, in demo mode, with labelled stand-in photos.
The video says so on screen. Malik's real-phone video (docs/DEMO_SCRIPT.md) replaces it when recorded.
Chromium: PLAYWRIGHT_CHROMIUM, system chromium, or `python -m playwright install chromium`.
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
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DEMO = ROOT / "docs" / "demo"
SHOTS = DEMO / "screenshots"
VOICE = DEMO / "voice"
FIX = ROOT / "api" / "tests" / "fixtures"
ARCH = ROOT / "docs" / "img" / "architecture.png"
W, H = 1920, 1080
ORANGE, INK, BG, MUTED = (255, 122, 0), (29, 35, 43), (246, 243, 238), (107, 116, 128)
VOICE_NAME = "en-US-AndrewNeural"


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in (("DejaVuSans-Bold.ttf",) if bold else ("DejaVuSans.ttf",)):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


# ---------------------------------------------------------------- scenes (the script)
@dataclass
class Scene:
    key: str
    image: str            # screenshot name, "title:<text>", or "arch"
    caption: str          # on-screen caption (what the viewer reads)
    say: str              # voice-over (English)
    min_s: float = 5.0


SCENES: list[Scene] = [
    Scene("hook", "title:Motor mogok. Bengkelnya tutup.|Bike won't start. The repair shop is closed.",
          "Indonesia runs on ~130 million motorbikes, water pumps and rice cookers.",
          "In Indonesia, a small fault on a motorbike or a water pump can cost a day's wage. "
          "Repair videos can't see your problem, and they're not in your language.", 7),
    Scene("intro", "01_home", "Photo + voice in Bahasa, Javanese or English. No photo? ▶ 1-tap demo.",
          "Take a photo and say what's wrong. This recording runs in demo mode, with labelled stand-in photos.", 5),
    Scene("progress", "02_progress", "Results stream in as each Meta model finishes: what it saw, SAM 3.1's outlines, the likely cause.",
          "You watch the agent work: as each stage finishes, its result appears. What Muse Spark saw, "
          "the parts SAM 3.1 outlined, then the likely cause.", 6),
    Scene("question", "03_question", "Unsure? It asks ONE question instead of guessing.",
          "When the evidence is ambiguous, it asks one short question instead of guessing.", 4),
    Scene("diagnosis", "04_diagnosis", "Likely causes with confidence, safety level, tools, time, cost vs bengkel price.",
          "Then the diagnosis: likely causes with confidence, a safety level, tools, time, and the parts cost against the repair-shop price.", 6),
    Scene("parts", "05_parts", "SAM 3.1 masks the real parts on YOUR photo, numbered.",
          "The parts are masked and numbered on your own photo by SAM 3.1, not a generic diagram.", 5),
    Scene("preflight", "15_preflight", "Safety first: the steps stay locked until every check is ticked.",
          "Before step one, a short safety checklist. The steps stay locked until you tick every item.", 5),
    Scene("live", "16_live_guide", "Live camera guide: SAM 3.1 highlights the part to touch, on the live camera.",
          "New: the live camera guide. Point the phone and SAM 3.1 outlines the exact part to touch, about once a second, "
          "on the live picture. In this demo the camera is Chromium's fake camera playing a stand-in photo.", 9),
    Scene("check_fail", "07_check_fail", "Check my step: the photo is verified. ⚠ Correction when it's wrong.",
          "After each step, Check my step. Muse Spark compares the photo with the expected state. "
          "Too dark here, so it asks for the torch instead of guessing.", 7),
    Scene("check_pass", "08_check_pass", "✓ Verified by the camera, then on to the next step.",
          "Retake it, and the step is verified before you move on.", 4),
    Scene("handsfree", "17_hands_free", "Hands-free: steps read aloud, voice commands like “lanjut”, “ulang”, “cek”.",
          "Hands dirty? Go hands-free: each step is read aloud, and the phone listens for lanjut, ulang or cek.", 6),
    Scene("replan", "09_replan", "Still broken? The agent re-plans to the next likely cause.",
          "Still broken? Say what happened, and the agent re-plans to the next most likely cause. Plan, act, verify, re-plan.", 6),
    Scene("agent", "23_agent_log", "“What the AI did”: every decision, the model that made it, and why it asked.",
          "Every decision is on screen: what it saw, why it asked, each photo check, each re-plan, and which Meta model did it.", 6),
    Scene("jump", "24_agent_jump", "Tap any log line: it jumps to the step it checked, highlighted.",
          "Tap a line, and it jumps to the exact step that was checked.", 4),
    Scene("handoff", "18_handoff", "Hand-off to a bengkel: WhatsApp summary, nearest workshop, PDF with a mechanic brief.",
          "And when it's a job for a pro, one tap hands it off: a WhatsApp summary of what was found and tried, "
          "a search for the nearest bengkel, and a PDF with a brief for the mechanic.", 8),
    Scene("pdf", "25_pdf_agent", "The PDF report carries the same agent log, for the mechanic or the judges.",
          "The PDF report carries the same log, so a mechanic can see what was already tried.", 5),
    Scene("share", "26_share_card", "Share a guide link: WhatsApp and X show this card (marked photo, cause, safety level).",
          "Share the guide, and WhatsApp or X shows a card with your marked photo, the likely cause and the safety level.", 6),
    Scene("rice", "11_rice_stop", "RED STOP: opening 220 V internals → take it to a service centre.",
          "It also knows when to say no. A rice cooker that won't heat would mean opening 220 volt internals, "
          "so the safety gate stops the guidance.", 7),
    # v1.22: the stop-PDF scene was dropped to make room for the agent log and keep the cut under 3:00
    Scene("lang", "20_javanese_result", "Basa Jawa UI and Javanese voice input, plus English.",
          "The whole app runs in Bahasa Indonesia, Javanese and English, with Javanese voice input.", 5),
    Scene("ow", "21_open_weights", "One switch: reasoning on Muse Spark Open (open weights) via Baseten.",
          "And with one switch, diagnosis and planning run on Muse Spark Open, Meta's open-weights model, on Baseten. "
          "The app shows a badge when it does.", 6),
    Scene("arch", "arch", "Meta models: Voice Transcribe · Muse Spark · SAM 3.1 · Muse Image · Muse Spark Open (open weights).",
          "Under the hood: Voice Transcribe, Muse Spark to see, reason and check, SAM 3.1 for masks and live tracking, "
          "and Muse Image for diagrams. Safety is enforced in code.", 9),
    Scene("close", "title:Tukang Copilot|Every phone becomes a mechanic's apprentice.",
          "Open source, MIT licence, built during the Meta Global AI Developer Hackathon.",
          "Tukang Copilot. Every phone becomes a mechanic's apprentice.", 5),
]


# ---------------------------------------------------------------- screenshots
def _server() -> tuple[str, Any]:
    os.environ.setdefault("MOCK", "1")
    os.environ.setdefault("NARRATION_VOICE", "0")
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    import uvicorn

    from api.main import app
    from api.settings import settings

    settings.data_dir = Path(tempfile.mkdtemp(prefix="tukang-demo-"))
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
    """Chromium's fake camera plays a .y4m file: a few seconds of a labelled stand-in photo with a slow drift."""
    out = Path(tempfile.mkdtemp()) / "cam.y4m"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(photo), "-t", "4", "-r", "10",
                    "-vf", "scale=1024:768,crop=984:738:20+16*sin(t):15+12*cos(t),scale=640:480,format=yuv420p",
                    "-f", "yuv4mpegpipe", str(out)], check=True)
    return out


def shots() -> None:
    from playwright.sync_api import sync_playwright

    from api.settings import settings

    SHOTS.mkdir(parents=True, exist_ok=True)
    base, srv = _server()
    dark = Path(tempfile.mkdtemp()) / "dark.jpg"
    Image.new("RGB", (800, 600), (6, 6, 6)).save(dark)
    cam = _fake_camera_y4m(FIX / "standin_pump_overview.jpg")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=_chromium(), args=[
            "--no-proxy-server", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream",
            f"--use-file-for-fake-video-capture={cam}"])
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        ctx.grant_permissions(["camera", "microphone"], origin=base)
        ctx.add_init_script(SR_STUB)
        pg = ctx.new_page()

        def snap(name: str, full: bool = False) -> None:
            pg.wait_for_timeout(350)
            pg.screenshot(path=str(SHOTS / f"{name}.png"), full_page=full)
            print("shot", name, flush=True)

        def go_sample(sample: str, lang: str = "id") -> None:
            pg.goto(base + "/"); pg.select_option("#lang", lang); pg.wait_for_timeout(200)
            pg.click(f'button.sample[data-sample="{sample}"]')

        def tick_preflight() -> None:
            for box in pg.locator("#preList input").all():
                box.check()
            pg.wait_for_timeout(200)

        pg.goto(base + "/"); pg.wait_for_selector("#modeBadge:not(.hidden)")
        pg.set_input_files("#photo", str(FIX / "standin_motor_plug_area.jpg"))
        pg.fill("#text", "Motor saya Honda Beat susah hidup, distarter cuma bunyi tapi mesin nggak nyala.")
        pg.evaluate("document.activeElement && document.activeElement.blur(); window.scrollTo(0, 0)")
        snap("01_home")
        pg.click("#goBtn"); pg.wait_for_selector("#progress:not(.hidden)")
        # v1.23: partial results stream in (demo pacing MOCK_PACE holds each finished stage on screen)
        pg.wait_for_selector("#lf-segment img", timeout=30000)
        pg.wait_for_function("document.querySelector('#lf-segment img').naturalWidth > 0", timeout=10000)
        pg.evaluate("document.querySelector('#stageList').scrollIntoView({block: 'start'}); window.scrollBy(0, -110)")
        snap("02_progress")
        pg.wait_for_selector("#question:not(.hidden)", timeout=30000); pg.fill("#answerText", "Tidak bau bensin")
        snap("03_question")
        pg.click("#answerBtn"); pg.wait_for_selector("#result:not(.hidden)", timeout=30000)
        pg.evaluate("window.scrollTo(0,0)"); snap("04_diagnosis")
        pg.locator("#partsWrap").scroll_into_view_if_needed(); pg.evaluate("window.scrollBy(0,-120)"); snap("05_parts")
        pg.locator("#preflight").scroll_into_view_if_needed(); pg.evaluate("window.scrollBy(0,-80)"); snap("15_preflight")
        tick_preflight()
        pg.locator("#stepCard").scroll_into_view_if_needed(); snap("06_step")
        pg.set_input_files("#stepPhoto", str(dark))
        pg.wait_for_function("!document.querySelector('#checkResult').textContent.includes('…')", timeout=20000)
        pg.locator("#checkResult").scroll_into_view_if_needed(); snap("07_check_fail")
        pg.set_input_files("#stepPhoto", str(FIX / "standin_motor_step_cap_on.jpg"))
        pg.wait_for_timeout(600)
        pg.wait_for_function("!document.querySelector('#checkResult').textContent.includes('…')", timeout=20000)
        pg.locator("#checkResult").scroll_into_view_if_needed(); snap("08_check_pass")
        pg.wait_for_function("document.querySelector('#stepNo').textContent.trim() === '2'", timeout=10000)  # auto-advanced
        pg.locator("#agent .agGo", has_text="Langkah 1 dicek").first.click()          # v1.23: tap a log line → back to that step
        pg.wait_for_selector("#stepCard.flash"); pg.wait_for_timeout(900)
        pg.evaluate("window.scrollBy(0, -40)"); snap("24_agent_jump")
        pg.check("#handsFree"); pg.wait_for_selector("#voiceBar:not(.hidden)", timeout=5000); pg.wait_for_timeout(600)
        pg.locator("#voiceBar").scroll_into_view_if_needed(); pg.evaluate("window.scrollBy(0,180)"); snap("17_hands_free")
        pg.uncheck("#handsFree")
        pg.fill("#stuckText", "Sudah dicoba, mesin tetap tidak nyala."); pg.click("#stuckBtn")
        pg.wait_for_function("document.querySelector('#stuckMsg').textContent.length > 3 && !document.querySelector('#stuckBtn').disabled",
                             timeout=20000); pg.wait_for_timeout(600)
        pg.wait_for_selector("#planBanner:not(.hidden)"); pg.evaluate("window.scrollTo(0, 0)"); snap("09_replan")  # v1.24: re-plan banner + tried cause
        pg.evaluate("document.querySelector('#agent').scrollIntoView({block: 'start'}); window.scrollBy(0, -70)"); snap("23_agent_log")
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
        pg.click("#mechBtn"); pg.wait_for_selector("#handoff:not(.hidden)", timeout=10000)
        pg.evaluate("document.querySelector('#handoff details') && (document.querySelector('#handoff details').open = true)")
        pg.evaluate("document.querySelector('#mechBtn').scrollIntoView({block: 'start'}); window.scrollBy(0, -90)"); snap("18_handoff")
        pg.locator("#pdfBtn").scroll_into_view_if_needed(); snap("12_report")
        # live camera guide on the pump repair (Chromium fake camera playing a labelled stand-in photo)
        go_sample("pump"); pg.wait_for_selector("#result:not(.hidden)", timeout=30000)
        pg.evaluate("window.scrollTo(0,0)"); snap("10_pump")
        tick_preflight()
        pg.click("#liveBtn"); pg.wait_for_selector("#live:not(.hidden)")
        pg.wait_for_function("/^🎯/.test(document.querySelector('#liveState').textContent)", timeout=20000)
        pg.wait_for_timeout(900)
        pg.evaluate("document.querySelector('#liveBtn').scrollIntoView({block: 'start'}); window.scrollBy(0, -90)"); snap("16_live_guide")
        pg.click("#liveClose")
        # safety stop with PDF + hand-off
        go_sample("rice"); pg.wait_for_selector("#stopBox:not(.hidden)", timeout=30000)
        pg.wait_for_selector("#stopHandoff:not(.hidden)", timeout=10000)
        pg.evaluate("window.scrollTo(0, 0)"); snap("11_rice_stop")  # v1.24: the STOP card sits under the "Stopped for your safety" heading
        pg.evaluate("document.querySelector('#stopHandoff').scrollIntoView({block: 'end'}); window.scrollBy(0, 40)"); snap("22_stop_handoff")
        sid = pg.evaluate("S && S.id")
        pdf = Path(tempfile.mkdtemp()) / "stop.pdf"
        pdf.write_bytes(pg.request.get(f"{base}/api/sessions/{sid}/report.pdf").body())
        subprocess.run(["pdftoppm", "-png", "-r", "110", "-f", "1", "-l", "1", "-singlefile", str(pdf), str(SHOTS / "19_stop_pdf")], check=True)
        print("shot 19_stop_pdf", flush=True)
        go_sample("faucet", "en"); pg.wait_for_selector("#result:not(.hidden)", timeout=30000)
        pg.evaluate("window.scrollTo(0,0)"); snap("13_english")
        go_sample("tire", "jv"); pg.wait_for_selector("#result:not(.hidden)", timeout=30000)
        pg.evaluate("window.scrollTo(0,0)"); snap("20_javanese_result")
        pg.goto(base + "/"); pg.select_option("#lang", "jv"); pg.wait_for_timeout(300); snap("14_garage_jv", full=True)
        # open-weights badge: what the header shows when USE_OPEN_WEIGHTS=1 + a Baseten key (still demo answers here)
        settings.use_open_weights, settings.baseten_api_key = True, "stand-in-not-a-key"
        pg.goto(base + "/"); pg.select_option("#lang", "en"); pg.wait_for_selector("#owBadge:not(.hidden)", timeout=5000); snap("21_open_weights")
        settings.use_open_weights, settings.baseten_api_key = False, ""
        # v1.24 recorded demo: what a judge sees when the server sleeps (forced here with ?replay=1)
        pg.goto(base + "/?replay=1"); pg.select_option("#lang", "en"); pg.click("#demoBtn")
        pg.wait_for_selector("#question:not(.hidden)", timeout=20000); pg.click('#quickAns button[data-q="qNo"]')
        pg.wait_for_selector("#result:not(.hidden)", timeout=20000); pg.evaluate("window.scrollTo(0, 0)"); snap("27_recorded_demo")
        b.close()
    srv.should_exit = True
    print("screenshots ->", SHOTS, sorted(p.name for p in SHOTS.glob("*.png")))


# ---------------------------------------------------------------- architecture diagram
def diagram() -> None:
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.text((80, 50), "Tukang Copilot: one agent loop, five Meta models", fill=INK, font=font(52))
    d.text((80, 120), "plan → act → verify → re-plan, with a safety gate in code", fill=MUTED, font=font(32, False))
    boxes = [
        ("Phone (PWA)", "photo · voice · text\nid / jv / en", (80, 230), (230, 230, 230)),
        ("Listen", "Muse Voice Transcribe\n(Jawa: Spark 1.2 audio)", (420, 230), (255, 228, 204)),
        ("Look", "Muse Spark 1.3 vision\n→ ObjectReport JSON", (760, 230), (255, 228, 204)),
        ("Find parts", "SAM 3.1 masks →\nphoto + live camera", (1100, 230), (204, 230, 255)),
        ("Diagnose", "Muse Spark 1.3\nor Muse Spark Open*", (1440, 230), (255, 228, 204)),
        ("Safety gate", "3 layers in code\nred = STOP + pro", (1440, 560), (255, 210, 205)),
        ("Plan", "Muse Spark → steps\nwith expected state", (1100, 560), (255, 228, 204)),
        ("Illustrate", "Muse Image edit\nof YOUR photo", (760, 560), (225, 214, 245)),
        ("Verify step", "new photo → Spark\n✓ pass / ⚠ correction", (420, 560), (210, 240, 220)),
        ("Report", "PDF · bengkel\nhand-off · garage", (80, 560), (230, 230, 230)),
    ]
    bw, bh = 300, 200
    for title, sub, (x, y), col in boxes:
        d.rounded_rectangle([x, y, x + bw, y + bh], radius=24, fill=col, outline=INK, width=3)
        d.text((x + 20, y + 20), title, fill=INK, font=font(34))
        d.multiline_text((x + 20, y + 80), sub, fill=INK, font=font(24, False), spacing=8)

    def arrow(a: tuple[int, int], b: tuple[int, int], label: str = "") -> None:
        d.line([a, b], fill=ORANGE, width=8)
        ax, ay = b; dx, dy = (b[0] - a[0]), (b[1] - a[1]); n = max(1.0, (dx * dx + dy * dy) ** 0.5); ux, uy = dx / n, dy / n
        d.polygon([(ax, ay), (ax - 26 * ux + 14 * uy, ay - 26 * uy - 14 * ux), (ax - 26 * ux - 14 * uy, ay - 26 * uy + 14 * ux)], fill=ORANGE)
        if label:
            d.text(((a[0] + b[0]) // 2 - 60, (a[1] + b[1]) // 2 + 12), label, fill=MUTED, font=font(22, False))

    for x in (380, 720, 1060, 1400):
        arrow((x, 330), (x + 40, 330))
    arrow((1590, 430), (1590, 560))
    for x in (1440, 1100, 760, 420):
        arrow((x, 660), (x - 40, 660))
    d.line([(570, 760), (570, 840), (1250, 840), (1250, 760)], fill=ORANGE, width=6)
    d.text((620, 850), "fails twice → re-plan to the next cause (or escalate to a professional)", fill=INK, font=font(26, False))
    d.text((80, 950), "* USE_OPEN_WEIGHTS=true runs Diagnose + Plan on Muse Spark Open (open weights) on Baseten.", fill=INK, font=font(28, False))
    d.text((80, 995), "All calls go through api/meta_client.py: auth, retries, timeouts, JSON-schema validation, per-session cost cap.", fill=MUTED, font=font(26, False))
    ARCH.parent.mkdir(parents=True, exist_ok=True)
    im.save(ARCH)
    print("diagram ->", ARCH)


# ---------------------------------------------------------------- voice-over
def voice() -> None:
    """edge-tts (Microsoft neural voices, free, needs internet). Set EDGE_TTS_PROXY if the network needs a proxy."""
    import edge_tts

    VOICE.mkdir(parents=True, exist_ok=True)
    proxy = os.environ.get("EDGE_TTS_PROXY")
    if not proxy:  # aiohttp chokes on some proxy URLs in the environment; edge-tts goes direct unless EDGE_TTS_PROXY is set
        for k in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy", "ALL_PROXY", "all_proxy"):
            os.environ.pop(k, None)

    async def run() -> None:
        for sc in SCENES:
            out = VOICE / f"{sc.key}.mp3"
            if out.exists() and out.stat().st_size > 1000:
                continue
            await edge_tts.Communicate(sc.say, VOICE_NAME, rate="+4%", proxy=proxy).save(str(out))
            print("voice", sc.key, out.stat().st_size)

    asyncio.run(run())


def _dur(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(p)], capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])


# ---------------------------------------------------------------- frames + video
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


def _frame(sc: Scene, vertical: bool = False) -> Image.Image:
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
        else:
            im.paste(a.resize((fw, int(a.height * fw / a.width))), (0, 0))
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
            d.text((80, 60), "demo mode · labelled stand-in photos", fill=MUTED, font=font(30, False))
        if not vertical:
            hx = cap_x if wide else x + pw_ + 120
            d.text((hx, 120), "Tukang Copilot", fill=ORANGE, font=font(56))
            d.text((hx, 195), "demo mode · labelled stand-in photos", fill=MUTED, font=font(28, False))
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
        for ln in lines:
            d.text((cx, cy), ln, fill=("white" if sc.image == "arch" or sc.image.startswith("title:") else INK), font=f); cy += lh
    return im


def _srt_time(t: float) -> str:
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def video() -> None:
    DEMO.mkdir(parents=True, exist_ok=True)
    work = Path(os.environ.get("DEMO_BUILD_DIR", Path(tempfile.gettempdir()) / "tukang-video"))  # segments are cached: re-run to resume
    work.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []
    srt: list[str] = []
    t = 0.0
    has_voice = all((VOICE / f"{s.key}.mp3").exists() for s in SCENES)
    for i, sc in enumerate(SCENES):
        png = work / f"{i:02}.png"; _frame(sc).save(png)
        mp3 = VOICE / f"{sc.key}.mp3"
        dur = max(sc.min_s, (_dur(mp3) + 0.7) if has_voice else sc.min_s)
        seg = work / f"{i:02}_{sc.key}.mp4"
        parts.append(seg)
        srt.append(f"{i + 1}\n{_srt_time(t)} --> {_srt_time(t + dur)}\n{sc.say}\n")
        t += dur
        if seg.exists() and seg.stat().st_size > 0:
            continue
        audio = ["-i", str(mp3)] if has_voice else ["-f", "lavfi", "-t", f"{dur:.2f}", "-i", "anullsrc=r=44100:cl=stereo"]
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-t", f"{dur:.2f}", "-i", str(png), *audio,
                        "-filter_complex", f"[1:a]apad=whole_dur={dur:.2f},aresample=44100[a]", "-map", "0:v", "-map", "[a]",
                        "-t", f"{dur:.2f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "22",
                        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2", "-tune", "stillimage", str(seg) + ".part.mp4"], check=True)
        os.replace(str(seg) + ".part.mp4", seg)
        print("segment", seg.name, f"{dur:.1f}s", flush=True)
    lst = work / "list.txt"; lst.write_text("".join(f"file '{p}'\n" for p in parts))
    out = DEMO / "tukang-copilot-demo.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
    (DEMO / "tukang-copilot-demo.en.srt").write_text("\n".join(srt))
    print(f"video -> {out} ({t:.1f}s, voice={'yes' if has_voice else 'no'})")
    vertical(work, has_voice)


def vertical(work: Path, has_voice: bool) -> None:
    """~45 s 9:16 clip for X: hook, streaming progress, parts, live camera, check, share card, rice stop, models, close."""
    keys = ["hook", "progress", "parts", "live", "check_pass", "share", "rice", "arch", "close"]
    short = {"hook": "Motor mogok, bengkel tutup? Foto + ngomong.", "parts": "SAM 3.1 menandai part di foto KAMU.",
             "live": "Kamera langsung: part yang harus dipegang ditandai (demo).", "check_pass": "Tiap langkah dicek kamera ✓",
             "handsfree": "Tangan kotor? Bilang “lanjut”.", "handoff": "Kerjaan ahli? Kirim ringkasan ke bengkel via WhatsApp.",
             "rice": "Bahaya? Dia bilang STOP.", "progress": "Lihat AI bekerja: hasil muncul tiap tahap.",
             "share": "Bagikan: WhatsApp & X tampilkan kartu ini (demo).",
             "arch": "Built with Meta Muse Spark + SAM 3.1 + Muse Image", "close": "Tukang Copilot · open source · mode demo"}
    parts: list[Path] = []
    for k in keys:
        sc = next(s for s in SCENES if s.key == k)
        v = Scene(sc.key, sc.image, short[k], sc.say, 5.5)
        png = work / f"v_{k}.png"; _frame(v, vertical=True).save(png)
        seg = work / f"v_{k}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-t", "5", "-i", str(png),
                        "-f", "lavfi", "-t", "5", "-i", "anullsrc=r=44100:cl=stereo", "-t", "5",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-ar", "44100", "-ac", "2", str(seg)], check=True)
        parts.append(seg)
    lst = work / "vlist.txt"; lst.write_text("".join(f"file '{p}'\n" for p in parts))
    out = DEMO / "tukang-copilot-x-vertical.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
    print("vertical ->", out)


GIF_SHOTS = ["01_home", "02_progress", "03_question", "05_parts", "23_agent_log", "24_agent_jump", "15_preflight", "07_check_fail", "08_check_pass",
             "16_live_guide", "09_replan", "11_rice_stop", "20_javanese_result"]


def gif() -> None:
    """README hero: the phone flow as a small looping GIF (~1.4 s per screen, 320 px wide) from the screenshots."""
    work = Path(tempfile.mkdtemp())
    for i, name in enumerate(GIF_SHOTS):
        im = Image.open(SHOTS / f"{name}.png").convert("RGB")
        im = im.resize((320, int(im.height * 320 / im.width)), Image.Resampling.LANCZOS).crop((0, 0, 320, 600))
        im.save(work / f"{i:02}.png")
    out = DEMO / "hero.gif"
    vf = "fps=10,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "1/1.4", "-i", str(work / "%02d.png"), "-vf", vf,
                    "-loop", "0", str(out)], check=True)
    print("gif ->", out, f"{out.stat().st_size // 1024} KB")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = {"shots": [shots], "diagram": [diagram], "voice": [voice], "video": [video], "gif": [gif],
             "all": [shots, diagram, voice, video, gif]}
    for fn in steps[cmd]:
        fn()


if __name__ == "__main__":
    main()
