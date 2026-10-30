# AI pipeline

Code: `api/pipeline/engine.py`. Prompts: `prompts/*.md` (each has a version header). Schemas: `api/schemas.py`. All Meta calls: `api/meta_client.py`.

| # | Stage | Model | Prompt | Output schema | Failure handling |
|---|---|---|---|---|---|
| 1 | Listen | `muse-voice-transcribe-1.0` (id, en) · `muse-spark-1.2` audio (jv) | built-in instruction | text | voice optional; typed text works; recording deleted after |
| – | Gate | none (regex) | – | allow / stop | hard stop before any paid call |
| 2 | Look | `muse-spark-1.3` vision | `look.md` | `ObjectReport` | retry once on invalid JSON, then error |
| 3 | Find parts | `sam-3.1` | box prompts from Look, else noun phrase per part | masks | a part with no mask is shown as "(?)", never blocks |
| 4 | Diagnose | `muse-spark-1.3` · or Muse Spark Open | `diagnose.md` | `Diagnosis` | follow-up question if top cause < 60% |
| 5 | Plan | `muse-spark-1.3` · or Open | `plan.md` (+ `replan.md`) | `RepairPlan` | retry once |
| 9 | Safety | none (regex on plan) + model level | – | allow / red | red → stop with reason, no steps shown |
| 6 | Illustrate | `muse-image-1.0` `/v1/images/edits` + Spark review | `diagram.md`, `diagram_review.md` | PNG | max `MAX_DIAGRAMS`; bad review → redraw once; error → step uses highlighted photo |
| 7 | Narrate | edge-tts (Meta has no TTS) | – | MP3 | offline → browser `speechSynthesis` |
| 8 | Verify step | `muse-spark-1.3` vision | `verify_step.md` | `StepCheck` | `MAX_CHECK_FAILS` fails → escalate hint |
| 5b | Re-plan | `muse-spark-1.3` | `plan.md` + `replan.md` | `RepairPlan` | causes exhausted → "see a mechanic" with report |

## Why each Meta model

- **Muse Spark 1.3** is Meta's recommended model for new work, takes images, and supports strict `json_schema` structured output, so every stage returns typed data the UI can trust.
- **Muse Spark 1.2** for Javanese audio: the docs say 1.3's audio understanding is degraded and Voice Transcribe has no Javanese.
- **Muse Voice Transcribe** is the dedicated speech-to-text with keyword biasing (we bias toward words like *busi, kampas, van belt, seal*).
- **SAM 3.1** gives pixel-accurate masks of the exact parts on the user's own photo. Look returns approximate boxes, so all parts go in **one** SAM call (Meta's box/point grammar, built with `meta_sam_parser.build_object_prompt`); if that fails we fall back to one noun-phrase call per part.
- **Muse Image** edits *the user's own photo* (reference image), so diagrams show the same object, not a generic one. A Spark review catches garbled text or wrong objects.
- **Muse Spark Open** (open weights) can take over the two reasoning stages via Baseten for the open-weight track; same schemas, `max_tokens` 16384 because reasoning and answer share the budget.

## Agentic behaviour (plan → act → verify → re-plan)

1. **Ask before guessing**: low confidence produces exactly one follow-up question; the run pauses (`needs_answer`) and resumes with the answer in context.
2. **Self-check generated art**: each diagram is reviewed by Spark; a failing one is redrawn with Spark's improved brief.
3. **Verify the physical world**: each step has an `expected_state` written so a camera can confirm it; the user's photo is judged against it.
4. **Re-plan**: "still broken" plus what happened moves to the next cause and plans again with the history of attempts in context.
5. **Escalate**: repeated failed checks or exhausted causes end in a clear handoff to a professional.

## Prompt rules shared by all stages
- User-facing text in the chosen language (`{lang_name}`); SAM phrases and diagram briefs in English.
- Never medical advice, never bypass safety devices, red for gas/mains/high voltage/brake hydraulics/fuel/airbags.
- Prices are labelled estimates in integer rupiah.

## Cost guard
`api/cost.py` meters every call (Spark tokens at $1.25/$4.25 per 1M, Muse Image $0.01, SAM $0.0025/image, ASR $0.18/h) and raises `BudgetExceeded` before a call that would pass `MAX_COST_PER_SESSION_USD`. Typical repair in the fake-server run: **$0.008–0.024**.

## Demo / offline mode
`MOCK=1` or no key → `mock.py` answers each stage for three scenarios (motorbike amber with follow-up, faucet green with one diagram, rice cooker red). Step checks fail on dark or blank photos so the ⚠️ path can be demoed.
