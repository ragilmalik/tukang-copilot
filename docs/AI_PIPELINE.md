# AI pipeline

Code: `api/pipeline/engine.py`. Prompts: `prompts/*.md` (each has a version header). Schemas: `api/schemas.py`. All Meta calls: `api/meta_client.py`.

| # | Stage | Model | Prompt | Output schema | Failure handling |
|---|---|---|---|---|---|
| 1 | Listen | `muse-voice-transcribe-1.0` (id, en) · `muse-spark-1.2` audio (jv) | built-in instruction | text | voice optional; typed text works; recording deleted after |
| - | Gate | none (regex) | - | allow / stop | hard stop before any paid call |
| 2 | Look | `muse-spark-1.3` vision | `look.md` | `ObjectReport` | retry once on invalid JSON, then error |
| 3 | Find parts | `sam-3.1` | box prompts from Look, else noun phrase per part | masks | a part with no mask is shown as "(?)", never blocks |
| 4 | Diagnose | `muse-spark-1.3` · or Muse Spark Open | `diagnose.md` | `Diagnosis` | follow-up question if top cause < 60% |
| 5 | Plan | `muse-spark-1.3` · or Open | `plan.md` (+ `replan.md`) | `RepairPlan` | retry once |
| 9 | Safety | none (regex on plan) + model level | - | allow / red | red → stop with reason, no steps shown |
| 6 | Illustrate | `muse-image-1.0` `/v1/images/edits` + Spark review | `diagram.md`, `diagram_review.md` | PNG | max `MAX_DIAGRAMS`; bad review → redraw once; error → step uses highlighted photo |
| 7 | Narrate | edge-tts (Meta has no TTS) | - | MP3 | offline → browser `speechSynthesis` |
| 8 | Verify step | `muse-spark-1.3` vision | `verify_step.md` | `StepCheck` | `MAX_CHECK_FAILS` fails → escalate hint |
| 5b | Re-plan | `muse-spark-1.3` | `plan.md` + `replan.md` | `RepairPlan` | causes exhausted → "see a mechanic" with report |

## Why each Meta model

Muse Spark 1.3 is Meta's recommended model for new work. It takes images and supports strict `json_schema` structured output, so every stage returns typed data the UI can trust.

Muse Spark 1.2 handles Javanese audio, because the docs say 1.3's audio understanding is degraded and Voice Transcribe has no Javanese.

Muse Voice Transcribe is the dedicated speech-to-text model, and it has keyword biasing. I bias it toward repair words like *busi, kampas, van belt, seal*.

SAM 3.1 gives pixel-accurate masks of the exact parts on the user's own photo. Look returns rough boxes, so all parts go into one SAM call (Meta's box/point grammar, built with `meta_sam_parser.build_object_prompt`). If that call fails, the app falls back to one noun-phrase call per part.

Muse Image edits the user's own photo (as a reference image), so a diagram shows the same object instead of a generic one. A Spark review catches garbled text or the wrong object.

Muse Spark Open (open weights) can take over the two reasoning stages through Baseten, for the open-weight track. The schemas are the same. `max_tokens` is 16384 because reasoning and answer share that budget.

## Agentic behaviour (plan, act, verify, re-plan)

1. Ask before guessing. Low confidence produces exactly one follow-up question; the run pauses (`needs_answer`) and resumes with the answer in context.
2. Self-check the generated art. Spark reviews each diagram, and a failing one is redrawn from Spark's improved brief.
3. Verify the physical world. Each step has an `expected_state` written so a camera can confirm it, and the user's photo is judged against it.
4. Re-plan. "Still broken" plus what happened moves on to the next cause and plans again, with the earlier attempts in context.
5. Escalate. Repeated failed checks or running out of causes end in a clear hand-off to a professional.

## Prompt rules shared by all stages
User-facing text is in the chosen language (`{lang_name}`), while SAM phrases and diagram briefs stay in English. No stage gives medical advice or bypasses a safety device, and gas, mains, high voltage, brake hydraulics, fuel and airbags are always red. Prices are labelled estimates in whole rupiah.

## Cost guard
`api/cost.py` meters every call (Spark tokens at $1.25/$4.25 per 1M, Muse Image $0.01, SAM $0.0025/image, ASR $0.18/h) and raises `BudgetExceeded` before a call that would pass `MAX_COST_PER_SESSION_USD`. A typical repair in the fake-server run cost $0.008 to $0.024.

## Demo / offline mode
With `MOCK=1` or no key, `mock.py` answers each stage for three scenarios (motorbike amber with follow-up, faucet green with one diagram, rice cooker red). Step checks fail on dark or blank photos, so I can demo the ⚠️ path.
