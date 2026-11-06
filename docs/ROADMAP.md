# Roadmap

Some things I first put on this list got built in the first weeks after all: the WhatsApp channel (webhook and
simulator done, a real number still needs my Meta app setup), installing the app as a PWA, SAM 3.1 on live camera
frames with hands-free voice commands, the bengkel hand-off (WhatsApp summary, Maps search, mechanic brief PDF), the
water pump scenario, and an axe-core accessibility pass on every main screen. What is left:

| When | What | Why |
|---|---|---|
| Nov 2026 | The first live run on the real Meta API is done (5 Nov 2026, [EVAL.md](EVAL.md)). Next: the same eval on real Semarang photos (50 photos, 5 object types) with expected parts and causes; track SAM hit rate and top-1 diagnosis accuracy | Honest accuracy numbers |
| Nov 2026 | Connect the WhatsApp channel to a real number and run the user trials there | Where Indonesians already are |
| Nov 2026 | Fan, washing machine and bicycle scenarios, plus prompt tuning | Most common household faults |
| Dec 2026 | Realtime Voice Transcribe over WebSocket for the live camera guide, and SAM video tracking instead of one frame a second | Smoother hands-free repairs |
| Dec 2026 | Cloudflare R2 storage plus a SQLite index, so sessions survive restarts and scale past one server | Production |
| Q1 2027 | Offline / low-signal diagnosis on Muse Glimmer (open weights, on-device); sync when online | Rural areas |
| Q1 2027 | "Kirim ke bengkel" part two: a nearby mechanic gets the report with photos and what was tried, and can send a quote and a booking | Local shops get the jobs people can't finish |
| Q2 2027 | Turn a successful repair into a clean illustrated guide (Muse Image) that other people can follow | Community knowledge base |
| Q2 2027 | Apprentice mode for repair shops: training checklists verified by camera | B2B |
| Later | More languages (Sundanese, Madurese), and a test with real TalkBack and VoiceOver users | Reach |
