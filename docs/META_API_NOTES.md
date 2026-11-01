# Meta Model API notes (verified)

I read these on dev.meta.ai on 2026-10-30 (WIB). Re-check them before the final demo: nothing marked ⚠️ has been tried with a real key yet (see VERIFICATION_REPORT.md).

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
Decoding is constrained. Recursive schemas are rejected (400), and nesting is capped at 10, so I inline `$defs`.

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
- A dev HTTP proxy can turn `localhost` calls into 404s: set `NO_PROXY=127.0.0.1,localhost` when testing against the fake server.
- Model availability varies by country (Geographic Use Policy). Indonesia wasn't listed as restricted when I read it. ⚠️ Confirm with `scripts/check_keys.py`.
- ⚠️ The exact error bodies and rate limits for a new hackathon team still need confirming on the first real call.
