# Meta Model API notes (verified live)

I read these on dev.meta.ai on 2026-10-30 (WIB) and checked every one against the real API with my own key on 2026-11-05 (WIB): all five models answered, and the runs are written up in [LIVE_RUN.md](LIVE_RUN.md). The section "What I saw on the live API" at the end lists where the real behaviour differs from what I expected from the docs.

Base URL `https://api.meta.ai/v1` · header `Authorization: Bearer $MODEL_API_KEY` (docs name the variable `MODEL_API_KEY`; the app also accepts `META_API_KEY`). OpenAI-compatible SDKs work with `base_url`.

## Model ids (https://dev.meta.ai/docs/models)

| Model | Id | Used for |
|---|---|---|
| Muse Spark 1.3 | `muse-spark-1.3` | Look, Diagnose, Plan, Verify, diagram review (recommended for new work) |
| Muse Spark 1.2 | `muse-spark-1.2` | Javanese audio (1.3 audio input "not fully supported") |
| Muse Image | `muse-image-1.0` | Diagrams via `/v1/images/edits` |
| Muse Voice Transcribe | `muse-voice-transcribe-1.0` | Speech-to-text, 25 languages (no Javanese), **no TTS** |
| SAM 3.1 | `sam-3.1` | Part masks via `/v1/responses` |
| Muse Wonder | `muse-wonder-1.0` | not used (cost) |
| Muse Spark Open | Baseten `meta-models/muse-spark-open` | Optional open-weights reasoning |

`GET /v1/models` lists what your team can use (the key check script calls it).

## Endpoints used

**Chat Completions + structured output** (https://dev.meta.ai/docs/structured-output, /docs/image-understanding)
```json
POST /v1/chat/completions
{"model":"muse-spark-1.3","reasoning_effort":"medium",
 "messages":[{"role":"system","content":"…"},
             {"role":"user","content":[{"type":"image_url","image_url":{"url":"data:image/jpeg;base64,…"}},
                                        {"type":"text","text":"…"}]}],
 "response_format":{"type":"json_schema","json_schema":{"name":"diagnosis","schema":{…}}}}
```
Decoding is constrained. Recursive schemas are rejected (400), and nesting is capped at 10, so I inline `$defs`. Two things only the live API showed me: list every property in `required` (optional ones are left out), and send `"stream": true` (see below).

**Audio input** (https://dev.meta.ai/docs/video-understanding#audio): content part `{"type":"input_audio","input_audio":{"data":"<base64 wav>","format":"wav"}}`, model `muse-spark-1.2`, `max_tokens` ≥ 4000.

**Voice Transcribe file endpoint** (https://dev.meta.ai/docs/speech-to-text): `POST /v1/asr/transcribe?sessionId=…` multipart: part `request` (JSON `{"mode":"PUSH_TO_TALK","model":"muse-voice-transcribe-1.0","audioEncoding":"WAV","languageBias":[…],"keywords":[…]}`) and part `audio` (mono 16-bit PCM WAV, 16/24 kHz, ≤ 10 min). Response `{"transcript": "…"}`. Realtime alternative: `wss://api.meta.ai/v1/asr/realtime` (not used).

**SAM 3.1** (https://dev.meta.ai/docs/media-segmentation, /docs/sam/segmenting, /docs/sam/client-libraries)
```json
POST /v1/responses   (stream: true, Accept: text/event-stream)
{"model":"sam-3.1",
 "input":[{"type":"message","role":"user","content":[
   {"type":"input_text","text":"spark plug cap"},
   {"type":"input_image","image_url":"data:image/jpeg;base64,…"}]}],
 "stream":true,
 "metadata":{"mask_encoding":"one_bit","include_confidence":"true"}}
```
- The prompt is either one noun phrase (one concept per request, no lists) **or** box/point grammar, e.g. `<0f>1<|box;x1=444;y1=626;x2=675;y2=849;w=1800;h=1200|>`; up to 16 objects per request.
- `w`/`h` must be the displayed size **after EXIF rotation** (aspect mismatch gives 400). I normalise every photo first.
- `metadata` values must be strings. Output arrives as `response.output_text.delta` events; parse with `pip install meta-sam-parser` (`parse_responses_stream(…, image_segmentation_format())`, `decode_mask_to_raster`). Masks are box-local. Zero matches is a normal empty result.

**Muse Image** (https://dev.meta.ai/docs/image-generation, /docs/api-reference/images/edit-image): `POST /v1/images/edits` JSON `{"model":"muse-image-1.0","prompt":"…","images":[{"image_url":"data:…"}],"n":1,"output_format":"png","reasoning_strength":"low|high","tool_enablement":{…}}` → `data[0].b64_json` or `url`. 1-10 reference images.

**Muse Spark Open on Baseten** (https://dev.meta.ai/docs/muse-spark-open/deploy#baseten): `https://inference.baseten.co/v1/chat/completions`, model `meta-models/muse-spark-open` (overridable via `OPEN_MODEL`), reasoning always on (`low|medium|high|xhigh`), reasoning and answer share `max_tokens`, so I send 16384. If `json_schema` is refused, the client retries with `json_object`.

## Pricing (https://dev.meta.ai/docs/pricing-rate-limits, Standard mode)
Muse Spark $1.25 in / $4.25 out per 1M tokens · Muse Image $0.01 per image · SAM 3.1 $2.50 per 1,000 images · Voice Transcribe $0.18 per hour. Contributor-mode ids (`-contributor`) are cheaper but let Meta train on content: not used.

## Gotchas
- A dev HTTP proxy can turn `localhost` calls into 404s: set `NO_PROXY=127.0.0.1,localhost` when testing against the test double.
- Model availability varies by country (Geographic Use Policy). Indonesia wasn't listed as restricted, and from Semarang `scripts/check_keys.py` passed for all five models (2026-11-05).

## What I saw on the live API (2026-11-05)

- **Headers.** Responses carry `x-request-id`, `x-ratelimit-limit-requests: 3000`, `x-ratelimit-limit-tokens: 4000000` and the matching `x-ratelimit-remaining-*`. I never hit a 429 during these runs.
- **504 after about 20 s.** A non-streamed chat call with `response_format: json_schema` that thought for more than about 20 s came back as `504` with the body `upstream request deadline exceeded`, three times in a row. The same body with `"stream": true, "stream_options": {"include_usage": true}` ran for 48 s fine. The stream sends no content while the model reasons, then the JSON in a few `delta.content` chunks, then a last chunk with `usage` (it includes `completion_tokens_details.reasoning_tokens`), then `data: [DONE]`. The app streams every structured call now.
- **Optional fields are skipped.** Under constrained decoding the model leaves out any property that is not in `required`, even when the prompt asks for it. `api/schemas.json_schema()` marks every property required.
- **Reasoning eats `max_tokens`.** With `max_tokens: 3000` and `reasoning_effort: high` a hard prompt returned `content: null` and `finish_reason: length` (all 3000 tokens were reasoning). The app sends no `max_tokens` on Muse Spark 1.3 calls.
- **SAM 3.1.** The stream is `response.created`, `response.in_progress`, `response.output_item.added`, `response.content_part.added`, one `response.output_text.delta` with the whole grammar, then the `.done` events and `response.completed`. A noun phrase ("tire") on the motorbike photo gave one box with `c=0.777` and a 196x120 one-bit mask; a box prompt with five boxes gave five masks in 3 to 8 s. Zero masks on the synthetic check image in `check_keys.py` is normal (nothing in it to find).
- **Muse Image.** `reasoning_strength: high` takes about 20 s and sometimes hit the same 504; the client retries once and then asks at `low`. A 1536 px PNG came back as `b64_json` (about 0.8 to 1.8 MB).
- **Errors.** I did not get a 401, 403 or 429 on the live API, so I have not seen their exact bodies. The client never retries a 4xx other than 429, and honours `Retry-After` (seconds, capped at 30 s) on 429/503.
- **Cost.** A full repair (look, SAM, diagnose, plan, one step check) costs $0.05 to $0.07; a Muse Image diagram adds $0.01; a model-side red stop costs about $0.03.
