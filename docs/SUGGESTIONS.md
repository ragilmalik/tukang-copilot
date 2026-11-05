# Suggestions and improvements

Ten things I would build next, most useful first. Features come before polish. The dated plan is in [ROADMAP.md](ROADMAP.md); this list says why each one matters and roughly how I'd do it.

1. **Real owner trials in Semarang.**
   *Why:* every impact number today is "not measured yet". Five to ten real repairs with real owners would show whether people finish the job and what they save.
   *How:* the kit is ready in [USER_TRIAL_KIT.md](USER_TRIAL_KIT.md) and `scripts/impact_report.py` turns the outcomes into a report.

2. **An eval set of real photos.**
   *Why:* the live eval uses labelled AI-generated sample photos. Real photos (bad light, grease, odd angles) are the real test of SAM hit rate and top-1 diagnosis.
   *How:* 50 photos over 5 object types with the expected parts and causes, run through `scripts/run_eval.py` live.

3. **Per-step sample photos for the camera check.**
   *Why:* one close-up sample photo fits only the steps it shows. A sample per step would let the demo show a pass on every step.
   *How:* take real photos of each step on a real bike, not generated ones, and link them to the plan's `expected_state`.

4. **WhatsApp on a real number.**
   *Why:* most Indonesians already live in WhatsApp; no link to open, no install.
   *How:* the webhook and chat flow are built and tested ([WHATSAPP.md](WHATSAPP.md)); it needs a Meta app, a test number and four env vars.

5. **Smoother hands-free guide.**
   *Why:* hands are greasy during a repair. Today the live camera guide samples about one frame a second.
   *How:* realtime Voice Transcribe over WebSocket and SAM video tracking.

6. **Sessions that survive a restart.**
   *Why:* the free host wipes `/tmp` on restart, so a repair in progress is lost.
   *How:* Cloudflare R2 for files plus a small SQLite index; the engine already writes everything through one save function.

7. **Send the report to a nearby bengkel.**
   *Why:* jobs the owner can't finish should go to a local mechanic with photos and what was already tried, not start from zero.
   *How:* a mechanic page that opens the shared report and can reply with a quote.

8. **More objects.**
   *Why:* fans, washing machines and bicycles are among the most common household faults.
   *How:* new sample masks, prompt examples and safety rules per kind, plus eval cases.

9. **Low-signal mode.**
   *Why:* rural areas have weak data.
   *How:* a small on-device model for the first look, then sync the full diagnosis when online.

10. **Accessibility with real users.**
    *Why:* axe-core passes on every main screen, but that is not the same as a TalkBack user finishing a repair.
    *How:* one session each with a TalkBack and a VoiceOver user, then fix what they hit.

## Smaller polish I noted

- Let the owner crop or mark the problem area on the photo before sending.
- Show the bengkel price range next to each part, with the date the price was checked.
- Add Sundanese and Madurese once the Javanese flow has had real users.
