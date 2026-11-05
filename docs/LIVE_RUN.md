# Live runs on the real Meta Model API

I ran every sample scenario against the real Meta Model API on 5 November 2026 (WIB), from Semarang, with my own key. Nothing below comes from the offline canned answers. The photos are the labelled AI-generated sample photos in `samples/`, so this shows what the models do with those pictures, not how they do on my own repairs.

Models, as the API reported them: `muse-spark-1.3` (look, diagnose, plan, step checks, diagram review), `sam-3.1` (part masks), `muse-image-1.0` (diagrams), `muse-voice-transcribe-1.0` and `muse-spark-1.2` (voice notes, checked by `scripts/check_keys.py`, not used in these typed runs). `GET /v1/models` listed 9 models for my key, all 5 the app needs.

The step-by-step voice (edge-tts, a Microsoft voice, not a Meta model) was off for these runs. Costs are what the API reported in `usage`, priced with `api/cost.py`.

## Results per scenario

| Scenario | Language | Result | Photo in to plan ready | SAM 3.1 masks | Cost |
|---|---|---|---|---|---|
| Motorbike won't start | Bahasa | ready, asked one question first | 105 s (54 s + 51 s after the answer) | 5 of 5 parts | $0.060 |
| Motorbike, then "still won't start" | English | ready, re-planned to cause 2 | 89 s, re-plan 30 s | 5 of 5 | $0.072 |
| Water pump spins, no water | Bahasa | ready | 82 s | 5 of 5 | $0.052 |
| Dripping kitchen tap | English | ready, 1 Muse Image diagram | 82 s (diagram 21 s) | 5 of 5 | $0.060 |
| Flat scooter tyre with a nail | Bahasa | ready | 76 s | 4 of 5 (axle nut not found) | $0.049 |
| Rice cooker won't heat | Basa Jawa | red stop from the model | 48 s | 5 of 5 | $0.028 |
| "Rem blong" (brakes fail) | Bahasa | red stop in code, before any model call | 0.2 s | none | $0.000 |

Time per stage was steady across runs: look 12 to 27 s, SAM 3.1 3 to 8 s for all parts in one call, diagnose 18 to 25 s, plan 26 to 36 s, a camera step check 6 to 13 s. Total spend for these seven runs was about $0.37.

## What the models said

**Motorbike (Bahasa).** Look named the cylinder head area with the plug cap, ignition cable, cylinder head, carburettor and side cover, each with a box. SAM 3.1 masked all five on the photo. Diagnose was unsure at first and asked "Setelah beberapa kali distarter, ujung busi basah bensin atau kering?". After the answer: weak ignition, dirty plug or loose cap 65%, fuel supply 60%, amber safety ("ada bensin dan percikan api busi"). The 5-step plan: key off and engine cool, pull the cap off, take the plug out with a 16 mm plug spanner and clean or replace it, refit and push the cap until it clicks, then try the starter for 5 seconds at most.

**Motorbike re-plan (English).** It asked whether the plug is wet or black and gives a blue spark. After "Tried it, still won't start" it moved to cause 2, the plug cap and ignition cable contact, with 6 new steps (check the cap for rust or a loose clip, screw the cable back into the cap, push the cap on until it clicks).

**Water pump (Bahasa).** Air leak on the suction side 78%, foot valve 65%, mechanical seal 58%, amber because a 220 V pump sits over a wet well. Plan: unplug, check the suction joints, open the brass priming plug, fill with water, close it, run for 1 to 2 minutes.

**Kitchen tap (English).** Worn washer 78%, green safety. 7 steps from the stop valve to the washer swap. Muse Image drew the washer step (a cutaway of the tap with the washer coming out) and Muse Spark accepted it on review.

**Tyre (Bahasa).** Nail puncture in a tubeless tyre 88%, green. 7 steps with a tubeless plug kit: pull the nail, ream, glue and insert the plug, trim to 5 mm, pump up.

**Rice cooker (Basa Jawa).** The model itself said red: fixing it means opening the 220 V internals. The app stopped with the answer in Javanese and sent the owner to a service centre.

**Camera step checks.** The pump check photo passed step 1 ("steker hitam terlihat sudah tercabut"). The motorbike and tyre after-photos were refused for step 1 with a concrete reason (the photo does not show the key switch or the centre stand). That is the right answer: those photos show a later step. The dark photo used in the demo is refused on every step.

## Problems the live runs found, and what I changed

1. **504 "upstream request deadline exceeded" after about 20 s.** A plain (non-streamed) structured-output call that thought for longer than about 20 s came back as 504, three times in a row, and the first motorbike run failed at the plan stage. A streamed call with the same body ran for 48 s without trouble. `meta_client.chat_json` now always sends `stream: true` with `stream_options.include_usage` and joins the deltas. Tests: `api/tests/test_live_stream.py`.
2. **The model skipped every optional field.** With constrained decoding, a field that is not in `required` was simply left out: no components (so SAM had nothing to outline), no follow-up question, no `needs_diagram`, no tool list. `api/schemas.json_schema()` now lists every property as required at every depth. With the full schema, diagnose also went from 107 s in that first run to 18 to 25 s.
3. **Muse Image at high effort can hit the same 504.** Images can't stream, so the client tries once more at high effort and then sends the same request at low effort.
4. **Retry-After.** A 429 or 503 with `Retry-After` in seconds is now honoured (capped at 30 s). Auth and 400 errors are never retried.

## How to repeat it

```
python scripts/check_keys.py          # free model list + one tiny call per model
python scripts/first_live_run.py      # one motorbike repair, prints time and cost
python scripts/record_replay.py       # re-records the 1-tap demo from the live API (about $0.60)
python scripts/run_eval.py --modes live,mock,fake   # the eval with a live column (about $1.50)
```

`first_live_run.py` writes its own short report to `docs/FIRST_LIVE_RUN.md`.
