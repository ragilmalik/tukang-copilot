# User trial kit: 5 real repairs with neighbours (1 page)

The point is to replace the MOCK numbers in docs/IMPACT.md and docs/img/impact.png with 5 real repairs.
Plan on about an hour per person. The only cost is the Meta API, a few cents per repair.

## Before you start (once)
1. Run the app in live mode (real key) and use a phone with signal: open the deployed link.
2. On each tester's phone, open the link once with a label at the end, for example `https://<your-app>/?trial=T1`
   (T2 for the next person, and so on). The label stays on that phone. No names needed.
3. Pick real small faults: a motorbike that won't start, a flat tyre, a pump with no water, a dripping tap.
   Nothing with gas, house wiring or a car's brakes (the app will stop those anyway).

## Consent line (read it out, then tick it in your notebook)
> EN: "This is a test of a repair helper app. It takes photos of the broken thing (not of you) and your voice
> description. Photos and voice are deleted from the server within 24 hours; only the result numbers are kept
> (fixed or not, minutes, rupiah saved). You can stop at any time. Is that OK?"
>
> ID: "Ini uji coba aplikasi bantu perbaikan. Aplikasi memotret barang yang rusak (bukan Anda) dan merekam
> cerita Anda. Foto dan suara dihapus dari server dalam 24 jam; yang disimpan hanya angka hasilnya (beres atau
> tidak, berapa menit, berapa rupiah hemat). Anda boleh berhenti kapan saja. Boleh?"

## During each repair
1. Let the tester use the app themselves. Help only if they are stuck or unsafe.
2. At the end they tap "Sudah beres" (it works) or "Dibawa ke bengkel" (mechanic).
3. In the small box "Uji coba: berapa menit?" type the minutes it really took (from first photo to working).

## What to write in your notebook (one line per repair)
| Tester | Object | Fixed? | Minutes | Bengkel price they would have paid | Notes (what was hard) |
|---|---|---|---|---|---|

The app records the same numbers by itself. The notebook is a backup, and it gives you quotes for the video.

## After the 5 trials
```bash
# app running on your own computer: the log is already in data/impact/outcomes.jsonl
python scripts/impact_report.py
# app on Render: download the log FIRST (a redeploy can wipe the server disk). Needs IMPACT_TOKEN set on Render.
curl -H "X-Impact-Token: <your token>" https://<your-app>/api/impact/outcomes.jsonl -o outcomes.jsonl
python scripts/impact_report.py --data outcomes.jsonl
```
That rewrites docs/IMPACT.md and docs/img/impact.png without the MOCK stamp. Check the numbers against your
notebook. Don't edit the numbers by hand; if a repair was logged wrong, add a note in IMPACT.md under the table.

## Safety
If anything smells of gas, sparks or smokes, or the app says STOP: stop, unplug, step back. Emergency number: 112.
