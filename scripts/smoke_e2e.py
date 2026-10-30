"""End-to-end smoke test of a RUNNING Tukang Copilot (local or deployed), over plain HTTP, like a phone would.

    python scripts/smoke_e2e.py                         # http://localhost:8000
    python scripts/smoke_e2e.py https://your-app.onrender.com

Runs the three demo scenarios (motorbike, faucet, rice cooker), answers the follow-up question, checks a
step with a photo, asks for a re-plan, fetches the report and every image the guide links to.
Exits 0 only if every check passed. Works in demo (mock) and live mode.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
fails: list[str] = []


def ok(cond: bool, what: str) -> None:
    print(("  PASS " if cond else "  FAIL ") + what)
    if not cond:
        fails.append(what)


def wait(c: httpx.Client, sid: str, timeout: float = 240) -> dict:
    t0 = time.time()
    while time.time() - t0 < timeout:
        s = c.get(f"/api/sessions/{sid}").json()
        if s["status"] not in ("created", "running"):
            return s
        time.sleep(1)
    raise TimeoutError(sid)


def main() -> int:
    with httpx.Client(base_url=BASE, timeout=120, trust_env=not BASE.startswith("http://localhost")) as c:
        h = c.get("/health").json()
        print(f"{BASE}  mode={h['mode']}  version={h['version']}")
        ok(h["ok"] is True, "/health")
        ok(c.get("/").status_code == 200 and "Tukang" in c.get("/").text, "home page loads")
        ok(c.get("/manifest.webmanifest").status_code == 200 and c.get("/sw.js").status_code == 200, "PWA manifest + service worker")
        for sample, expect in (("motor", "ready"), ("pump", "ready"), ("faucet", "ready"), ("rice", "stopped")):
            print(f"[{sample}]")
            t0 = time.time()
            sid = c.post("/api/sessions", data={"sample": sample, "language": "id"}).json()["id"]
            s = wait(c, sid)
            if s["status"] == "needs_answer":
                ok(bool(s["question"]), f"agent asked a follow-up: {s['question'][:60]}")
                c.post(f"/api/sessions/{sid}/answer", data={"text": "Tidak"})
                s = wait(c, sid)
            ok(s["status"] == expect, f"status {s['status']} (expected {expect}) in {time.time() - t0:.1f}s {s.get('error') or ''}")
            if s.get("parts_image"):
                ok(c.get(f"/files/{sid}/{s['parts_image']}").status_code == 200, "highlighted-parts image")
            if expect != "ready":
                ok(s["safety"]["level"] == "red", "red safety stop shown")
                r = c.get(f"/api/sessions/{sid}/report.pdf")
                ok(r.status_code == 200 and r.content[:4] == b"%PDF", "PDF report for the technician")
                continue
            r = c.get(f"/api/sessions/{sid}/workshop.pdf")
            ok(r.status_code == 200 and r.content[:4] == b"%PDF", "workshop sheets PDF")
            for d in s["diagrams"].values():
                if d.get("file"):
                    ok(c.get(f"/files/{sid}/{d['file']}").status_code == 200, f"diagram {d['file']}")
            photo = (ROOT / "samples" / f"{sample}.jpg").read_bytes()
            r = c.post(f"/api/sessions/{sid}/steps/1/check", files={"photo": ("p.jpg", photo, "image/jpeg")})
            ok(r.status_code == 200 and "passed" in r.json(), f"check-my-step: passed={r.json().get('passed')}")
            r = c.post(f"/api/sessions/{sid}/replan", data={"report": "masih rusak"})
            ok(r.status_code == 200 and r.json()["cause_index"] == 1, "re-plan to next cause")
            rep = c.get(f"/api/sessions/{sid}/report").json()
            ok(bool(rep.get("problem")), "report")
            ok(c.get(f"/guide/{sid}").status_code == 200, "shareable guide page")
            r = c.get(f"/api/sessions/{sid}/report.pdf")
            ok(r.status_code == 200 and r.content[:4] == b"%PDF", f"PDF report ({len(r.content) // 1024} KB)")
    print("\nALL PASSED" if not fails else f"\n{len(fails)} FAILED: {fails}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
