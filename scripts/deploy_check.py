"""Check a deployed Tukang Copilot (Render, or any URL) the way a judge's phone would see it.

    python scripts/deploy_check.py https://tukang-copilot.onrender.com
    python scripts/deploy_check.py https://tukang-copilot.onrender.com --live   # also run real-model checks (costs cents)
    python scripts/deploy_check.py http://localhost:8000 --quick                 # skip the full end-to-end smoke

Prints PASS / WARN / FAIL lines, each FAIL with a plain-English fix. Exit 0 = no FAIL (WARNs are allowed).

What it checks: https, /api/health fields and mode, home page, PWA manifest + service worker (install to
home screen), security headers (the camera needs `camera=(self)`), a PDF report, and then the full
scripts/smoke_e2e.py run (all five demo scenarios). In LIVE mode any session whose `fallback` list is
non-empty is a FAIL: DEMO_FALLBACK (on by default) would otherwise hide a bad key behind demo answers.

Spend: in DEMO mode everything is free. In LIVE mode every repair calls real Meta models, so the PDF check
and the full smoke only run with --live (about 5 repairs, roughly $0.10 to $0.50 in total, each repair is
capped by MAX_COST_PER_SESSION_USD).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parent.parent
STAGES = ("listen", "look", "segment", "diagnose", "plan", "illustrate", "verify")
_COLOR = sys.stdout.isatty()
G, R, Y, D, E = (("\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m") if _COLOR else ("",) * 5)
counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
FALLBACK_FIX = ("DEMO_FALLBACK=1 hid a failing live call (usually a wrong or expired MODEL_API_KEY, or no credit). "
                "Run  python scripts/check_keys.py  with the same key, fix it in Render > Environment, or set "
                "DEMO_FALLBACK=0 while testing so errors show instead of demo answers.")


def line(status: str, what: str, fix: str = "") -> None:
    counts[status] += 1
    color = {"PASS": G, "WARN": Y, "FAIL": R}[status]
    print(f"{color}{status}{E} {what}")
    if fix and status != "PASS":
        print(f"     {D}fix:{E} {fix}")


def get_health(c: httpx.Client, base: str, wait_s: float) -> dict[str, Any] | None:
    """The free Render plan sleeps after 15 min idle; the first request can take about a minute to wake it."""
    t0, last = time.time(), ""
    while time.time() - t0 < wait_s:
        try:
            r = c.get("/api/health")
            if r.status_code == 200:
                waited = time.time() - t0
                if waited > 15:
                    line("WARN", f"server took {waited:.0f}s to answer (it was asleep)",
                         "Normal on Render's free plan. For judging day switch the service to the Starter plan "
                         "(Settings > Instance type) so it never sleeps, or open the URL a minute before the demo.")
                data: dict[str, Any] = r.json()
                return data
            last = f"HTTP {r.status_code}"
        except httpx.HTTPError as e:
            last = type(e).__name__
        time.sleep(5)
    line("FAIL", f"{base}/api/health did not answer within {wait_s:.0f}s ({last})",
         "Open the Render dashboard > your service > Logs. A red 'Deploy failed' means the build broke: "
         "click 'Manual Deploy > Deploy latest commit' or roll back (docs/DEPLOY.md, Roll back).")
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", help="e.g. https://tukang-copilot.onrender.com")
    ap.add_argument("--live", action="store_true", help="in LIVE mode, also run the PDF check and the full smoke (real model calls, costs cents)")
    ap.add_argument("--quick", action="store_true", help="skip the full end-to-end smoke test")
    ap.add_argument("--wait", type=float, default=120, help="seconds to wait for a sleeping server (default 120)")
    a = ap.parse_args()
    base = a.url.rstrip("/")
    local = "://localhost" in base or "://127.0.0.1" in base
    print(f"Checking {base}\n")

    # 1. https
    if base.startswith("https://"):
        line("PASS", "uses https (phones only allow the camera and microphone on https)")
    elif local:
        line("WARN", "plain http on this computer (fine for local tests; the real deploy must be https)")
    else:
        line("FAIL", "the address is not https", "Use the https://... address Render shows at the top of your service page.")

    with httpx.Client(base_url=base, timeout=60, follow_redirects=True, trust_env=not local) as c:
        if base.startswith("https://"):
            try:
                r = httpx.get("http://" + base[len("https://"):] + "/health", timeout=30, follow_redirects=False, trust_env=True)
                if r.status_code in (301, 302, 307, 308) and r.headers.get("location", "").startswith("https://"):
                    line("PASS", "http:// redirects to https://")
                else:
                    line("WARN", f"http:// answered {r.status_code} instead of redirecting to https://",
                         "Render redirects automatically; on another host turn on 'force https'.")
            except httpx.HTTPError:
                line("WARN", "could not test the http -> https redirect")

        # 2. health
        h = get_health(c, base, a.wait)
        if h is None:
            print(f"\n{R}Stopped: the server is not answering.{E}")
            return 1
        missing = [k for k in ("ok", "version", "mode", "meta_api_key", "open_weights", "models") if k not in h]
        if h.get("ok") is True and not missing:
            line("PASS", f"/api/health ok: version {h['version']}, mode {h['mode']}")
        else:
            line("FAIL", f"/api/health is missing {missing or 'ok=true'}", "The deploy is running old or broken code: redeploy the latest commit.")
        models = h.get("models") or {}
        no_model = [s for s in STAGES if not models.get(s)]
        if no_model:
            line("WARN", f"/api/health lists no model for: {', '.join(no_model)}")
        else:
            line("PASS", "every stage names its Meta model: " + ", ".join(sorted({str(v).split(' ')[0] for v in models.values()})))
        mode = h.get("mode")
        if mode == "live":
            line("PASS", "LIVE mode: real Meta models answer (the key is set and MOCK=0)")
        elif h.get("meta_api_key"):
            line("WARN", "DEMO mode although a key is set (MOCK=1)",
                 "Render > your service > Environment: set MOCK to 0, Save. Leave it at 1 if you want the free demo on purpose.")
        else:
            line("WARN", "DEMO mode: no MODEL_API_KEY on the server (free recorded answers)",
                 "Render > your service > Environment > add MODEL_API_KEY with your dev.meta.ai key, Save (it redeploys by itself).")
        if mode == "live" and h.get("demo_fallback"):
            line("PASS", "demo fallback ON: if a live call fails the repair still finishes on a labelled demo answer "
                         "(this check flags any session that used it)")
        if h.get("open_weights"):
            line("PASS", "open weights ON: diagnosis and plan run on Muse Spark Open (badge shows in the app)")
        else:
            line("PASS", "open weights off (optional; see docs/SETUP_FOR_MALIK.md to turn it on)")

        # 3. home page + PWA
        r = c.get("/")
        if r.status_code == 200 and "Tukang" in r.text:
            line("PASS", "home page loads")
        else:
            line("FAIL", f"home page answered {r.status_code}", "Check the Render logs for an error at startup.")
        hdr = r.headers
        try:
            m = c.get("/manifest.webmanifest")
            man = m.json()
            icons_ok = all(c.get(i["src"]).status_code == 200 for i in man.get("icons", []))
            if m.status_code == 200 and man.get("start_url") and man.get("icons") and icons_ok:
                line("PASS", f"PWA manifest ({man.get('short_name')}) with {len(man['icons'])} icons that load")
            else:
                line("FAIL", "PWA manifest incomplete or icons missing", "Redeploy the latest commit (web/ folder must be in the image).")
        except (json.JSONDecodeError, httpx.HTTPError, KeyError):
            line("FAIL", "PWA manifest is not valid JSON", "Redeploy the latest commit.")
        sw = c.get("/sw.js")
        if sw.status_code == 200 and "javascript" in sw.headers.get("content-type", ""):
            line("PASS", "service worker served as JavaScript")
        else:
            line("FAIL", f"service worker: HTTP {sw.status_code} {sw.headers.get('content-type', '')}", "Redeploy the latest commit.")

        # 4. security headers
        need = {"x-content-type-options": "nosniff", "x-frame-options": "SAMEORIGIN", "referrer-policy": "no-referrer"}
        bad = [k for k, v in need.items() if hdr.get(k, "").lower() != v.lower()]
        if bad:
            line("FAIL", f"security headers missing: {', '.join(bad)}", "The app sets these itself: the deploy is running old code, redeploy.")
        else:
            line("PASS", "security headers: nosniff, SAMEORIGIN, no-referrer")
        pp = hdr.get("permissions-policy", "")
        if "camera=(self)" in pp and "microphone=(self)" in pp:
            line("PASS", "camera and microphone allowed for this site (permissions-policy)")
        else:
            line("FAIL", f"permissions-policy does not allow camera/microphone: '{pp}'",
                 "If a proxy (Cloudflare etc.) rewrites headers, let it pass the app's Permissions-Policy through.")
        if base.startswith("https://"):
            if hdr.get("strict-transport-security"):
                line("PASS", "HSTS header present")
            else:
                line("WARN", "no HSTS header (optional; Render serves https anyway)")

        # 5. PDF report (one sample repair)
        if mode == "live" and not a.live:
            line("WARN", "PDF check skipped in LIVE mode (it would make real model calls)", "Run again with --live to include it (costs a few cents).")
        else:
            try:
                r = c.post("/api/sessions", data={"sample": "rice", "language": "en"})
                r.raise_for_status()
                sid, own = r.json()["id"], {"X-Owner-Token": r.json().get("owner_token", "")}
                t0 = time.time()
                st = ""
                while time.time() - t0 < 240:
                    st = c.get(f"/api/sessions/{sid}").json()["status"]
                    if st not in ("created", "running"):
                        break
                    time.sleep(1)
                fb = c.get(f"/api/sessions/{sid}").json().get("fallback") or []
                if mode == "live" and fb:
                    line("FAIL", f"LIVE repair silently used demo answers for: {', '.join(map(str, fb))}",
                         FALLBACK_FIX)
                elif mode == "live":
                    line("PASS", "LIVE sample repair answered by real models (no demo fallback)")
                pdf = c.get(f"/api/sessions/{sid}/report.pdf")
                if pdf.status_code == 200 and pdf.content[:4] == b"%PDF":
                    line("PASS", f"PDF report downloads ({len(pdf.content) // 1024} KB, sample repair finished as '{st}' in {time.time() - t0:.0f}s)")
                else:
                    line("FAIL", f"PDF report: HTTP {pdf.status_code} (repair status '{st}')",
                         "Fonts or Pillow missing in the image: redeploy from the repo's Dockerfile (Render: runtime docker).")
                c.delete(f"/api/sessions/{sid}", headers=own)
            except (httpx.HTTPError, KeyError, ValueError) as e:
                line("FAIL", f"could not run a sample repair ({e})",
                     "429/503 = the public spend guard (RATE_LIMIT_PER_HOUR / DAILY_BUDGET_USD) blocked it; wait or raise it in Environment.")

    # 6. full end-to-end smoke (all five scenarios)
    if a.quick:
        line("WARN", "full end-to-end smoke skipped (--quick)")
    elif mode == "live" and not a.live:
        line("WARN", "full end-to-end smoke skipped in LIVE mode", "Run again with --live (about 5 real repairs, well under $1).")
    else:
        print(f"\n{D}Running scripts/smoke_e2e.py (all five demo repairs)...{E}")
        p = subprocess.run([sys.executable, str(ROOT / "scripts" / "smoke_e2e.py"), base], capture_output=True, text=True, timeout=1500)
        fails = [ln.strip() for ln in p.stdout.splitlines() if ln.strip().startswith("FAIL")]
        fbs = [ln.strip() for ln in p.stdout.splitlines() if ln.strip().startswith("FALLBACK")]
        if mode == "live" and fbs:
            line("FAIL", f"{len(fbs)} LIVE smoke session(s) silently used demo answers: {'; '.join(fbs[:3])}", FALLBACK_FIX)
        elif mode == "live":
            line("PASS", "no smoke session needed the demo fallback (every answer came from the live models)")
        if p.returncode == 0:
            n = sum(1 for ln in p.stdout.splitlines() if ln.strip().startswith("PASS"))
            line("PASS", f"end-to-end smoke: {n} checks passed across all five demo repairs")
        else:
            line("FAIL", f"end-to-end smoke: {len(fails) or 'some'} check(s) failed: {'; '.join(fails[:4]) or (p.stderr or '')[-300:]}",
                 "Run  python scripts/smoke_e2e.py " + base + "  to see every line, and check the Render logs.")

    print(f"\n{counts['PASS']} PASS, {counts['WARN']} WARN, {counts['FAIL']} FAIL")
    if counts["FAIL"]:
        print(f"{R}NOT READY: fix the FAIL lines above.{E}")
        return 1
    print(f"{G}READY: the deploy works.{E}" + (" (WARN lines are optional improvements.)" if counts["WARN"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
