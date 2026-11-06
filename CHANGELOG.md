# Changelog

Dates are WIB (UTC+7). Everything here was built during the hackathon window (Oct 26 to Nov 4, 2026); 1.30.0 is the live-API run and polish after it, 1.31.0 a UI pass, 1.31.1 media and docs on it, 1.32.0 a weakness hunt (races, security, what breaks when files or requests go wrong).

## 1.33.0 media remake (in progress, 2026-11-06)
- Changed: new photorealistic sample photos for every scenario (labelled "Sample photo (AI-generated)", outlines in api/pipeline/sample_masks.json redrawn); the old ones are kept outside the repo.
- Changed: the recorded 1-tap demo is recorded again from the live Meta Model API on the new photos (6 Nov, 14:01 WIB; about $0.60 by the spend ledger of that run). In all three languages the model was 85 to 88% sure the plug cap is off the spark plug, so it asked no follow-up question.
- Fixed: `scripts/record_replay.py` needed a follow-up question and recorded the same language up to four times until the model asked one; on the clear new photo it never did (4 of 4 takes at 88 to 92%), so the recording failed after paying for every take. It now records one take per language as the model answered it, stores `"asked"`, and the shape check leaves the question part (and the log's ask and answer lines) out only when one side asked and the other did not. `web/replay.js` already played both. Tests: test_shape_check_allows_a_recording_without_the_follow_up_question; test_replay.py, test_playwright_replay.py and test_playwright_static.py accept both flows.
- Fixed: `scripts/make_og.py` could leave `web/demo-thumb.jpg` over its 30 KB budget with a detailed photo (it stopped at quality 50 without saying so); it now goes lower and fails if it still cannot fit. og.png and the demo thumbnail are re-made from the new recording's SAM-marked photo.
- Changed: offline cache v27 (the recording's photos changed).
- Changed: screenshots re-shot on the new photos at device scale 3: 26 of the 33 numbered shots (`scripts/make_demo_assets.py shots`) and a new gallery of 85 (`scripts/make_screenshots.py`: every screen in Bahasa Indonesia, Basa Jawa and English, Bahasa Indonesia in dark mode, static build, laptop, PDF pages, error and offline states; no model calls). `scripts/make_screenshot_index.py` writes docs/demo/screenshots/INDEX.md with all 118 files; 7 shots from the previous photo set stay and are marked there (03_question, 16_live_guide, the 5 WhatsApp simulator shots).
- Fixed: `scripts/make_demo_assets.py shots` opened recorded sessions without their owner token, so since 1.32.0 the live guide, step checks and "Still broken" answered 403 in the screenshots. It now puts the session's token into the page's store (`tc_owner`) first. `DEMO_PORT` pins the server port. Tests: test_open_recorded_uses_the_sessions_owner_token, test_screenshot_index_lists_every_png.

## 1.32.0 (2026-11-06)
A weakness hunt after the lost-answer race CI found in 1.31.1: every request that changes a repair, checked against every other one, plus security, missing files and restarts, and the docs. No change to the AI pipeline's prompts, the safety rules or the recorded demo.
- Fixed: one change to a repair at a time. Each repair has a lock (`engine.locked`); the first analysis and a re-plan hold it for their whole run and the short writers for a few lines. Before, each writer saved its own copy and the later save dropped the other's change. What that broke: a second "Still broken" while one was planning (two tabs, WhatsApp and the web) was accepted, showed a plan for the third cause and was then overwritten by the first; a step check that finished after "Still broken" ticked the same step number on the new plan; parallel photo checks all got past `MAX_STEP_CHECKS` (the cap was checked before the model call and counted after) and two checks on one step overwrote each other's photo; two quick Try again taps could both start; a live-guide frame, a voice command or "It works now" saved during a re-plan could put the old plan back. Now a second re-plan answers 409 ("busy", in the owner's language, Retry-After 3), a check is counted and named before the model looks and given back if the call fails, a check that belongs to a plan that is gone comes back as `"stale": true` and is not recorded (its cost still counts), and a live-guide frame during a re-plan is refused like a too-fast frame.
- Fixed: a repair that is not on its steps no longer takes step checks or live-guide frames (a red stop used to accept them), a re-plan is only taken from a plan on screen (after "All tried" one more "Still broken" used to add the last cause to the tried list again), and "It works now" is refused while the repair is still running.
- Fixed: starting a worker twice for one repair (Try again on the web and "coba lagi" on WhatsApp) ran diagnose and plan again over the finished repair. A worker now only runs a repair that is waiting for one.
- Fixed: a server restart or redeploy in the middle of a repair left it at "running" forever, with no Try again button. At startup such a repair is marked as an error ("The server restarted while this repair was running. Tap Try again to carry on.", in all three languages) and Try again carries on from the stages already done.
- Fixed: the photo check ran on the server's event loop (an `async` route calling the engine directly), so a live check of several seconds froze every other request, progress streams and other phones included. It now runs in a worker thread.
- Security: a shared guide link is read-only at the API too. Answer, Try again, Still broken, the step check, the live guide and the voice command now need the owner token, like "It works now" and erase already did; anyone with the link could re-plan the owner's repair, use up its photo checks and live-guide frames and spend on it. The app sends the token on each of them. A tab left open across this update runs the older app until it is reloaded once. Offline cache v26.
- Security: the rate limit keyed on the first X-Forwarded-For entry, which the visitor writes, so a random header per request skipped it. It now uses a header the edge proxy overwrites when `CLIENT_IP_HEADER` names one (render.yaml: `cf-connecting-ip`, since Render serves through Cloudflare; still to be checked on a live deploy), else the X-Forwarded-For entry `FORWARDED_HOPS` places from the right (default 1).
- Security: erasing a repair (or a `RETENTION_HOURS` under 24) took its spend out of the 24 h sum, so `DAILY_BUDGET_USD` could be dodged by erasing each repair. The spend of an erased or expired repair is kept for 24 h in `data/spend-erased.jsonl` (time and dollars only).
- Security: `/api/` and `/files/` answers send `Cache-Control: no-store` (the owner's photos and repair), except the public link-preview card. Session ids must be ASCII letters and digits (`str.isalnum` also took full-width and Arabic digits).
- Fixed: a decompression-bomb picture sent to the step check or the live guide answered 503 "the AI service is busy" instead of 400 "could not read that photo"; it no longer uses up a check or a frame either.
- Fixed: memory and disk that grew forever on a server that stays up: one lock per repair ever made, one entry per erase, one live-guide throttle entry per repair, folders a crash left without a `session.json` and stale `session.*.tmp` files. The janitor now clears them; an erase also ends an open progress stream cleanly instead of raising inside it. A picture's file is closed as soon as it is read.
- Submission: on 6 Nov 2026 at 09:29 WIB the Cerebral Valley submit page (signed in as ragilmalika through Google) showed a disabled "Event Finished" button and "That's time! All submissions are due now." No form opened and nothing was submitted (docs/SUBMISSION_CHECKLIST.md row 10). The repo is public (row 4 done).
- Added: `scripts/check_voice.py`, a writing check for the repo's own docs, comments and docstrings: filler words and phrases (from the humanizer and stop-slop checklists and Wikipedia's "Signs of AI writing" list), em dashes and en dashes used as dashes, the "not-just-X-but-Y" frame, all-caps orders, and notes that read like they were aimed at a tool instead of a person. Prompts keep their imperative voice. Every exception is in one allowlist with its reason, and an unused exception fails the check. test_check_voice.py runs it in CI. The docs and comments it flagged are rewritten, and HANDOFF.md now reads as my notes to the next maintainer.
- Fixed: test_shared_guide_after_a_replan_says_which_plan still posted "Still broken" without the owner token and got 403 after this release's owner-token change; it now sends the token the create call returns, like the app. test_robust_missing_files.py is now test_missing_files.py.
- Fixed: the progress clock ("⏱ 12 s") waited for the first state from the server, so on a slow connection the screen showed no clock until that answer arrived, and an earlier repair's finished state still in memory kept it blank too. It now counts from the tap. CI caught it through test_progress_stays_honest_on_a_slow_connection; test_the_clock_starts_before_the_first_answer_arrives holds the server's answers back and fails on the old app.js.
- Fixed: the erased-spend ledger rounded the erase time to 0.1 s with round(), so a line could be stored up to 0.05 s after the erase, and a daily sum asked right after it left that spend out. A fast CI runner hit it (test_erasing_a_repair_keeps_its_spend_in_the_daily_cap). The time is now rounded down; test_an_erase_counts_in_the_cap_at_once fails on the old code.
- Tests: test_races.py (28, deterministic: a held lock, a model call blocked on an Event, or a Barrier, never a sleep), test_owner_routes.py (owner token on every route that changes a repair, rate-limit key, ASCII ids, bomb on the step check), test_playwright_screens_clean.py (every main screen with no console or page error, a repair a restart interrupted coming back with Try again, the progress screen on a throttled connection), test_no_english_string_shows_in_bahasa_or_basa_jawa, test_private_repair_data_is_never_cached. Tests that act as the owner use `OwnerClient` (api/tests/owner_auth.py), which sends the token the way the app does; the old test that pinned the left-most X-Forwarded-For entry now pins the new rule.

## 1.31.1 (2026-11-06)
Media and docs on the 1.31.0 screens, and one fix in the recorded demo. No change to the AI pipeline, the prompts or the safety rules.
- Fixed: in the recorded 1-tap demo the hand-off message (WhatsApp summary, guide link, PDF link) still carried the address of the machine it was recorded on ("http://testserver/..."). The links now point at the site you are on: the guide link opens the recorded demo and the PDF link the recorded report. Offline cache v25.
- Changed: the 28 phone screenshots are re-shot on the 1.31.0 screens from recorded live answers: the motorbike flow from the recorded 1-tap demo, the pump, rice cooker, faucet and Basa Jawa screens from live sessions I recorded on 6 Nov 2026, reopened in the app. Only the live camera guide shot calls SAM 3.1 live. The 5 WhatsApp simulator shots are unchanged.
- Changed: `scripts/make_demo_assets.py` and `scripts/demo_video.py` have a recorded mode (`DEMO_RECORDED_DATA`): pages open at the public address and any request that would start new model work fails the run, except the live camera guide. The intro voice-over says the answers were recorded on a live run when they are played back, and the video refuses a voice clip made for the other mode.
- Changed: demo video, X clip, hero GIF and YouTube thumbnail re-made on the 1.31.0 screens (main video 2:54, 174.1 s, 1920x1080 at 60 fps, 34.2 MB, -16.0 LUFS integrated, true peak -3.9 dBFS; X clip 43.5 s, 1080x1920, 12.1 MB; hero GIF 640x1200, 2.2 MB).
- Added: `python docs/launch/make_launch_assets.py onepager` builds docs/launch/one-pager.pdf from ONE_PAGER.md (pandoc and WeasyPrint) and stops with an error if it would not be exactly one A4 page or still has a placeholder. The one-pager is rebuilt with the 1.31.1 numbers.
- Fixed: CI never ran the axe-core accessibility check (the test looked for axe only in /tmp/jd and skipped). It now finds axe where it finds jsdom (JSDOM_DIR, the repo's node_modules, /tmp/jd), and CI installs it. A missing demo video now fails the video test with a clear message instead of `KeyError: 'format'`.
- Fixed: docs/TEST_REPORT.md no longer says the live Meta models were never called ("no key yet"); it says this run is offline and points at LIVE_RUN.md and EVAL.md for the live runs.
- Fixed: the log-scrubber test cases have short ids (bearer, graph, github, ...) so the made-up token strings no longer show up as test names in docs/TEST_REPORT.md, where the repo's own secret scan flagged them.
- Fixed: a race in the follow-up question. The worker that asked the question wrote the session once more on its way out; an answer sent in that moment was overwritten, so the repair asked the same question again and never went on. The answer now waits for that worker to finish (the session lock), and the question is written once, with the cost line. Found by a CI run on 6 Nov; test_an_answer_waits_for_the_worker_that_asked fails on the old code.
- Fixed: test_typed_repair_says_why_listening_was_skipped read the note from the screen, and a fast CI runner had already left the progress screen; it now reads the text from the page.
- Tests: test_an_answer_waits_for_the_worker_that_asked, test_recorded_hand_off_links_point_at_this_site (real Chromium), test_intro_says_where_the_answers_come_from, test_launch_assets.py (3), test_axe_is_found_where_jsdom_is_found.

## 1.31.0 (2026-11-06)
A UI pass on the phone app: smoother screen changes, instant feedback on every tap, and the layout bugs I found at 360 px. No change to the AI pipeline, the prompts, the safety rules or the recorded demo.
- Added: screens (first screen, progress, question, result) change through a same-document View Transition where the browser has one (Chrome, Edge, Safari 18): the header and the laptop side panel stay put and the content slides 18 to 24 px in the direction you are going, in 200 ms. Browsers without it switch at once. The first tap or key during a transition skips it, and the tap still reaches the button under the finger (during a transition the browser sends taps to the page root, so I hand the click on myself). All of it is off under "reduce motion".
- Added: moving between steps (Next, Back, voice commands, the auto-advance after a pass) slides the step number, picture and instruction in from the side you are going. The step changes at once, so a quick second tap or a timer still counts right; the card is brought up under the header when its top is off screen, and screen readers hear "Step 2 of 4: ...".
- Added: placeholders on the progress screen. When a repair starts, "Found so far" lays out one grey row per finding still to come (what it saw, the SAM 3.1 photo box, the top cause, the step count), each the size of its result, and only the stage that is really running shimmers. The real finding takes over the same row, so the agent log under it no longer jumps down as results stream in (cumulative layout shift on a paced offline run at 390x844 went from 0.23 in 1.30.0 to 0.007). A placeholder stays at least 400 ms so it never blinks, and never shows a number.
- Added: the progress line says what is working right now, for example "34 s · Diagnosing (muse-spark-1.3)", and the running row counts its own seconds (counted on the phone since that stage started, not a guess of what is left). On the live server it adds that a live repair usually takes 1 to 2 minutes.
- Added: buttons that start something (the 1-tap demo, Check it now, the samples, Send and the quick answers, Check this step and the sample photos, Still broken, Call a mechanic, It works now, Share, Try again) keep their label, show a small spinner and ignore more taps until done. A double tap on the demo used to start two repairs; now it starts one.
- Added: a short vibration when a step check passes or fails and when a red stop opens, on phones that support it (Android Chrome; iPhones have no Vibration API, so nothing happens there).
- Added: Back, Forward or a reload in the middle of a repair returns to the step you were on (kept for this tab only).
- Fixed: in hands-free mode the enlarged "Lanjut" button stuck out past the step card (by 22 px at 360 px wide, and also on 390 px phones and in the laptop frame). Back and Listen are now square icon buttons (Listen keeps its word for screen readers and as a tooltip) and Next takes the rest of the row, 68 px tall in hands-free mode. The first version of this fix cut the Basa Jawa "Rungokna" to "Rungo..." on a 430 px phone, so the label check is in the layout test too.
- Fixed: under 400 px wide (and in the laptop's phone frame) the language picker covered the app name in Bahasa Indonesia. The header now shows a short "ID / JV / EN" pill there, with the real picker laid over it, so the target is still full size.
- Fixed: anything scrolled into view (the step card, a jump from the agent log) landed under the sticky header; the page now keeps a header's height of room on top.
- Fixed: a changing step picture (photo, part close-up or diagram) could change the step card's height; it now sits in a fixed 4:3 box. The result screen opens once its marked photo is decoded (at most 1.2 s) instead of with an empty box that then grows.
- Changed: no double-tap zoom and no tap delay on controls (touch-action: manipulation); the language picker uses 16 px text so iOS does not zoom in when you open it; the footer and the side gutters keep clear of the iPhone home bar and notch; a pull-down no longer reloads the page during a repair (the first screen keeps pull-to-refresh); long sample-photo labels wrap under their text instead of centring away from the icon.
- Changed: first paint. Both scripts load with defer, the 600 weight of Barlow is preloaded with the two others (buttons use it on the first screen), and the landing picture asks for high fetch priority. Offline cache v24.
- Tests: test_playwright_layout.py (nothing sticks out of its card and the header never collides, on each main screen at 360x740, 390x844, 430x932 and 1280x800, light and dark, id/jv/en; the hands-free button fits its card; the narrow language pill still switches language), test_playwright_motion.py (view transitions, reduced motion, a tap during a transition, the busy demo button, placeholders with layout shift under 0.1, the running-stage clock, a reload keeps the step, pull-to-refresh only off mid-repair, Next handler time) and test_ui_motion.py.

## 1.30.0 (2026-11-06)
The first release that ran on the real Meta Model API. Everything in the video, the screenshots and the recorded demo now comes from live answers.
- Added: live runs of every scenario (docs/LIVE_RUN.md) and what the API actually did (docs/META_API_NOTES.md); the eval has a live column (docs/EVAL.md, results kept in docs/eval); the recorded 1-tap demo is recorded from the live API in all three languages.
- Fixed (from the live runs): structured calls stream, because a plain call that reasons for more than about 20 s gets a gateway 504; every schema field is listed as required, because the decoder skipped optional ones and SAM got no parts; Muse Image gets one more try at high effort and then low effort after a 504; Meta retries honour Retry-After.
- Changed: logs scrub secrets (configured keys and anything shaped like a token, tracebacks too), one access line per request with a request id, no query strings or owner text. The canned-answer fallback is off by default. Offline mode is called "offline sample mode" everywhere and `OFFLINE=1` switches it on (`MOCK=1` still works). CORS is off unless `CORS_ORIGINS` names a site, and there is no Server header.
- Fixed: a red stop's PDF report no longer lists tools and parts to buy (live, the rice cooker stop listed a thermal fuse and a multimeter under the STOP card).
- Fixed: names from the model start with a capital in the PDF, the mechanic brief, the share card, My garage and WhatsApp, not only in the app heading. A diagnosis without tools or parts no longer fails validation and costs a retry.
- Fixed: number badges on the marked photo never sit on top of each other (on the live tap photo, badge 2 was hidden under badge 4).
- Fixed: the follow-up question asks one thing that fits the Yes / No / Not sure buttons (live, the motorbike question asked three things at once).
- Fixed: the recorded demo shipped 70 identical copies of the two step-check photos, about 5 MB the offline cache downloaded on install; now one copy per language. Offline cache v23.
- Fixed: the WhatsApp reply in Basa Jawa said "Keamanan" for safety; it says "Keslametan" like the app.
- Fixed: the 1-tap demo's "Right photo ✓" (a close-up of the plug cap pushed back on) was checked against the step on screen, step 1 "turn the key off", and the live model rightly said "Not quite", so the good sample photo failed on screen. The sample photo is now checked on the step it shows: the server picks it (`sample_step`, api/sample_step.py, matching the step's expected state in all three languages), the recording stores it per plan, the step card moves there and a line says "Checking step N with this sample photo". The buttons say what the photos are ("Sample photo: plug cap on", "Sample photo: too dark"); the dark one is still checked on the open step. `python scripts/record_replay.py --resample` re-picks that step in the committed recording from its own plans and checks, with no model calls. The demo was recorded again from the live API on 6 Nov (01:23 WIB): the follow-up question is one yes/no question in all three languages, and the plug cap photo passes on its step in every plan.
- Changed: the WhatsApp simulator label reads "Simulator, menjalankan mesin yang sama dengan jawaban contoh offline" (Basa Jawa: "nglakokake mesin sing padha"), matching the English line.
- Changed: the sample photos are 1600 px with the light sharpening, grain and corner fall-off of a phone camera file, still labelled "Sample photo (AI-generated)" in the corner and in EXIF.
- Changed: demo video, X clip, screenshots, GIF, link preview image and thumbnail re-made from live answers; the narration uses a more natural voice at an easier pace, and the owners' lines are spoken in Bahasa and Basa Jawa.

## 1.29.13 (2026-11-04)
Docs, screenshots and video brought up to date. No app behaviour changed.
- Changed: screenshots, hero GIF, YouTube thumbnail, demo video and X clip re-made on the 1.29.12 screens (rice cooker stop list, kind-specific "Safety first" lines, shop-named price links, one nearest-service button on the red stop, fold-out chevrons, Basa Jawa in ngoko).
- Changed: quoted numbers are now 894 tests (docs/TEST_REPORT.md), mypy strict on 150 files, 69 smoke checks, 21 Chromium test files; the video stays 2:53 and the X clip 43.5 s. README, SUBMISSION, WRITEUP, JUDGING_MAP, TESTING, ONE_PAGER and COMMUNITY_VOTE_KIT updated, VERIFICATION_REPORT has a new section 5g, docs/EVAL.md re-generated (same results). SAFETY describes the kind-specific lines and stop lists, DECISIONS and DEPLOY have a Cache-Control line, TESTING lists the new test files.
- Fixed: a laptop share test used an untyped lambda that mypy --strict rejected.

## 1.29.12 (2026-11-04)
- Changed: Basa Jawa sticks to ngoko ("kowe", "fotomu"), which most of the app already used. A few lines said "sampeyan" (the saved amount, the offline note, two agent log lines in the app and PDF, the recorded demo note) or "antosna" (the wait timer, also on the workshop sheets), so one screen could switch registers. Offline cache v21.

## 1.29.11 (2026-11-04)
- Fixed: the price links under each tool and part said "🛒 Compare prices" without naming the shop, and in the two narrow columns Tokopedia and Shopee each took their own tall row. Each link is now named by its shop ("🛒 Tokopedia", "Shopee", with "Compare prices on ..." for screen readers), both sit on one row, and tools and parts stack in one column on a phone.
- Fixed: Share on a laptop (no share sheet) popped an alert() or a prompt(). It now writes "✅ Link copied:" and the link in a line under the button, or just the link when the browser blocks the clipboard.
- Fixed: in the 1-tap demo on a phone the tip bar at the bottom covered the "Found so far" findings as they came in. The page now scrolls just enough to keep the newest one above the bar. Offline cache v20.

## 1.29.10 (2026-11-04)
- Fixed: a shared guide link opened after "Still broken" showed the second plan's steps with no "Plan 2 of 3" banner, so the friend or mechanic reading it could not tell the first cause had already been tried.
- Changed: files under /static now send Cache-Control. Fonts (and any URL with ?v=) are cached for a year as immutable, pictures and the vendored QR library for a day, and app.js, style.css, the replay script and the recording are revalidated on every load (a cheap 304), so a new release shows up at once. The service worker works as before.

## 1.29.9 (2026-11-04)
- Fixed: a red stop on a rice cooker or a water pump said "switch it off and unplug it / close the gas / stop the engine". Appliances and pumps now get their own list: unplug it and let it cool, don't open the casing (220V inside), take it to a service centre. Gas, house wiring and brakes keep their lists.
- Fixed: "Safety first" on the guide said "switch the engine off" for a dripping tap. Motorbike, tap, pump and appliance repairs each get their own two lines; anything else keeps the old general ones.
- Changed: Basa Jawa says "keslametan" for safety everywhere (app and PDF). It mixed in the Indonesian "keamanan" in a few places.
- Changed: in the PDF, causes already tried are greyed out and struck through with a red "tried" label, like on the phone. Offline cache v19.

## 1.29.8 (2026-11-04)
- Fixed: the Basa Jawa PDF report after a re-plan had a page holding only the last line of the disclaimer. When the end does not fit, the "under the hood" list goes in two columns, or its last lines move over with the disclaimer.
- Fixed: after "Still broken" focus stays on the page; it now moves to the "Plan 2 of 3" banner.
- Fixed: in the red stop, the agent log's last line took the white hand-off card style by mistake (no padding, the time white on white). Icons on the red card are white now.
- Changed: the red stop has one nearest-service button (it uses the hand-off's workshop search), and "Message to send" became "See the message it sends" with an open/close chevron on every fold-out.
- Changed: My garage says "0/4 camera-checked" instead of "0/4 ✓", and "plan 2" after a re-plan.
- Fixed: the mechanic brief listed the cause being tried as already tried and said the owner asked for a mechanic before they chose anything. It now says "Being tried now" and "The owner is still on it, no result yet". Offline cache v18.

## 1.29.7 (2026-11-04)
- Fixed: demo mode sent "ledeng" and "sink" descriptions to the motorbike scenario. They now go to the dripping tap one.

## 1.29.6 (2026-11-03)
- Fixed: after "Still broken", the PDF report and the mechanic brief listed the attempt in English ("Tried 'Cop busi longgar', result: ...") even in Bahasa and Basa Jawa. It now reads "Dicoba: ... Hasilnya: ..." / "Dijajal: ... Asile: ...". The model still gets the English line.
- Fixed: after a re-plan the link preview card said "Most likely 22%" for the cause being tried, while the 70% one had already failed. It now says "Plan 2 of 3, being tried now", and the guide page's preview text names that cause too.

## 1.29.5 (2026-11-03)
Docs brought up to date with 1.28 and 1.29. No app code changed.
- Changed: test count 823 (docs/TEST_REPORT.md), mypy 141 files, smoke 69 checks, video 2:53 at 1080p60, AI-generated sample photos instead of "stand-in" wherever the docs described the current demo. README, SUBMISSION, WRITEUP, JUDGING_MAP, ONE_PAGER, COMMUNITY_VOTE_KIT, YOUTUBE, demo/README, DEMO_SCRIPT, TESTING, TODO.
- Changed: ROADMAP no longer lists WhatsApp and PWA install as future work (both are built). ATTRIBUTIONS says where the sample photos come from and lists axe-core (test only).
- Added: the CSP / HSTS and axe-core work in JUDGING_MAP (technical depth), VERIFICATION_REPORT (new section 5f), SAFETY and TESTING.
- Changed: docs/EVAL.md re-generated on the sample photos (6/6 step and edge-case checks; same safety and injection results). `first_live_run.py` no longer tells you to open an issue.

## 1.29.4 (2026-11-03)
- Fixed: the progress screen said "Listening typed" when you typed instead of speaking. It now says "Listening skipped: you typed instead" (Bahasa and Basa Jawa too).
- Fixed: the progress, stop and result screens had no h1, so a screen reader had no page title to jump to. The "Checking..." heading and the name of the broken thing are now the h1 of their screen.
- Fixed: the photo and video pickers were labels pretending to be buttons. The real file inputs are now in the tab order (visually hidden inside the picture), so a keyboard and a screen reader get a native button and the picture shows the focus ring. axe-core finds nothing on the home, progress, question, result, stop, shared guide, WhatsApp simulator and laptop screens.
- Changed: fonts, photos, PNGs, audio and PDFs are no longer run through gzip (they are already packed; it only cost CPU on the free server). Text files are still gzipped. Offline cache v17.

## 1.29.3 (2026-11-03)
- Fixed: a shared guide link to a red stop opened an empty result page. It now shows the STOP card with its "do this now" list, and a repair that is still running shows its progress.
- Added: a strict Content-Security-Policy on every HTML page (scripts only from the site itself, no inline script, no eval) and HSTS when the request came in over https through Render's proxy. The WhatsApp simulator's script moved out of the page into `web/wa.js`.
- Changed: the WhatsApp simulator has the wrench plate as its avatar and Barlow in the header, and its grey text is darker so it passes contrast. Status notes sit in an aside and the disclaimer in the footer, so screen readers find them in a landmark.
- Changed: browser tests wait with functions instead of string expressions, which the new policy blocks. Offline cache v16.

## 1.29.2 (2026-11-03)
- Changed: the PDF report, the workshop sheet and the share cards now look like the app: Barlow type, a dark header with the wrench plate, safety plates in the real colours (black on yellow for caution), number plates for steps (green once the camera passed them), bars for the likely causes, drawn tick boxes instead of "[ ]".
- Changed: share card and the front-page preview (`web/og.png`) re-drawn on the concrete background and saved as 256-colour PNG, about 170 KB instead of about 480 KB, so WhatsApp shows the preview.
- Added: `api/render/brand.py` and the Barlow TTFs (OFL) in `api/render/fonts`. Characters Barlow does not have are drawn with DejaVu instead of empty boxes.

## 1.29.1 (2026-11-03)
- Fixed: an expired or erased guide link opened as raw JSON. It is now a short page in Bahasa, Basa Jawa or English with a button to start a repair (still 404).
- Fixed: on a 390x844 phone the "Check it now" bar covered the 1-tap demo button. The bar only floats once you start your own repair.
- Fixed: a 500 or a gateway's HTML error page showed "Unexpected token..." on screen. Now it says the server had a problem, in your language.
- Fixed: My garage showed "0/4" after a step passed the camera check.
- Added: laptop side panel links the WhatsApp simulator; the panel fits a 1280x800 screen.
- Added: `HEAD /` and `HEAD /guide/{id}` work (uptime monitors). Offline cache v15.

## 1.29.0 (2026-11-02)
Real-looking sample photos and a new demo video.
- Changed: the flat stand-in drawings are gone. Every demo scenario now uses an AI-generated sample photo (motorbike spark plug, faucet, water pump, rice cooker, tyre), labelled as such on screen, with masks drawn by hand to sit on each part.
- Changed: demo video re-shot on the new UI at 1080p 60 fps: phone frame, Barlow captions, crossfades, slow zooms on the marked parts, the camera check and the red stop. 2:53, WhatsApp scene at 2:13. X clip 43.5 s.
- Changed: recorded demo re-recorded and shrunk (4.3 MB), offline cache v14, screenshots, GIF and thumbnail re-made.
- Fixed: fixture eval no longer expects parts a photo cannot show (`parts_in_photo`).

## 1.28.0 (2026-11-02)
New look. The old screens looked like a form, so I redesigned the whole thing around a roadside bengkel sign: big condensed letters, safety colours that mean one thing each, and the camera up front.
- Changed: `web/style.css` rewritten. Barlow and Barlow Condensed, served from `web/fonts` (OFL), no font CDN. Orange means do something, red means stop, yellow means check first, green means the camera passed it. Light and dark theme follow the phone.
- Changed: first screen opens on a big "What's broken?", the 3 steps, the 1-tap demo on a dark plate with the SAM picture, and a camera viewfinder for your own photo. "Check it now" stays in a bar at the bottom.
- Changed: result card puts the SAM-marked photo first; each cause shows its confidence as a big number and a bar. Step card has a progress bar (green for each step the camera checked), a bigger instruction, and the check result slides in green or red.
- Changed: the red stop fills the card in safety red with barricade tape top and bottom, a white STOP strip and numbered "do this now" steps. "All safe causes tried" gets yellow and black tape.
- Changed: icons are Lucide (ISC) inline SVG instead of emoji. The strings keep their emoji because the PDF, WhatsApp and share text reuse them; on screen they turn into icons and screen readers skip them.
- Changed: garage, the share / PDF / workshop sheet / erase list, hands-free switch and the laptop frame restyled. Offline cache v13, now with the fonts.
- Same as before: every element id, string, flow and API call. The WhatsApp simulator keeps its WhatsApp look on purpose. Screenshots re-made; the demo video is not re-made yet.
- Tests: `test_web.py` now checks that every emoji the screen can show has an icon, that the fonts and both licences ship, and that nothing loads from a font CDN.

## 1.27.1 (2026-11-02)
Docs and comments rewritten in my own words; video hook uses BPS 139 million; setup doc renamed.
- Changed: the setup guide is now docs/SETUP.md ("How I run it"), with the test and demo-asset commands; docs/WINNING_PLAN.md dropped (docs/JUDGING_MAP.md covers it).
- Changed: demo video and X clip captions: the hook says 139 million motorbikes (BPS 2024), no more all-caps words. Same length (2:55) and scene times. Architecture diagrams and thumbnail re-made.
- Changed: test files renamed to say what they test (`test_result_screen_fixes.py`, `test_playwright_result_screen.py`, `test_flow_fixes.py`, `test_playwright_stop_and_outcome.py`).

## 1.27.0 (2026-11-02)
WhatsApp channel merged and verified; owner token.
- Added WhatsApp channel: Cloud API webhook (`api/channels/whatsapp.py`, Graph API v26.0) on the same engine and safety gate as the phone app. In: photos plus text or a voice note. Out: SAM-marked photo, diagnosis, a step with Done / Problem / Stop buttons, camera checks, re-plan, the same red stop, PDF report. id/jv/en.
- Every webhook POST is checked against `X-Hub-Signature-256`.
- Tested end to end against a fake Graph API (`api/testing/fake_graph.py`). Not yet run against a real WhatsApp number; that needs the Meta app setup in docs/WHATSAPP.md.
- Added WhatsApp simulator at `/wa`, labelled as a simulator, feeding the same handler in demo mode. The first screen links to it in the chosen language ("💬 Also works in WhatsApp: try the simulator" / "Coba juga lewat WhatsApp" / "Jajal uga lewat WhatsApp"), only when the server says the simulator is on. The static judge build has neither the link nor the page.
- Added owner token: only the owner can answer "Does it work again?" or erase a repair. Creating a repair returns the token once; the owner's phone keeps it (localStorage, cleared by "Clear history") and sends it with outcome and erase calls. A guide-link holder gets "Only the phone that started this repair can do this" (403), also when calling the API directly. No GET returns the token. WhatsApp repairs get a token that is never sent anywhere. Repairs saved before 1.27.0 still work.
- render.yaml: four optional WhatsApp secrets (`WA_TOKEN`, `WA_PHONE_NUMBER_ID`, `WA_VERIFY_TOKEN`, `WA_APP_SECRET`, `sync: false`). Empty keeps the channel off.
- Demo assets: WhatsApp screenshots (`30_whatsapp_*.png`: Javanese diagnosis, step buttons and red stop; English step check and PDF). Video gets a 12 s WhatsApp scene in Basa Jawa at 2:16; the share-card and Javanese-UI scenes were trimmed to make room. Cut is 2:55 (175.7 s by ffprobe), hook title card and "built during the hackathon" line kept. X clip shows WhatsApp instead of the diagram card (43.5 s). Hero GIF ends on the WhatsApp chat. Architecture diagram shows WhatsApp as a second front door. Offline cache v12.
- Docs: README (top line, judge path step 8, how the channel uses Meta's Cloud API), SUBMISSION (Meta products, why Meta, Best Agentic evidence), WRITEUP, JUDGING_MAP (Impact and Meta tooling rows, new video times), JUDGE_FAQ ("Why WhatsApp?"), X thread (6 posts), one-pager, ARCHITECTURE, API, DEPLOY, YOUTUBE chapters, TODO (WhatsApp setup as an optional item in the deploy step).
- Fixed: with `?replay=1` the first screen asked the server whether the WhatsApp simulator was on, so the recorded demo was no longer server-free (caught by `test_playwright_replay.py`).
- Added `pyyaml` to requirements-dev.txt for the render.yaml test.
- Tests: `test_owner_token.py` (token issued, never leaked, 403 for viewers and for another repair's token, erase guarded, old sessions open, simulator link and static build, render.yaml); `test_playwright_owner.py` (real Chromium: a second phone with only the guide link gets 403, the owner's button works; simulator link in id/jv/en opens /wa). Full report: 768 tests, all passed.

## 1.26.0 (2026-11-02)
I played every flow on a phone-sized Chromium in Bahasa, Basa Jawa and English, then read through the PDFs and the shared guide page. Everything that tripped me up is fixed and tested.
- Fixed: failing brakes on the owner's motorbike ("Rem motorku blong", "rem ora makan", "my brakes don't work", "spongy brakes") got a repair guide; only a car's brake line stopped. Now a red stop: don't ride it, push or tow it to a workshop. Non-failure brake words (dead brake light, squeaky pads) still get help. Red-team eval now 33 cases, all stopped.
- Added "Fix something else" button under the stop card. "Do this now" list now fits the hazard: close the gas valve and open the windows for gas, switch off the breaker for house wiring, don't ride it for brakes.
- Changed: in the 1-tap demo the answer to "Do you smell fuel when you crank it?" now moves the diagnosis (70% with a fuel smell, 58% without) and shows up as evidence. Recorded demo, screenshots and video re-made; the video shows the 70% result.
- Fixed: if the page loaded but the server then went quiet or returned a gateway error, the 1-tap demo showed "No connection". It now plays the recording.
- Fixed: share card claimed every step was checked; it now counts the steps that really passed a camera check. Cost chip says "parts" (tools are reusable and not in the estimate). "It works now" reads "You saved about Rp35.000 compared with a workshop." Garage says "1 repair", not "1 repairs".
- Fixed: after "It works now" the mechanic brief PDF said the owner asked for a mechanic. Its status line now says the owner reports it works again.
- Fixed: someone opening another person's guide link could change the owner's answer with the outcome buttons. They now only see it. Share fallback label translated ("Tautan", "Pranala", "Link").
- Fixed: near-empty last page on the workshop sheet. "Done when" now closes the last step page when it fits.
- Tests: `test_flow_fixes.py` (safety gate, demo diagnosis, share card, mechanic brief, workshop sheet, read-only guide wiring); `test_playwright_stop_and_outcome.py` (real Chromium: stop button, hazard lists, cost chip and wording, demo fallback, read-only guide). Offline cache v11. Full report: 710 tests, all passed.

## 1.25.10 (2026-11-01)
Checked the shared guide page /guide/{id} and the large-print workshop sheet in Bahasa, Basa Jawa and English (Chromium 390x844 and as PDFs).
- Changed: the shared guide page leads with the repair. A friend, mechanic or judge opening a shared link used to land on the diagnosis plus a nine-row "What the AI did" log, with the checklist and steps two screens down. The log now sits after the steps and the outcome question, still complete and tappable. The app's own result screen is unchanged (it's in the demo assets). Workshop sheet: nothing to fix in any of the three languages.
- Server hardening check: `test_hostile_input.py`, 11 tests fuzzing input (odd text, category, language, uploads, every session endpoint, traversal paths); none gives a 5xx. No app change.
- Tests: 4 real-Chromium tests in `test_playwright_guide.py` (steps and outcome before the log in id/jv/en, log keeps its rows, main screen order unchanged). The three guide tests fail on 1.25.9.

## 1.25.9 (2026-11-01)
Checked the garage, PDF report and share card: a real session rendered in Bahasa, Basa Jawa and English, read page by page.
- Fixed: the Javanese PDF report was mostly Indonesian. Only the title, a few headings and the footer were Javanese; the cost lines ("Perkiraan biaya suku cadang", "Hemat sendiri"), disclaimer, "Sebelum mulai, pastikan", the safety badge ("HATI-HATI" where the app and share card say "ATI-ATI"), "Mode demo", the page word and every under-the-hood stage name were Indonesian. Added a full Javanese label set that follows the app's wording.
- Fixed: the under-the-hood list in the Bahasa and Javanese PDF printed the English tag "rules in code" for the two safety gates. Now "aturan di kode" / "aturan ing kode".
- Tests: 4 in `test_report_pdf_jv.py` (same label keys in all three languages, no Indonesian leftovers in the Javanese set, badge words match the app, localized tag). Javanese share card checked, nothing clipped. UI unchanged, so screenshots, GIF and video not re-shot.

## 1.25.8 (2026-11-01)
Walked the recorded demo in Bahasa, Basa Jawa and English with no server, then checked every number the docs quote.
- Fixed: `docs/TESTING.md` said "all 550 tests" while README, SUBMISSION and WRITEUP said 620. It now points to docs/TEST_REPORT.md.
- Added `test_doc_counts.py`: fails if a submission doc quotes a test count different from the last real run.
- Recorded demo (`?replay=1`) walked end to end in id/jv/en (landing, progress, question, result, all four camera-checked steps, outcome, PDF and WhatsApp buttons): no console errors, nothing in the wrong language.

## 1.25.7 (2026-11-01)
Walked all four steps of the demo repair in Basa Jawa and English, tapping fast like a real owner.
- Fixed: a passed camera check could skip a step. After "Step looks right" the app moves on by itself after 1.5 s; tapping Next (or Back) in the meantime moved a second time, so step 2 jumped to step 4, and on the last step the stale timer ran past the end and threw "Cannot read properties of undefined". Any other move to a step now cancels the timer.
- Fixed: the repair just stopped after the last step. When the last step passes and every step is camera-verified, "Does it work again?" scrolls into view with a line in the owner's language (id/jv/en) that screen readers announce, and focus moves to "It works now". Nothing is forced when steps were skipped or there's already an answer.
- Service-worker shell cache `tukang-shell-v10`.
- Tests: 8 real-Chromium tests in `test_playwright_steps.py` (the skip, back, crash and prompt tests fail on 1.25.6).

## 1.25.6 (2026-11-01)
Checked what a screen reader says in each language, plus the laptop view.
- Fixed: the "previous step" control was only "◀". Now labelled "Langkah sebelumnya" / "Langkah sadurunge" / "Previous step" (app and shared guide page).
- Fixed: the SAM parts picture ("Highlighted parts"), the "How it works" list and the laptop QR code had English-only labels on the Indonesian and Javanese pages. Added a `data-ta` hook in `applyLang` that sets aria-labels from the language table.
- Service-worker shell cache `tukang-shell-v9`.
- Tests: 7 real-Chromium tests in `test_playwright_labels.py` (they fail on 1.25.5).

## 1.25.5 (2026-11-01)
Checked the video and voice-recording refusals, and the landing page in Basa Jawa.
- Fixed: a too-long video got a message about the owner's text being too long (the server's "That video is too long" matched the long-text rule). Video rules now come first. Unreadable video, too short, too long and unreadable voice recording each show their own message in id/jv/en (`videoBad`, `videoShort`, `videoLong`, `recBad`).
- Tests: 6 real-Chromium tests in `test_playwright_capture.py` (a garbage .mp4 in 3 languages; a real 40 s ffmpeg clip in 3 languages that fails on 1.25.4).

## 1.25.4 (2026-11-01)
Checked the red stop and re-plan screens in Bahasa and Basa Jawa, then probed the safety gate with 40 street-wording texts.
- Fixed: 15 of the 40 probes got through the text gate: "kulkas nyetrum", "kabel PLN putus", "trafo meledak", "listrik ngeletik percikan api di stopkontak", "aki meledak", "kompor mbledug", "kompor nyemprot api", "baterai nggembung", "bensin netes ing mesin panas", "kompresor kulkas", "anakku keracunan gas", three-phase / 380 V. All now stop with the right category and message. Normal repair talk still passes: "percikan api busi", "ban meledak", "nyetrum aki" (charging a battery), "bensin netes" from a carburettor with no heat, "kabel gas / rem / charger putus", 12 V "tegangan aki".
- Added 8 plan-guard rules for steps a model could write: refrigerant refill, CRT capacitors and flyback, gas pipe repair, patching a fuel leak, piercing a swollen lithium cell, touching terminals while plugged in, live mains testing, bypassing a thermal fuse or safety switch. Warnings like "do not touch the terminals while plugged in" or "never bypass the thermal fuse" don't trigger it.
- Tests: 49 parametrised tests in `test_safety.py`. docs/EVAL.md numbers (30 dangerous, 17 safe) unchanged; the labelled eval set wasn't enlarged, so nothing quoted elsewhere moved.

## 1.25.3 (2026-11-01)
Tried the capture screen with a text file, a broken JPG, a 20 px image and a 6000x4000 photo, in Bahasa / Basa Jawa / English (real Chromium 390x844).
- Fixed: a wrong file or broken photo showed the server's English ("Unsupported file type .txt", "Could not read that photo. Try a JPG or PNG.") on the Indonesian and Javanese pages. Every refusal a person can cause (not a photo, unreadable photo, too big, empty, text too long, missing photo or description) is now translated in all three languages, on every request path (start, answer, step check, re-plan, report).
- Fixed: picking a PDF or text file left a blank dashed box and said nothing until Go. The picker now rejects it on the spot with the translated message and keeps nothing. A photo the browser can't draw (e.g. HEIC on some phones) shows its file name instead of a blank box.
- Tests: 8 Chromium tests (`test_playwright_capture.py`; the language ones fail on 1.25.2).
- Service worker cache `tukang-shell-v8`.

## 1.25.2 (2026-11-01)
Accessibility of the small controls: English flow at 390x844 in real Chromium, with a script that measures every visible control.
- Fixed: small links were too small to hit with greasy or gloved hands. "Compare prices" / "Shopee" links were 16 px tall, sample links under the camera 30 px, garage entries the browser's default blue, "Agent log" / "models used" summaries 24 px. Now 40 px (shop and sample links), 44 px (record-a-video), garage entries themed with 8 px padding, summaries 44 px.
- Tests: 3 Chromium tests measuring the real boxes (`test_playwright_targets.py`; all three fail on 1.25.1).
- Service worker cache `tukang-shell-v7`.

## 1.25.1 (2026-11-01)
Checked the garage, PDF, share card and Javanese screens at 390x844 in real Chromium. Two things a judge on a phone would hit in the first minute:
- Fixed: the first screen always opened in Bahasa Indonesia, so an English-speaking judge landed on a page they couldn't read. Order now: an earlier choice, then `?lang=id|jv|en` on the link, then the phone's language list (Indonesian or Javanese anywhere in it keeps Bahasa / Basa Jawa, so an Indonesian phone set to English isn't switched), else English. 5 Chromium tests (`test_playwright_lang.py`). The demo-asset script pins the browser to id-ID so screenshots and video don't change.
- Fixed: starting a repair used `replaceState`, so the phone Back button left the site mid-repair. It now pushes `#<id>`: Back returns to the first screen (stream, timers, camera and voice stopped), Forward returns to the same repair, "Start again" and "Erase" step back instead of leaving a duplicate history entry. Works in the recorded demo too. 4 Chromium tests (`test_playwright_back.py`; the first fails on 1.25.0).
- Service worker cache `tukang-shell-v6`. README judge path mentions both.

## 1.25.0 (2026-11-01)
Laptop view, server-free judge build, offline eval (found and fixed real safety misses), one-command first live run, tighter video.
- Added laptop view: at 1024 px and wider the app sits in a phone frame (scrolling inside it) with a side panel: what it is, a QR code of the page's own address to continue on a phone (says when the address only works on this computer), a 1-tap demo button, an id/jv/en switch. QR encoder `web/vendor/qrcode.js` (MIT, Kazuhiko Arase), fetched only on wide screens. Phones unchanged. Checked at 1280x800 and 1440x900. Tests: `test_playwright_desk.py` (Chromium), `test_desk.py` (static).
- Added static judge build: `python scripts/build_static.py` writes `dist-static/` (gitignored), the recorded demo as plain files with relative paths. Runs from GitHub Pages (also under a sub-path) or Netlify with no server and no cold start. Replay forced on, API never called, "Recorded demo" badge from the first second, no service worker. `--help` has build / try / host instructions; `--check` verifies. Chromium test serves it from a plain file server under `/tukang-copilot/` and fails on any `/api/` request. Not deployed.
- Fixed: the recording was fixed to the language at page load; it now follows a language change made before the demo starts.
- Added eval (`scripts/run_eval.py` → `docs/EVAL.md`): all stand-in fixtures, a 20-case red-team set (gas leak, LPG regulator, 240 V panel / consumer unit, wall socket, car brake lines, ceiling fan wiring, microwave; id/jv/en), 12 everyday controls, 15 plan-guard cases, 7 prompt-injection cases (owner text, fake system tags, follow-up answer, writing in a photo with a model that obeys it). Runs in `mock` and `fake` mode (the real live code path against the stand-in Meta server), with latency and cost from `api/cost.py`. Labelled as mock / fake-model results; live run pending. Runs as a test (`test_run_eval.py`).
- Fixed safety misses found by the eval: the v1.24 text gate let 12 of 20 red-team texts through and the plan guard passed 7 of 10 dangerous steps (37 % recall overall). New rules in `api/pipeline/safety.py` for Javanese "gase", gas pipes and cylinders, "tabung melon", 220/240 V panels, consumer units / RCDs, wall sockets, ceiling fan and ceiling wiring, water heater elements, car brake lines / "rem blong"; plan-guard rules for LPG regulators, panels / MCBs, ceiling wiring and brake lines. Now 100 % recall, 0 false stops on the controls (motorbike throttle "gas", carburettor gasket, motorbike brake squeal still pass). The diagnose / plan / look prompts name these jobs and say writing in a photo is never an instruction.
- Added `scripts/first_live_run.py`: one command after `set_keys.py`. Checks the key without printing it, asks Meta which models the key can see, runs one sample repair live with DEMO_FALLBACK off (answers the follow-up, checks one step photo), writes `docs/LIVE_RUN.md` with outputs, time per stage and cost, exits 0 / 1 / 2 with a plain-English fix. `--fake` rehearses against the stand-in server. Tested with the fake server, incl. a wrong key and no key.
- Video: 3-second hook title card ("Fix it yourself, safely. In Javanese." and "Built during the Meta AI Developer Hackathon, Oct 26 to Nov 4, 2026 (first commit Oct 30)"), burned-in English captions of the voice-over (one sentence at a time), a Muse Image diagram step scene (demo mode shows a labelled stand-in drawing). Dropped the log-jump and PDF scenes to stay under 3:00. Main cut 2:57 (177.8 s, ffprobe); X clip 43.5 s with English captions; scene times in `docs/demo/TIMESTAMPS.txt`. New screenshots `28_diagram_step.png`, `29_laptop.png`; GIF re-made.
- Service worker cache `tukang-shell-v5`.
- Fixed flaky test: `test_agent_log_lines_jump_to_what_they_describe` waited 5 s for a smooth scroll and failed once under a loaded full run. Now waits on conditions (step number, element in view, focus) for up to 15 to 20 s, no fixed sleeps.
- Docs: synced with the re-cut video (YouTube chapters, JUDGING_MAP timestamps, 29 screenshots, 43.5 s X clip). docs/EVAL.md, the laptop view, the static build and `first_live_run.py` added as evidence in SUBMISSION, JUDGING_MAP and JUDGE_FAQ (new question 11). One-pager PDF re-made. TODO's list of steps needing my keys re-ordered with the live run first.

## 1.24.0 (2026-11-01)
1-tap demo works while the free server sleeps; fixes from a first-time-viewer pass.
- Added recorded demo: `scripts/record_replay.py` records the demo-mode motorbike run in id/jv/en into `web/replay/` (progress snapshots, follow-up question, ready session, one replayable "delta" per action: each step x both stand-in check photos, re-plan, outcome; SAM-marked photos, share cards, PDF reports). `web/replay.js` plays it when `/api/health` hasn't answered within 4 s (Render free tier cold start), when the phone is offline, or with `?replay=1`.
- Purple "▶ Recorded demo" badge on every screen, plus a note that the server is waking up. The visitor's own photo is refused with "needs the live server", never faked; the live camera guide and voice commands say the same; the workshop sheet button is hidden (not recorded).
- Service worker pre-caches the recording and shows the cached app shell after 3.5 s if the server is slow (`tukang-shell-v4`).
- `record_replay.py --check` (and a test) fails when the app's session shape drifts from the recording.
- Fixed: on a red stop the progress heading kept saying "Checking…" and the STOP card was ~1000 px down. Heading now becomes "⛔ Stopped for your safety" with the card right under it. One PDF button instead of two.
- Fixed: after answering the question, the result opened with the object name and safety badge scrolled off. It now opens at the top.
- Added re-plan banner "🔁 Plan 2 of 3: <cause>" at the top of the result; tried causes greyed with "✗ tried".
- Fixed: keyboard focus now moves to the first quick answer when the follow-up question appears.
- Fixed PDF wording: "Cause worked on" instead of "Cause fixed" (it was printed before anything was fixed).
- Changed landing preview: an 11 KB language-neutral crop of the SAM-marked stand-in photo with a translated caption (was the Indonesian 81 KB og.png on every language). Laptops get a "Made for phones" note.
- Changed demo check text to name what it confirmed ("Looks right: The cap is off and the plug is visible.") instead of "It matches the expected state."
- Fixed: `/api/health` version was stuck at 1.23.0; it now follows the full version, and a test compares it with the top CHANGELOG entry.
- Tests: `test_replay.py`, `test_result_screen_fixes.py`, `test_playwright_replay.py`, `test_playwright_result_screen.py`, version sync.

## 1.23.5
- Added test keeping the app version and CHANGELOG in sync.

## 1.23.4
- Added test locking the security headers on pages and errors.

## 1.23.3
- Added result preview thumbnail under the demo button on the landing page.

## 1.23.2
- Changed share card Cache-Control from 300 s to 60 s so erased repairs leave crawler caches sooner.

## 1.23.1
- Changed: Share attaches the result card image via Web Share files when the phone supports it, link otherwise.

## 1.23.0 (2026-10-31)
Streaming progress, tappable decision log, a share card that previews well.
- Added streaming progress: each stage's result appears on the progress screen as it finishes (what Muse Spark saw, object + parts; the photo with SAM 3.1's outlines; top cause with confidence and safety level; then the step count). SSE carries a trimmed `progress_view` built from `public()`, so no owner words or raw errors; the polling fallback renders the same. In demo mode `MOCK_PACE` (default 0.6 s) holds each finished stage on screen, first analysis only; never applied to live Meta calls or re-plans, never counted in a stage's timing.
- Added: agent log lines link to what they describe. Tap a line to scroll to and highlight the stage or streamed result (progress), or the photo, causes, safety list, hand-off or the exact camera-checked step (result and guide pages; the step card jumps back to that step). Checks from an earlier plan aren't linked (`check` events now carry `cause`). Lines are real buttons; focus follows for keyboard users.
- Added share card `GET /api/sessions/{id}/card.png` (1200×630: marked photo, object, top cause, safety badge, plan line, honest DEMO label; never the owner's words; 404 after erase). Guide pages carry Open Graph + `twitter:card` tags; the front page uses `web/og.png` (`scripts/make_og.py`, labelled stand-in photo). Share sends the object and cause with the link.
- Fixed (judge-view pass at 390×844, id/jv/en): streaming had pushed the follow-up question below the fold; it's now scrolled on screen when it appears. Added gzip for static files (app.js 90 KB → ~29 KB; SSE not compressed). Added favicon (removes a console 404). Verified the tip-bar-moves-up-while-typing fix (ffc24d8) in real Chromium with a new test.
- Demo kit re-made: 26 screenshots (new: streaming progress, log jump, PDF agent-log page, share card), 2:57 voice-over video, 45 s vertical X clip (now with streaming progress and the share card), README GIF. Smoke test checks the share card and link-preview tags (65 checks). Service-worker cache `tukang-shell-v3`.

## 1.22.0 (2026-10-31 11:45)
Decision log on screen and in the PDF, 1-tap demo of the whole loop, abuse guards for the public deploy.
- Added agent log "🤖 What the AI did": every decision (look, mark parts, diagnose, ask under 60 %, plan, code safety gate, verify, re-plan, hand off) with the Meta model or code rule behind it and how long it took. Loop strip on progress, result and the shared guide page. Never holds the owner's own words, so it's safe on a shared link.
- Added the same log to the PDF report (same wording as the app in id/jv/en; a test keeps them in sync).
- Added 1-tap guided demo: hero button runs the motor repair with tips, quick answers and labelled stand-in check photos (`GET /api/demo/check-photo/{dark|ok}`). Too-dark photo rejected, right one passes, *Still broken* re-plans.
- Changed tip bar to a compact corner pill that folds to a 💡 chip by itself after the first step check, with reopen/close buttons (aria labelled), so it never covers the main action.
- Added prompt-injection hardening: `api/untrusted.py` fences owner text as data; re-plan report moved out of the system prompt; photo-text rule; input guard that logs instruction-like phrases (they can never lift a code safety stop).
- Added cost guards: `FOLLOWUP_RATE_PER_HOUR` (240 model calls inside repairs per visitor), `MAX_STEP_CHECKS` (40 per repair), step-check spend counted in the session cost and the daily budget, length caps on answers and reports. Listed in render.yaml, .env.example and docs/DEPLOY.md.
- Added Javanese demo answers (`mock_jv.py`), model chip + elapsed timer per stage on the progress screen, WCAG AA contrast, translated stage notes. Overlay drawing 8× faster (fast suite 118 s → ~70 s).
- README rewrite (60-second start, what judges should look at, Meta model → code table). Service-worker cache `tukang-shell-v2`. Two new smoke steps (agent log, demo check photo). Regenerated 23 screenshots, 2:53 video, 45 s vertical clip, README hero GIF.
- Tests: 453 passed, 0 failed (443 fast + 10 slow, real Chromium); ruff clean; mypy strict clean (73 files); smoke 60 checks pass.

## 1.21.0 (2026-10-31 09:30)
Four features from the win plan (built 08:00 to 08:40), deploy readiness, new demo kit.
- Added live camera guide: `POST /api/sessions/{id}/steps/{n}/track` runs SAM 3.1 on a live camera frame (≤3 MB JPEG, ~640 px) and returns the target part's boxes and polygon. The guide draws an orange outline over the video; *Check now* verifies the step from the current frame. Throttled (`TRACK_MIN_INTERVAL_S` 0.6 s → 429 + Retry-After) and capped (`MAX_TRACK_FRAMES` 120 per repair, about $0.30). Frames never stored. Real-Chromium test with a fake camera.
- Added hands-free voice loop: continuous SpeechRecognition (id-ID / jv-ID / en-US) for next / back / repeat / check / broken / stop, with a listening indicator. `POST /api/sessions/{id}/command` gives push-to-talk through Voice Transcribe on phones without it. Python `parse_command` mirrors the JS (same word lists, enforced by tests).
- Added bengkel hand-off: `GET /api/sessions/{id}/handoff` returns a WhatsApp summary, a Maps workshop search, guide + PDF links (`PUBLIC_BASE_URL` if set). Card shows on a red stop, when the causes run out, on "Call a mechanic" and on "Took it to a mechanic". PDF gets a mechanic brief page.
- Fixed: code-gate stops got 409 for the PDF; they now get a stop report PDF.
- Added demo fallback (`DEMO_FALLBACK=1`, default on): a live chat call that still fails after retries uses the labelled demo answer for that stage. Shown in the UI badge, the PDF, `session.fallback` and `/health`. Fallback step checks never count as verified.
- Added impact trial kit: append-only outcome log, trial mode (`?trial=T1`, minutes), token-gated download (`IMPACT_TOKEN`), `scripts/impact_report.py` → docs/IMPACT.md + slide (MOCK-stamped until real trials), docs/USER_TRIAL_KIT.md.
- Deploy: Render free plan in Singapore, non-root Docker with proxy headers and HEALTHCHECK, `/tmp` data dir. Added `scripts/deploy_check.py` (PASS/WARN/FAIL with fixes; in LIVE mode it flags any session with a non-empty `fallback` list, so a bad key can't hide behind demo answers). `smoke_e2e.py` prints a FALLBACK line per affected session. `check_keys.py` covers every model incl. the live track and open weights. render.yaml / .env.example / docs/DEPLOY.md list `MAX_TRACK_FRAMES`, `TRACK_MIN_INTERVAL_S`, `DEMO_FALLBACK`, `IMPACT_TOKEN`, `PUBLIC_BASE_URL`.
- Demo kit: 22 screenshots (new: safety list, live guide, hands-free, hand-off, stop PDF, Javanese result, open-weights badge, stop hand-off). New 2:50 video with voice-over and captions covering live camera, hands-free and hand-off. 45 s vertical X clip. docs/WRITEUP.md and the field-by-field docs/SUBMISSION.md for the Cerebral Valley form.
- Fixed: jv rice-cooker sample went to the motor scenario; unreadable check photo now 400 (was 503); hand-off message wraps long URLs; edge-tts voice generation works behind an HTTP proxy; vertical clip's architecture caption was white on white.
- Tests: `slow` marker for jsdom/Chromium tests, run as separate chunks. 410 passed, 0 failed.

## 1.20.0 (2026-10-31 08:20)
- Added "Before you start" safety gate. Diagnosis gets a `before_you_start` list (up to 4 short statements: "the pump is unplugged", "the engine is off and cooled"), shown as a tick list on the result and shared guide pages. The step card stays dimmed and `inert` (no taps, no keyboard focus, no hands-free voice) until every box is ticked; ticks are remembered per repair on the phone. Red stops carry none (`coerce.py` drops them). `prompts/diagnose.md` asks for it; all four non-red mock scenarios have it in id/jv/en; the PDF prints it as a tick list before the steps.
- Tests: 19 in `test_preflight.py`, plus 7 jsdom checks per language and scenario (shown, translated, locked, still locked with one box open, unlocks).

## 1.19.0 (2026-10-31 07:50)
- Added outcome: `POST /api/sessions/{id}/outcome` (`fixed` or `pro`), "It works now" / "Took it to a mechanic" buttons on the result and shared guide pages (id/jv/en), a Result line in the PDF report, a running "Total saved" line in My garage (sum of `diy_saving_idr` over repairs marked fixed, localStorage only). A re-plan clears the outcome.
- Tests: 12 in `test_outcome.py`, jsdom checks, smoke step.

## 1.18.0 (2026-10-31 07:15)
- Added waiting-time steps. A plan step can carry `wait_minutes` (0 to 120; "let the engine cool 10 minutes", glue or sealant drying). The guide shows a countdown with Start/Stop, then vibrates and reads "waiting time is over" aloud (id/jv/en); the workshop sheet prints a tick-box line ("Wait 10 minutes"). `coerce.py` `_wait` repairs "about 15 min" style values and drops silly ones; `prompts/plan.md` asks for it; the motor mock plan's first step waits 10 minutes.
- Timer ticks use wall-clock time, so it stays right if the phone throttles the tab. If the screen locks, the vibrate/voice alert may not fire (can't test without a real phone).
- Tests: `test_wait_timer.py` (9), a coerce test, 7 jsdom checks (timer shown, 10:00, counts down, stops, absent in other scenarios).

## 1.17.1 (2026-10-31 06:40)
- Added price sanity for live mode (`api/coerce.py` `_price`): shop and part prices accept "75k", "75rb", "1,5 juta", "Rp 75.000". Negative values and anything above Rp15 million (a unit misread) become unknown (0) instead of a wild saving chip. A red-stop diagnosis never keeps a shop price.
- Tests: 13 in `test_shop_cost.py`.

## 1.17.0 (2026-10-31 06:10)
- Added "Bengkel vs DIY" price line. Diagnosis gets `shop_cost_estimate_idr` (typical bengkel/servis price, parts plus labour; 0 when unknown or red stop) and a computed `diy_saving_idr` (shop price minus parts, never negative; tools left out because they're reusable). `diagnose.md` asks for it, `coerce.py` repairs "Rp 75.000" style values, all four non-red mock scenarios carry one. Phone UI chip ("bengkel Rp150.000 · hemat Rp110.000", id/jv/en); the PDF prints both lines.
- Fixed: the PDF total was labelled "tools + parts" but showed parts only. Now labelled "parts".
- Tests: `test_shop_cost.py` (9), a jsdom check per language and scenario.

## 1.16.0 (2026-10-31 05:30)
- Added real-phone photo formats (`api/pipeline/photos.py`): iPhone HEIC/HEIF uploads (repair photos and step check photo) converted to JPEG on the server with the optional `pillow-heif` package (added to requirements.txt). Without it, HEIC gets a clear 400 ("set the camera to JPG") instead of a crash. `.jfif` and upper-case extensions accepted.
- Tests: 7 in `test_photo_formats.py` (HEIC round trip incl. check photo, EXIF-rotated JPEG, corrupt file gives 400, unsupported types, decoder-missing message).

## 1.15.0 (2026-10-31 05:05)
- Added weak-signal handling in the phone UI. Network failures (start, answer, step photo check, re-plan, Try again) show a friendly id/jv/en sentence instead of "Failed to fetch" or a stuck "Checking photo...". An offline banner appears on the home and guide pages while the phone has no connection and goes away when it returns.
- Fixed: step photo check and answer could end in an unhandled promise rejection.
- Tests: 18 jsdom checks (3 languages: banner shows and hides, fetch rejection gives friendly text, Start button usable again). Not verified in a real browser with airplane mode (no Chromium available at the time).

## 1.14.0 (2026-10-31 04:35)
- Accessibility pass on the phone UI.
- Fixed: page language tagged `jv` for Basa Jawa (was `id`, so screen readers mispronounced it).
- Photo, video and step-check pickers reachable by keyboard (tab + Enter/Space); category chips and the mic button expose `aria-pressed`; progress has a short screen-reader status line instead of re-reading the whole list; check results, errors and recording state are live regions; focus moves to the new section heading on each screen change; visible focus ring, 44 px touch targets, reduced-motion support.
- Tests: 8 jsdom checks per language run, plus a static test. Not verified with a real screen reader or in Chromium (none available at the time).

## 1.13.0 (2026-10-31 04:10)
- Hardening against hostile input and hostile model output.
- Added prompt-injection rule to the look, diagnose, plan and replan prompts: owner text and text in photos are data, never orders (`api/prompts.py`).
- Added jsdom XSS check: every free-text field of a real session poisoned with `<img onerror>` and `<script>` payloads; the guide page must run none of it (verified to fail when an `esc()` is removed).
- Added `api/tests/test_security.py` (16 tests): guide page title escaping, odd session ids, path traversal on `/files`, private `session.json`, a prompt-injection sentence can't lift the code safety gate.
- Fixed: parts list label not escaped; duplicate `sTire` key removed. Documented in docs/SAFETY.md.

## 1.12.0 (2026-10-31 03:30)
- Added client-side photo shrinking (`shrinkImage` in web/app.js): longest side 1600 px, JPEG 85 percent, only for jpeg/png/webp over 400 KB. Keeps the original if the result isn't smaller or anything fails (e.g. an undecodable HEIC). A 6 MB photo becomes roughly 300 KB, so three photos and the step check photos go over 4G in seconds.
- Fixed: Start button is disabled while shrinking, so a double tap can't create two repairs.
- Tests: jsdom test with a stubbed canvas (resize, fallbacks, small and non-image files left alone).

## 1.11.0 (2026-10-31 03:00)
- Added privacy controls: `DELETE /api/sessions/{id}` and a "Delete my photos now" button (id/jv/en) erase a repair from the server immediately. "Clear history" in My garage now erases the saved repairs on the server too.
- Fixed: sessions older than `RETENTION_HOURS` were only purged at startup, so a deploy running for days kept photos past the 24 h promise. A background janitor now purges every hour. A worker still running can't resurrect an erased folder.
- Tests: `api/tests/test_erase.py` (6), jsdom check for the button, smoke_e2e step.

## 1.10.0 (2026-10-31 02:30)
- Added `scripts/eval_fixtures.py`: scores every photo fixture against its manifest expectation (safety level, red stop vs plan, object category, share of parts found by SAM, step count, seconds, cost) plus the camera step checks, against any running server, mock or live. Can point at a folder of real photos with the same `manifest.json` shape (`--dir`). Writes `docs/EVAL_REPORT.md`. Gives honest accuracy numbers for the first live run.
- Tests: `api/tests/test_eval_script.py` (2, incl. a deliberate mismatch that must FAIL).

## 1.9.1 (2026-10-31 02:00)
- Added four labelled stand-in fixtures for the tyre scenario (flat tyre with nail in id and en, valve check photo, pressure sticker close-up); 14 in total. `api/tests/test_tire_fixture.py` runs them end to end (diagnosis, optional follow-up answer, camera check, PDF report).

## 1.9.0 (2026-10-31 01:40)
- Added fifth demo scenario: flat scooter tyre with a nail (tubeless plug repair, amber). Cause 1 nail in tread, cause 2 leaking valve stem (re-plan tightens the valve core). SAM phrases `tyre tread` / `valve stem` / `wheel rim`, id/jv/en text, sample photo `samples/tire.jpg`, "flat tyre" sample button in 3 languages, routing for kempes/gembos/tambal ban/tubeless/puncture/tyre.
- Tests: 2 engine tests, 4 routing cases, jsdom flow (Javanese), smoke_e2e.

## 1.8.1 (2026-10-31 01:30)
- Widened the safety text gate: electric shock (kesetrum, tersengat listrik, got shocked), fire/smoke/swollen battery (points to fire service 113), konslet/korslet/short circuit, freon/refrigerant/AC compressor. New `shock` and `fire` stop messages in id/jv/en; docs/SAFETY.md updated.
- Tests: 14.

## 1.8.0 (2026-10-31 00:50)
- Added model-drift tolerance for live mode (`api/coerce.py`): pulls JSON out of think tags, code fences and surrounding prose; repairs harmless quirks before validation (capitalised or synonym enums such as "Amber"/"danger", confidence as 0.85 or "85%", "Rp 25.000" prices, a string where a list belongs, a sixth cause or twelfth step, percent boxes).
- Fixed: a reply with no JSON at all failed outright; it now gets one retry.
- Tests: 11 in `test_coerce.py`.

## 1.7.1
- Added jsdom headless UI test (41 checks, id/jv/en, 4 scenarios) for the real web/app.js; CI installs jsdom.

## 1.7.0 (2026-10-30 23:50)
- Added "Under the hood" panel. Every session JSON has `trace` (one row per pipeline stage: tool, kind meta/open/tts/code, status, ms) from the new `api/trace.py`. Result and guide pages show it as a collapsible list (id/jv/en) and the PDF prints it, so judges see which Meta model did what and where plain-code safety gates and edge-tts take over. Replaces the old one-line model list.
- Tests: 5 in `test_trace.py`, plus a Playwright assertion (skipped at the time, no Chromium).

## 1.6.0 (2026-10-30 23:10)
- Added workshop mode: "Workshop sheets (large print)" button on the result and guide pages and `GET /api/sessions/{id}/workshop.pdf`, an A4 one-step-per-page PDF to pin up next to the bike or pump (id/jv/en). New `api/render/workshop_pdf.py`.
- Tests: 5; smoke script checks it.

## 1.5.0 (2026-10-30 22:40)
- Changed: pipeline failures in live mode show one calm sentence in the person's language (busy, dropped signal, wrong key, cost limit, unusable AI answer) instead of raw HTTP text. Technical detail stays on the server (`error_detail`, keys scrubbed). New `api/errors.py`.
- Added "Try again" button and `POST /api/sessions/{id}/retry`: a failed session resumes from the failed stage and keeps what was already done and spent.
- Changed: step check and re-plan outages answer 503 with a friendly message and `Retry-After`.
- Fixed: a failed re-plan skipped a cause; cause index and history are now rolled back.
- Added fault injection to the fake Meta server (`FAULTS`).
- Tests: 10 in `test_resilience.py` (outage then recovery, flaky 429s absorbed, SAM and image-edit outages degrade gracefully, bad key in Javanese).

## 1.4.0 (2026-10-30 22:00)
- Added shopping help: every tool and part in the result and guide gets "Compare prices" links to Tokopedia and Shopee search pages (links only; Tukang Copilot never buys), plus a "Send shopping list to WhatsApp" button (wa.me share of tools, parts and rough prices in the session language). New `api/shop.py`; session JSON carries `shop_url`, `shop_alt_url` and `whatsapp_url`. Front end only accepts those three https hosts.
- Tests: 4, plus one Playwright assertion.

## 1.3.1 (2026-10-30 21:30)
- Changed uploads to stream to disk in 1 MB chunks and stop at the size limit (no whole file in memory).
- Fixed: a corrupt, disguised or decompression-bomb image now gives a friendly 400 and leaves no half-made session folder behind. 8 tests (`test_hardening.py`).
- Fixed test isolation: conftest waits for pipeline threads at teardown, so a late worker can't write into the next test's folder or the repo `data/` folder.

## 1.3.0 (2026-10-30, night)
- Added abuse guard for a public deployment (`api/guard.py`): per-visitor rate limit (`RATE_LIMIT_PER_HOUR`, default 30) and a rolling 24 h spend cap across all repairs (`DAILY_BUDGET_USD`, default 10). Live mode only, so demo mode and judges on a mock site are never blocked. Friendly id/jv/en message, `Retry-After` header, 429 or 503.
- Tests: 8.

## 1.2.0 (2026-10-30, evening)
- Added video capture: a 5 to 10 s clip instead of photos. One ffmpeg pass samples 12 frames; the sharpest (Laplacian variance) of each third is kept as a photo. With no voice note or text, the clip's own sound is transcribed. Max 30 s / 40 MB, clean 400s.
- Added Basa Jawa for every UI string (ngoko); a test fails if any string is missing in jv or en.
- Added open-weights badge in the header when diagnosis and planning really run on Muse Spark Open (flag + Baseten key), id/jv/en.
- Added safety escalation card for red stops and "all safe causes tried": why, what to do now, nearby service-centre search, technician PDF, 112 emergency line.
- Added PWA: manifest, generated icons (scripts/make_icons.py), shell-only service worker (never caches API or photos).
- Tests: 10 labelled stand-in photo fixtures run end to end; Playwright browser smoke (6 tests, skipped without Chromium); mypy strict config (mypy.ini) + CI step; scripts/check_all.sh. 121 tests.
- Demo assets from the real app in demo mode: 2:37 1080p video with captions and edge-tts voice-over, .srt, 36 s vertical X clip, 14 phone screenshots, architecture diagram.
- Added `set_keys.py` one-step key swap: `--stdin` (non-interactive), `--check-only`, `--help`; never creates .env without a key.
- Docs: SPEC §17 (verified judging criteria → features), a judging plan, docs/SUBMISSION_CHECKLIST.md, README screenshots/diagram, judge 60-second tour.

## 1.1.0 (2026-10-30, evening)
- Added water pump scenario (SPEC §8 case 2): Shimizu pump runs but gives no water. Amber (220V near water, unplug first). Plan 1 re-primes the pump; "still broken" re-plans to the clogged foot valve. New sample photo and "Try a sample" button.
- Added printable PDF repair report `GET /api/sessions/{id}/report.pdf` (A4, id/jv/en): safety badge, marked SAM photo, every step with its camera check, tools and parts with prices, attempts, disclaimer. Pure Pillow, no new dependency. "Download PDF report" button on the result and shared guide pages.
- Added "My garage": past repairs kept only on the phone (localStorage, max 20), shown on the start screen with safety level, steps verified and a link back to the guide.
- Added PWA plumbing: root routes for `/manifest.webmanifest` and `/sw.js`, manifest link + theme colour, service worker registration (worker, icons and manifest themselves landed in 1.2.0).
- mypy strict passes on all of `api/` (typed `_chat_json` generic, FastAPI handlers, SSE generator).

## 1.0.0 (2026-10-30, first complete build)
- Spec (SPEC.md) and plan.
- Verified the Meta Model API docs: model ids, Chat Completions structured output, audio input, Voice Transcribe file endpoint, SAM 3.1 Responses streaming + box grammar, Muse Image edits, Muse Spark Open on Baseten, pricing (docs/META_API_NOTES.md).
- Backend: `meta_client` (retries, cost meter), pydantic schemas, versioned prompts, pipeline engine (listen → gate → look → SAM → diagnose → follow-up → plan → plan safety gate → Muse Image diagrams with review → narration), step verification, re-plan, report, 24 h cleanup, per-session budget.
- Three-layer safety gate (text, model level, plan scan) in id/jv/en.
- Phone web app: camera + mic capture, category chips, live stage progress (SSE), diagnosis card with SAM overlay, guided steps with voice and hands-free mode, check-my-step, still-broken re-plan, shareable read-only guide, Bahasa/Javanese/English UI.
- Demo mode with three scenarios (motorbike, faucet, rice cooker) and drawn sample photos.
- Fake Meta API server; `scripts/check_keys.py`, `scripts/set_keys.py`, `scripts/smoke_e2e.py`.
- 78 automated tests, ruff, GitHub Actions CI, Dockerfile, docker-compose, Render blueprint.
- Docs: README, TODO, setup tutorial, how-to-use (EN/ID), architecture, AI pipeline, API, safety, testing, test report, verification report, troubleshooting, demo script, submission text + X drafts, roadmap, attributions, decisions.
- Fixed: "gas" alone (motorbike throttle) tripped the gas safety stop; now only LPG/cooking-gas phrases do.
