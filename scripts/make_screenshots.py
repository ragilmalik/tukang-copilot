"""Full screenshot gallery: every screen and state of the app, in Bahasa Indonesia, Basa Jawa and English, light and dark.

    DEMO_RECORDED_DATA=<folder> python scripts/make_screenshots.py      # -> docs/demo/screenshots/gallery/*.png

What it shows and where the answers come from
  Every answer on screen is a recorded live answer from the Meta Model API; this script starts no new model work.
  - The motorbike repair (main flow, three languages) is the app's own recorded 1-tap demo (web/replay/demo.json,
    opened with ?replay=1, "Recorded demo" badge on screen).
  - The pump, rice cooker (red stop), faucet (English, with a Muse Image diagram) and Basa Jawa tyre repairs are live
    sessions recorded earlier into DEMO_RECORDED_DATA (a copy of a live run's data folder, see make_demo_assets.py).
    When one of them asked its follow-up question, an untouched copy of the paused session in <folder>/paused/ gives
    the question screen.
  - The error screen is a real failed run: the Meta API address is pointed at a closed local port for that one run,
    so the app's own error path and Retry button show. Nothing is sent to Meta and nothing is paid.
  - The offline bar is Chromium switched offline (the page's own navigator.onLine handling).
  - The static build (scripts/build_static.py) is built to a temp folder and served to the browser by a route.
  The numbered shots next to this folder (01_home.png ...) are the video and README set from make_demo_assets.py shots.

Phone shots: 390x844 CSS px at device scale 3 (1170x2532 PNG). Laptop: 1280x800 at scale 2.
DEMO_PORT (default 8765) is the port of the in-process server. This script makes no paid calls.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("DEMO_PORT", "8765")
os.environ.setdefault("NARRATION_VOICE", "0")

import make_demo_assets as M  # noqa: E402  (helpers: recorded-mode server, public relay, Chromium path)

OUT = M.SHOTS / "gallery"
LANGS = ("id", "jv", "en")
PHONE: dict[str, Any] = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 3, "is_mobile": True, "has_touch": True,
         "timezone_id": M.TZ}
TEXT = {  # what an owner types on the capture screen (same sentence in each language)
    "id": "Motor saya Honda Beat susah hidup, distarter cuma bunyi tapi mesin nggak nyala.",
    "jv": "Motorku Honda Beat angel urip, distarter mung muni nanging mesine ora urip.",
    "en": "My Honda Beat won't start: the starter turns but the engine doesn't catch.",
}
ANSWER = {"id": "Ya", "jv": "Nggih", "en": "Yes"}
STUCK = {"id": "Sudah dicoba, mesin tetap tidak nyala.", "jv": "Sampun dijajal, mesine taksih mboten urip.",
         "en": "Tried it, the engine still won't start."}
STATIC_ORIGIN = "https://static.example/tukang-copilot"  # where the static build is served from (a route, not a host)
SHOT_LOG: list[dict[str, str]] = []


def snap(pg: Any, name: str, what: str, full: bool = False) -> None:
    """One PNG plus a line for INDEX.md. Never mid screen change, never with the 1-tap tip bar over the bottom."""
    pg.wait_for_timeout(350)
    if pg.is_visible("#tourClose"):
        pg.click("#tourClose"); pg.wait_for_timeout(250)
    pg.wait_for_function("() => !document.documentElement.matches(':active-view-transition')", timeout=5000)
    pg.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    SHOT_LOG.append({"file": f"gallery/{name}.png", "what": what})
    print("shot", name, flush=True)


def top_at(pg: Any, sel: str, y: int = 80) -> None:
    """Scroll so `sel` starts just under the sticky header (same rule as make_demo_assets.shots)."""
    for _ in range(5):
        pg.evaluate("([s, y]) => { const el = document.querySelector(s);"
                    " window.scrollTo({top: Math.max(0, el.getBoundingClientRect().top + scrollY - y), behavior: 'instant'}); }", [sel, y])
        pg.wait_for_timeout(250)
        off = pg.evaluate("([s, y]) => document.querySelector(s).getBoundingClientRect().top - y", [sel, y])
        at_end = pg.evaluate("scrollY <= 0 || innerHeight + scrollY >= document.documentElement.scrollHeight - 1")
        if abs(off) < 2 or at_end:
            break


def tick_preflight(pg: Any) -> None:
    for box in pg.locator("#preList input").all():
        box.check()
    pg.wait_for_timeout(200)


def check_done(pg: Any) -> None:
    pg.wait_for_function("() => { const el = document.querySelector('#checkResult');"
                         " return (el.classList.contains('isPass') || el.classList.contains('isFail'))"
                         " && !el.textContent.includes('…'); }", timeout=20000)


def main_flow(pg: Any, origin: str, lang: str, tag: str, label: str) -> None:
    """The recorded motorbike repair from the first screen to the hand-off, in one language."""
    p = f"{tag}_"
    pg.goto(origin + "/"); pg.wait_for_selector("#goBtn")
    pg.select_option("#lang", lang); pg.wait_for_timeout(400)
    pg.evaluate("window.scrollTo(0, 0)")
    snap(pg, p + "01_home", f"First screen ({label})")
    pg.set_input_files("#photo", str(M.FIX / "sample_motor_plug_area.jpg"))
    pg.fill("#text", TEXT[lang])
    pg.evaluate("document.activeElement && document.activeElement.blur()")
    top_at(pg, "#photoBox", 72)  # the picked photo, the categories and the typed problem, down to the Check button
    snap(pg, p + "02_capture", f"Capture: sample photo picked and the problem typed, nothing sent yet ({label})")
    pg.goto(origin + "/?replay=1"); pg.select_option("#lang", lang); pg.wait_for_timeout(300)
    pg.evaluate("window.TCReplay._state.tick = 3000")  # slower ticks: time to shoot the progress screen
    pg.click("#demoBtn"); pg.wait_for_selector("#progress:not(.hidden)")
    pg.wait_for_selector("#lf-segment img", timeout=30000)
    pg.wait_for_function("() => document.querySelector('#lf-segment img').naturalWidth > 0", timeout=10000)
    top_at(pg, "#progress", 72)
    snap(pg, p + "03_progress", f"Progress: each stage streams in, SAM 3.1 outline already on the photo ({label})")
    pg.evaluate("window.TCReplay._state.tick = 900")
    pg.wait_for_selector("#question:not(.hidden), #result:not(.hidden)", timeout=30000)
    if pg.is_visible("#question"):
        pg.fill("#answerText", ANSWER[lang]); pg.evaluate("document.activeElement && document.activeElement.blur()")
        top_at(pg, "#question"); snap(pg, p + "04_question", f"Follow-up question ({label})")
        pg.click("#answerBtn")
    pg.wait_for_selector("#result:not(.hidden)", timeout=30000)
    pg.evaluate("window.scrollTo(0, 0)")
    snap(pg, p + "05_result_top", f"Result, top: object, safety level, recorded-demo badge ({label})")
    top_at(pg, "#dxSummary"); snap(pg, p + "06_diagnosis", f"Diagnosis: likely causes with confidence ({label})")
    top_at(pg, "#partsWrap", 72); snap(pg, p + "07_parts", f"Parts: SAM 3.1 masks numbered on the photo ({label})")
    top_at(pg, "#result .safety", 84); snap(pg, p + "08_safety", f"Safety: before-you-start list to tick ({label})")
    tick_preflight(pg)
    top_at(pg, "#stepCard", 72); snap(pg, p + "09_step", f"Step card ({label})")
    pg.click("#sampleBad"); check_done(pg)
    top_at(pg, "#stepPhotoLabel"); snap(pg, p + "10_check_fail", f"Step check fails: photo too dark ({label})")
    pg.click("#sampleGood"); check_done(pg)
    top_at(pg, "#stepPhotoLabel"); snap(pg, p + "11_check_pass", f"Step check passes on the step the photo shows ({label})")
    pg.check("#handsFree"); pg.wait_for_selector("#voiceBar:not(.hidden)", timeout=5000); pg.wait_for_timeout(600)
    top_at(pg, "#prevBtn"); snap(pg, p + "12_hands_free", f"Hands-free voice bar on ({label})")
    pg.uncheck("#handsFree")
    pg.fill("#stuckText", STUCK[lang]); pg.click("#stuckBtn")
    pg.wait_for_function("() => document.querySelector('#stuckMsg').textContent.length > 3 && !document.querySelector('#stuckBtn').disabled",
                         timeout=20000)
    pg.wait_for_selector("#planBanner:not(.hidden)"); pg.evaluate("window.scrollTo(0, 0)")
    snap(pg, p + "13_replan", f"Re-plan: next cause after 'still broken' ({label})")
    pg.evaluate("document.querySelector('#agent').scrollIntoView({block: 'start'}); window.scrollBy(0, -70)")
    snap(pg, p + "14_agent_log", f"Agent log: every model call and decision ({label})")
    top_at(pg, "#result .actions", 72); snap(pg, p + "15_report_actions", f"Share, PDF report and hand-off buttons ({label})")
    pg.click("#mechBtn"); pg.wait_for_selector("#handoff:not(.hidden)", timeout=10000)
    pg.evaluate("document.querySelector('#handoff details') && (document.querySelector('#handoff details').open = true)")
    top_at(pg, "#mechBtn"); snap(pg, p + "16_handoff", f"Hand-off to a mechanic (WhatsApp text) ({label})")


def open_rec(pg: Any, origin: str, sid: str, lang: str) -> None:
    """Reopen a recorded session as the phone that made it (owner token in the page's store, see M.open_recorded)."""
    pg.goto(f"{origin}/")
    pg.evaluate("([id, tok]) => { let m = {}; try { m = JSON.parse(localStorage.getItem('tc_owner') || '{}') || {}; } catch (_) {}"
                " m[id] = tok; localStorage.setItem('tc_owner', JSON.stringify(m)); }", [sid, M.owner_token(sid)])
    pg.goto(f"{origin}/#{sid}")
    pg.reload()
    pg.wait_for_selector("#result:not(.hidden), #stopBox:not(.hidden), #question:not(.hidden)", timeout=30000)
    if pg.input_value("#lang") != lang:
        pg.select_option("#lang", lang); pg.wait_for_timeout(400)


def other_repairs(pg: Any, origin: str, tag: str, dark: bool) -> dict[str, str]:
    """Pump, rice cooker red stop, English faucet with diagram, Basa Jawa tyre, garage, share page, gone page."""
    p, d = f"{tag}_", " (dark)" if dark else ""
    sids = {"pump": M.recorded_session("pump", "id"), "rice": M.recorded_session("rice", "id"),
            "faucet": M.recorded_session("faucet", "en", diagram=True), "tire": M.recorded_session("tire", "jv")}
    open_rec(pg, origin, sids["rice"], "id")
    pg.wait_for_selector("#stopBox:not(.hidden)", timeout=30000); pg.wait_for_selector("#stopHandoff:not(.hidden)", timeout=10000)
    pg.evaluate("window.scrollTo(0, 0)"); snap(pg, p + "20_red_stop", "Rice cooker: red safety stop, Bahasa Indonesia" + d)
    top_at(pg, "#stopBox > p:nth-of-type(3)"); snap(pg, p + "21_red_stop_handoff", "Red stop: do this now, service buttons, hand-off" + d)
    if dark:
        return sids
    open_rec(pg, origin, sids["pump"], "id")
    pg.evaluate("window.scrollTo(0, 0)"); snap(pg, p + "22_pump_result", "Water pump result, Bahasa Indonesia")
    # the live camera guide (paid SAM 3.1 frames) is shot once, in the numbered set (16_live_guide.png)
    open_rec(pg, origin, sids["faucet"], "en"); tick_preflight(pg)
    pg.evaluate("window.scrollTo(0, 0)"); snap(pg, p + "23_faucet_result_en", "Kitchen tap result, English")
    for _ in range(10):
        if "diagram" in (pg.get_attribute("#stepImg", "src") or "") and pg.is_visible("#stepImg"):
            break
        pg.click("#nextBtn"); pg.wait_for_timeout(300)
    top_at(pg, "#stepCard", 72); snap(pg, p + "24_diagram_step_en", "Step with a Muse Image diagram, English")
    open_rec(pg, origin, sids["tire"], "jv")
    pg.evaluate("window.scrollTo(0, 0)"); snap(pg, p + "25_tire_result_jv", "Scooter tyre result, Basa Jawa")
    pg.goto(f"{origin}/guide/{sids['pump']}"); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(600)
    snap(pg, p + "26_share_page", "Share link page (/guide/<id>) of the pump repair")
    pg.goto(f"{origin}/guide/0000deadbeef"); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(300)
    snap(pg, p + "27_gone_404", "404: a share link whose guide was deleted (HTTP 404 page)")
    return sids


def garage(pg: Any, origin: str, tag: str, lang: str, what: str) -> None:
    pg.goto(origin + "/"); pg.select_option("#lang", lang); pg.wait_for_timeout(500)
    if pg.is_visible("#garage"):
        top_at(pg, "#garage", 80); snap(pg, f"{tag}_28_garage", what)
    else:
        print("garage empty: no garage shot", flush=True)


def question_from_paused(pg: Any, origin: str, tag: str) -> None:
    """The question screen from an untouched copy of a recorded live session paused at its follow-up question."""
    from api.settings import settings

    rec = Path(os.environ["DEMO_RECORDED_DATA"]) / "paused"
    paused = sorted(rec.glob("*/session.json"), key=lambda f: f.stat().st_mtime) if rec.exists() else []
    if not paused:
        print("no paused session recorded: no question shot from the samples", flush=True)
        return
    src = paused[-1].parent
    d = json.loads(paused[-1].read_text(encoding="utf-8"))
    live_dir = settings.data_dir / "sessions" / src.name
    keep = Path(tempfile.mkdtemp()) / "answered"
    shutil.copytree(live_dir, keep)       # the answered copy goes back afterwards
    shutil.rmtree(live_dir); shutil.copytree(src, live_dir)
    os.utime(live_dir / "session.json")
    try:
        lang = str(d.get("lang") or "id")
        open_rec(pg, origin, src.name, lang)
        pg.wait_for_selector("#question:not(.hidden)", timeout=15000)
        top_at(pg, "#question"); snap(pg, f"{tag}_29_question_{d.get('sample')}_{lang}",
                                      f"Follow-up question, recorded live ({d.get('sample')}, {lang})")
    finally:
        shutil.rmtree(live_dir); shutil.copytree(keep, live_dir)


def pdf_pages(base: str, pump_sid: str, rice_sid: str) -> None:
    import urllib.request

    tmp = Path(tempfile.mkdtemp())
    jobs = [("report-id.pdf", f"{base}/static/replay/report-id.pdf", "30_report_pdf_id", "PDF report, motorbike, Bahasa Indonesia"),
            ("report-en.pdf", f"{base}/static/replay/report-en.pdf", "31_report_pdf_en", "PDF report, motorbike, English"),
            ("stop.pdf", f"{base}/api/sessions/{rice_sid}/report.pdf", "32_stop_pdf", "PDF report of the red stop (rice cooker)")]
    for fname, url, name, what in jobs:
        with urllib.request.urlopen(url, timeout=30) as r:  # noqa: S310 (local server)
            (tmp / fname).write_bytes(r.read())
        n = int(next((ln.split()[1] for ln in subprocess.run(["pdfinfo", str(tmp / fname)], capture_output=True, text=True).stdout.splitlines()
                      if ln.startswith("Pages:")), "1"))
        for page in range(1, min(n, 2) + 1):
            out = OUT / f"pdf_{name}_p{page}"
            subprocess.run(["pdftoppm", "-png", "-r", "110", "-f", str(page), "-l", str(page), "-singlefile", str(tmp / fname), str(out)], check=True)
            SHOT_LOG.append({"file": f"gallery/{out.name}.png", "what": f"{what}, page {page} of {n}"})
            print("shot", out.name, flush=True)
    with urllib.request.urlopen(f"{base}/static/replay/card-id.png", timeout=30) as r:  # noqa: S310
        (OUT / "pdf_33_share_card_id.png").write_bytes(r.read())
    SHOT_LOG.append({"file": "gallery/pdf_33_share_card_id.png", "what": "Share card image (link preview), motorbike, Bahasa Indonesia"})


def error_retry(b: Any, base: str) -> None:
    """A real failed run: the Meta API address points at a closed port for this one run (nothing reaches Meta)."""
    from api.settings import settings

    old_base, old_mock = settings.meta_api_base, settings.mock
    settings.meta_api_base, settings.mock = "http://127.0.0.1:9/v1", False
    ctx = b.new_context(**PHONE, locale="id-ID")
    pg = ctx.new_page()
    try:
        pg.goto(base + "/"); pg.select_option("#lang", "id"); pg.wait_for_timeout(300)
        pg.set_input_files("#photo", str(M.FIX / "sample_motor_plug_area.jpg"))
        pg.fill("#text", TEXT["id"]); pg.click("#goBtn")
        pg.wait_for_selector("#retryBtn:not(.hidden)", timeout=120000)
        pg.wait_for_timeout(500)
        top_at(pg, "#jobErr", 200)
        snap(pg, "id_light_34_error_retry", "Error and Retry: a real failed run (Meta API unreachable, forced for this shot)")
    finally:
        settings.meta_api_base, settings.mock = old_base, old_mock
        ctx.close()


def offline_bar(pg: Any, ctx: Any, origin: str) -> None:
    pg.goto(origin + "/"); pg.select_option("#lang", "id"); pg.wait_for_timeout(400)
    ctx.set_offline(True); pg.wait_for_selector("#offlineBar:not(.hidden)", timeout=5000); pg.wait_for_timeout(300)
    snap(pg, "id_light_35_offline", "Offline: the bar the phone shows when it loses its connection")
    ctx.set_offline(False); pg.wait_for_timeout(300)


def static_build(b: Any) -> None:
    tmp = Path(tempfile.mkdtemp()) / "site"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_static.py"), "--out", str(tmp)], check=True, capture_output=True)
    ctx = b.new_context(**PHONE, locale="en-GB")

    def serve(route: Any) -> None:
        rel = route.request.url.split("?")[0].split("#")[0][len(STATIC_ORIGIN):].lstrip("/") or "index.html"
        f = tmp / rel
        if f.is_dir():
            f = f / "index.html"
        if f.is_file():
            route.fulfill(path=str(f))
        else:
            route.fulfill(status=404, body="not in the static build")
    ctx.route(STATIC_ORIGIN + "/**", serve)
    ctx.route("**/api/**", lambda r: r.abort())  # the static build must never call the API
    pg = ctx.new_page()
    pg.goto(STATIC_ORIGIN + "/"); pg.select_option("#lang", "en"); pg.wait_for_timeout(500)
    snap(pg, "static_01_home_en", "Static build (no server): first screen with the recorded-demo badge, English")
    pg.click("#demoBtn")
    pg.wait_for_selector("#question:not(.hidden), #result:not(.hidden)", timeout=30000)
    if pg.is_visible("#question"):
        pg.click("#quickAns button >> nth=0")
    pg.wait_for_selector("#result:not(.hidden)", timeout=30000); pg.evaluate("window.scrollTo(0, 0)")
    snap(pg, "static_02_result_en", "Static build: recorded motorbike result, English")
    ctx.close()


def laptop(b: Any, base: str, dark: bool) -> None:
    ctx = b.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=2, timezone_id=M.TZ,
                        color_scheme="dark" if dark else "light")
    M.serve_as_public(ctx, base)
    pg = ctx.new_page()
    pg.goto(M.PUBLIC_BASE + "/"); pg.select_option("#lang", "en"); pg.wait_for_selector("#qrBox svg", timeout=5000); pg.wait_for_timeout(400)
    name = "laptop_home_en_dark" if dark else "laptop_home_en"
    pg.screenshot(path=str(OUT / f"{name}.png"))
    SHOT_LOG.append({"file": f"gallery/{name}.png", "what": "Laptop: phone frame plus side panel (QR code, 1-tap demo, language switch)" + (" (dark)" if dark else "")})
    print("shot", name, flush=True)
    ctx.close()


def main() -> int:
    from playwright.sync_api import sync_playwright

    if not M.recorded():
        raise SystemExit("set DEMO_RECORDED_DATA to a folder of recorded live sessions (see the docstring)")
    OUT.mkdir(parents=True, exist_ok=True)
    base, srv = M._server()
    origin = M.site(base)
    errors: list[str] = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=M._chromium(), args=["--no-proxy-server"])
        for dark in (False, True):
            for lang in (LANGS if not dark else ("id",)):
                ctx = b.new_context(**PHONE, locale={"id": "id-ID", "jv": "jv-ID", "en": "en-GB"}[lang],
                                    color_scheme="dark" if dark else "light")
                ctx.add_init_script(M.SR_STUB)
                M.serve_as_public(ctx, base); M.no_new_runs(ctx, errors)
                pg = ctx.new_page(); M._console_watch(pg, errors)
                tag = f"{lang}_{'dark' if dark else 'light'}"
                label = {"id": "Bahasa Indonesia", "jv": "Basa Jawa", "en": "English"}[lang] + (", dark" if dark else "")
                main_flow(pg, origin, lang, tag, label)
                if lang == "id":
                    sids = other_repairs(pg, origin, tag, dark)
                    garage(pg, origin, tag, "id", "Garage: repairs opened on this phone" + (" (dark)" if dark else ""))
                    if not dark:
                        question_from_paused(pg, origin, tag)
                        offline_bar(pg, ctx, origin)
                ctx.close()
        pdf_pages(base, sids["pump"], sids["rice"])
        laptop(b, base, False); laptop(b, base, True)
        static_build(b)
        error_retry(b, base)
        b.close()
    srv.should_exit = True
    # the live camera guide's paid frames are the only model calls recorded mode lets through; none are wanted here
    (OUT / "shots.json").write_text(json.dumps(SHOT_LOG, indent=1, ensure_ascii=False), encoding="utf-8")
    real = [e for e in errors if "refused a new model call" in e or "pageerror" in e]
    if errors:
        print("page messages:\n" + "\n".join(errors), flush=True)
    return 1 if real else 0


if __name__ == "__main__":
    raise SystemExit(main())
