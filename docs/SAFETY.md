# Safety and privacy

## Safety levels
| Level | Shown as | Meaning | App behaviour |
|---|---|---|---|
| green | 🟢 AMAN / SAFE | Beginner job, basic tools | Full guide |
| amber | 🟠 HATI-HATI / CAUTION | Hot, sharp, heavy, fuel nearby, water + unplugged electrics | Full guide with warnings per step |
| red | 🔴 STOP | Could injure or kill | No steps. Reason + who to call |

## Hard stops (in code, `api/pipeline/safety.py`)
Three independent layers, so a model mistake can't produce a dangerous guide:
1. **Text gate** on what the user said or typed, before any paid call: gas (elpiji, LPG, regulator, bau gas), house wiring (MCB, panel, kWh meter, kabel dalam tembok, korsleting, melted socket), high-energy parts (microwave, CRT, high voltage, airbag, brake fluid / hydraulic brakes, fuel leak), electric shock (kesetrum, tersengat), fire, smoke or swollen batteries (fire service 113), refrigerant gas, and anything medical (luka, berdarah, obat, dokter…). Also applied to "still broken" reports.
2. **Model level**: `diagnose.md` defines red; a red Diagnosis stops the session.
3. **Plan gate**: every generated plan is scanned for hard-stop actions (opening 220 V casings / heating elements, opening rice cookers, microwaves, fridges, AC, dispensers; bleeding brake lines; splicing into wall/panel wiring; gas hoses). A hit forces red even if the model said green.

Every guide also shows two base rules (unplug / engine off and cool; gloves and eye protection) and the disclaimer, in the user's language.

Step checks: the verify prompt fails a photo that shows exposed live wires, fuel near flame or a cut gas hose and tells the user to stop.

## Messages
Every stop message exists in Bahasa Indonesia, Javanese and English and names a concrete next action (service centre, licensed electrician, PLN, medical help 119).

## Not covered
Tukang Copilot does not give medical advice, does not handle cars' high-voltage EV systems, gas appliances, structural work or work at height. These either hit the gate or are red by prompt.

## Disclaimer (shown under every guide)
> Panduan ini dibuat AI dan bisa salah. Kamu bertanggung jawab atas keselamatanmu. Berhenti bila ragu.
> This guide is AI-generated and can be wrong. You are responsible for your safety. Stop if unsure.

## Privacy
- **No accounts, no names, no phone numbers** collected.
- The **voice recording is deleted** right after transcription.
- Photos and sessions live only on the server disk and are **deleted after 24 h** (`RETENTION_HOURS`).
- `GET /api/sessions/{id}` never returns the raw typed description; `session.json` itself is never served.
- Session ids are random 12-hex strings; shared links are read-only.
- Meta Standard-mode model ids are used, so content is not used to train Meta models (per Meta's docs). Contributor-mode ids are deliberately avoided.
- Keys live in `.env` / Render secrets only, never in code or the browser.
