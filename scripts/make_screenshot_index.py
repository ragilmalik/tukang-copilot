"""Write docs/demo/screenshots/INDEX.md from the files on disk: every PNG, what it shows and its pixel size.

    python scripts/make_screenshot_index.py      # exit 1 when a PNG is not listed or a listed file is missing

Numbered set: descriptions below (make_demo_assets.py shots). Gallery: gallery/shots.json written by
scripts/make_screenshots.py. Every PNG on disk must be listed, and every listed file must exist.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parent.parent
SHOTS = REPO / "docs" / "demo" / "screenshots"
NUMBERED = {
    "01_home": "Capture screen: sample photo picked, problem typed (Bahasa Indonesia)",
    "02_progress": "Progress while the recorded run streams in",
    "03_question": "Follow-up question (only when the recorded run asked one)",
    "04_diagnosis": "Diagnosis: likely causes with confidence",
    "05_parts": "SAM 3.1 masks numbered on the photo",
    "06_step": "Step card",
    "07_check_fail": "Step check fails: photo too dark",
    "08_check_pass": "Step check passes on the step the photo shows",
    "09_replan": "Re-plan banner after 'still broken'",
    "10_pump": "Water pump result (recorded live session)",
    "11_rice_stop": "Rice cooker: red safety stop",
    "12_report": "Share, PDF and hand-off buttons",
    "13_english": "Kitchen tap result in English",
    "14_garage_jv": "Home in Basa Jawa with My garage (full page)",
    "15_preflight": "Safety tick list before step 1",
    "16_live_guide": "Live camera guide: SAM 3.1 outline on the camera picture (live call)",
    "17_hands_free": "Hands-free voice bar",
    "18_handoff": "Hand-off to a mechanic",
    "19_stop_pdf": "PDF report of the red stop, page 1",
    "20_javanese_result": "Scooter tyre result in Basa Jawa",
    "22_stop_handoff": "Red stop: do this now, service buttons, hand-off",
    "23_agent_log": "Agent log",
    "24_agent_jump": "Tap a log line: the step card flashes",
    "25_pdf_agent": "PDF report page with the agent log",
    "26_share_card": "Share card image (1200x630)",
    "27_recorded_demo": "Recorded demo in English (what a visitor sees while the server sleeps)",
    "28_diagram_step": "Step with a Muse Image diagram (English)",
    "29_laptop": "Laptop view: phone frame, QR code, 1-tap demo, language switch",
    "30_whatsapp_jv_diagnosis": "WhatsApp simulator, Basa Jawa: marked photo and likely cause",
    "30_whatsapp_jv_steps": "WhatsApp simulator, Basa Jawa: step with buttons",
    "30_whatsapp_jv_redstop": "WhatsApp simulator, Basa Jawa: gas smell, red stop",
    "30_whatsapp_en_check": "WhatsApp simulator, English: camera check",
    "30_whatsapp_en_pdf": "WhatsApp simulator, English: PDF report in the chat",
}


def size(p: Path) -> str:
    with Image.open(p) as im:
        return f"{im.width}x{im.height}"


def main() -> int:
    gallery = json.loads((SHOTS / "gallery" / "shots.json").read_text(encoding="utf-8"))
    on_disk = {p.relative_to(SHOTS).as_posix() for p in SHOTS.rglob("*.png")}
    listed: set[str] = set()
    out = ["# Screenshot index", "",
           "Every screenshot of the app in this folder, what it shows and its pixel size. Phone shots are 390x844 CSS px",
           "at device scale 3 (1170x2532; the kept older ones are scale 2). All answers on screen are recorded answers from the live Meta Model API on the",
           "AI-generated sample photos (labelled on each photo); see the notes at the end for the shots that are not.",
           "",
           "Re-make: `python scripts/make_demo_assets.py shots` (numbered set, needs `DEMO_RECORDED_DATA`; the live camera",
           "guide is the only live call) and `python scripts/make_screenshots.py` (gallery, no model calls); then",
           "`python scripts/make_screenshot_index.py` rewrites this file.", "",
           "## Numbered set (README, video end card, marketing images)", "", "| File | Shows | Size |", "|---|---|---|"]
    OLD = ["03_question", "16_live_guide", "30_whatsapp_jv_diagnosis", "30_whatsapp_jv_steps", "30_whatsapp_jv_redstop",
           "30_whatsapp_en_check", "30_whatsapp_en_pdf"]
    for name, what in NUMBERED.items():
        rel = f"{name}.png"
        if rel in on_disk and name not in OLD:
            out.append(f"| `{rel}` | {what} | {size(SHOTS / rel)} |")
            listed.add(rel)
    out += ["", "## Kept from the previous sample photo set (1.31.1, not re-taken)", "",
            "These show the old sample photos with the live answers recorded on them on 6 Nov 2026 (before the new photos).",
            "They stay as a record of those screens; the video and the GIF re-made on 6 Nov 2026 use none of them. Why they were not re-taken:",
            "the new 1-tap demo recording has no follow-up question (the model was sure), no recorded sample session asked",
            "one, and the live camera guide and the WhatsApp simulator need new live calls that the $1.00 cap of the remake",
            "no longer covered (the live guide run spent $0.05 on 20 SAM 3.1 frames and did not lock on the new pump photo).",
            "", "| File | Shows | Size |", "|---|---|---|"]
    for name in OLD:
        rel = f"{name}.png"
        if rel in on_disk:
            out.append(f"| `{rel}` | {NUMBERED[name]} (old sample photo) | {size(SHOTS / rel)} |")
            listed.add(rel)
    groups = [("Bahasa Indonesia, light", "id_light_"), ("Basa Jawa, light", "jv_light_"), ("English, light", "en_light_"),
              ("Bahasa Indonesia, dark", "id_dark_"), ("Static build (no server)", "static_"), ("Laptop", "laptop_"),
              ("PDF pages and share card", "pdf_")]
    for title, prefix in groups:
        rows = [g for g in gallery if Path(g["file"]).name.startswith(prefix)]
        if not rows:
            continue
        out += ["", f"## Gallery: {title}", "", "| File | Shows | Size |", "|---|---|---|"]
        for g in rows:
            out.append(f"| `{g['file']}` | {g['what']} | {size(SHOTS / g['file'])} |")
            listed.add(g["file"])
    missing = sorted(on_disk - listed)
    gone = sorted(g["file"] for g in gallery if g["file"] not in on_disk)
    out += ["", "## Notes", "",
            "- `gallery/id_light_34_error_retry.png` is a real failed run: for that one run the server's Meta API address",
            "  pointed at a closed local port, so the app's own error message and Retry button show. Nothing reached Meta.",
            "- `gallery/id_light_35_offline.png` is Chromium switched offline; the bar is the page's own offline handling.",
            "- The motorbike flow is the app's recorded 1-tap demo (\"Recorded demo\" badge on screen). In this recording",
            "  the model was sure of the cause (plug cap off the spark plug) in every language, so it asked no follow-up",
            "  question. The four recorded sample sessions did not ask either, so there is no current question screen.",
            f"- {len(listed)} PNG files listed."]
    (SHOTS / "INDEX.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    if missing or gone:
        print("not listed:", missing, "listed but missing:", gone)
        return 1
    print(f"INDEX.md: {len(listed)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
