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
          "In Indonesia, a small fault on a motorbike or a water pump can cost a day's wage, or days without water. "
          "The repair videos online are not for your model, not in your language, and they can't see your problem.", 9),
    Scene("intro", "01_home", "Tukang Copilot: photo + voice in Bahasa, Javanese or English.",
          "Tukang Copilot turns any phone into a mechanic's apprentice. Take a photo, say what's wrong, in Bahasa Indonesia, "
          "Javanese or English, and pick a category. This recording runs in demo mode, with labelled stand-in photos.", 8),
    Scene("progress", "02_progress", "Live stages: Listening → Looking → Finding the parts → Diagnosing.",
          "Behind the progress bar, Muse Voice Transcribe hears the problem, Muse Spark looks at the photo, "
          "and SAM 3.1 segments the exact parts.", 7),
    Scene("question", "03_question", "Unsure? It asks ONE question instead of guessing.",
          "When the evidence is ambiguous, the agent asks one short question instead of guessing. Do you smell fuel? No.", 6),
    Scene("diagnosis", "04_diagnosis", "Diagnosis: likely causes with confidence, safety level, tools, time, cost estimate.",
          "Then the diagnosis card: the most likely causes with confidence and evidence, a safety level, "
          "the tools you need, the time, and an estimated parts cost in rupiah.", 8),
    Scene("parts", "05_parts", "SAM 3.1 masks the real parts on YOUR photo, numbered.",
          "The parts are highlighted and numbered on your own photo, using SAM 3.1 masks, not a generic diagram.", 6),
    Scene("step", "06_step", "Guided repair: one step per screen, read aloud, with the why and the warnings.",
          "The repair is guided one step at a time, with the target part marked, a voice readout, the reason why, and warnings.", 7),
    Scene("check_fail", "07_check_fail", "Check my step: a new photo is verified. ⚠ Correction when it's wrong.",
          "After each step you tap Check my step and snap a photo. Muse Spark compares it with the expected state. "
          "Here the photo is too dark, so it asks for the torch instead of guessing.", 8),
    Scene("check_pass", "08_check_pass", "✓ Verified by the camera, then on to the next step.",
          "Retake it, and the step is verified. Every step is checked by the camera before you move on.", 6),
    Scene("replan", "09_replan", "Still broken? The agent re-plans to the next likely cause.",
          "If it still doesn't work, you say what happened, and the agent re-plans to the next most likely cause. "
          "Plan, act, verify, re-plan.", 7),
    Scene("pump", "10_pump", "Water pump runs but no water: loss of prime, step by step.",
          "Same loop for a water pump that hums but gives no water: unplug first, then re-prime it, step by step.", 7),
    Scene("rice", "11_rice_stop", "RED STOP: opening 220 V internals → take it to a service centre.",
          "And it knows when to say no. A rice cooker that won't heat would need opening its 220 volt internals, "
          "so the safety gate stops the guidance and recommends a service centre.", 8),
    Scene("report", "12_report", "Repair report as PDF + 'My garage' history on the phone. No account.",
          "When you finish, you get a repair report as a PDF to share, and the job is saved to My garage on your phone. No account needed.", 7),
    Scene("lang", "13_english", "English and Basa Jawa too (Javanese UI + Javanese voice input).",
          "The app also runs in English, and in Javanese, with Javanese voice input.", 5),
    Scene("arch", "arch", "Meta models: Voice Transcribe · Muse Spark · SAM 3.1 · Muse Image · Muse Spark Open (open weights).",
          "Under the hood: Muse Voice Transcribe, Muse Spark for vision, diagnosis, planning and verification, SAM 3.1 for masks, "
          "and Muse Image for diagrams when your photo can't show the action. One switch runs the reasoning on Muse Spark Open, "
          "Meta's open-weights model, on Baseten. The safety gate is enforced in code, in three layers.", 14),
    Scene("close", "title:Tukang Copilot|Every phone becomes a mechanic's apprentice.",
          "Open source, MIT licence, built during the Meta Global AI Developer Hackathon.",
          "Tukang Copilot. Every phone becomes a mechanic's apprentice.", 6),
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


def shots() -> None:
    from playwright.sync_api import sync_playwright

    SHOTS.mkdir(parents=True, exist_ok=True)
    base, srv = _server()
    dark = Path(tempfile.mkdtemp()) / "dark.jpg"
    Image.new("RGB", (800, 600), (6, 6, 6)).save(dark)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=_chromium(), args=["--no-proxy-server"])
        pg = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True).new_page()

        def snap(name: str, full: bool = False) -> None:
            pg.wait_for_timeout(350)
            pg.screenshot(path=str(SHOTS / f"{name}.png"), full_page=full)

        def go_sample(sample: str, lang: str = "id") -> None:
            pg.goto(base + "/"); pg.select_option("#lang", lang); pg.wait_for_timeout(200)
            pg.click(f'button.sample[data-sample="{sample}"]')

        pg.goto(base + "/"); pg.wait_for_selector("#modeBadge:not(.hidden)")
        pg.set_input_files("#photo", str(FIX / "standin_motor_plug_area.jpg"))
        pg.fill("#text", "Motor saya Honda Beat susah hidup, distarter cuma bunyi tapi mesin nggak nyala.")
        snap("01_home")
        pg.click("#goBtn"); pg.wait_for_selector("#progress:not(.hidden)"); pg.wait_for_timeout(250)
        snap("02_progress")
        pg.wait_for_selector("#question:not(.hidden)", timeout=30000); pg.fill("#answerText", "Tidak bau bensin")
        snap("03_question")
        pg.click("#answerBtn"); pg.wait_for_selector("#result:not(.hidden)", timeout=30000)
        pg.evaluate("window.scrollTo(0,0)"); snap("04_diagnosis")
        pg.locator("#partsWrap").scroll_into_view_if_needed(); pg.evaluate("window.scrollBy(0,-120)"); snap("05_parts")
        pg.locator("#stepCard").scroll_into_view_if_needed(); snap("06_step")
        pg.set_input_files("#stepPhoto", str(dark))
        pg.wait_for_function("!document.querySelector('#checkResult').textContent.includes('…')", timeout=20000)
        pg.locator("#checkResult").scroll_into_view_if_needed(); snap("07_check_fail")
        pg.set_input_files("#stepPhoto", str(FIX / "standin_motor_step_cap_on.jpg"))
        pg.wait_for_timeout(600)
        pg.wait_for_function("!document.querySelector('#checkResult').textContent.includes('…')", timeout=20000)
        pg.locator("#checkResult").scroll_into_view_if_needed(); snap("08_check_pass")
        pg.fill("#stuckText", "Sudah dicoba, mesin tetap tidak nyala."); pg.click("#stuckBtn"); pg.wait_for_timeout(1500)
        pg.locator("#stepCard").scroll_into_view_if_needed(); pg.evaluate("window.scrollBy(0,-260)"); snap("09_replan")
        pg.locator("#pdfBtn").scroll_into_view_if_needed(); snap("12_report")
        go_sample("pump"); pg.wait_for_selector("#result:not(.hidden)", timeout=30000)
        pg.evaluate("window.scrollTo(0,0)"); snap("10_pump")
        go_sample("rice"); pg.wait_for_selector("#stopBox:not(.hidden)", timeout=30000)
        pg.locator("#stopBox").scroll_into_view_if_needed(); pg.evaluate("window.scrollBy(0,140)"); snap("11_rice_stop")
        go_sample("faucet", "en"); pg.wait_for_selector("#result:not(.hidden)", timeout=30000)
        pg.evaluate("window.scrollTo(0,0)"); snap("13_english")
        pg.goto(base + "/"); pg.select_option("#lang", "jv"); pg.wait_for_timeout(300); snap("14_garage_jv", full=True)
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
        ("Find parts", "SAM 3.1 masks\n→ numbered overlay", (1100, 230), (204, 230, 255)),
        ("Diagnose", "Muse Spark 1.3\nor Muse Spark Open*", (1440, 230), (255, 228, 204)),
        ("Safety gate", "3 layers in code\nred = STOP + pro", (1440, 560), (255, 210, 205)),
        ("Plan", "Muse Spark → steps\nwith expected state", (1100, 560), (255, 228, 204)),
        ("Illustrate", "Muse Image edit\nof YOUR photo", (760, 560), (225, 214, 245)),
        ("Verify step", "new photo → Spark\n✓ pass / ⚠ correction", (420, 560), (210, 240, 220)),
        ("Report", "PDF + My garage\n(no account)", (80, 560), (230, 230, 230)),
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
        shot = shot.resize((pw_, ph), Image.Resampling.LANCZOS)
        x = (fw - pw_) // 2 if vertical else 140
        y = 140 if vertical else 60
        d.rounded_rectangle([x - 14, y - 14, x + pw_ + 14, y + ph + 14], radius=36, fill=INK)
        im.paste(shot, (x, y))
        if not vertical:
            d.text((x + pw_ + 120, 120), "Tukang Copilot", fill=ORANGE, font=font(56))
            d.text((x + pw_ + 120, 195), "demo mode · labelled stand-in photos", fill=MUTED, font=font(28, False))
    if sc.image != "arch" or True:
        f = font(46 if not vertical else 44)
        cw = (fw - 900) if (not vertical and not sc.image.startswith(("title:", "arch"))) else fw - 160
        cx = 900 if (not vertical and not sc.image.startswith(("title:", "arch"))) else 80
        lines = _wrap(d, sc.caption, f, cw)
        lh = 60
        if vertical:
            cy = fh - 380 if not sc.image.startswith("title:") else fh - 520
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
    """30-45 s 9:16 clip for X: hook, parts, check, rice stop, models, close."""
    keys = ["hook", "parts", "check_pass", "rice", "arch", "close"]
    short = {"hook": "Motor mogok, bengkel tutup? Foto + ngomong.", "parts": "SAM 3.1 menandai part di foto KAMU.",
             "check_pass": "Tiap langkah dicek kamera ✓", "rice": "Bahaya? Dia bilang STOP.",
             "arch": "Built with Meta Muse Spark + SAM 3.1 + Muse Image", "close": "Tukang Copilot · open source"}
    parts: list[Path] = []
    for k in keys:
        sc = next(s for s in SCENES if s.key == k)
        v = Scene(sc.key, sc.image, short[k], sc.say, 5.5)
        png = work / f"v_{k}.png"; _frame(v, vertical=True).save(png)
        seg = work / f"v_{k}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-t", "6", "-i", str(png),
                        "-f", "lavfi", "-t", "6", "-i", "anullsrc=r=44100:cl=stereo", "-t", "6",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-ar", "44100", "-ac", "2", str(seg)], check=True)
        parts.append(seg)
    lst = work / "vlist.txt"; lst.write_text("".join(f"file '{p}'\n" for p in parts))
    out = DEMO / "tukang-copilot-x-vertical.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
    print("vertical ->", out)


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = {"shots": [shots], "diagram": [diagram], "voice": [voice], "video": [video], "all": [shots, diagram, voice, video]}
    for fn in steps[cmd]:
        fn()


if __name__ == "__main__":
    main()
