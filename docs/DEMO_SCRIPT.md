# 3-minute demo video

Rules: show only what was built during the hackathon; keep it under 3:00; real objects, real phone.
Record: phone screen (Android: built-in screen recorder) + a second phone or friend filming the bike. Voice-over in English with Bahasa on screen, or Bahasa with English subtitles.

| Time | Shot | Say / show |
|---|---|---|
| 0:00–0:15 | Bike in a Semarang alley, starter whining, won't start. Shop shutter closed. | "Motor mogok. Bengkelnya tutup." Text: *130 million motorbikes in Indonesia. One small fault = a day's wage.* |
| 0:15–0:30 | Phone opens Tukang Copilot. | "Tukang Copilot turns any phone into a mechanic's apprentice. It sees the real part, speaks your language, and checks your work." |
| 0:30–0:50 | Snap the plug area, tap Motor, hold mic: "Motor saya susah hidup, starter bunyi tapi nggak nyala." | Stages tick live: Listening → Looking → Finding parts (SAM 3.1) → Diagnosing. |
| 0:50–1:05 | Question appears: "Apakah tercium bau bensin?" Answer "Tidak". | "When it's unsure, it asks one question instead of guessing." |
| 1:05–1:20 | Diagnosis: numbered parts on *his own photo*, 🟠 caution, causes with %, tools + Rp estimate. | Point at the orange mask on the plug cap. |
| 1:20–1:45 | Step 3 "push the cap until it clicks". Hands-free voice reads it. Take a quick dark photo → ⚠️ "turn on your torch". Retake → ✅. | "Every step is checked with the camera." |
| 1:45–1:55 | Starter → engine runs. | Big smile. ✅ 4/4 steps verified. |
| 1:55–2:15 | Second case, fast: rice cooker → 🔴 STOP "needs opening 220V internals, take it to a service centre". | "And it knows when to say no." |
| 2:15–2:45 | Architecture slide (README diagram): Voice Transcribe → Spark vision → SAM 3.1 masks → Spark diagnose/plan → Muse Image diagram (edited from your photo) → Spark verify → re-plan. Toggle: Muse Spark Open on Baseten. | "Five Meta models, one agent loop: plan, act, verify, re-plan." |
| 2:45–3:00 | Logo + repo + live link. | "Tukang Copilot. Every phone becomes a mechanic's apprentice." |

## Shot list / prep
- [ ] Bike with plug cap slightly pulled off (safe, engine cold) so the fix is real
- [ ] Charged phone, brightness up, Do Not Disturb, Chrome on the Render link
- [ ] One test run 10 minutes before (wakes the server)
- [ ] Rice cooker on a table, unplugged
- [ ] Architecture slide (export the README Mermaid diagram as PNG)

## Backup plan
- API slow or down: set `DEMO_MODE=1` on Render (or locally) and use the "motor mogok" sample; say "recorded run" on screen.
- No 4G: run locally + Cloudflare tunnel over home Wi-Fi.
- Bike won't cooperate: use the faucet scenario as the main case.

## 30–45 s vertical clip for X
0:00 bike won't start · 0:05 snap + speak · 0:12 parts light up · 0:18 step check ✅ · 0:25 engine starts · 0:32 "Built with Meta's Muse Spark + SAM 3.1" + link.
