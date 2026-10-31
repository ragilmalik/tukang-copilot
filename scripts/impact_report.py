#!/usr/bin/env python3
"""Impact report: aggregate the outcome log into docs/IMPACT.md and a 1920x1080 "impact slide" PNG.

  python scripts/impact_report.py            # real trials: DATA_DIR/impact/outcomes.jsonl (live-mode rows only)
  python scripts/impact_report.py --mock     # 5 fictional testers, every output stamped MOCK DATA
  python scripts/impact_report.py --data some.jsonl --include-demo

Numbers: fixed rate, median minutes (fixed repairs), total and median rupiah saved vs the bengkel estimate
(fixed repairs only; saving = shop estimate - parts), all of it per scenario too. See docs/USER_TRIAL_KIT.md.
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

MOCK_STAMP = "MOCK DATA - replace with real trials"
SCENARIO_NAME = {"motor": "Motorbike", "pump": "Water pump", "plumbing": "Tap / pipes", "appliance": "Home appliance", "other": "Other"}


def mock_rows() -> list[dict[str, Any]]:
    """Five fictional neighbours, two repairs each. Plausible, fixed numbers (no randomness) so the output is stable."""
    data = [  # tester, scenario, object, fixed, minutes, shop estimate, parts cost
        ("T1 (fictional)", "motor", "Honda Beat, spark plug cap", True, 18, 60000, 0),
        ("T1 (fictional)", "motor", "Scooter rear tyre (tubeless)", True, 27, 35000, 10000),
        ("T2 (fictional)", "pump", "Shimizu water pump", True, 32, 150000, 5000),
        ("T2 (fictional)", "plumbing", "Kitchen tap", True, 24, 75000, 3000),
        ("T3 (fictional)", "pump", "Sanyo water pump", False, 55, 150000, 35000),
        ("T3 (fictional)", "motor", "Yamaha Mio, fouled plug", True, 22, 60000, 25000),
        ("T4 (fictional)", "plumbing", "Bathroom tap", True, 35, 75000, 8000),
        ("T4 (fictional)", "appliance", "Rice cooker (safety stop)", False, 4, 0, 0),
        ("T5 (fictional)", "motor", "Honda Vario tyre", True, 31, 35000, 10000),
        ("T5 (fictional)", "pump", "Shimizu water pump", True, 41, 150000, 5000),
    ]
    rows = []
    for i, (tester, sc, obj, fixed, mins, shop, parts) in enumerate(data):
        rows.append({"ts": f"2026-11-0{1 + i // 4}T0{i % 10}:00:00Z", "session": f"mock{i:02d}", "tester": tester, "mode": "mock-trial",
                     "lang": "id", "scenario": sc, "object": obj, "result": "fixed" if fixed else "pro", "fixed": fixed,
                     "minutes": mins, "minutes_source": "owner", "saved_idr": max(0, shop - parts) if fixed and shop else 0,
                     "shop_cost_idr": shop, "parts_cost_idr": parts, "replans": 1 if sc == "pump" and not fixed else 0,
                     "steps_total": 4, "steps_verified": 3 if fixed else 1, "fallback": False})
    return rows


def latest_per_session(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The log is append-only, so an owner who taps "fixed" then "mechanic" has two rows: the last one counts."""
    last: dict[str, dict[str, Any]] = {}
    for r in rows:
        last[str(r.get("session"))] = r
    return list(last.values())


def _median(xs: list[float]) -> float:
    return float(statistics.median(xs)) if xs else 0.0


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    fixed = [r for r in rows if r.get("fixed")]
    saved = [int(r.get("saved_idr") or 0) for r in fixed]
    return {"repairs": len(rows), "fixed": len(fixed), "fixed_rate": (len(fixed) / len(rows)) if rows else 0.0,
            "median_minutes": _median([float(r.get("minutes") or 0) for r in fixed]),
            "total_saved_idr": sum(saved), "median_saved_idr": _median([float(x) for x in saved]),
            "testers": len({r.get("tester") for r in rows if r.get("tester")}),
            "shop_total_idr": sum(int(r.get("shop_cost_idr") or 0) for r in fixed),
            "verified_steps": sum(int(r.get("steps_verified") or 0) for r in rows),
            "total_steps": sum(int(r.get("steps_total") or 0) for r in rows)}


def by_scenario(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for sc in sorted({str(r.get("scenario") or "other") for r in rows}):
        out[sc] = summarize([r for r in rows if (r.get("scenario") or "other") == sc])
    return out


def rp(n: float) -> str:
    return "Rp" + f"{int(round(n)):,}".replace(",", ".")


def markdown(rows: list[dict[str, Any]], mock: bool, source: str) -> str:
    s, per = summarize(rows), by_scenario(rows)
    stamp = f"> **{MOCK_STAMP}.** These are fictional testers made up to show the format. Do not quote them as results.\n\n" if mock else ""
    lines = [f"# Impact{' (MOCK DATA)' if mock else ''}", "", stamp + f"Source: `{source}` · {s['repairs']} repairs by {s['testers']} testers · generated "
             + time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()) + " by `scripts/impact_report.py`.", ""]
    if not rows:
        lines += ["No outcomes recorded yet. Run the trials in docs/USER_TRIAL_KIT.md, then run this script again.", ""]
        return "\n".join(lines)
    lines += ["| Measure | Value |", "|---|---|",
              f"| Fixed by the owner | {s['fixed']}/{s['repairs']} ({s['fixed_rate']:.0%}) |",
              f"| Median time to fix (fixed repairs) | {s['median_minutes']:.0f} min |",
              f"| Total saved vs bengkel estimate | {rp(s['total_saved_idr'])} |",
              f"| Median saved per fixed repair | {rp(s['median_saved_idr'])} |",
              f"| Steps verified by camera | {s['verified_steps']}/{s['total_steps']} |", "",
              "## By scenario", "", "| Scenario | Repairs | Fixed | Median min | Total saved | Median saved |", "|---|---|---|---|---|---|"]
    for sc, v in per.items():
        mm, ms = (f"{v['median_minutes']:.0f}", rp(v["median_saved_idr"])) if v["fixed"] else ("-", "-")
        lines.append(f"| {SCENARIO_NAME.get(sc, sc)} | {v['repairs']} | {v['fixed']} ({v['fixed_rate']:.0%}) | {mm} | "
                     f"{rp(v['total_saved_idr'])} | {ms} |")
    lines += ["", "How the numbers are made: saving = the model's bengkel price estimate (labour + parts) minus the parts the owner "
              "bought, counted only when the owner said it works again. Minutes are what the owner reported (or the time from start "
              "to the outcome tap). A safety stop or a hand-off to a mechanic counts as not fixed.", ""]
    if mock:
        lines += [f"**{MOCK_STAMP}.**", ""]
    return "\n".join(lines)


def _font(size: int, bold: bool = False) -> Any:
    for folder in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu"):
        p = Path(folder) / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default(size=size)


def slide(rows: list[dict[str, Any]], mock: bool, out: Path) -> Path:
    """1920x1080 slide: four big numbers, a fixed-rate bar per scenario, and the MOCK stamp when it applies."""
    W, H = 1920, 1080
    ORANGE, INK, MUTED = (255, 122, 0), (29, 35, 43), (107, 116, 128)
    im = Image.new("RGB", (W, H), (246, 243, 238))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 18], fill=ORANGE)
    s, per = summarize(rows), by_scenario(rows)
    d.text((90, 70), "Tukang Copilot: impact from real repairs" if not mock else "Tukang Copilot: impact (format preview)", font=_font(64, True), fill=INK)
    d.text((90, 160), f"{s['repairs']} repairs by {s['testers']} neighbours in Semarang" if rows else "No trials recorded yet", font=_font(36), fill=MUTED)
    cards = [(f"{s['fixed_rate']:.0%}", "fixed by the owner"), (f"{s['median_minutes']:.0f} min", "median time to fix"),
             (rp(s["total_saved_idr"]), "saved vs bengkel"), (rp(s["median_saved_idr"]), "median saved per fix")]
    cw = (W - 180 - 3 * 40) // 4
    for i, (big, small) in enumerate(cards):
        x = 90 + i * (cw + 40)
        d.rounded_rectangle([x, 250, x + cw, 500], radius=28, fill="white", outline=(225, 222, 215), width=3)
        f = _font(78 if len(big) < 9 else 58, True)
        d.text((x + 36, 300), big, font=f, fill=ORANGE)
        d.text((x + 36, 420), small, font=_font(32), fill=MUTED)
    d.text((90, 560), "Fixed rate by scenario", font=_font(40, True), fill=INK)
    y = 630
    for sc, v in list(per.items())[:5]:
        d.text((90, y + 6), SCENARIO_NAME.get(sc, sc), font=_font(32), fill=INK)
        x0, x1 = 430, 1500
        d.rounded_rectangle([x0, y, x1, y + 50], radius=14, fill=(230, 226, 218))
        if v["fixed_rate"] > 0:
            d.rounded_rectangle([x0, y, x0 + max(28, int((x1 - x0) * v["fixed_rate"])), y + 50], radius=14, fill=(31, 157, 85))
        d.text((x1 + 30, y + 6), f"{v['fixed']}/{v['repairs']}  ·  {rp(v['total_saved_idr'])}", font=_font(30), fill=MUTED)
        y += 76
    d.text((90, H - 70), "Saving = bengkel estimate - parts bought, counted only when it works again. Source: scripts/impact_report.py",
           font=_font(24), fill=MUTED)
    if mock:
        stamp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(stamp)
        f = _font(88, True)
        tw = int(sd.textlength(MOCK_STAMP, font=f))
        sd.rounded_rectangle([(W - tw) // 2 - 40, 455, (W + tw) // 2 + 40, 585], radius=20, fill=(205, 40, 40, 150))
        sd.text(((W - tw) // 2, 470), MOCK_STAMP, font=f, fill=(255, 255, 255, 255))
        stamp = stamp.rotate(12, resample=Image.Resampling.BICUBIC, center=(W // 2, 520))
        im = Image.alpha_composite(im.convert("RGBA"), stamp).convert("RGB")
        d = ImageDraw.Draw(im)
        d.rectangle([0, H - 18, W, H], fill=(205, 40, 40))
        d.text((W - 90 - int(d.textlength(MOCK_STAMP, font=_font(30, True))), 170), MOCK_STAMP, font=_font(30, True), fill=(205, 40, 40))
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "PNG")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mock", action="store_true", help="use 5 fictional testers (outputs stamped MOCK DATA)")
    ap.add_argument("--data", type=Path, help="outcomes.jsonl (default: DATA_DIR/impact/outcomes.jsonl)")
    ap.add_argument("--include-demo", action="store_true", help="also count demo-mode (mock) sessions")
    ap.add_argument("--md", type=Path, default=ROOT / "docs" / "IMPACT.md")
    ap.add_argument("--png", type=Path, default=ROOT / "docs" / "img" / "impact.png")
    a = ap.parse_args(argv)
    if a.mock:
        rows, source = mock_rows(), "MOCK (scripts/impact_report.py --mock)"
    else:
        from api import impact

        path = a.data or impact.log_path()
        rows = latest_per_session(impact.read(path))
        if not a.include_demo:
            rows = [r for r in rows if r.get("mode") == "live"]
        try:
            source = str(path.relative_to(ROOT))
        except ValueError:
            source = str(path)
    a.md.parent.mkdir(parents=True, exist_ok=True)
    a.md.write_text(markdown(rows, a.mock, source), encoding="utf-8")
    slide(rows, a.mock, a.png)
    s = summarize(rows)
    print(f"{'MOCK DATA: ' if a.mock else ''}{s['repairs']} repairs, fixed {s['fixed_rate']:.0%}, median {s['median_minutes']:.0f} min, "
          f"saved {rp(s['total_saved_idr'])} -> {a.md}, {a.png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
