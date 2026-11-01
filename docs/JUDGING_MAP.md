# Judging map: every criterion to evidence in this repo

Checked 2026-11-01 (WIB) against the official sources below. Video timestamps refer to the current backup cut
`docs/demo/tukang-copilot-demo.mp4` (2:57, v1.24, demo mode). If the video is re-cut, re-sync the timestamps from
`docs/demo/tukang-copilot-demo.en.srt`.

## Official sources (opened, not summarised from memory)

| What | Where |
|---|---|
| Official Rules (judging weights, prizes, IP) | https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver (needs sign-in) |
| Participant Guide (3 judging stages, bonus prize table, demo rules, anti-projects) | https://cerebralvalley.ai/e/meta-ai-developer-hackathon/details (needs sign-in) |
| Submission form (fields, read without submitting) | https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit |
| Event page (tracks, themes, dates) | https://cerebralvalley.ai/e/meta-ai-developer-hackathon and https://dev.meta.ai/events/global-hackathon |
| Kickoff webinar slides (rubric, bonus prizes, anti-projects), mirrored by another entrant | https://github.com/FrankieBiz/Faultline/blob/main/docs/HACKATHON_BRIEF.md |

### Key rules in one place
- **Deadline:** Wed Nov 4, 2026, 9:00 PM ET = **Thu Nov 5, 09:00 WIB**. "Late submissions won't be considered."
- **Judging:** Nov 5 to Nov 8. Stage 1 = pass/fail: the project "reasonably fits the theme and reasonably used Meta Model API and/or Meta's open-weight models". Stage 2 = four criteria scored 0 to 10. Stage 3 = top 5 per track; final judges "watch the video demos live and rank them using the same rubric". Closing ceremony and live finals Mon Nov 9, 12:00 PM ET.
- **Video:** form field "3-Minute Demo Video*", YouTube-style link. Guide: the video must highlight "the specific features, code, and functionality you built during the Hackathon" and is "one of the primary artifacts Judges use ... along with your code and live product". Judges must be able to tell what was built during the event, or the entry can be disqualified.
- **Repo:** "Public GitHub Repository*". Rules: "Repositories must be public." New work only.
- **Anti-projects named by the organisers:** AI medical advice, basic RAG, *simple image analyzers*, Streamlit apps, dashboards, education chatbots, job screeners, nutrition coaches, personality and sports analyzers. Tukang Copilot must never be described as "an image analyzer": it is an agent that acts, verifies and re-plans on a physical object.

## Main rubric (Indie track lens: "creativity, technical ambition, and whether it works")

### Impact 30%: "real-world potential, who benefits, how much it matters, whether it could become something people use, and whether it fits one of the problem statements"

| Evidence | Where |
|---|---|
| Real Indonesian problem with sourced numbers: 139.45 million motorbikes (BPS 2024), 68 million native Javanese speakers, a pump repair visit Rp180k to Rp450k vs a Semarang minimum wage of Rp3.70 million a month | docs/SUBMISSION.md "Problem", docs/launch/ONE_PAGER.md |
| Five everyday scenarios: motorbike, water pump, faucet, rice cooker (safety stop), flat scooter tyre | `api/pipeline/mock.py`, video 0:00 to 2:23, screenshots `10_pump.png`, `11_rice_stop.png` |
| Three languages, every UI string, incl. Basa Jawa | `web/app.js` (T.jv), `api/tests/test_i18n.py`, video 2:23, `20_javanese_result.png`, `14_garage_jv.png` |
| Money: parts cost vs bengkel price, "My garage" total saved | `04_diagnosis.png`, video 0:32 |
| Hand-off to a real mechanic (WhatsApp summary, Maps search, PDF brief) | `api/main.py` `/handoff`, `18_handoff.png`, video 1:50 |
| Product path: PWA, no account, open-weights self-host option for a co-op or vocational school | `web/manifest.webmanifest`, docs/ROADMAP.md |
| Theme fit "Push the Frontier": gives a phone a new physical-world capability (see, act, verify, re-plan) | docs/SUBMISSION.md field 4 |
| **GAP (Malik):** real user trials. `docs/IMPACT.md` is MOCK DATA. Even 3 real Semarang repairs with photos would beat every number we have. | docs/USER_TRIAL_KIT.md |

### Use of Meta AI tooling 25%: "how creatively ... whether they went beyond a basic integration, and whether they surfaced unexpected capabilities"

| Evidence | Where |
|---|---|
| Five Meta models in one loop, one client file | `api/meta_client.py`, README table, video 2:39 |
| SAM 3.1 masks on the user's *own* photo from boxes the vision model found (one box-prompt call for all parts) | `api/pipeline/engine.py` `stage_segment`, `05_parts.png`, video 0:41 |
| SAM 3.1 on live camera frames (live guide), about 1 frame a second, capped per repair | `api/pipeline/track.py`, `16_live_guide.png`, video 0:53 |
| Muse Spark as a *verifier*: compares a new photo with the expected state and returns pass or a specific correction | `engine.check_step`, `07_check_fail.png`, `08_check_pass.png`, video 1:07 |
| Unexpected capability: Muse Spark 1.2 audio transcribes Javanese, which Voice Transcribe does not list | `meta_client.transcribe_with_spark_audio` |
| Muse Image edits the user's photo into a diagram; Spark reviews it and a bad one is redrawn once | `engine.make_diagram` |
| Muse Spark Open (open weights) on Baseten behind one switch, with a visible badge | `USE_OPEN_WEIGHTS`, `21_open_weights.png`, video 2:30 |
| **GAP (Malik + code lane):** no live Meta answer verified yet. Stage 1 asks whether we "reasonably used Meta Model API". A real-key run with saved logs (`scripts/first_live_run.py`, planned C4) and one live clip in the video close this. | docs/VERIFICATION_REPORT.md |

### Technical depth and execution 20%: "engineering is sound and thoughtfully refined ... real craft"

| Evidence | Where |
|---|---|
| 496 automated tests, 0 failed, 0 skipped (incl. real Chromium with a fake camera, and jsdom) | docs/TEST_REPORT.md (2026-11-01 03:53 WIB) |
| HTTP smoke of a running server: ALL PASSED, 66 checks | `scripts/smoke_e2e.py`, HANDOFF.md |
| mypy strict, no issues in 84 files; ruff clean; CI | `mypy.ini`, `.github/workflows/` |
| Strict JSON schemas with tolerant repair and one retry; per-repair and per-day cost caps; rate limits | `api/schemas.py`, `api/coerce.py`, `api/cost.py`, `api/guard.py` |
| Safety in code (3 layers) and prompt-injection fencing | `api/pipeline/safety.py`, `api/untrusted.py`, `test_security.py`, `test_injection.py` |
| Resilience: retries, friendly errors, labelled demo fallback, recorded demo when the server sleeps | `api/errors.py`, `test_demo_fallback.py`, `test_replay.py`, `27_recorded_demo.png` |
| Live path tested against a stand-in server built from the official API docs | `api/testing/fake_meta.py`, `test_live_path.py` |
| Fixture eval: 10/10 photos and 3/3 step checks met expectations (mock mode, labelled stand-ins) | docs/EVAL_REPORT.md |
| **GAP (code lane, C3):** a red-team eval table (safety-stop recall on gas, mains, brakes; injection refusals; latency and cost per repair) would turn "we test" into numbers a judge can quote. | docs/EVAL.md (planned) |

### Demo 25%: "working, impressive demo, whether the product holds up live, and the quality of the demo video"

| Evidence | Where |
|---|---|
| 2:57 video, captions, voice-over, under the 3-minute limit | `docs/demo/tukang-copilot-demo.mp4`, `.en.srt` |
| 1-tap demo with no photo needed; recorded demo plays if the free server is asleep | README "Try it in 60 seconds", `27_recorded_demo.png` |
| 27 screenshots and a hero GIF | `docs/demo/screenshots/`, `docs/demo/hero.gif` |
| Every frame says demo mode and stand-in photos (honesty) | docs/demo/README.md |
| **GAP (Malik):** the live URL ([LIVE_URL]) and YouTube link ([YOUTUBE_URL]) are not filled. Final judges watch the video live, so the first 10 seconds must hook. | docs/launch/YOUTUBE.md |
| **GAP (Malik):** a real-phone, real-object clip (even 20 seconds of a real faucet or pump) inside the video. All current footage is demo mode. | docs/DEMO_SCRIPT.md |
| **GAP (code lane, C1/C2/C5):** laptop phone-frame layout, a static judge build with no cold start, burned-in hook title card. | ../WIN_PLAN.md |

## Bonus prizes (Participant Guide table and webinar slide; $50K total, announced on or about Nov 10)

| Prize | Exactly how it is judged | Our evidence | Status / gap |
|---|---|---|---|
| **Most Viral Project, $20K** | "Post your project demo on X and submit the post link through the hackathon platform. ... total engagement (likes, reposts, and comments) up until November 8 EOD" (slide: Nov 8, 11:59 PM ET). | 45 s vertical clip `docs/demo/tukang-copilot-x-vertical.mp4`; thread in docs/launch/X_THREAD.md; share cards (`26_share_card.png`) | Malik posts before submitting so the link goes in form field 5. Engagement window closes Nov 8 11:59 PM ET = **Nov 9, 11:59 WIB**. |
| **Best Build on Meta Open Weights, $10K** | "best project built using Muse Glimmer or Muse Spark Open, served on participants' own hardware or through partner-provided inference. Projects are flagged during the first judging round. The infrastructure partner verifies that the project runs on an eligible Meta open-weight model." | `USE_OPEN_WEIGHTS=1` moves diagnosis + planning to Muse Spark Open via Baseten; badge in UI; tested against a stand-in Baseten server | **GAP (Malik):** needs a real Baseten deployment and one logged run, otherwise the partner cannot verify it. If no Baseten credits, do not claim this prize. |
| **Community Vote, $10K** | "most votes in the public gallery ... total number of votes received through the hackathon platform, limited to one vote per verified account." Vote opens at the Nov 9 closing ceremony (12:00 PM ET = Nov 10, 00:00 WIB); winner announced Nov 16 on Discord. | Kit in docs/launch/COMMUNITY_VOTE_KIT.md (id, jv, en) | The gallery URL is not public yet (checked 2026-11-01). Voters need a verified Cerebral Valley account. Send the kit only when the vote opens. |
| **Best Agentic Use-Case, $5K** | "strongest use of AI agents to complete meaningful tasks, make decisions, or coordinate multi-step workflows. Judges evaluate the project's level of autonomy, effectiveness in completing its intended task, and practical usefulness." | Loop: ask when unsure, plan, gate on safety, verify each step from a photo, re-plan, escalate or hand off. Agent log "What the AI did" with the model per decision (`23_agent_log.png`, `24_agent_jump.png`, `25_pdf_agent.png`, video 1:28 to 1:50) | Strongest bonus claim. Effectiveness numbers wait on the live run and trials. |
| **Best Creative Build, $5K** | "most original and compelling creative project built using Muse Image or Muse Wonder. Projects are flagged during the first judging round and evaluated on creative originality, execution, and how effectively the model is used in the final experience." | Muse Image turns the user's own photo into an instructional diagram, reviewed by Spark | Weak: Muse Image is a supporting feature, not the core, and no live diagram is in the video. Mention it, do not lead with it. |

## Gaps, ranked by expected score gain

**For Malik (only he can do these)**
1. Real Meta key, one live run, save the log and a screen recording (Stage 1 pass/fail + Use of Meta tooling).
2. Push the public GitHub repo, deploy, fill [GITHUB_URL], [LIVE_URL] (required fields; "holds up live").
3. Upload the video to YouTube (unlisted is fine, test logged out) and fill [YOUTUBE_URL].
4. 20 to 40 seconds of real-object footage (faucet or pump in a Semarang house) for the video's opening.
5. Post the X clip before submitting; put the link in form field 5.
6. Baseten key + one logged open-weights run, or drop the open-weights claim.
7. Three to five real trials with `?trial=T1` to replace the MOCK impact numbers.

**For the code lane**
1. `scripts/first_live_run.py` writes a dated live-run report that docs can link (C4).
2. docs/EVAL.md red-team table: safety-stop recall, injection refusals, latency and cost per repair (C3).
3. Hook title card in the first 3 seconds and an on-screen "built Oct 26 to Nov 4" line (C5), then re-sync the chapter times in docs/launch/YOUTUBE.md.
4. Static judge build without cold start (C2) and a laptop phone frame (C1).
5. Show one Muse Image diagram step in the video so the Creative and Meta-tooling claims are visible, not only in code.

**For Malik (docs)**
1. After the live run, replace every "not yet verified" line with the real result (SUBMISSION, WRITEUP, JUDGE_FAQ, ONE_PAGER).
2. After the trials, replace MOCK impact numbers.
