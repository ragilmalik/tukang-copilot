"""Build the static demo: the recorded 1-tap demo as plain files, no server needed.

Run `python scripts/build_static.py --help` for the instructions (they are the user-facing docs for this build).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
DEFAULT_OUT = ROOT / "dist-static"

HELP = """\
Static build of Tukang Copilot (recorded demo, no server).

What it makes
  A folder (default: dist-static/, which git ignores) with index.html and static/.
  Opening it plays ONE recorded demo-mode run of the 1-tap demo (motorbike that
  will not start: question, diagnosis, SAM-marked photo, steps, camera checks,
  re-plan, PDF). A purple "Recorded demo" badge is on screen the whole time.
  Nothing is computed: the page never calls the API and never sends a photo.
  Own photos, other samples, the live camera guide and voice commands say
  plainly that they need the live server.

Why
  The free Render server sleeps and takes about a minute to wake. A static
  host answers at once, so whoever opens this link sees the demo right away.
  Put the live server link next to it for the real AI.

Build
  python scripts/build_static.py              # writes dist-static/
  python scripts/build_static.py --out DIR    # somewhere else
  python scripts/build_static.py --check      # build to a temp folder and verify only

Try it on your computer
  python -m http.server 8080 --directory dist-static
  then open http://localhost:8080 and tap "Try the 1-tap demo".

Host it (this publishes a public page, so only with my approval)
  GitHub Pages: push the CONTENTS of dist-static/ to a gh-pages branch (or its
    own repo), then Settings > Pages > Deploy from branch. Works under a
    sub-path such as https://ragilmalik.github.io/tukang-copilot/ because every
    path in the build is relative. A .nojekyll file is included.
  Netlify: drag the dist-static/ folder onto app.netlify.com/drop.
  Rebuild after any change to web/ or after python scripts/record_replay.py.
"""


def _version() -> str:
    m = re.search(r'__version__ = "([^"]+)"', (ROOT / "api" / "__init__.py").read_text(encoding="utf-8"))
    return m.group(1) if m else "unknown"


def _index_html(version: str) -> str:
    html = (WEB / "index.html").read_text(encoding="utf-8")
    html = re.sub(r'\s*<link rel="manifest"[^>]*>', "", html)  # no PWA install: the build has no service worker
    html = re.sub(r'\s*<p [^>]*id="waSim"[^>]*>.*?</p>', "", html, flags=re.S)  # no /wa simulator without a server
    html = re.sub(r'\s*<a [^>]*id="sideWa"[^>]*>.*?</a>', "", html, flags=re.S)
    html = html.replace('href="/static/', 'href="static/').replace('src="/static/', 'src="static/')
    flag = (
        '\n  <!-- Static build (scripts/build_static.py): plays a RECORDED demo-mode run, never calls the API. -->\n'
        f'  <script>window.TC_STATIC = {{ build: "{version}" }};</script>\n'
        '  <style>#garage{display:none!important}</style>\n'
        '  <meta name="robots" content="noindex">\n'
    )
    html = html.replace('<meta charset="utf-8">', '<meta charset="utf-8">' + flag, 1)
    return html


def build(out: Path) -> dict[str, object]:
    demo = WEB / "replay" / "demo.json"
    if not demo.exists():
        raise SystemExit("No recording in web/replay/. Run: python scripts/record_replay.py")
    if out.exists():
        shutil.rmtree(out)
    static = out / "static"
    skip = {"index.html", "guide.html", "gone.html", "wa.html", "wa.js", "sw.js", "manifest.webmanifest"}
    shutil.copytree(WEB, static, ignore=lambda d, names: [n for n in names if Path(d) == WEB and n in skip])
    # the recording points at /static/replay/...: make it relative to the page
    rec = (static / "replay" / "demo.json").read_text(encoding="utf-8").replace('"/static/replay/', '"static/replay/')
    (static / "replay" / "demo.json").write_text(rec, encoding="utf-8")
    version = _version()
    (out / "index.html").write_text(_index_html(version), encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    info = {
        "kind": "tukang-copilot static judge build",
        "app_version": version,
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "recorded_with": json.loads(rec).get("recorded_with"),
        "note": "Plays one RECORDED demo-mode run (labelled on screen). No server, no model calls, no uploads.",
    }
    (out / "BUILD_INFO.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return info


def verify(out: Path) -> list[str]:
    """Problems that would break the build on a static host (empty list = fine)."""
    probs = []
    html = (out / "index.html").read_text(encoding="utf-8")
    if "window.TC_STATIC" not in html:
        probs.append("index.html has no TC_STATIC flag")
    for ref in re.findall(r'(?:src|href)="([^"#]+)"', html):
        if ref.startswith("/"):
            probs.append(f"root-absolute path in index.html: {ref}")
        elif not ref.startswith(("http", "mailto:", "data:")) and not (out / ref).exists():
            probs.append(f"missing file: {ref}")
    rec = json.loads((out / "static" / "replay" / "demo.json").read_text(encoding="utf-8"))
    for a in rec.get("assets", []):
        if a.startswith("/") or not (out / a).exists():
            probs.append(f"recording asset not found: {a}")
    if "waSim" in html:
        probs.append("index.html still links the WhatsApp simulator (needs a server)")
    for name in ("sw.js", "manifest.webmanifest", "guide.html", "gone.html", "wa.html", "wa.js"):
        if (out / "static" / name).exists():
            probs.append(f"server-only file copied: {name}")
    return probs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="build_static.py", description=HELP, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output folder (default: dist-static/)")
    ap.add_argument("--check", action="store_true", help="build into a temporary folder, verify, and delete it")
    a = ap.parse_args(argv)
    if a.check:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "dist-static"
            build(out)
            probs = verify(out)
    else:
        out = a.out.resolve()
        info = build(out)
        probs = verify(out)
        print(f"Built the static demo (app {info['app_version']}, recording from {info['recorded_with']}) in {out}")
    if probs:
        print("PROBLEMS:\n  " + "\n  ".join(probs))
        return 1
    print("OK: no server needed, every path is relative, recorded demo included.")
    if not a.check:
        print(f"Try it: python -m http.server 8080 --directory {out}  then open http://localhost:8080")
    return 0


if __name__ == "__main__":
    sys.exit(main())
