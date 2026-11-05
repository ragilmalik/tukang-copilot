# 3-minute demo video

The rules: show only what was built during the hackathon and keep it under 3:00. I want real objects and a real phone.
Recording setup: the phone's screen recorder (Android has one built in), plus a second phone or a friend filming the
bike. Voice-over in English with Bahasa on screen, or Bahasa with English subtitles.

| Time | Shot | Say / show |
|---|---|---|
| 0:00–0:12 | Bike in a Semarang alley, starter whining, won't start. Shop shutter closed. | "Motor mogok. Bengkelnya tutup." Text: *139 million motorbikes in Indonesia. One small fault = a day's wage.* |
| 0:12–0:22 | Phone opens Tukang Copilot. | "Tukang Copilot turns any phone into a mechanic's apprentice." |
| 0:22–0:40 | Snap the plug area, tap Motor, hold mic: "Motor saya susah hidup, starter bunyi tapi nggak nyala." Question "Apakah tercium bau bensin?" → "Tidak". | Stages tick live. "When it's unsure, it asks one question." |
| 0:40–0:55 | Diagnosis: numbered parts on *his own photo*, 🟠 caution, causes with %, Rp cost vs bengkel price. Tick the safety list. | "SAM 3.1 marks the real part. Steps stay locked until it's safe." |
| 0:55–1:15 | Live camera guide: point the phone at the engine and the plug cap gets outlined live. | "Point the camera and it outlines exactly what to touch." |
| 1:15–1:35 | Hands-free: dirty hands, say "lanjut" / "ulang". Dark photo → ⚠️ "turn on your torch". Retake → ✅. | "Every step is checked with the camera." |
| 1:35–1:45 | Starter → engine runs. "Sudah beres 🎉". | Big smile. ✅ steps verified, money saved. |
| 1:45–2:05 | Second case, fast: rice cooker → 🔴 STOP "220 V internals" → hand-off card: WhatsApp summary opens, nearest bengkel, PDF brief. | "And it knows when to say no, and who to hand it to." |
| 2:05–2:15 | Switch to Basa Jawa; open-weights badge. | "Javanese too, and the reasoning can run on Meta's open weights." |
| 2:15–2:45 | Architecture slide (docs/img/architecture.png). | "Five Meta models, one agent loop: plan, act, verify, re-plan." |
| 2:45–2:55 | Logo + repo + live link. | "Tukang Copilot. Every phone becomes a mechanic's apprentice." |

The backup cut already exists: docs/demo/tukang-copilot-demo.mp4 (2:53, offline sample mode, labelled AI-generated sample photos and
Chromium's test camera feed, English voice-over + captions .srt). It follows the same order in 21 scenes (v1.29 cut on the new UI, 1080p60, start times
in docs/demo/TIMESTAMPS.txt): hook title card, hook, intro, progress with streaming results, question, diagnosis, parts,
safety list, live camera, check ⚠, check ✓, hands-free, re-plan, Muse Image diagram, agent log, hand-off, rice STOP,
WhatsApp in Basa Jawa (simulator), open weights, architecture, close.

## Shot list / prep
- [ ] Bike with the plug cap slightly pulled off (safe, engine cold) so the fix is real
- [ ] Charged phone, brightness up, Do Not Disturb, Chrome on the Render link
- [ ] One test run 10 minutes before, to wake the server
- [ ] Rice cooker on a table, unplugged
- [ ] Architecture slide: docs/img/architecture.png
- [ ] Phone on https (the live camera and mic need it); test hands-free once somewhere quiet
- [ ] WhatsApp installed (the hand-off opens it)

## Backup plan
- If the API is slow or down, set `OFFLINE=1` on Render (or locally), use the "motor mogok" sample, and say "recorded run" on screen.
- If there's no 4G, run it locally with a Cloudflare tunnel over home Wi-Fi.
- If the bike won't cooperate, use the faucet scenario as the main case.

## ~45 s vertical clip for X
Already made: docs/demo/tukang-copilot-x-vertical.mp4 (43.5 s, 1080×1920, silent, Bahasa captions, labelled offline sample mode): hook · parts on your photo · live camera · step check ✓ · hands-free "lanjut" · bengkel hand-off · STOP · Meta models · close.
Real-phone version: 0:00 bike won't start · 0:05 snap + speak · 0:10 parts light up live · 0:18 "lanjut" hands-free · 0:24 step check ✅ · 0:30 engine starts · 0:36 "Built with Meta's Muse Spark + SAM 3.1" + link.
