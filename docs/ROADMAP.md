# Roadmap (after the hackathon)

| When | What | Why |
|---|---|---|
| Nov 2026 | Real-photo eval set (50 photos, 5 object types) with expected parts and causes; track SAM hit rate and top-1 diagnosis accuracy | Honest accuracy numbers |
| Nov 2026 | Water pump, fan, washing machine and bicycle fixtures, plus prompt tuning | Most common household faults |
| Dec 2026 | Live camera mode: realtime Voice Transcribe over WebSocket, plus SAM video tracking of the part while the user works | Hands-free, no photo taking |
| Dec 2026 | Cloudflare R2 storage plus a SQLite index, so sessions survive restarts and scale past one server | Production |
| Q1 2027 | Offline / low-signal diagnosis on Muse Glimmer (open weights, on-device); sync when online | Rural areas |
| Q1 2027 | "Kirim ke bengkel": send the report to a nearby mechanic with photos and what was tried; quote and booking | Local shops get the jobs people can't finish |
| Q1 2027 | WhatsApp chat (photo and voice note in, steps out) | Where Indonesians already are |
| Q2 2027 | Workshop mode: turn a successful session into a clean illustrated guide (Muse Image) for others | Community knowledge base |
| Q2 2027 | Apprentice mode for repair shops: training checklists verified by camera | B2B |
| Later | PWA install, more languages (Sundanese, Madurese), accessibility review | Reach |
