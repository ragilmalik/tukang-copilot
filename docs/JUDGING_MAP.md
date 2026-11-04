# Judging map: each criterion and where the evidence is

I checked this on 2026-11-01 (WIB) against the official sources below. Video timestamps refer to the current backup
cut, `docs/demo/tukang-copilot-demo.mp4` (2:53, v1.29 cut: 3 s hook title card, WhatsApp scene at 2:13, demo mode).
The times are the scene starts in `docs/demo/TIMESTAMPS.txt`; if the video is re-cut, re-sync them from that file.

## Official sources (I opened each one)

| What | Where |
|---|---|
| Official Rules (judging weights, prizes, IP) | https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver (needs sign-in) |
| Participant Guide (3 judging stages, bonus prize table, demo rules, anti-projects) | https://cerebralvalley.ai/e/meta-ai-developer-hackathon/details (needs sign-in) |
| Submission form (fields, read without submitting) | https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit |
| Event page (tracks, themes, dates) | https://cerebralvalley.ai/e/meta-ai-developer-hackathon and https://dev.meta.ai/events/global-hackathon |
| Kickoff webinar slides (rubric, bonus prizes, anti-projects), mirrored by another entrant | https://github.com/FrankieBiz/Faultline/blob/main/docs/HACKATHON_BRIEF.md |

### The rules that matter most
- Deadline: Wed Nov 4, 2026, 9:00 PM ET = **Thu Nov 5, 09:00 WIB**. "Late submissions won't be considered."
- Judging runs Nov 5 to Nov 8. Stage 1 is pass/fail: the project "reasonably fits the theme and reasonably used Meta Model API and/or Meta's open-weight models". Stage 2 scores four criteria from 0 to 10. Stage 3 takes the top 5 per track, and the final judges "watch the video demos live and rank them using the same rubric". The closing ceremony and live finals are Mon Nov 9, 12:00 PM ET.
- Video: the form field is "3-Minute Demo Video*", a YouTube-style link. The guide says the video must highlight "the specific features, code, and functionality you built during the Hackathon" and is "one of the primary artifacts Judges use ... along with your code and live product". Judges have to be able to tell what was built during the event, or the entry can be disqualified.
- Repo: "Public GitHub Repository*". The rules say "Repositories must be public." New work only.
- The organisers named these anti-projects: AI medical advice, basic RAG, *simple image analyzers*, Streamlit apps, dashboards, education chatbots, job screeners, nutrition coaches, personality and sports analyzers. So I never describe Tukang Copilot as "an image analyzer". It is an agent that acts, verifies and re-plans on a physical object.

## Main rubric (Indie track lens: "creativity, technical ambition, and whether it works")

### Impact 30%: "real-world potential, who benefits, how much it matters, whether it could become something people use, and whether it fits one of the problem statements"

| Evidence | Where |
|---|---|
| A real Indonesian problem with sourced numbers: 139.45 million motorbikes (BPS 2024), 68 million native Javanese speakers, a pump repair visit at Rp180k to Rp450k against a Semarang minimum wage of Rp3.70 million a month | docs/SUBMISSION.md "Problem", docs/launch/ONE_PAGER.md |
| Five everyday scenarios: motorbike, water pump, faucet, rice cooker (safety stop), flat scooter tyre | `api/pipeline/mock.py`, video 0:03 to 2:13, screenshots `10_pump.png`, `11_rice_stop.png` |
| Three languages for every UI string, Basa Jawa included | `web/app.js` (T.jv), `api/tests/test_i18n.py`, video 2:13 (WhatsApp chat in Basa Jawa), `20_javanese_result.png`, `14_garage_jv.png`, `30_whatsapp_jv_*.png` |
| Money: parts cost vs bengkel price, and the "My garage" total saved | `04_diagnosis.png`, video 0:34 |
| Hand-off to a real mechanic (WhatsApp summary, Maps search, PDF brief) | `api/main.py` `/handoff`, `18_handoff.png`, video 1:53 |
| The same agent runs in WhatsApp, where people already are (photo and voice note in; marked photo, diagnosis, step buttons, camera checks, red stop and PDF out), with no install and no website to trust. Tested with a fake Graph API and the `/wa` simulator; a real number waits on my Meta app setup | `api/channels/whatsapp.py`, docs/WHATSAPP.md, `30_whatsapp_*.png`, video 2:13 |
| Product path: PWA, no account, and an open-weights self-host option for a co-op or vocational school | `web/manifest.webmanifest`, docs/ROADMAP.md |
| Theme fit, "Push the Frontier": it gives a phone a new capability in the physical world (see, act, verify, re-plan) | docs/SUBMISSION.md field 4 |
| **Still open (me):** real user trials. `docs/IMPACT.md` is MOCK DATA. Even 3 real Semarang repairs with photos would beat every number I have now. | docs/USER_TRIAL_KIT.md |

### Use of Meta AI tooling 25%: "how creatively ... whether they went beyond a basic integration, and whether they surfaced unexpected capabilities"

| Evidence | Where |
|---|---|
| Five Meta models in one loop, one client file | `api/meta_client.py`, README table, video 2:34 |
| SAM 3.1 masks on the user's *own* photo, from the boxes the vision model found (one box-prompt call for all parts) | `api/pipeline/engine.py` `stage_segment`, `05_parts.png`, video 0:43 |
| SAM 3.1 on live camera frames (live guide), about 1 frame a second, capped per repair | `api/pipeline/track.py`, `16_live_guide.png`, video 0:56 |
| Muse Spark as a *verifier*: it compares a new photo with the expected state and returns a pass or a specific correction | `engine.check_step`, `07_check_fail.png`, `08_check_pass.png`, video 1:07 |
| Unexpected capability: Muse Spark 1.2 audio transcribes Javanese, which Voice Transcribe does not list | `meta_client.transcribe_with_spark_audio` |
| Muse Image edits the user's photo into a diagram; Spark reviews it and a bad one is redrawn once | `engine.make_diagram`, `28_diagram_step.png`, video 1:36 (demo: placeholder drawing) |
| Muse Spark Open (open weights) on Baseten behind one switch, with a visible badge | `USE_OPEN_WEIGHTS`, `21_open_weights.png`, video 2:25 |
| Meta's WhatsApp Cloud API (Graph v26.0) as a second channel into the same agent loop: signed webhook (`X-Hub-Signature-256`), two-step media download, reply buttons per step, PDF as a document. Tested against a fake Graph API (`api/testing/fake_graph.py`), not yet on a real number | `api/channels/whatsapp.py`, `test_whatsapp.py`, `test_playwright_wa.py`, docs/WHATSAPP.md, video 2:13 |
| One-command first live run: after `set_keys.py`, `scripts/first_live_run.py` runs one sample repair on the real API and writes `docs/LIVE_RUN.md` with models, timings and cost; `--fake` rehearses it against the stand-in server | `scripts/first_live_run.py`, `test_first_live_run.py` |
| **Still open (me), top priority:** no live Meta answer is verified yet, and Stage 1 is pass/fail on whether the project "reasonably used Meta Model API". Running `python scripts/set_keys.py` then `python scripts/first_live_run.py` closes it, and one live clip in the video would help. | docs/VERIFICATION_REPORT.md |

### Technical depth and execution 20%: "engineering is sound and thoughtfully refined ... real craft"

| Evidence | Where |
|---|---|
| 894 automated tests, 0 failed, 0 skipped (including 21 real-Chromium test files with a fake camera, and jsdom) | docs/TEST_REPORT.md (v1.29.13, 2026-11-04) |
| HTTP smoke of a running server: ALL PASSED, 69 checks | `scripts/smoke_e2e.py` |
| mypy strict with no issues in 150 files; ruff clean; CI | `mypy.ini`, `.github/workflows/` |
| Web security on the public pages: a strict Content-Security-Policy on every HTML page (scripts only from the site itself, no inline script, no eval; the WhatsApp simulator's script lives in `web/wa.js` for that reason), HSTS when the request came in over https through Render's proxy, signed WhatsApp webhooks, an owner token so a guide-link holder can't answer or erase someone else's repair | `api/main.py`, `test_csp.py`, `test_headers.py`, `test_owner_token.py`, `test_hostile_input.py` |
| Accessibility checked with a tool as well as by eye: axe-core (WCAG 2.1 AA rules plus best practice) finds nothing serious or critical on the home, progress, question, result, stop, shared guide, WhatsApp simulator and laptop screens; one h1 per screen; the photo and video pickers are native file inputs in the tab order; screen-reader labels in id/jv/en; touch targets of 40 to 44 px | `test_playwright_a11y.py`, `test_playwright_labels.py`, `test_playwright_targets.py`, `test_a11y_buttons.py` |
| Details a real owner hits: a shared link to a red stop opens the STOP card with its "do this now" list; an expired or erased guide link gets a short page in the owner's language with a button to start a repair (still a 404) instead of raw JSON; fonts, photos and PDFs are not gzipped twice on the free server; the red stop's "do this now" list and the "Safety first" lines fit the thing being fixed (a rice cooker or pump says unplug it, a tap says close the stop valve); a guide link shared after "Still broken" says "Plan 2 of 3" and the PDF strikes through causes already tried; tools and parts link to Tokopedia and Shopee by name; Share on a laptop shows the copied link in a line instead of an alert; /static files send Cache-Control so a new release shows up on the next load; Basa Jawa stays in one register (ngoko) | `test_playwright_guide.py`, `test_gone_page.py`, `test_gzip.py`, `test_playwright_kind_safety.py`, `test_report_tried_and_jv_words.py`, `test_playwright_share_shop_tour.py`, `test_static_cache.py`, `test_jv_register.py` |
| Strict JSON schemas with tolerant repair and one retry; per-repair and per-day cost caps; rate limits | `api/schemas.py`, `api/coerce.py`, `api/cost.py`, `api/guard.py` |
| Safety in code (3 layers) and prompt-injection fencing | `api/pipeline/safety.py`, `api/untrusted.py`, `test_security.py`, `test_injection.py` |
| Resilience: retries, friendly errors, a labelled demo fallback, and a recorded demo when the server sleeps | `api/errors.py`, `test_demo_fallback.py`, `test_replay.py`, `27_recorded_demo.png` |
| Live path tested against a stand-in server built from the official API docs | `api/testing/fake_meta.py`, `test_live_path.py` |
| Fixture eval: 10/10 photos and 5/5 step checks met expectations (mock mode, labelled AI-generated sample photos) | docs/EVAL_REPORT.md |
| Red-team eval: safety-stop recall 100% on 33 dangerous cases (23 owner texts, 10 plan steps), 0 false stops on 17 safe cases, 7/7 prompt-injection cases resisted, plus latency and cost per repair. Labelled mock / fake-model; the live run is pending. Run against the v1.24 rules, it found 12 of 20 red-team texts and 7 of 10 dangerous plan steps slipping through, and I fixed those gaps in 1.25 | docs/EVAL.md, `scripts/run_eval.py`, `test_run_eval.py` |

### Demo 25%: "working, impressive demo, whether the product holds up live, and the quality of the demo video"

| Evidence | Where |
|---|---|
| 2:53 video with captions and voice-over, under the 3-minute limit | `docs/demo/tukang-copilot-demo.mp4`, `.en.srt` |
| 1-tap demo with no photo needed; a recorded demo plays if the free server is asleep | README "Try it in 60 seconds", `27_recorded_demo.png` |
| Laptop view: on a screen 1024 px or wider the app sits in a phone frame with a side panel (QR code of the current URL, 1-tap demo, id/jv/en switch) | `29_laptop.png`, `test_playwright_desk.py` |
| Static judge build with no server and no cold start: `scripts/build_static.py` writes `dist-static/` (recorded demo, relative paths; not hosted yet) | `scripts/build_static.py --help`, `test_playwright_static.py` |
| 34 screenshots (5 of them from the WhatsApp simulator) and a hero GIF | `docs/demo/screenshots/`, `docs/demo/hero.gif` |
| Every frame says demo mode and AI-generated sample photos | docs/demo/README.md |
| **Still open (me):** the live URL ([LIVE_URL]) and the YouTube link ([YOUTUBE_URL]) are not filled in. Final judges watch the video live, so the first 10 seconds have to hook them. | docs/launch/YOUTUBE.md |
| **Still open (me):** a clip of a real phone on a real object (even 20 seconds of a real faucet or pump) inside the video. All the current footage is demo mode. | docs/DEMO_SCRIPT.md |

## Bonus prizes (Participant Guide table and webinar slide; $50K total, announced on or about Nov 10)

| Prize | How it is judged (quoted) | My evidence | Status / gap |
|---|---|---|---|
| Most Viral Project, $20K | "Post your project demo on X and submit the post link through the hackathon platform. ... total engagement (likes, reposts, and comments) up until November 8 EOD" (slide: Nov 8, 11:59 PM ET). | 43.5 s vertical clip `docs/demo/tukang-copilot-x-vertical.mp4`; thread in docs/launch/X_THREAD.md; share cards (`26_share_card.png`) | I post before submitting so the link can go in form field 5. The engagement window closes Nov 8 11:59 PM ET = **Nov 9, 11:59 WIB**. |
| Best Build on Meta Open Weights, $10K | "best project built using Muse Glimmer or Muse Spark Open, served on participants' own hardware or through partner-provided inference. Projects are flagged during the first judging round. The infrastructure partner verifies that the project runs on an eligible Meta open-weight model." | `USE_OPEN_WEIGHTS=1` moves diagnosis + planning to Muse Spark Open via Baseten; badge in the UI; tested against a stand-in Baseten server | **Still open (me):** needs a real Baseten deployment and one logged run, otherwise the partner can't verify it. Without Baseten credits I won't claim this prize. |
| Community Vote, $10K | "most votes in the public gallery ... total number of votes received through the hackathon platform, limited to one vote per verified account." The vote opens at the Nov 9 closing ceremony (12:00 PM ET = Nov 10, 00:00 WIB); the winner is announced Nov 16 on Discord. | Kit in docs/launch/COMMUNITY_VOTE_KIT.md (id, jv, en) | The gallery URL isn't public yet (checked 2026-11-01). Voters need a verified Cerebral Valley account. I send the kit only once the vote opens. |
| Best Agentic Use-Case, $5K | "strongest use of AI agents to complete meaningful tasks, make decisions, or coordinate multi-step workflows. Judges evaluate the project's level of autonomy, effectiveness in completing its intended task, and practical usefulness." | The loop: ask when unsure, plan, gate on safety, verify each step from a photo, re-plan, escalate or hand off. The agent log "What the AI did" shows the model behind each decision (`23_agent_log.png`, `24_agent_jump.png`, `25_pdf_agent.png`, video 1:07 to 2:04); the same loop runs over WhatsApp (`30_whatsapp_*.png`, video 2:13) | My strongest bonus claim. Effectiveness numbers wait on the live run and the trials. |
| Best Creative Build, $5K | "most original and compelling creative project built using Muse Image or Muse Wonder. Projects are flagged during the first judging round and evaluated on creative originality, execution, and how effectively the model is used in the final experience." | Muse Image turns the user's own photo into an instructional diagram, and Spark reviews it | Weak. Muse Image is a supporting feature here. The video shows a diagram step at 1:36, but it's a demo-mode placeholder drawing, not a live Muse Image output. Mention it, don't lead with it. |

## Gaps, ranked by expected score gain

**Things only I can do**
1. Run `python scripts/set_keys.py` then `python scripts/first_live_run.py` (writes docs/LIVE_RUN.md). Stage 1 is pass/fail on real Meta model use, so this comes first.
2. Optional: get a Baseten key and log one open-weights run, or drop the open-weights claim.
3. Record 20 to 40 seconds of real-object footage (faucet or pump) and run 3 to 5 real trials with `?trial=T1` to replace the MOCK impact numbers.
4. Push to GitHub, deploy on Render and host the static judge build (`dist-static/`); fill in [GITHUB_URL] and [LIVE_URL].
5. Upload the video to YouTube (unlisted is fine, test it logged out) and post the X thread; fill in [YOUTUBE_URL] and [X_POST_URL].
6. Paste docs/SUBMISSION.md into the Cerebral Valley form before Thu Nov 5, 09:00 WIB.

**Code** (done in 1.25.0: `first_live_run.py`, docs/EVAL.md, hook title card + chapter re-sync, static judge build, laptop phone frame, diagram scene in the video)
1. After the live run, run `run_eval.py` against the live API and replace the mock / fake-model labels with real numbers.

**Docs**
1. After the live run, replace every "not yet verified" line with the real result (SUBMISSION, WRITEUP, JUDGE_FAQ, ONE_PAGER).
2. After the trials, replace the MOCK impact numbers.
