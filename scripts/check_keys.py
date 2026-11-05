"""Check that your real keys work. Run after `python scripts/set_keys.py` (or after pasting MODEL_API_KEY into .env):

    python scripts/check_keys.py            # tiny real calls, well under $0.05 in total
    python scripts/check_keys.py --no-cost  # only checks the key and the model list (free)

It prints one PASS / FAIL / SKIP line per Meta model the app uses, with a plain-English fix for every FAIL,
and a separate line for the optional open-weights model (Muse Spark Open on Baseten).

Exit codes: 0 = everything the app needs passed (LIVE mode will work), 1 = something failed,
2 = no MODEL_API_KEY found at all (the app will run in free DEMO mode).

See what it looks like without a key (built-in fake Meta server, no cost):

    python scripts/check_keys.py --fake            # every check passes, incl. open weights
    python scripts/check_keys.py --fake-bad-key    # what a wrong key looks like
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys
import tempfile
import time
import wave
from collections.abc import Callable
from typing import Any
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api import meta_client  # noqa: E402
from api.pipeline import mock  # noqa: E402
from api.settings import settings  # noqa: E402

_COLOR = sys.stdout.isatty() and not os.getenv("NO_COLOR")
GREEN, RED, YELLOW, DIM, END = (("\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m") if _COLOR else ("",) * 5)
results: list[tuple[str, str, str]] = []  # (name, PASS|FAIL|SKIP, detail)


def plain(e: Exception, who: str = "Meta") -> str:
    """Turn an API error into one plain-English sentence (never echoes a key)."""
    s = str(e)
    m = re.match(r"(?:SAM )?(\d{3})\b", s)
    code = int(m.group(1)) if m else 0
    reasons = {
        401: f"{who} says this key is not valid (401).",
        402: f"{who} says billing/credits are needed on this account (402).",
        403: "This key is not allowed to use this model (403).",
        404: f"{who} does not know this model id (404). It may have been renamed or not deployed.",
        429: "Too many requests or the account's rate limit is hit (429). Wait a minute and run again.",
    }
    if code in reasons:
        return reasons[code]
    if code >= 500:
        return f"{who}'s server had a problem ({code}). Usually temporary: run again in a few minutes."
    if "failed:" in s or "ConnectError" in s or "timed out" in s.lower():
        return "Could not reach the server (no internet, a proxy, or the server is down)."
    if "cost cap" in s.lower() or "budget" in s.lower():
        return "The app's own spend cap stopped the call (MAX_COST_PER_SESSION_USD)."
    return s[:200]


def check(name: str, fn: Callable[[], str | None], fix: str, who: str = "Meta") -> bool:
    t0 = time.time()
    try:
        detail = fn() or ""
        results.append((name, "PASS", detail))
        print(f"{GREEN}PASS{END} {name} {DIM}({time.time() - t0:.1f}s) {detail}{END}")
        return True
    except Exception as e:  # show the reason and what to do
        results.append((name, "FAIL", plain(e, who)))
        print(f"{RED}FAIL{END} {name}: {plain(e, who)}\n     fix: {fix}")
        return False


def skip(name: str, why: str) -> None:
    results.append((name, "SKIP", why))
    print(f"{YELLOW}SKIP{END} {name}: {why}")


def _wav(path: Path, seconds: float = 1.0) -> Path:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * int(16000 * seconds))
    return path


def _small_frame(src: Path, out: Path) -> Path:
    """A ~640 px JPEG like the phone sends during the live camera guide."""
    from PIL import Image

    im = Image.open(src).convert("RGB")
    im.thumbnail((640, 640))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=70)
    out.write_bytes(buf.getvalue())
    return out


def run_open_weights(json_schema: Callable[..., dict[str, Any]], step_check: type) -> None:
    name = f"Muse Spark Open on Baseten, open weights ({settings.open_model})"
    if not settings.baseten_api_key:
        if settings.use_open_weights:
            results.append((name, "FAIL", "USE_OPEN_WEIGHTS=1 but no BASETEN_API_KEY"))
            print(f"{RED}FAIL{END} {name}: USE_OPEN_WEIGHTS=1 but there is no BASETEN_API_KEY.\n"
                  "     fix: run python scripts/set_keys.py again and paste the Baseten key, or set USE_OPEN_WEIGHTS=0.")
        else:
            skip(name, "optional; no BASETEN_API_KEY set (the app uses Muse Spark 1.3 for everything)")
        return

    def open_w() -> str:
        msgs = [{"role": "user", "content": "Return {\"passed\": true, \"observation\": \"ok\"}"}]
        out = meta_client.chat_json(msgs, json_schema(step_check), "step_check", reasoning_effort="low", open_weights=True)
        if not isinstance(out, dict):
            raise RuntimeError("Baseten answered but not with a JSON object")
        state = "ON: the open-weights badge will show" if settings.use_open_weights else \
            "key works, but USE_OPEN_WEIGHTS=0 so the app will not use it yet"
        return f"JSON reply OK. {state}"

    check(name, open_w, "Check BASETEN_API_KEY (baseten.co > API keys) and that Muse Spark Open is deployed in that "
                        "Baseten account (OPEN_MODEL / OPEN_API_BASE in .env if you deployed your own copy).", who="Baseten")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-cost", action="store_true", help="only check the key and the model list (free)")
    ap.add_argument("--fake", action="store_true", help="dry run against the built-in fake Meta + Baseten server (no key, no cost)")
    ap.add_argument("--fake-bad-key", action="store_true", help="dry run with a wrong key, to see the failure message")
    args = ap.parse_args()
    if args.fake or args.fake_bad_key:
        from api.tests.doubles import fake_meta

        base = fake_meta.serve_in_thread()
        settings.meta_api_base = base
        settings.meta_api_key = "wrong-key-0000" if args.fake_bad_key else fake_meta.TEST_KEY
        settings.open_api_base, settings.baseten_api_key = base.replace("/v1", "/baseten/v1"), "test-baseten-key"
        settings.use_open_weights = True
        settings.mock = False
        print("Dry run against the built-in fake Meta server (no real key, no cost).")

    print(f"Meta API base: {settings.meta_api_base}")
    if not settings.meta_api_key:
        print(f"{RED}No MODEL_API_KEY found.{END} The app will run in free DEMO mode.\n"
              "To go live: run  python scripts/set_keys.py  and paste your key from dev.meta.ai > API keys.")
        return 2
    print(f"Key: ...{settings.meta_api_key[-4:]}  (only the last 4 characters are shown)")
    if settings.mock:
        print(f"{YELLOW}Note:{END} MOCK=1 is set, so the app stays in DEMO mode even if the key works. "
              "set_keys.py sets MOCK=0 for you.")
    print()

    needed = {settings.vision_model: "look + diagnose + plan + verify", settings.reason_model: "diagnose + plan",
              settings.audio_model: "Javanese voice notes", settings.asr_model: "voice notes",
              settings.image_model: "step diagrams", settings.sam_model: "highlight parts + live camera guide"}
    models: list[str] = []

    def list_models() -> str:
        models.extend(meta_client.list_models())
        missing = [f"{m} ({use})" for m, use in needed.items() if m not in models]
        if missing:
            raise RuntimeError("Key works, but these models are not enabled for it: " + ", ".join(missing))
        return f"{len(models)} models enabled, all {len(needed)} the app needs are there"

    key_ok = check("API key + model list (GET /v1/models)", list_models,
                   "Wrong key: copy it again from dev.meta.ai > API keys and run python scripts/set_keys.py. "
                   "402/403: add a card or claim the hackathon credits on the dev.meta.ai Billing page. "
                   "Model not enabled: turn it on in dev.meta.ai or ask the organisers.")
    if not key_ok and "not enabled" not in results[-1][2]:
        print(f"\n{RED}Stopped: the key itself did not work, so the model checks were skipped.{END}")
        return 1
    if args.no_cost:
        ok = all(st != "FAIL" for _, st, _ in results)
        print(f"\n{(GREEN + 'Key OK (free check only). Run without --no-cost to test each model.') if ok else (RED + 'See the fix line above.')}{END}")
        return 0 if ok else 1

    tmp = Path(tempfile.mkdtemp())
    photos = mock.make_sample_photos(tmp)

    from api.schemas import StepCheck, json_schema

    def spark_vision() -> str:
        msgs = [{"role": "user", "content": [meta_client.image_part(photos["faucet"]),
                                             {"type": "text", "text": "Is there a faucet in this picture? passed=true if yes. observation: one short sentence."}]}]
        out = StepCheck.model_validate(meta_client.chat_json(msgs, json_schema(StepCheck), "step_check", model=settings.vision_model, reasoning_effort="low"))
        return f"structured output OK: {out.observation[:60]}"

    check(f"Muse Spark vision + structured output ({settings.vision_model})", spark_vision,
          "If it mentions response_format, open an issue with the error text. If the model id is unknown, check dev.meta.ai/docs/models and set VISION_MODEL in .env.")

    def sam() -> str:
        recs = meta_client.segment(photos["faucet"], "faucet handle")
        return f"{len(recs)} mask(s) parsed"

    check(f"SAM 3.1 segmentation, highlighted parts ({settings.sam_model})", sam,
          "Run pip install -r requirements.txt (needs meta-sam-parser). If it is a 403, SAM is not enabled for this key.")

    def track() -> str:
        frame = _small_frame(photos["faucet"], tmp / "frame.jpg")
        t0 = time.time()
        recs = meta_client.segment(frame, "faucet handle")
        dt = time.time() - t0
        speed = "fast enough for the live overlay" if dt < 3 else "slow: the live overlay will lag, the still-photo check still works"
        return f"{len(recs)} box(es) on a {frame.stat().st_size // 1024} KB frame in {dt:.1f}s ({speed})"

    check(f"Live camera guide, SAM 3.1 on a small camera frame ({settings.sam_model})", track,
          "Same fix as SAM above. If only this one fails, the live overlay is off but the rest of the app works.")

    def image() -> str:
        out = tmp / "img.png"
        meta_client.generate_image("a simple orange wrench icon on a white background", out, size="1024x1024", fast=True)
        return f"{out.stat().st_size // 1024} KB image"

    check(f"Muse Image, step diagrams ({settings.image_model})", image,
          "Image generation may need billing enabled on dev.meta.ai. To run without diagrams set ILLUSTRATE=0.")

    def asr() -> str:
        meta_client.transcribe(_wav(tmp / "silence.wav"), 1.0, language_bias=["Indonesian"])
        return "accepted a 1 s WAV"

    check(f"Muse Voice Transcribe, voice notes ({settings.asr_model})", asr, "Check the key has speech-to-text access on dev.meta.ai.")

    def spark_audio() -> str:
        meta_client.transcribe_with_spark_audio(_wav(tmp / "silence2.wav"), "Javanese")
        return "accepted a 1 s WAV"

    check(f"Muse Spark audio, Javanese voice notes ({settings.audio_model})", spark_audio,
          "Only Basa Jawa voice notes use this. Typed Javanese and other languages still work.")

    print(f"\n{DIM}Optional open weights:{END}")
    run_open_weights(json_schema, StepCheck)

    fails = [n for n, st, _ in results if st == "FAIL"]
    if not fails:
        print(f"\n{GREEN}ALL GOOD: the app will run in LIVE mode.{END}")
        return 0
    print(f"\n{RED}{len(fails)} check(s) failed: see the fix lines above.{END}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
