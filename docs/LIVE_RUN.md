# First live run: real Meta models

Made by `python scripts/first_live_run.py` on 2026-11-05 22:45 WIB (app 1.29.13), sample `motor`, language `id`, server `api.meta.ai`. No key is stored in this file.

## Result

- Status: **ready**
- Demo answers used as a fallback: none (every stage answered by the model)
- Models: listen = muse-voice-transcribe-1.0, listen_javanese = muse-spark-1.2, look = muse-spark-1.3, segment = sam-3.1, diagnose = muse-spark-1.3, plan = muse-spark-1.3, illustrate = muse-image-1.0, verify = muse-spark-1.3
- Models this key could not see: none
- Total time (photo in to plan ready, incl. the follow-up answer): **146.5 s**
- Cost of the repair: **$0.1118** (cap $0.5); by model: muse-spark-1.3 $0.1118

## What went in

- Photo: `samples/motor.jpg` (labelled AI-generated sample photo)
- Owner text: Motor saya Honda Beat susah hidup dari pagi, distarter cuma bunyi tapi mesin nggak nyala.

## What the AI said

- Object: Mesin sepeda motor, area kepala silinder dan cop busi
- Cause: Busi kotor, basah, aus atau cop busi longgar (65 %)
- Cause: Aki lemah atau terminal aki kendor dan berkarat (55 %)
- Cause: Suplai bensin terhambat, bensin habis atau karburator kotor (48 %)
- Safety level: amber; Ada bensin di sekitar mesin dan tegangan tinggi di kabel serta cop busi, mesin juga bisa panas. Jauhkan api dan jangan pegang cop busi saat starter diputar.
- SAM 3.1 outlined 0 of 0 parts
  1. Putar kunci kontak ke OFF dan cabut kuncinya. Pastikan mesin dingin dan jauhkan api, rokok, dan bensin.
  2. Tarik cop busi hitam lurus ke belakang dengan tangan kering. Lap debu tebal di kepala silinder dengan lap kering.
  3. Pasang kunci busi 16 mm dan putar ke kiri untuk melepas busi. Angkat busi keluar dari lubangnya.
  4. Sikat ujung busi sampai bersih dan kering dengan sikat kecil. Ganti dengan busi baru jika ujung hitam gosong, basah oli, atau aus.
  5. Pasang busi dengan tangan lalu kencangkan secukupnya dengan kunci. Dorong cop busi sampai masuk penuh tanpa celah.
- Diagrams drawn (Muse Image): 0
- Voice clips: 0
- Step 1 camera check (9.0 s): not passed: Foto menunjukkan mesin dan cop busi tanpa asap atau tanda panas, tetapi kunci kontak tidak terlihat sama sekali dalam foto.

## Time per stage

| Stage | Status | ms |
|---|---|---|
| listen | skipped | - |
| gate | done | - |
| look | done | 16805 |
| segment | skipped | - |
| diagnose | done | 106865 |
| plan | done | 22553 |
| safety | done | - |
| illustrate | skipped | - |
| narrate | done | 199 |

## Next

- If everything above is fine: `python scripts/run_eval.py` and `python scripts/smoke_e2e.py http://127.0.0.1:8000` in live mode.
- Once checked, copy the total time and cost into WRITEUP and SUBMISSION.
