# Tukang Copilot on WhatsApp

Almost every Indonesian already has WhatsApp open. This channel lets an owner fix something by chatting with
Tukang Copilot there, with no web page and nothing to install. It runs on the same engine as the phone web app,
so the safety gate, the Meta models (Muse Spark, SAM 3.1, Muse Voice Transcribe), the camera checks and the PDF
report are all the same. Only the way messages come in and go out is different.

Code: `api/channels/whatsapp.py` (webhook + chat), `api/channels/wa_text.py` (id/jv/en texts, language guess),
`api/channels/wa_sim.py` (simulator), `web/wa.html` (simulator page), `api/tests/doubles/fake_graph.py` (fake Graph
API for tests), tests in `api/tests/test_whatsapp.py`.

## What it does

| The owner sends | Tukang Copilot answers |
|---|---|
| "Halo" | A short welcome: send a photo and say what is wrong. |
| Text only | Asks for a photo. If the text already describes a danger (gas leak, house wiring, smoke, a shock), it stops at once with the safety message and a Google Maps link to the nearest workshop, and never sends steps. |
| Photo(s) (up to 3) plus text, a caption or a voice note | "One moment...", then the SAM-marked photo with the object, the likely cause and its confidence, the safety level, parts cost, workshop price and the saving, then step 1 with the reply buttons Done / Problem / Stop. |
| A red case (for example a rice cooker that needs opening) | The safety message and the nearest-workshop link. No steps. |
| A low-confidence case | One follow-up question; the next text or voice note is the answer. |
| A photo during a step | The step camera check. Pass: "✅" and the next step. Fail: "❌", what to fix, and the same step again. |
| Done | The next step. After the last step: "All steps done", the final check, then the PDF report as a document. |
| Problem (or "masih rusak", "isih rusak", "still broken") | A new plan for the next likely cause ("🔁 Plan 2: ..."). When every safe cause is tried: the workshop link and the PDF. |
| Stop | The workshop link and the PDF report. |
| A voice note during a step | Read as a command (next, back, repeat, check, still broken, stop). |
| HAPUS / BUSAK / DELETE | Erases the repair and any pending photos from the server at once. |
| A sticker, location, contact, video or file | A polite line: "I can read text, photos and voice notes". |

The chat follows the owner's language: Bahasa Indonesia, Basa Jawa or English, guessed from
the text (Javanese-only words such as "ora", "piye", "kudu" pick Basa Jawa). Until the owner types something,
it answers in Bahasa Indonesia. The repair itself (diagnosis, steps, PDF) uses the language of the chat at the
moment the repair starts. A voice note sent before any text is transcribed as Indonesian, so a Javanese
speaker gets the Javanese voice path (Muse Spark 1.2 audio) after typing one line in Javanese.

WhatsApp sends each photo of an album as its own message, so the channel waits `WA_DEBOUNCE_S`
(default 2 s) after the last photo before it starts.

The simulator at `/wa` is a WhatsApp-style page, clearly labelled "Simulator, runs the same engine in demo
mode". It calls `/api/wa-sim/*`, which builds the same webhook message objects and runs them through the same
handler; the replies it shows are the exact Cloud API message objects the real channel would send. It works
in id/jv/en and needs no WhatsApp number, which lets judges and the demo video show the channel. It is on in demo
mode only (`WA_SIM=1` also allows it with a live key, which then spends real model calls).

## Setup (10 steps, about 20 minutes)

1. Open https://developers.facebook.com/apps and log in with your Facebook account. If asked, finish the free developer registration.
2. Click **Create App**, type the name "Tukang Copilot", pick the use case **Connect with customers through WhatsApp**, choose (or create) a business portfolio, then click **Create app**.
3. In the app, open **Use cases > Customize > API Setup** (older dashboards: **WhatsApp > API Setup**). Meta gives you a free **test phone number**.
4. Under **To**, add your own WhatsApp number and type the code WhatsApp sends you. The test number can only message numbers you add here (up to 5).
5. On the same page, copy the **Phone number ID** (a long number, not the phone number itself). This is `WA_PHONE_NUMBER_ID`.
6. Click **Generate access token** and copy it. This is `WA_TOKEN`. It expires after about a day; for the judging week make a permanent one: Business Settings > System users > Add > Generate token with `whatsapp_business_messaging` and `whatsapp_business_management`.
7. Open **App settings > Basic**, click **Show** next to **App secret**, and copy it. This is `WA_APP_SECRET`.
8. Make up a verify word (for example `tukang-semarang-2026`). This is `WA_VERIFY_TOKEN`.
9. In Render, open the tukang-copilot service > **Environment**, fill in the four values `WA_TOKEN`, `WA_PHONE_NUMBER_ID`, `WA_VERIFY_TOKEN`, `WA_APP_SECRET` (render.yaml already lists them as empty secrets) and save. Render restarts the app.
10. Back in the Meta app, open **Configuration > Webhook**, paste the Callback URL `https://<your-render-app>.onrender.com/webhooks/whatsapp` and your verify word, click **Verify and save**, then click **Manage** and subscribe to **messages**. Send "Halo" from your phone to the test number: Tukang Copilot answers.

Open the Render link in a browser a minute before you test. The free server sleeps, and Meta gives up on
a webhook that answers too slowly (it retries later, and the channel handles a retried message only once).

## Settings

| Variable | Default | Meaning |
|---|---|---|
| `WA_TOKEN` | (empty) | Cloud API access token. Secret. |
| `WA_PHONE_NUMBER_ID` | (empty) | The business phone number ID from API Setup. |
| `WA_VERIFY_TOKEN` | (empty) | Your own word, also typed into the Meta webhook form. |
| `WA_APP_SECRET` | (empty) | App secret, used to check `X-Hub-Signature-256` on every POST. Secret. |
| `WA_GRAPH_VERSION` | `v26.0` | Graph API version in every call. |
| `WA_GRAPH_BASE` | `https://graph.facebook.com` | Only changed by the tests (fake Graph API). |
| `WA_DEBOUNCE_S` | `2` | Wait after the last album photo before starting. |
| `WA_SIM` | `0` | 1 = the `/wa` simulator also works with a live Meta key. |
| `WA_SIM_RATE_PER_HOUR` | `120` | Simulator messages per visitor per hour. |

The channel stays off (`/webhooks/whatsapp` answers 404) until the first four variables are all set.

## Limits

- Same limits as the web app: text up to 2000 characters, photos up to 15 MB (WhatsApp itself caps images at 5 MB), voice notes up to 20 MB, up to 3 photos per repair, `MAX_STEP_CHECKS` photo checks per repair, `MAX_COST_PER_SESSION_USD` per repair.
- Live mode: the web app's abuse guard applies per phone number (hashed): `RATE_LIMIT_PER_HOUR` new repairs, `FOLLOWUP_RATE_PER_HOUR` checks / re-plans / voice notes, and `DAILY_BUDGET_USD` for the whole server. A blocked owner gets the same friendly message in their language.
- Cloud API rules (from the docs below): the business number can answer freely for 24 hours after the owner's last message (customer service window); reply buttons are at most 3, titles at most 20 characters, body at most 1024; captions at most 1024. The channel cuts text to fit.
- The chat state is kept in memory: a server restart forgets where a chat was (the repair files on disk stay until `RETENTION_HOURS`). The owner just sends a new photo. One server process only (Render free plan); several processes would need a shared store.
- The test number reaches only the 5 numbers added in API Setup. A real public number needs Meta business verification, which is not needed for the hackathon.
- Not built: video messages (the web app takes a 5 to 10 s clip; on WhatsApp send photos instead), group chats, template messages outside the 24-hour window.

## Privacy

- Every POST is checked with HMAC-SHA256 of the raw body and `WA_APP_SECRET` (`X-Hub-Signature-256`); a bad or missing signature gets 403 and nothing is read.
- Photos and voice notes are downloaded from WhatsApp only to run the repair. The voice recording is deleted right after transcription (same as the web app). Repairs are deleted after `RETENTION_HOURS` (default 24 h); a chat that is silent that long is forgotten, pending photos included. HAPUS / BUSAK / DELETE erases at once.
- Logs never contain the token, the app secret or a full phone number (only the last 3 digits, for example `***890`). Chats are keyed by a hash of the number.
- The owner's own words never appear on a shared page or in the agent log (same rule as the web app).

## Graph API version and the pages it was built from

Graph API v26.0, the version used in every current example on these pages (read 2026-11-02 WIB):

- Webhook endpoint, verify request and `X-Hub-Signature-256`: https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/create-webhook-endpoint
- Sending messages (`POST /<PHONE_NUMBER_ID>/messages`, 24-hour window): https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages
- Reply buttons (max 3, title 20, body 1024, footer 60, `button_reply` webhook): https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/interactive-reply-buttons-messages
- Document messages (PDF, `filename`, caption 1024): https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/document-messages
- Media upload, media URL, download, supported types and sizes: https://developers.facebook.com/documentation/business-messaging/whatsapp/business-phone-numbers/media
- Image message webhook: https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/messages/image
- Audio (voice note) webhook: https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/messages/audio
- Get started (app, test number, token, system user): https://developers.facebook.com/documentation/business-messaging/whatsapp/get-started

## Honest status

Tested end to end against `api/tests/doubles/fake_graph.py` (real HTTP, real multipart uploads, the two-step media
download) and in the simulator, in demo mode. It has not been run against a real WhatsApp number yet;
that needs the 10 setup steps above.
