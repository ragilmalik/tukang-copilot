"""Check that your real keys work. Run after pasting MODEL_API_KEY into .env:

    python scripts/check_keys.py            # tiny real calls, costs well under $0.02 in total
    python scripts/check_keys.py --no-cost  # only checks the key and the model list (free)

It prints one line per Meta model with PASS or FAIL and a plain-English fix, and exits 0 only if
everything the app needs passed. See what a pass looks like without a key:

    python scripts/check_keys.py --fake
"""
from __future__ import annotations

import argparse
import sys
import tempfile
import time
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api import meta_client  # noqa: E402
from api.pipeline import mock  # noqa: E402
from api.settings import settings  # noqa: E402

GREEN, RED, DIM, END = "\033[32m", "\033[31m", "\033[2m", "\033[0m"
results: list[tuple[str, bool, str]] = []


def check(name: str, fn, fix: str) -> None:
    t0 = time.time()
    try:
        detail = fn() or ""
        results.append((name, True, detail))
        print(f"{GREEN}PASS{END} {name} {DIM}({time.time() - t0:.1f}s) {detail}{END}")
    except Exception as e:  # show the reason and what to do
        results.append((name, False, str(e)))
        print(f"{RED}FAIL{END} {name}: {str(e)[:220]}\n     fix: {fix}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-cost", action="store_true", help="only check the key and the model list")
    ap.add_argument("--fake", action="store_true", help="dry run against the built-in fake Meta server (no key, no cost)")
    args = ap.parse_args()
    if args.fake:
        from api.testing import fake_meta

        settings.meta_api_base, settings.meta_api_key = fake_meta.serve_in_thread(), fake_meta.TEST_KEY
        print("Dry run against the built-in fake Meta server.")

    print(f"Meta API base: {settings.meta_api_base}")
    if not settings.meta_api_key:
        print(f"{RED}No MODEL_API_KEY found.{END} Open the .env file next to app.py, paste your key after MODEL_API_KEY=, save, run again.")
        return 2
    print(f"Key: ...{settings.meta_api_key[-4:]}  (only the last 4 characters are shown)\n")

    needed = [settings.vision_model, settings.reason_model, settings.audio_model, settings.asr_model, settings.image_model, settings.sam_model]
    models: list[str] = []

    def list_models():
        models.extend(meta_client.list_models())
        missing = [m for m in needed if m not in models]
        if missing:
            raise RuntimeError(f"key works but these models are not enabled: {', '.join(missing)}")
        return f"{len(models)} models enabled"

    check("API key + model list (GET /v1/models)", list_models,
          "401 = wrong key (copy it again from dev.meta.ai > API keys). 402/403 = add a card / claim credits on the Billing page.")
    if not results[-1][1] and "not enabled" not in results[-1][2]:
        return 1
    if args.no_cost:
        return 0 if all(ok for _, ok, _ in results) else 1

    tmp = Path(tempfile.mkdtemp())
    photos = mock.make_sample_photos(tmp)

    from api.schemas import StepCheck, json_schema

    def spark_vision():
        msgs = [{"role": "user", "content": [meta_client.image_part(photos["faucet"]),
                                             {"type": "text", "text": "Is there a faucet in this picture? passed=true if yes. observation: one short sentence."}]}]
        out = StepCheck.model_validate(meta_client.chat_json(msgs, json_schema(StepCheck), "step_check", model=settings.vision_model, reasoning_effort="low"))
        return f"structured output OK: {out.observation[:60]}"

    check(f"Muse Spark vision + structured output ({settings.vision_model})", spark_vision,
          "If 400 mentions response_format, tell Malik; if 404 model_not_found, the model id changed: check dev.meta.ai/docs/models.")

    def sam():
        recs = meta_client.segment(photos["faucet"], "faucet handle")
        return f"{len(recs)} mask(s) parsed"

    check(f"SAM 3.1 segmentation ({settings.sam_model})", sam, "Needs `pip install -r requirements.txt` (meta-sam-parser).")

    def image():
        out = tmp / "img.png"
        meta_client.generate_image("a simple orange wrench icon on a white background", out, size="1024x1024", fast=True)
        return f"{out.stat().st_size // 1024} KB image"

    check(f"Muse Image ({settings.image_model})", image, "Image generation may need billing enabled on your Meta account.")

    def asr():
        wav = tmp / "silence.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes(b"\x00\x00" * 16000)
        meta_client.transcribe(wav, 1.0, language_bias=["Indonesian"])
        return "accepted a 1 s WAV"

    check(f"Muse Voice Transcribe ({settings.asr_model})", asr, "Check the key has speech-to-text access.")

    if settings.use_open_weights:
        def open_w():
            msgs = [{"role": "user", "content": "Return {\"passed\": true, \"observation\": \"ok\"}"}]
            meta_client.chat_json(msgs, json_schema(StepCheck), "step_check", reasoning_effort="low", open_weights=True)
            return settings.open_model

        check("Muse Spark Open on Baseten (open weights)", open_w, "Check BASETEN_API_KEY and OPEN_MODEL in .env.")

    ok = all(r[1] for r in results)
    print(f"\n{(GREEN + 'ALL GOOD: the app will run in LIVE mode.') if ok else (RED + 'Some checks failed: see the fix lines above.')}{END}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
