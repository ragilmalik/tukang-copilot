/* Tukang Copilot phone web app. Plain JavaScript, no build step. Strings in id / jv / en. */
const $ = (id) => document.getElementById(id);
const T = {
  id: { hero: "Apa yang rusak?", heroSub: "Foto barangnya, ceritakan masalahnya, dapat panduan perbaikan langkah demi langkah.", takePhoto: "Ambil foto (1–3)",
        catMotor: "Motor", catPump: "Pompa air", catAppliance: "Elektronik rumah", catPlumbing: "Pipa/keran", catOther: "Lainnya",
        record: "Ketuk untuk bicara", stop: "Ketuk untuk berhenti", typeHere: "…atau ketik masalahnya di sini", go: "Periksa sekarang",
        samples: "Coba contoh:", sMotor: "motor mogok", sPump: "pompa tidak keluar air", sFaucet: "kran menetes", sRice: "rice cooker mati", sTire: "ban kempes",
        working: "Sedang memeriksa…", retry: "Coba lagi", answerHere: "Jawaban kamu", send: "Kirim", diagnosis: "Diagnosa", safetyFirst: "Keselamatan dulu",
        tools: "Alat", materials: "Suku cadang", listen: "Dengarkan", next: "Lanjut", handsFree: "Mode tangan bebas (dibacakan + perintah suara)", vListening: "Mendengarkan… ucapkan lanjut, kembali, ulang, cek, masih rusak, atau berhenti.", vHelp: "Perintah suara: lanjut · kembali · ulang · cek · masih rusak · berhenti", vNoSR: "HP ini tidak bisa mendengar terus. Ketuk tombol mikrofon untuk setiap perintah.", ptt: "🎙️ Ketuk, lalu ucapkan perintah", pttRec: "⏹️ Bicara sekarang… (ketuk untuk kirim)", vHeard: "Terdengar «{text}»", vUnknown: "Belum paham «{text}». Coba lanjut, kembali, ulang, cek.", vOff: "Mode tangan bebas mati.",
        done: "Selesai kalau:", outcomeAsk: "Sudah jalan lagi?", fixedBtn: "Sudah beres 🎉", proBtn: "Dibawa ke bengkel", fixedThanks: "Mantap! Perbaikan selesai.", proThanks: "Tidak apa-apa, membawa ke ahli itu pilihan yang aman. Laporan PDF bisa ditunjukkan ke mekanik.", savedTotal: "Total hemat", savedFrom: "dari", savedUnit: "perbaikan", preTitle: "Sebelum mulai, pastikan:", preLocked: "Centang semua dulu, baru langkah 1 terbuka.", preReady: "✅ Siap. Langkah 1 terbuka.", waitFor: "Tunggu {n} menit", timerStart: "Mulai pengatur waktu", timerStop: "Hentikan", timerDone: "Waktu tunggu selesai. Lanjut ke langkah berikutnya.", checkStep: "Cek langkah ini", trialMin: "Uji coba: berapa menit perbaikannya?", fbNote: "🧪 Jawaban contoh (API live sedang tidak tersedia)", mech: "🧑‍🔧 Panggil mekanik / bengkel", hoSub: "Kirim ringkasan ini ke bengkel, lalu cari yang terdekat. Laporan PDF berisi ringkasan untuk mekanik.", hoWa: "Kirim lewat WhatsApp", hoMaps: "Bengkel/servis terdekat", hoPdf: "Laporan PDF untuk mekanik", hoMsg: "Pesan yang dikirim", liveGuide: "Panduan kamera langsung", liveCheck: "📸 Cek sekarang", liveClose: "Tutup kamera", liveStart: "Menyalakan kamera…", liveAim: "Arahkan kamera ke {name}", liveFound: "🎯 Ketemu {name}", liveLost: "Belum ketemu {name}. Gerakkan HP pelan-pelan.", liveNoPart: "Langkah ini tidak menunjuk bagian tertentu. Pakai Cek sekarang.", liveNoCam: "Kamera langsung tidak bisa dipakai di HP ini. Pakai tombol foto untuk cek langkah.", liveLimit: "Batas kamera langsung untuk perbaikan ini sudah habis. Pakai foto untuk cek langkah.", share: "Bagikan laporan", pdf: "Unduh laporan PDF", workshop: "Lembar bengkel (cetak besar)", hood: "Di balik layar: model yang dipakai", hs_listen: "Dengar suara", hs_gate: "Cek keselamatan teks", hs_look: "Lihat foto", hs_segment: "Tandai bagian", hs_diagnose: "Diagnosa", hs_plan: "Susun langkah", hs_safety: "Cek keselamatan rencana", hs_illustrate: "Gambar bantu", hs_narrate: "Suara pemandu", wa: "Kirim daftar belanja ke WhatsApp", buy: "Cari harga", garage: "Garasi saya", garageNote: "Riwayat perbaikan hanya disimpan di HP ini. Panduan bisa dibuka 24 jam.", garageClear: "Hapus riwayat", again: "Perbaiki barang lain", erase: "Hapus foto saya sekarang", eraseAsk: "Hapus foto, suara, dan panduan ini dari server sekarang?", erased: "Sudah dihapus dari server.",
        stuck: "Masih rusak, coba rencana lain", stuckHere: "Apa yang terjadi? (mis. sudah dicoba, tetap mati)",
        needPhoto: "Ambil atau unggah foto dulu.", needDesc: "Ceritakan masalahnya (suara atau ketik).",
        footer: "Hanya untuk perbaikan ringan. Untuk gas, listrik rumah, atau tegangan tinggi, panggil teknisi.",
        stages: { listen: "Mendengarkan", gate: "Cek keselamatan awal", look: "Melihat foto", segment: "Menandai bagian (SAM 3.1)", diagnose: "Mendiagnosa",
                  plan: "Menyusun langkah", safety: "Cek keselamatan rencana", illustrate: "Menggambar diagram", narrate: "Menyiapkan suara" },
        diff: "Kesulitan", min: "menit", est: "perkiraan", shopCost: "bengkel", save: "hemat",  stopTitle: "STOP: jangan lanjutkan sendiri", triedTitle: "Saatnya ke bengkel/servis", stopNow: "Lakukan sekarang:",
        stopNowRed: ["Matikan dan cabut dari listrik / tutup gas / matikan mesin.", "Jangan buka casing atau bagian dalamnya.", "Bawa ke servis resmi atau panggil teknisi, tunjukkan laporan ini."],
        stopNowTried: ["Biarkan dalam keadaan mati dan aman.", "Unduh laporan PDF: berisi apa saja yang sudah dicoba.", "Tunjukkan ke bengkel/servis supaya tidak mengulang dari nol."],
        findService: "Cari servis terdekat", emergency: "Darurat (api, asap, bau gas kuat): telepon 112.", copied: "Tautan disalin", openW: "Penalaran: Muse Spark Open (open weights)", demo: "Mode demo: jawaban contoh, tanpa biaya API.",
        green: "AMAN", amber: "HATI-HATI", red: "STOP", pass: "✅ Langkah ini beres", fail: "⚠️ Belum pas", checking: "Memeriksa foto…",
        verified: "langkah terverifikasi kamera", recording: "Merekam…", recorded: "Suara terekam ✓", micErr: "Mikrofon tidak bisa dipakai. Ketik saja masalahnya.",
        netErr: "Koneksi terputus. Cek sinyal lalu coba lagi.", offline: "Tidak ada internet. Diagnosis butuh sinyal; foto kamu tetap aman di HP.",
        exhausted: "Sudah semua", newPlan: "Rencana baru siap.", photos: "foto", videoBtn: "🎥 Atau rekam video 5–10 detik", videoOk: "Video siap ✓ (3 gambar terbaik diambil otomatis)", videoBig: "Videonya terlalu besar. Rekam 5–10 detik saja.", badFile: "Berkas itu bukan foto. Pilih foto JPG, PNG, atau HEIC.", unreadPhoto: "Foto itu tidak bisa dibaca. Coba foto JPG atau PNG.", bigFile: "Berkasnya terlalu besar. Coba foto yang lebih kecil.", emptyFile: "Berkasnya kosong. Coba ambil lagi.", tooLong: "Teksnya terlalu panjang. Persingkat dulu." },
  en: { hero: "What's broken?", heroSub: "Snap it, say what's wrong, get a step-by-step repair guide.", takePhoto: "Take photos (1–3)",
        catMotor: "Motorbike", catPump: "Water pump", catAppliance: "Home appliance", catPlumbing: "Pipes/taps", catOther: "Other",
        record: "Tap to talk", stop: "Tap to stop", typeHere: "…or type the problem here", go: "Check it now",
        samples: "Try a sample:", sMotor: "bike won't start", sPump: "pump gives no water", sFaucet: "dripping tap", sRice: "dead rice cooker", sTire: "flat tyre",
        working: "Checking…", retry: "Try again", answerHere: "Your answer", send: "Send", diagnosis: "Diagnosis", safetyFirst: "Safety first",
        tools: "Tools", materials: "Parts", listen: "Listen", next: "Next", handsFree: "Hands-free mode (read aloud + voice commands)", vListening: "Listening… say next, back, repeat, check, still broken or stop.", vHelp: "Voice commands: next · back · repeat · check · still broken · stop", vNoSR: "This phone can't listen continuously. Tap the mic button for each command.", ptt: "🎙️ Tap, then say a command", pttRec: "⏹️ Speak now… (tap to send)", vHeard: "Heard «{text}»", vUnknown: "Didn't catch «{text}». Try next, back, repeat, check.", vOff: "Hands-free mode off.",
        done: "Done when:", outcomeAsk: "Does it work again?", fixedBtn: "It works now 🎉", proBtn: "Took it to a mechanic", fixedThanks: "Great, repair done.", proThanks: "That is a safe choice. Show the PDF report to the mechanic.", savedTotal: "Total saved", savedFrom: "from", savedUnit: "repairs", preTitle: "Before you start, make sure:", preLocked: "Tick everything first to unlock step 1.", preReady: "✅ Ready. Step 1 is open.", waitFor: "Wait {n} minutes", timerStart: "Start timer", timerStop: "Stop", timerDone: "Waiting time is over. Go on to the next step.", checkStep: "Check this step", trialMin: "Trial: how many minutes did the fix take?", fbNote: "🧪 Demo answer (live API unavailable)", mech: "🧑‍🔧 Call a mechanic", hoSub: "Send this summary to a workshop, then find the nearest one. The PDF report has a mechanic brief page.", hoWa: "Send on WhatsApp", hoMaps: "Workshops near me", hoPdf: "PDF report for the mechanic", hoMsg: "Message to send", liveGuide: "Live camera guide", liveCheck: "📸 Check now", liveClose: "Close camera", liveStart: "Starting the camera…", liveAim: "Point the camera at the {name}", liveFound: "🎯 Found {name}", liveLost: "Can't see the {name} yet. Move the phone slowly.", liveNoPart: "This step does not point at one part. Use Check now.", liveNoCam: "The live camera is not available on this phone. Use the photo button to check the step.", liveLimit: "The live camera limit for this repair is used up. Use a photo to check the step.", share: "Share report", pdf: "Download PDF report", workshop: "Workshop sheets (large print)", hood: "Under the hood: models used", hs_listen: "Listen", hs_gate: "Text safety gate", hs_look: "Look at photo", hs_segment: "Mark parts", hs_diagnose: "Diagnose", hs_plan: "Plan steps", hs_safety: "Plan safety gate", hs_illustrate: "Helper diagram", hs_narrate: "Voice guide", wa: "Send shopping list to WhatsApp", buy: "Compare prices", garage: "My garage", garageNote: "Your repair history stays on this phone only. Guides open for 24 hours.", garageClear: "Clear history", again: "Fix something else", erase: "Delete my photos now", eraseAsk: "Delete the photos, voice and guide of this repair from the server now?", erased: "Deleted from the server.",
        stuck: "Still broken, try another plan", stuckHere: "What happened? (e.g. tried it, still dead)",
        needPhoto: "Take or upload a photo first.", needDesc: "Describe the problem (voice or text).",
        footer: "Light repairs only. For gas, house wiring, or high voltage, call a professional.",
        stages: { listen: "Listening", gate: "First safety check", look: "Looking at the photo", segment: "Finding the parts (SAM 3.1)", diagnose: "Diagnosing",
                  plan: "Planning steps", safety: "Plan safety check", illustrate: "Drawing diagrams", narrate: "Preparing voice" },
        diff: "Difficulty", min: "min", est: "est.", shopCost: "shop", save: "save",  stopTitle: "STOP: don't continue on your own", triedTitle: "Time for a repair shop", stopNow: "Do this now:",
        stopNowRed: ["Switch it off and unplug it / close the gas / stop the engine.", "Don't open the casing or the inside.", "Take it to a service centre or call a technician, and show them this report."],
        stopNowTried: ["Leave it switched off and safe.", "Download the PDF report: it lists everything already tried.", "Show it to the shop so they don't start from zero."],
        findService: "Find a service centre nearby", emergency: "Emergency (fire, smoke, strong gas smell): call 112.", copied: "Link copied", openW: "Reasoning: Muse Spark Open (open weights)", demo: "Demo mode: sample answers, no API cost.",
        green: "SAFE", amber: "CAUTION", red: "STOP", pass: "✅ Step looks right", fail: "⚠️ Not quite", checking: "Checking photo…",
        verified: "steps verified by camera", recording: "Recording…", recorded: "Voice recorded ✓", micErr: "Microphone unavailable. Please type the problem.",
        netErr: "Connection lost. Check your signal and try again.", offline: "You are offline. Diagnosis needs a signal; your photos stay on your phone.",
        exhausted: "All tried", newPlan: "New plan ready.", photos: "photos", videoBtn: "🎥 Or record a 5–10 s video", videoOk: "Video ready ✓ (the 3 sharpest frames are picked for you)", videoBig: "That video is too big. Record 5–10 seconds.", badFile: "That file is not a photo. Pick a JPG, PNG or HEIC picture.", unreadPhoto: "That photo could not be read. Try a JPG or PNG.", bigFile: "That file is too big. Try a smaller photo.", emptyFile: "That file is empty. Take it again.", tooLong: "That text is too long. Shorten it a little." },
};
// Basa Jawa (ngoko, as spoken around Semarang). Falls back to Bahasa Indonesia for any key not listed.
T.jv = Object.assign({}, T.id, {
  hero: "Apa sing rusak?", heroSub: "Foto barange, critakna masalahe, entuk pandhuan ndandani langkah demi langkah.", takePhoto: "Jupuk foto (1–3)",
  catMotor: "Motor", catPump: "Pompa banyu", catAppliance: "Elektronik omah", catPlumbing: "Pipa/kran", catOther: "Liyane",
  record: "Tutul kanggo ngomong", stop: "Tutul kanggo mandheg", typeHere: "…utawa ketik masalahe ing kene", go: "Priksa saiki",
  samples: "Jajal conto:", sMotor: "motor mogok", sPump: "pompa ora metu banyu", sFaucet: "kran netes", sRice: "rice cooker mati", sTire: "ban kempes",
  working: "Lagi dipriksa…", retry: "Jajal maneh", answerHere: "Wangsulanmu", send: "Kirim", diagnosis: "Diagnosa", safetyFirst: "Slamet dhisik",
  tools: "Piranti", materials: "Suku cadang", listen: "Rungokna", next: "Terus", handsFree: "Mode tanpa tangan (diwacakake + prentah swara)", vListening: "Ngrungokake… ucapna terus, bali, baleni, priksa, isih rusak, utawa mandheg.", vHelp: "Prentah swara: terus · bali · baleni · priksa · isih rusak · mandheg", vNoSR: "HP iki ora bisa ngrungokake terus. Tutul tombol mikrofon saben prentah.", ptt: "🎙️ Tutul, banjur ucapna prentah", pttRec: "⏹️ Ngomong saiki… (tutul kanggo ngirim)", vHeard: "Krungu «{text}»", vUnknown: "Durung ngerti «{text}». Jajal terus, bali, baleni, priksa.", vOff: "Mode tanpa tangan mati.",
  done: "Rampung yen:", outcomeAsk: "Wis urip maneh?", fixedBtn: "Wis rampung 🎉", proBtn: "Digawa menyang bengkel", fixedThanks: "Apik! Ndandani rampung.", proThanks: "Ora apa-apa, digawa menyang ahli iku pilihan sing aman. Laporan PDF bisa dituduhake marang mekanik.", savedTotal: "Total irit", savedFrom: "saka", savedUnit: "ndandani", preTitle: "Sadurunge miwiti, priksa:", preLocked: "Centhang kabeh dhisik, banjur langkah 1 mbukak.", preReady: "✅ Siap. Langkah 1 wis mbukak.", waitFor: "Antosna {n} menit", timerStart: "Wiwiti pangetung wektu", timerStop: "Mandhegna", timerDone: "Wektu antosan wis rampung. Terus menyang langkah sabanjure.", checkStep: "Priksa langkah iki", trialMin: "Uji coba: pirang menit ndandani?", fbNote: "🧪 Wangsulan conto (API live lagi ora kasedhiya)", mech: "🧑‍🔧 Celuk mekanik / bengkel", hoSub: "Kirim ringkesan iki menyang bengkel, banjur goleki sing paling cedhak. Laporan PDF ana ringkesan kanggo mekanik.", hoWa: "Kirim lewat WhatsApp", hoMaps: "Bengkel/servis paling cedhak", hoPdf: "Laporan PDF kanggo mekanik", hoMsg: "Pesen sing dikirim", liveGuide: "Pandhuan kamera langsung", liveCheck: "📸 Priksa saiki", liveClose: "Tutup kamera", liveStart: "Nguripake kamera…", liveAim: "Arahna kamera menyang {name}", liveFound: "🎯 Ketemu {name}", liveLost: "Durung ketemu {name}. Obahna HP alon-alon.", liveNoPart: "Langkah iki ora nuduhake perangan tartamtu. Enggo Priksa saiki.", liveNoCam: "Kamera langsung ora bisa dienggo ing HP iki. Enggo tombol foto kanggo mriksa langkah.", liveLimit: "Wates kamera langsung kanggo ndandani iki wis entek. Enggo foto kanggo mriksa langkah.", share: "Bagekna laporan", pdf: "Undhuh laporan PDF", workshop: "Lembar bengkel (cetak gedhe)", hood: "Ing mburi layar: model sing dipakai", hs_listen: "Rungokake swara", hs_gate: "Priksa slamet teks", hs_look: "Delok foto", hs_segment: "Tandhani bagean", hs_diagnose: "Diagnosa", hs_plan: "Nyusun langkah", hs_safety: "Priksa slamet rencana", hs_illustrate: "Gambar bantu", hs_narrate: "Swara panuntun", wa: "Kirim dhaptar blanja menyang WhatsApp", buy: "Golek rega", garage: "Garasiku",
  garageNote: "Riwayat ndandani mung disimpen ing HP iki. Pandhuan bisa dibukak 24 jam.", garageClear: "Busak riwayat", again: "Ndandani barang liya", erase: "Busak fotoku saiki", eraseAsk: "Busak foto, swara, lan pandhuan iki saka server saiki?", erased: "Wis dibusak saka server.",
  stuck: "Isih rusak, jajal rencana liya", stuckHere: "Kepiye kedadeyane? (umpamane wis dijajal, tetep mati)",
  needPhoto: "Jupuk utawa unggah foto dhisik.", needDesc: "Critakna masalahe (swara utawa ketik).",
  footer: "Mung kanggo ndandani sing entheng. Yen gas, listrik omah, utawa tegangan dhuwur, celuk teknisi.",
  stages: { listen: "Ngrungokake", gate: "Priksa keamanan wiwitan", look: "Ndeleng foto", segment: "Nandhani perangan (SAM 3.1)", diagnose: "Nggoleki sebabe",
            plan: "Nyusun langkah", safety: "Priksa keamanan rencana", illustrate: "Nggambar diagram", narrate: "Nyiapake swara" },
  diff: "Angel", min: "menit", est: "kira-kira", shopCost: "bengkel", save: "irit",  stopTitle: "MANDHEG: aja diterusake dhewe", triedTitle: "Wayahe menyang bengkel/servis", stopNow: "Tindakake saiki:",
  stopNowRed: ["Pateni lan copot saka listrik / tutup gas / pateni mesin.", "Aja mbukak casing utawa jerone.", "Gawanen menyang servis resmi utawa celuk teknisi, tuduhna laporan iki."],
  stopNowTried: ["Jarna tetep mati lan aman.", "Undhuh laporan PDF: isine apa wae sing wis dijajal.", "Tuduhna menyang bengkel/servis supaya ora mbaleni saka nol."],
  findService: "Golek servis paling cedhak", emergency: "Darurat (geni, kebul, ambu gas banget): telpon 112.", copied: "Tautan wis disalin", openW: "Nalar: Muse Spark Open (open weights)",
  demo: "Mode demo: wangsulan conto, tanpa biaya API.",
  green: "AMAN", amber: "ATI-ATI", red: "MANDHEG", pass: "✅ Langkah iki wis bener", fail: "⚠️ Durung pas", checking: "Mriksa foto…",
  verified: "langkah wis dicek kamera", recording: "Ngrekam…", recorded: "Swara kerekam ✓", micErr: "Mikrofon ora bisa dienggo. Ketik wae masalahe.",
  netErr: "Sambungan megat. Priksa sinyal banjur coba maneh.", offline: "Ora ana internet. Diagnosis butuh sinyal; foto sampeyan tetep aman ing HP.",
  exhausted: "Wis kabeh dijajal", newPlan: "Rencana anyar wis siap.", photos: "foto", videoBtn: "🎥 Utawa rekam video 5–10 detik", videoOk: "Video siap ✓ (3 gambar paling cetha dijupuk otomatis)", videoBig: "Videone kegedhen. Rekam 5–10 detik wae.", badFile: "Berkas iku dudu foto. Pilih foto JPG, PNG, utawa HEIC.", unreadPhoto: "Foto iku ora bisa diwaca. Jajal foto JPG utawa PNG.", bigFile: "Berkase kegedhen. Jajal foto sing luwih cilik.", emptyFile: "Berkase kosong. Jupuk maneh.", tooLong: "Tulisane kepanjangen. Cekak-ana dhisik.",
});

/* I18N_EXTRA:start (v1.22: 1-tap demo, agent log, progress, quick answers). api/tests/test_i18n.py checks all three. */
const T_EXTRA = {
  id: { demoBtn: "▶ Coba demo 1 ketuk", demoSub: "Tanpa foto, tanpa akun: lihat AI memperbaiki motor mogok dari awal sampai cek kamera.",
        how1: "📷 Foto + cerita", how2: "🎯 AI tandai bagiannya", how3: "✅ Tiap langkah dicek kamera",
        agentTitle: "🤖 Yang dilakukan AI", agentSub: "Tiap keputusan agen, alat yang dipakai, dan kapan ia berhenti.", agentLive: "Log agen",
        lp_see: "Lihat", lp_think: "Nalar", lp_ask: "Tanya", lp_plan: "Rencana", lp_guard: "Jaga", lp_verify: "Cek", lp_replan: "Ulang rencana", lp_handoff: "Serahkan",
        ag_listen: "Mendengar suaramu dan mengubahnya jadi teks", ag_gate_ok: "Cek kata berbahaya (gas, listrik rumah, rem…): aman, lanjut",
        ag_gate_stop: "Kata berbahaya terdeteksi ({category}): berhenti sebelum memanggil model", ag_look: "Melihat foto: {object}, {n} bagian dikenali",
        ag_segment: "Menandai {found} dari {of} bagian di fotomu (masker piksel)", ag_diagnose: "Paling mungkin: {cause} ({conf}%), dari {n} kemungkinan",
        ag_ask: "Baru yakin {conf}% (di bawah {threshold}%): bertanya satu hal dulu, bukan menebak", ag_answer: "Jawabanmu diterima, diagnosa diulang",
        ag_plan: "Menyusun {steps} langkah untuk: {cause}", ag_guard_ok: "Rencana dicek aturan keselamatan di kode: lolos ({level})",
        ag_guard_stop: "Rencana ditolak aturan keselamatan: STOP", ag_illustrate: "Menggambar {made} dari {of} diagram dari fotomu",
        ag_redrawn: ", {redrawn} digambar ulang setelah diperiksa", ag_check_ok: "Langkah {step} dicek dari foto baru: benar",
        ag_check_fail: "Langkah {step} dicek dari foto baru: belum pas, diberi koreksi", ag_check_esc: " (gagal berulang, menyarankan rencana lain)",
        ag_replan: "Masih rusak: rencana baru {steps} langkah untuk {cause}", ag_esc_red: "Terlalu berbahaya dikerjakan sendiri: diarahkan ke teknisi + laporan",
        ag_esc_exhausted: "Semua sebab yang aman sudah dicoba: diserahkan ke bengkel dengan laporan",
        ag_fallback: "Model live gagal setelah dicoba ulang: tahap {stage} memakai jawaban demo (diberi label)",
        ag_input_guard: "Ada kalimat berupa perintah di inputmu: diperlakukan sebagai data dan diabaikan",
        ag_outcome_fixed: "Kamu konfirmasi: sudah beres", ag_outcome_pro: "Kamu memilih membawa ke bengkel", ag_retry: "Mencoba ulang tahap yang gagal (ke-{n})",
        note_typed: "diketik", note_stop: "dihentikan demi keselamatan", note_photo: "foto sudah cukup", note_browser: "suara browser", note_nocomp: "tidak ada bagian terlihat", note_steps: "{n} langkah",
        agCode: "kode", elapsed: "{n} dtk", qYes: "Ya", qNo: "Tidak", qUnsure: "Tidak tahu",
        tourProgress: "Demo: AI sedang bekerja. Tiap baris = satu model Meta atau aturan keselamatan.", tourAsk: "AI belum yakin, jadi ia bertanya. Ketuk salah satu jawaban.",
        tourResult: "Lihat bagian yang ditandai SAM 3.1 dan log 'Yang dilakukan AI'. Lalu centang daftar keselamatan untuk membuka langkah 1.",
        tourCheck: "Coba 'Cek langkah ini' dengan foto contoh: foto gelap ditolak, foto benar lolos.",
        tourStuck: "Lalu ketuk 'Masih rusak' di bawah untuk melihat AI menyusun ulang rencananya.", tourClose: "Tutup", tourTip: "Tampilkan tip", tourHide: "Kecilkan tip",
        sampleTry: "Belum punya foto? Coba foto contoh:", sampleBad: "📷 Foto gelap ✗", sampleGood: "📷 Foto benar ✓",
        pv_title: "Temuan sejauh ini", pv_seen: "👁️ Terlihat: {object}", pv_parts: "🎯 SAM 3.1 menandai {found} dari {of} bagian", pv_cause: "🧠 Paling mungkin: {cause} ({conf}%)", pv_steps: "📋 {n} langkah siap", pv_img: "Foto dengan bagian yang ditandai SAM 3.1", agJump: "Tunjukkan di layar" },
  jv: { demoBtn: "▶ Jajal demo sak tutulan", demoSub: "Tanpa foto, tanpa akun: delengen AI ndandani motor mogok saka wiwitan nganti dicek kamera.",
        how1: "📷 Foto + crita", how2: "🎯 AI nandhani perangane", how3: "✅ Saben langkah dicek kamera",
        agentTitle: "🤖 Sing ditindakake AI", agentSub: "Saben keputusan agen, piranti sing dienggo, lan kapan mandheg.", agentLive: "Log agen",
        lp_see: "Ndeleng", lp_think: "Mikir", lp_ask: "Takon", lp_plan: "Rancangan", lp_guard: "Njaga", lp_verify: "Mriksa", lp_replan: "Rancang maneh", lp_handoff: "Pasrahake",
        ag_listen: "Ngrungokake swaramu lan ngowahi dadi tulisan", ag_gate_ok: "Priksa tembung mbebayani (gas, listrik omah, rem…): aman, terus",
        ag_gate_stop: "Ana tembung mbebayani ({category}): mandheg sadurunge takon model", ag_look: "Ndeleng foto: {object}, {n} perangan ditemokake",
        ag_segment: "Nandhani {found} saka {of} perangan ing fotomu (masker piksel)", ag_diagnose: "Sing paling mungkin: {cause} ({conf}%), saka {n} kemungkinan",
        ag_ask: "Lagi yakin {conf}% (ing ngisor {threshold}%): takon siji bab dhisik, ora ngira-ira", ag_answer: "Wangsulanmu ditampa, diagnosa dibaleni",
        ag_plan: "Nyusun {steps} langkah kanggo: {cause}", ag_guard_ok: "Rencana dipriksa aturan keamanan ing kode: lolos ({level})",
        ag_guard_stop: "Rencana ditolak aturan keamanan: MANDHEG", ag_illustrate: "Nggambar {made} saka {of} diagram saka fotomu",
        ag_redrawn: ", {redrawn} digambar maneh sawise dipriksa", ag_check_ok: "Langkah {step} dipriksa saka foto anyar: bener",
        ag_check_fail: "Langkah {step} dipriksa saka foto anyar: durung pas, diwenehi koreksi", ag_check_esc: " (gagal bola-bali, nyaranake rencana liya)",
        ag_replan: "Isih rusak: rencana anyar {steps} langkah kanggo {cause}", ag_esc_red: "Kebangeten mbebayani yen digarap dhewe: diarahake menyang teknisi + laporan",
        ag_esc_exhausted: "Kabeh sebab sing aman wis dijajal: dipasrahake menyang bengkel karo laporan",
        ag_fallback: "Model live gagal sawise dijajal maneh: tahap {stage} nganggo wangsulan demo (ana labele)",
        ag_input_guard: "Ana ukara prentah ing inputmu: dianggep data lan ora digatekake",
        ag_outcome_fixed: "Sampeyan ngonfirmasi: wis rampung", ag_outcome_pro: "Sampeyan milih nggawa menyang bengkel", ag_retry: "Nyoba maneh tahap sing gagal (kaping {n})",
        note_typed: "ditulis", note_stop: "dimandhegake kanggo keamanan", note_photo: "foto wis cukup", note_browser: "swara browser", note_nocomp: "ora ana perangan sing katon", note_steps: "{n} langkah",
        agCode: "kode", elapsed: "{n} dtk", qYes: "Iya", qNo: "Ora", qUnsure: "Ora ngerti",
        tourProgress: "Demo: AI lagi nyambut gawe. Saben baris = siji model Meta utawa aturan keamanan.", tourAsk: "AI durung yakin, mula takon. Tutul salah siji wangsulan.",
        tourResult: "Delengen perangan sing ditandhani SAM 3.1 lan log 'Sing ditindakake AI'. Banjur centhang dhaptar keamanan kanggo mbukak langkah 1.",
        tourCheck: "Jajal 'Priksa langkah iki' nganggo foto conto: foto peteng ditolak, foto bener lolos.",
        tourStuck: "Banjur tutul 'Isih rusak' ing ngisor kanggo ndeleng AI nyusun rencana anyar.", tourClose: "Tutup", tourTip: "Tampilake pitutur", tourHide: "Cilikna pitutur",
        sampleTry: "Durung duwe foto? Jajal foto conto:", sampleBad: "📷 Foto peteng ✗", sampleGood: "📷 Foto bener ✓",
        pv_title: "Temuan nganti saiki", pv_seen: "👁️ Katon: {object}", pv_parts: "🎯 SAM 3.1 nandhani {found} saka {of} perangan", pv_cause: "🧠 Sing paling mungkin: {cause} ({conf}%)", pv_steps: "📋 {n} langkah wis siyap", pv_img: "Foto karo perangan sing ditandhani SAM 3.1", agJump: "Tuduhna ing layar" },
  en: { demoBtn: "▶ Try the 1-tap demo", demoSub: "No photo, no account: watch the AI fix a bike that won't start, right up to the camera check.",
        how1: "📷 Snap + say it", how2: "🎯 AI marks the part", how3: "✅ Every step camera-checked",
        agentTitle: "🤖 What the AI did", agentSub: "Every decision the agent made, the tool it used, and when it stopped.", agentLive: "Agent log",
        lp_see: "See", lp_think: "Reason", lp_ask: "Ask", lp_plan: "Plan", lp_guard: "Guard", lp_verify: "Verify", lp_replan: "Re-plan", lp_handoff: "Hand off",
        ag_listen: "Listened to your voice note and turned it into text", ag_gate_ok: "Scanned your words for hazards (gas, mains, brakes…): clear",
        ag_gate_stop: "Hazard words found ({category}): stopped before any model call", ag_look: "Looked at the photo: {object}, {n} parts located",
        ag_segment: "Outlined {found} of {of} parts on your photo (pixel masks)", ag_diagnose: "Most likely: {cause} ({conf}%), out of {n} causes",
        ag_ask: "Only {conf}% sure (below {threshold}%): asked one question instead of guessing", ag_answer: "Got your answer, re-ran the diagnosis",
        ag_plan: "Planned {steps} steps for: {cause}", ag_guard_ok: "Plan checked by safety rules in code: passed ({level})",
        ag_guard_stop: "Plan blocked by safety rules: STOP", ag_illustrate: "Drew {made} of {of} helper diagrams from your photo",
        ag_redrawn: ", {redrawn} redrawn after review", ag_check_ok: "Step {step} checked from your new photo: correct",
        ag_check_fail: "Step {step} checked from your new photo: not yet, sent a correction", ag_check_esc: " (repeated fails, suggested another plan)",
        ag_replan: "Still broken: new {steps}-step plan for {cause}", ag_esc_red: "Too dangerous to do alone: handed off to a professional with a report",
        ag_esc_exhausted: "Every safe cause tried: handed off to a workshop with a report",
        ag_fallback: "Live model failed after retries: {stage} used the labelled demo answer",
        ag_input_guard: "Your input contained instruction-like text: treated as data and ignored",
        ag_outcome_fixed: "You confirmed: it works now", ag_outcome_pro: "You chose to take it to a mechanic", ag_retry: "Retried the failed stage (#{n})",
        note_typed: "typed", note_stop: "safety stop", note_photo: "photo is enough", note_browser: "browser voice", note_nocomp: "no visible parts", note_steps: "{n} steps",
        agCode: "code", elapsed: "{n} s", qYes: "Yes", qNo: "No", qUnsure: "Not sure",
        tourProgress: "Demo: the AI is working. Each line is one Meta model or safety rule.", tourAsk: "The AI isn't sure, so it asks. Tap an answer.",
        tourResult: "See the parts SAM 3.1 outlined and the 'What the AI did' log. Then tick the safety list to unlock step 1.",
        tourCheck: "Try 'Check this step' with a sample photo: the dark one is rejected, the right one passes.",
        tourStuck: "Then tap 'Still broken' below to watch the AI re-plan.", tourClose: "Close", tourTip: "Show tip", tourHide: "Minimise tip",
        sampleTry: "No photo yet? Try a sample photo:", sampleBad: "📷 Dark photo ✗", sampleGood: "📷 Right photo ✓",
        pv_title: "Found so far", pv_seen: "👁️ Seen: {object}", pv_parts: "🎯 SAM 3.1 outlined {found} of {of} parts", pv_cause: "🧠 Most likely: {cause} ({conf}%)", pv_steps: "📋 {n} steps ready", pv_img: "Your photo with the parts SAM 3.1 outlined", agJump: "Show it on screen" },
};
/* I18N_EXTRA:end */
["id", "jv", "en"].forEach((k) => Object.assign(T[k], T_EXTRA[k]));

/* I18N_REPLAY:start (v1.24: recorded demo when the server sleeps). api/tests/test_replay.py checks all three. */
const T_REPLAY = {
  id: { rpBadge: "▶ Demo rekaman: putaran mode demo yang disimpan, tanpa server", rpWake: "Server sedang bangun (hosting gratis, bisa sampai 1 menit). Tombol demo langsung memutar demo rekaman.",
        rpOwnPhoto: "Demo rekaman hanya bisa memutar dua foto contoh. Foto kamu sendiri perlu server live: muat ulang halaman sebentar lagi.",
        rpOnlyDemo: "Demo rekaman hanya berisi contoh motor. Untuk foto sendiri atau contoh lain, muat ulang saat server sudah bangun.",
        rpNoLive: "Bagian ini perlu server live; demo rekaman tidak bisa melakukannya.", rpNoMore: "Demo rekaman hanya punya satu rencana ulang.",
        planOf: "🔁 Rencana {n} dari {m}: {cause}", triedMark: "sudah dicoba", stopHead: "Dihentikan demi keselamatan", deskNote: "Dibuat untuk HP: buka halaman ini di HP untuk kamera, suara, dan cek langkah.",
        thumbCap: "Foto contoh (pengganti) dengan bagian yang ditandai SAM 3.1" },
  jv: { rpBadge: "▶ Demo rekaman: puteran mode demo sing disimpen, tanpa server", rpWake: "Server lagi tangi (hosting gratis, bisa nganti 1 menit). Tombol demo langsung muter demo rekaman.",
        rpOwnPhoto: "Demo rekaman mung bisa muter loro foto conto. Foto sampeyan dhewe butuh server live: muat maneh kaca iki sedhela engkas.",
        rpOnlyDemo: "Demo rekaman mung isi conto motor. Kanggo foto dhewe utawa conto liya, muat maneh yen server wis tangi.",
        rpNoLive: "Bagean iki butuh server live; demo rekaman ora bisa nindakake.", rpNoMore: "Demo rekaman mung duwe siji rencana anyar.",
        planOf: "🔁 Rencana {n} saka {m}: {cause}", triedMark: "wis dijajal", stopHead: "Dimandhegake supaya slamet", deskNote: "Digawe kanggo HP: bukak kaca iki ing HP kanggo kamera, swara, lan cek langkah.",
        thumbCap: "Foto conto (gantosan) kanthi bagean sing ditandhani SAM 3.1" },
  en: { rpBadge: "▶ Recorded demo: a saved demo-mode run, no server", rpWake: "The server is waking up (free hosting, up to a minute). The demo button plays a recorded run right away.",
        rpOwnPhoto: "The recorded demo can only play the two sample photos. Your own photo needs the live server: reload the page in a moment.",
        rpOnlyDemo: "The recorded demo only has the motorbike sample. For your own photo or another sample, reload once the server is awake.",
        rpNoLive: "This part needs the live server; the recorded demo can't do it.", rpNoMore: "The recorded demo has only one re-plan.",
        planOf: "🔁 Plan {n} of {m}: {cause}", triedMark: "tried", stopHead: "Stopped for your safety", deskNote: "Made for phones: open this page on your phone for the camera, voice and step checks.",
        thumbCap: "Stand-in sample photo with the parts SAM 3.1 marked" },
};
/* I18N_REPLAY:end */
["id", "jv", "en"].forEach((k) => Object.assign(T[k], T_REPLAY[k]));

/* I18N_DESK:start (v1.25: laptop view side panel). api/tests/test_desk.py checks all three. */
const T_DESK = {
  id: { deskKicker: "Dibuat dengan Muse Spark + SAM 3.1", deskTag: "Perbaiki sendiri, dengan aman. Dalam Bahasa Jawa.",
        deskWhat: "Foto barang yang rusak dan ceritakan masalahnya. Muse Spark mencari penyebabnya, SAM 3.1 menandai bagiannya di foto, dan kamera mengecek tiap langkah perbaikan.",
        deskB1: "📷 Foto + suara, Bahasa Jawa, Indonesia, atau Inggris", deskB2: "🎯 Bagian yang perlu disentuh ditandai di fotomu", deskB3: "✅ Tiap langkah dicek kamera sebelum lanjut",
        deskB4: "⛔ Gas, listrik rumah, rem: berhenti dan arahkan ke teknisi", deskDemo: "▶ Putar demo 1 ketuk di sini",
        deskQr: "Pindai untuk membuka di HP", deskQrSub: "Kamera, suara, dan cek langkah paling enak di HP.", deskQrLocal: "Alamat ini hanya jalan di komputer ini." },
  jv: { deskKicker: "Digawe nganggo Muse Spark + SAM 3.1", deskTag: "Dandani dhewe, kanthi slamet. Nganggo Basa Jawa.",
        deskWhat: "Foto barang sing rusak lan critakna masalahe. Muse Spark nggoleki sababe, SAM 3.1 menehi tandha bagean ing foto, lan kamera mriksa saben langkah.",
        deskB1: "📷 Foto + swara, Basa Jawa, Indonesia, utawa Inggris", deskB2: "🎯 Bagean sing kudu didandani ditandhani ing fotomu", deskB3: "✅ Saben langkah dicek kamera sadurunge lanjut",
        deskB4: "⛔ Gas, listrik omah, rem: mandheg lan diarahke menyang teknisi", deskDemo: "▶ Puter demo sak tutulan ing kene",
        deskQr: "Pindai kanggo mbukak ing HP", deskQrSub: "Kamera, swara, lan cek langkah paling kepenak ing HP.", deskQrLocal: "Alamat iki mung mlaku ing komputer iki." },
  en: { deskKicker: "Built with Muse Spark + SAM 3.1", deskTag: "Fix it yourself, safely. In Javanese.",
        deskWhat: "Photograph something broken and say what's wrong. Muse Spark finds the likely cause, SAM 3.1 marks the parts on your photo, and the camera checks each repair step.",
        deskB1: "📷 Photo + voice in Javanese, Indonesian or English", deskB2: "🎯 The parts to touch are marked on your photo", deskB3: "✅ Each step is checked by the camera before you go on",
        deskB4: "⛔ Gas, mains power, brakes: it stops and hands you to a pro", deskDemo: "▶ Play the 1-tap demo here",
        deskQr: "Scan to open on your phone", deskQrSub: "Camera, voice and step checks work best on a phone.", deskQrLocal: "This address only works on this computer." },
};
/* I18N_DESK:end */
["id", "jv", "en"].forEach((k) => Object.assign(T[k], T_DESK[k]));

// First visit: ?lang=id|jv|en, else the phone's language list (Indonesian or Javanese anywhere in it means that language,
// so an Indonesian phone set to English still opens in Bahasa), else English for a visitor from anywhere else.
function pickLang() {
  let saved = ""; try { saved = localStorage.getItem("tc_lang") || ""; } catch (_) { /* storage blocked */ }
  if (["id", "jv", "en"].includes(saved)) return saved;
  try { const q = new URLSearchParams(location.search).get("lang"); if (["id", "jv", "en"].includes(q)) return q; } catch (_) { /* odd URL */ }
  const prefs = (navigator.languages && navigator.languages.length ? Array.from(navigator.languages) : [navigator.language]).map((x) => String(x || "").toLowerCase());
  if (!prefs[0]) return "id";
  const local = prefs.find((x) => /^(id|in|jv)(-|$)/.test(x));
  return local ? (/^jv/.test(local) ? "jv" : "id") : "en";
}
let lang = pickLang();
let videoFile = null;
let photoFiles = [], audioBlob = null, rec = null, chunks = [], S = null, stepIdx = 0, category = "", es = null;
const t = (k) => (T[lang] && T[lang][k] !== undefined ? T[lang][k] : T.id[k] !== undefined ? T.id[k] : k);
const rupiah = (n) => "Rp" + Number(n || 0).toLocaleString("id-ID");
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const on = (id, ev, fn) => $(id) && $(id).addEventListener(ev, fn);
window.tcT = (k) => t(k);  // web/replay.js shows its messages in the chosen language
const replayOn = () => !!(window.TCReplay && window.TCReplay.active());
const apiHref = (p) => (replayOn() ? window.TCReplay.href(p) : p);  // PDF links point at the recorded copy in a replay

function applyLang() {
  document.documentElement.lang = lang === "en" ? "en" : lang === "jv" ? "jv" : "id";
  document.querySelectorAll("[data-t]").forEach((el) => (el.textContent = t(el.dataset.t)));
  document.querySelectorAll("[data-tp]").forEach((el) => (el.placeholder = t(el.dataset.tp)));
  if ($("lang")) $("lang").value = lang;
  if (S) { renderProgress(S); if (S.plan) render(S); }
  if ($("garage") && !$("capture").classList.contains("hidden")) renderGarage();
  badges(); markLang();
  if (window.__offlineRefresh) window.__offlineRefresh();
}

let HEALTH = null;
// Header badges: demo mode, and the open-weights brain (Muse Spark Open on Baseten) when it is really in use.
function badges() {
  if (!HEALTH) return;
  if (HEALTH.mode === "mock") { $("modeBadge").textContent = t("demo"); $("modeBadge").classList.remove("hidden"); }
  if (HEALTH.mode === "replay") { $("modeBadge").textContent = t("rpBadge"); $("modeBadge").classList.add("replay"); $("modeBadge").classList.remove("hidden"); }
  if (HEALTH.open_weights && $("owBadge")) { $("owBadge").textContent = "🔓 " + t("openW"); $("owBadge").classList.remove("hidden"); }
}

// A sleeping free-tier server can take ~50 s to answer. Wait WAKE_MS at most: after that the 1-tap demo plays the
// recorded run (web/replay.js) instead, and a note says so. A late answer still fills in the badges.
const WAKE_MS = 4000;
let healthP = null, serverSlow = false;
function wakeNote(v) {
  serverSlow = v;
  const n = $("wakeNote"); if (!n) return;
  n.textContent = v ? "⏳ " + t("rpWake") : ""; n.classList.toggle("hidden", !v || replayOn());
}
function health() {
  if (window.TCReplay && window.TCReplay.forced() && !replayOn()) {  // ?replay=1: always the recording (judges, tests)
    healthP = window.TCReplay.start(lang).then((ok) => (ok ? fetch("/api/health") : Promise.reject(new Error("no replay"))))
      .then((r) => r.json()).then((h) => { HEALTH = h; badges(); return false; }).catch(() => false);
    return healthP;
  }
  const req = fetch("/api/health").then((r) => { if (!r.ok) throw new Error(r.statusText); return r.json(); });
  req.then((h) => { if (!replayOn() || h.mode === "replay") { HEALTH = h; badges(); } wakeNote(false); }).catch(() => {});
  healthP = Promise.race([req.then(() => true), new Promise((res) => setTimeout(() => res(false), WAKE_MS))])
    .catch(() => false).then((ok) => { if (!ok && window.TCReplay) wakeNote(true); return ok; });
  return healthP;
}
// true when the 1-tap demo should play the recording: offline, forced, or no server answer within WAKE_MS
async function useReplay() {
  if (!window.TCReplay) return false;
  if (replayOn()) return true;
  if (typeof navigator !== "undefined" && navigator.onLine === false) return true;
  if (HEALTH && !serverSlow) return false;
  return !(await (healthP || health()));
}

/* Network trouble: friendly text instead of "Failed to fetch", plus a banner while the phone is offline. */
/* The server's refusals are English; show the owner's language for the ones a person can cause. */
const SERVER_MSGS = [
  [/unsupported file type/i, "badFile"], [/could not read that (photo|frame)/i, "unreadPhoto"], [/file too large/i, "bigFile"],
  [/empty file/i, "emptyFile"], [/too long/i, "tooLong"], [/describe the problem by voice or text/i, "needDesc"],
  [/take or upload a photo/i, "needPhoto"],
];
function localServerMsg(m) {
  const hit = SERVER_MSGS.find(([re]) => re.test(m));
  return hit ? t(hit[1]) : "";
}
function netMsg(e) {
  const m = e && e.message ? String(e.message) : "";
  const local = localServerMsg(m);
  if (local) return local;
  return (!e || e.name === "TypeError" || /failed to fetch|load failed|networkerror|network request/i.test(m) || (typeof navigator !== "undefined" && navigator.onLine === false)) ? t("netErr") : (m || t("netErr"));
}
function setupOffline() {
  const bar = $("offlineBar"); if (!bar) return;
  const upd = () => { bar.textContent = "📡 " + t("offline"); bar.classList.toggle("hidden", navigator.onLine !== false); };
  window.addEventListener("online", upd); window.addEventListener("offline", upd);
  window.__offlineRefresh = upd; upd();
}

/* ---------------- capture ---------------- */
function isPhotoFile(f) {
  return /^image\//i.test(f.type || "") || /\.(jpe?g|png|webp|gif|bmp|heic|heif|jfif)$/i.test(f.name || "");
}
function setupCapture() {
  on("lang", "change", (e) => { lang = e.target.value; localStorage.setItem("tc_lang", lang); applyLang(); });
  on("video", "change", (e) => {
    videoFile = e.target.files[0] || null;
    if (videoFile && videoFile.size > 40 * 1024 * 1024) { videoFile = null; $("formErr").textContent = t("videoBig"); return; }
    $("videoHint").textContent = videoFile ? t("videoOk") : "";
  });
  on("photo", "change", (e) => {
    const picked = [...e.target.files];
    photoFiles = picked.filter(isPhotoFile).slice(0, 3);
    $("formErr").textContent = picked.length && !photoFiles.length ? t("badFile") : "";  // say so now, not after Go
    const pv = $("photoPreview");
    if (photoFiles.length) {
      pv.onerror = () => { pv.classList.add("hidden"); $("photoHint").textContent = "📷 " + (photoFiles[0].name || "") + (photoFiles.length > 1 ? ` +${photoFiles.length - 1}` : ""); };  // e.g. HEIC the browser can't draw
      pv.src = URL.createObjectURL(photoFiles[0]); pv.classList.remove("hidden");
      $("photoHint").textContent = photoFiles.length > 1 ? `${photoFiles.length} ${t("photos")}` : "";
    } else if (picked.length) {
      pv.removeAttribute("src"); pv.classList.add("hidden"); $("photoHint").textContent = "📷 " + t("takePhoto");
      e.target.value = "";
    }
  });
  document.querySelectorAll("#cats .chip").forEach((b) => b.addEventListener("click", () => {
    category = category === b.dataset.cat ? "" : b.dataset.cat;
    document.querySelectorAll("#cats .chip").forEach((x) => { x.classList.toggle("on", x.dataset.cat === category); x.setAttribute("aria-pressed", String(x.dataset.cat === category)); });
  }));
  document.querySelectorAll("#cats .chip").forEach((x) => x.setAttribute("aria-pressed", "false"));
  setupKeyboardPickers();
  on("micBtn", "click", toggleRec);
  on("goBtn", "click", () => submit(""));
  document.querySelectorAll(".sample").forEach((b) => b.addEventListener("click", () => submit(b.dataset.sample)));
  on("answerBtn", "click", sendAnswer);
  on("retryBtn", "click", async () => {
    $("retryBtn").disabled = true;
    try {
      const r = await fetch(`/api/sessions/${S.id}/retry`, { method: "POST" });
      if (r.ok) { $("jobErr").textContent = ""; $("retryBtn").classList.add("hidden"); follow(S.id); }
      else $("jobErr").textContent = (await r.json()).detail || "";
    } catch (e) { $("jobErr").textContent = netMsg(e);
    } finally { $("retryBtn").disabled = false; }
  });
}

async function toggleRec() {
  if (rec && rec.state === "recording") { rec.stop(); return; }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    chunks = []; rec = new MediaRecorder(stream);
    rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    rec.onstop = () => {
      stream.getTracks().forEach((tr) => tr.stop());
      audioBlob = new Blob(chunks, { type: rec.mimeType || "audio/webm" });
      $("micBtn").classList.remove("rec"); $("micBtn").setAttribute("aria-pressed", "false"); $("micBtn").innerHTML = "🎙️ " + esc(t("record")); $("recState").textContent = t("recorded");
    };
    rec.start(); $("micBtn").classList.add("rec"); $("micBtn").setAttribute("aria-pressed", "true"); $("micBtn").innerHTML = "⏹️ " + esc(t("stop")); $("recState").textContent = t("recording");
    setTimeout(() => rec && rec.state === "recording" && rec.stop(), 60000); // spec: max 60 s
  } catch (_) { $("formErr").textContent = t("micErr"); }
}

// Phone photos are 3-10 MB: shrink on the phone before upload so 4G is fast and cheap. Any failure sends the original.
async function shrinkImage(file, maxSide = 1600, quality = 0.85) {
  try {
    if (!file || !/^image\/(jpeg|png|webp)$/.test(file.type) || file.size < 400 * 1024) return file;
    if (typeof createImageBitmap !== "function" || typeof document === "undefined") return file;
    const bmp = await createImageBitmap(file);
    const k = Math.min(1, maxSide / Math.max(bmp.width, bmp.height));
    const c = document.createElement("canvas");
    c.width = Math.max(1, Math.round(bmp.width * k)); c.height = Math.max(1, Math.round(bmp.height * k));
    const ctx = c.getContext && c.getContext("2d");
    if (!ctx) return file;
    ctx.drawImage(bmp, 0, 0, c.width, c.height);
    if (bmp.close) bmp.close();
    const blob = await new Promise((res) => c.toBlob(res, "image/jpeg", quality));
    if (!blob || blob.size >= file.size) return file;
    return new File([blob], (file.name || "photo").replace(/\.[^.]+$/, "") + ".jpg", { type: "image/jpeg" });
  } catch (_) { return file; }
}

async function submit(sample) {
  $("formErr").textContent = "";
  const text = $("text").value.trim();
  if (!sample && !photoFiles.length && !videoFile) return ($("formErr").textContent = t("needPhoto"));
  if (!sample && !text && !audioBlob && !videoFile) return ($("formErr").textContent = t("needDesc"));
  $("goBtn").disabled = true;
  try {
    const fd = new FormData();
    fd.append("language", lang); fd.append("text", sample ? "" : text); fd.append("category", category);
    if (sample) fd.append("sample", sample);
    else (await Promise.all(photoFiles.map((f) => shrinkImage(f)))).forEach((f, i) => fd.append("photos", f, f.name || `photo${i + 1}.jpg`));
    if (videoFile && !sample) fd.append("video", videoFile, videoFile.name || "clip.mp4");  // server keeps the 3 sharpest frames
    if (audioBlob && !sample) {
      const ext = audioBlob.type.includes("mp4") ? "m4a" : audioBlob.type.includes("ogg") ? "ogg" : "webm";
      fd.append("audio", audioBlob, "voice." + ext);
    }
    const r = await fetch("/api/sessions", { method: "POST", body: fd });
    const j = await r.json();
    if (!r.ok) throw new Error(j.detail || r.statusText);
    history.pushState({ tc: 1 }, "", "#" + j.id);  // Back returns to the first screen instead of leaving the site
    show("progress"); startElapsed(); follow(j.id);
  } catch (e) { $("formErr").textContent = netMsg(e); }
  finally { $("goBtn").disabled = false; }
}

/* Keyboard and screen-reader access: the hidden file inputs sit inside labels, which a keyboard cannot reach. */
function setupKeyboardPickers() {
  ["photoBox", "videoBox", "stepPhotoLabel"].forEach((id) => {
    const el = $(id); if (!el) return;
    el.tabIndex = 0; el.setAttribute("role", "button");
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); const inp = el.querySelector("input"); if (inp) inp.click(); }
    });
  });
}

let firstShow = true;
// Laptop view: the app scrolls inside the phone frame (#screen), so a "back to the top" moves both.
function toTop() {
  if (typeof window.scrollTo === "function") window.scrollTo(0, 0);
  const sc = $("screen"); if (sc && sc.scrollHeight > sc.clientHeight) sc.scrollTop = 0;
}
function show(which) {
  ["capture", "progress", "result"].forEach((s) => $(s) && $(s).classList.toggle("hidden", s !== which));
  // Move focus to the new section's heading so screen-reader and keyboard users land on it (not on first load).
  if (!firstShow) {
    const h = $(which) && $(which).querySelector("h1, h2");
    if (h) { h.tabIndex = -1; try { h.focus({ preventScroll: true }); } catch (_) { /* old browsers */ } }
  }
  if (!firstShow) toTop();  // a new screen starts at its top (the result opened half-way down)
  firstShow = false;
  if ($("garage")) $("garage").classList.toggle("hidden", which !== "capture" || !loadGarage().length);
}

/* ---------------- progress (SSE, falls back to polling) ---------------- */
async function fetchSession(id) { const r = await fetch("/api/sessions/" + id); if (!r.ok) throw new Error("not found"); return r.json(); }

function follow(id) {
  if (es) es.close();
  const settle = async () => {
    S = await fetchSession(id); renderProgress(S);
    if (S.status === "ready") { stepIdx = 0; render(S); show("result"); }
  };
  if (window.EventSource) {
    es = new EventSource(`/api/sessions/${id}/events`);
    es.onmessage = (ev) => {
      const snap = JSON.parse(ev.data); S = Object.assign(S && S.id === snap.id ? S : {}, snap); renderProgress(S);
      if (!["created", "running"].includes(snap.status)) { es.close(); settle(); }
    };
    es.onerror = () => { es.close(); poll(id); };
  } else poll(id);
}

function poll(id) {
  fetchSession(id).then((s) => {
    S = s; renderProgress(s);
    if (["created", "running"].includes(s.status)) setTimeout(() => poll(id), 1200);
    else if (s.status === "ready") { stepIdx = 0; render(s); show("result"); }
  }).catch(() => setTimeout(() => poll(id), 2500));
}

function renderProgress(s) {
  if (!$("stageList") || !s.stages) return;
  $("stageList").innerHTML = Object.entries(s.stages).map(([k, v]) =>
    `<li id="st-${esc(k)}" class="${esc(v.status)}">${esc(t("stages")[k] || k)}${v.status === "skipped" ? "" : ` <code class="tool">${esc(stageTool(s, k))}</code>`}<span class="note">${esc(stageNote(v.note))}</span></li>`).join("");
  renderAgentLog(s, "agentLive"); renderPartial(s); reflash(); tickElapsed(); updateTour();
  if ($("progressStatus")) {  // short screen-reader status instead of re-announcing the whole list
    const run = Object.entries(s.stages).find(([, v]) => v.status === "running");
    const nDone = Object.values(s.stages).filter((v) => v.status === "done").length;
    $("progressStatus").textContent = run ? `${nDone}/${Object.keys(s.stages).length}: ${t("stages")[run[0]] || run[0]}` : "";
  }
  const asking = s.status === "needs_answer", wasAsking = !$("question").classList.contains("hidden");
  $("question").classList.toggle("hidden", !asking);
  if (asking) $("questionText").textContent = s.question;
  if (asking && !wasAsking) {  // the question is the one thing to act on: bring it on screen (stage list + results push it down)
    const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    setTimeout(() => {
      const q = $("question"); if (q.scrollIntoView) q.scrollIntoView({ block: "center", behavior: reduce ? "auto" : "smooth" });
      const first = q.querySelector("#quickAns button");  // keyboard and screen-reader users land on the answers, not at the top
      if (first && document.activeElement !== $("answerText")) { try { first.focus({ preventScroll: true }); } catch (_) { first.focus(); } }
    }, 50);
  }
  const stopped = ["stopped", "exhausted"].includes(s.status);
  if ($("progTitle")) $("progTitle").textContent = stopped ? (s.status === "stopped" ? "⛔ " + t("stopHead") : "🧰 " + t("triedTitle")) : t("working");
  $("stopBox").classList.toggle("hidden", !stopped);
  if (stopped) {
    const fresh = $("stopBox").classList.contains("hidden") || !$("stopBox").innerHTML;
    renderStop(s); saveGarage(s);
    if (fresh) toTop();  // the STOP card sits right under the heading
  }
  $("jobErr").textContent = s.status === "error" ? s.error : "";
  if ($("retryBtn")) $("retryBtn").classList.toggle("hidden", !(s.status === "error" && s.error_kind !== "budget"));
}

async function sendAnswer() {
  const v = $("answerText").value.trim(); if (!v) return;
  const fd = new FormData(); fd.append("text", v);
  try {
    const r = await fetch(`/api/sessions/${S.id}/answer`, { method: "POST", body: fd });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || t("netErr"));
  } catch (e) { $("jobErr").textContent = netMsg(e); return; }
  $("jobErr").textContent = ""; $("answerText").value = ""; startElapsed(); follow(S.id);
}

/* ---------------- safety stop / escalation card ---------------- */
// Red stop (safety gate) or "all safe causes tried": say why, what to do right now, and where to get help.
function renderStop(s) {
  const red = s.status === "stopped";
  const obj = ((s.object_report || {}).object || "").trim();
  const q = encodeURIComponent((lang === "en" ? "repair service " : "servis ") + (obj || ""));
  const actions = (red ? t("stopNowRed") : t("stopNowTried")).map((a) => `<li>${esc(a)}</li>`).join("");
  $("stopBox").innerHTML =
    `<p class="stopTitle">${red ? "⛔ " + esc(t("stopTitle")) : "🧰 " + esc(t("triedTitle"))}</p>`
    + `<p>${esc(s.stop_reason || "")}</p>`
    + `<p class="small"><b>${esc(t("stopNow"))}</b></p><ul class="small">${actions}</ul>`
    + `<p class="stopBtns"><a class="btn" target="_blank" rel="noopener" href="https://www.google.com/maps/search/?api=1&query=${q}">📍 ${esc(t("findService"))}</a>`
    + ` <a class="btn link" href="${esc(apiHref(`/api/sessions/${s.id}/report.pdf`))}">📄 ${esc(t("pdf"))}</a></p>`
    + `<p class="small">${esc(t("emergency"))}</p><div id="stopHandoff" class="handoff hidden"></div>`;
  showHandoff("stopHandoff");
}

/* ---------------- bengkel hand-off: WhatsApp summary + nearest workshop + PDF with a mechanic brief ---------------- */
const HO_SAFE = /^https:\/\/(wa\.me\/|www\.google\.com\/maps\/)/;
async function showHandoff(boxId) {
  const box = $(boxId); if (!box || !S || !S.id) return null;
  try {
    const r = await fetch(`/api/sessions/${encodeURIComponent(S.id)}/handoff`);
    if (!r.ok) return null;
    const h = await r.json();
    box.innerHTML = `<p class="hoTitle">🧑‍🔧 ${esc(h.title)}</p><p class="small">${esc(t("hoSub"))}</p>`
      + `<p class="hoBtns">${HO_SAFE.test(h.whatsapp_url || "") ? `<a class="btn wa" target="_blank" rel="noopener noreferrer" href="${esc(h.whatsapp_url)}">💬 ${esc(t("hoWa"))}</a>` : ""}`
      + `${HO_SAFE.test(h.maps_url || "") ? ` <a class="btn" target="_blank" rel="noopener noreferrer" href="${esc(h.maps_url)}">📍 ${esc(t("hoMaps"))}</a>` : ""}`
      + `${h.pdf_url && boxId !== "stopHandoff" ? ` <a class="btn" href="${esc(apiHref(`/api/sessions/${encodeURIComponent(S.id)}/report.pdf`))}">📄 ${esc(t("hoPdf"))}</a>` : ""}</p>`
      + `<details class="small"><summary>${esc(t("hoMsg"))}</summary><pre class="hoText">${esc(h.text)}</pre></details>`;
    box.classList.remove("hidden");
    return h;
  } catch (_) { return null; }
}

/* ---------------- result + guided repair ---------------- */
function render(s) {
  if (!s || !s.plan) return;
  const rep = s.object_report || {}, dx = s.diagnosis || {}, plan = s.plan, base = s.files_base;
  if ($("pdfBtn")) $("pdfBtn").href = apiHref(`/api/sessions/${s.id}/report.pdf`);
  if ($("workshopBtn")) { $("workshopBtn").href = apiHref(`/api/sessions/${s.id}/workshop.pdf`); $("workshopBtn").classList.toggle("hidden", replayOn()); }
  saveGarage(s);
  $("dxObject").textContent = rep.object || ""; $("dxSummary").textContent = dx.problem_summary || "";
  const lvl = (s.safety || {}).level || dx.safety_level;
  $("safetyBadge").className = "level " + lvl; $("safetyBadge").textContent = t(lvl);
  $("safetyReason").textContent = dx.safety_reason || "";
  const ci = s.cause_index || 0, causes = dx.causes || [];
  $("dxCauses").innerHTML = causes.map((c, i) => `<li${i === ci ? ' class="on"' : i < ci ? ' class="tried"' : ""}><span class="pct">${c.confidence}%</span> ${esc(c.title)}${i < ci ? ` <span class="triedTag">✗ ${esc(t("triedMark"))}</span>` : ""}<br><span class="muted small">${esc((c.evidence || []).join("; "))}</span></li>`).join("");
  if ($("planBanner")) {  // after a re-plan the top of the screen must show that the plan changed, not the same first cause
    const cur = causes[ci];
    $("planBanner").textContent = ci > 0 && cur ? t("planOf").replace("{n}", String(ci + 1)).replace("{m}", String(causes.length)).replace("{cause}", cur.title) : "";
    $("planBanner").classList.toggle("hidden", !(ci > 0 && cur));
  }
  if (s.parts_image) {
    $("partsWrap").classList.remove("hidden"); $("partsImg").src = base + s.parts_image;
    $("partsList").innerHTML = Object.values(s.parts || {}).map((p) => `<li>${esc(p.label)}. ${esc(p.name)}${p.found ? "" : " (?)"}</li>`).join("");
  }
  $("gTitle").textContent = plan.cause_title;
  $("gDiff").textContent = `${t("diff")} ${dx.difficulty}/5`; $("gTime").textContent = `⏱ ${dx.minutes_estimate} ${t("min")}`;
  $("gCost").textContent = `💰 ${t("est")} ${rupiah(dx.cost_estimate_idr)}`;
  if ($("gSave")) {
    const shop = Number(dx.shop_cost_estimate_idr || 0), sv = Number(dx.diy_saving_idr || 0);
    $("gSave").textContent = shop ? `🧾 ${t("shopCost")} ${rupiah(shop)}` + (sv ? ` · ${t("save")} ${rupiah(sv)}` : "") : "";
    $("gSave").classList.toggle("hidden", !shop);
  }
  $("gSafety").innerHTML = (window.SAFETY_BASE[lang] || []).map((x) => `<li>${esc(x)}</li>`).join("");
  const safeUrl = (u) => (/^https:\/\/(www\.tokopedia\.com|shopee\.co\.id|wa\.me)\//.test(u || "") ? u : "");
  const li = (i) => `<li>${esc(i.name)} <span class="muted small">${i.est_price_idr ? rupiah(i.est_price_idr) : ""}</span>` +
    (safeUrl(i.shop_url) ? ` <a class="buy small" href="${safeUrl(i.shop_url)}" target="_blank" rel="noopener noreferrer" title="Tokopedia">🛒 ${t("buy")}</a>` +
      (safeUrl(i.shop_alt_url) ? ` <a class="buy small" href="${safeUrl(i.shop_alt_url)}" target="_blank" rel="noopener noreferrer" title="Shopee">Shopee</a>` : "") : "") + `</li>`;
  if ($("waBtn")) { const w = safeUrl(s.whatsapp_url); $("waBtn").href = w || "#"; $("waBtn").classList.toggle("hidden", !w || !((dx.tools || []).length + (dx.parts || []).length)); }
  $("gTools").innerHTML = (dx.tools || []).map(li).join(""); $("gMats").innerHTML = (dx.parts || []).map(li).join("");
  $("gDone").textContent = plan.done_check || ""; $("gPro").textContent = plan.when_to_call_pro ? "🧑‍🔧 " + plan.when_to_call_pro : "";
  $("disclaimer").textContent = (s.safety || {}).disclaimer || "";
  if ($("fallbackNote")) { const fb = (s.fallback || []).length > 0; $("fallbackNote").textContent = fb ? t("fbNote") : ""; $("fallbackNote").classList.toggle("hidden", !fb); }
  renderHood(s); renderAgentLog(s, "agent");
  renderPreflight(s, dx);
  renderStep(); renderVerified(); renderOutcome();
  const sharedPage = !!document.body.dataset.sid && !document.body.dataset.sid.startsWith("{{");
  if ($("sampleCheckBox")) $("sampleCheckBox").classList.toggle("hidden", !s.sample || sharedPage);
  updateTour();
}

// "Before you start": things the owner must confirm (unplugged, engine cool) before the steps unlock.
function renderPreflight(s, dx) {
  const box = $("preflight"); if (!box) return;
  const items = (dx.before_you_start || []).filter((x) => typeof x === "string" && x);
  const key = "tc_pre_" + s.id;
  let ticked = [];
  try { ticked = JSON.parse(localStorage.getItem(key) || "[]"); } catch (e) { ticked = []; }
  if (!Array.isArray(ticked)) ticked = [];
  box.classList.toggle("hidden", !items.length);
  $("preList").innerHTML = items.map((x, i) => `<label class="preItem"><input type="checkbox" data-i="${i}"${ticked.includes(i) ? " checked" : ""}> ${esc(x)}</label>`).join("");
  const apply = () => {
    const boxes = Array.from($("preList").querySelectorAll("input"));
    const done = boxes.every((b) => b.checked);
    try { localStorage.setItem(key, JSON.stringify(boxes.map((b, i) => (b.checked ? i : -1)).filter((i) => i >= 0))); } catch (e) { /* private mode */ }
    const card = $("stepCard");
    card.classList.toggle("locked", !done);
    if (done) card.removeAttribute("inert"); else card.setAttribute("inert", "");
    $("preState").textContent = items.length ? (done ? t("preReady") : t("preLocked")) : "";
  };
  $("preList").querySelectorAll("input").forEach((b) => b.addEventListener("change", apply));
  apply();
}

// "Under the hood": one row per pipeline stage with the model that did it (SPEC v2: show the Meta stack).
function renderHood(s) {
  const box = $("hood"); if (!box) return;
  const rows = (s.trace || []).filter((r) => r.status === "done");
  box.classList.toggle("hidden", !rows.length);
  $("hoodTitle").textContent = t("hood");
  $("hoodList").innerHTML = rows.map((r) => {
    const mark = r.kind === "meta" ? "🟦" : r.kind === "open" ? "🔓" : "⚙️";
    const secs = r.ms >= 100 ? ` <span class="muted">${(r.ms / 1000).toFixed(1)}s</span>` : "";
    return `<li>${mark} <b>${esc(t("hs_" + r.stage))}</b>: ${esc(r.tool)}${secs}</li>`;
  }).join("");
}

function stepImage(st) {
  const d = (S.diagrams || {})[String(st.n)];
  if (d && d.file) return S.files_base + d.file;
  const p = (S.parts || {})[st.component_id];
  if (p && p.image) return S.files_base + p.image;
  return S.files_base + (S.parts_image || S.photos[0]);
}

function renderStep() {
  const st = S.plan.steps[stepIdx];
  $("stepNo").textContent = st.n; $("stepTitle").textContent = `${st.n} / ${S.plan.steps.length}`;
  $("stepText").textContent = st.instruction; $("stepWhy").textContent = st.why || "";
  const w = (st.warnings || []).join(" ");
  $("stepCaution").classList.toggle("hidden", !w); $("stepCaution").textContent = "⚠️ " + w;
  $("stepCheck").textContent = st.expected_state;
  setupTimer(st);
  $("stepImg").src = stepImage(st); $("stepImg").alt = st.instruction; $("stepImg").classList.remove("hidden");
  $("prevBtn").disabled = stepIdx === 0; $("nextBtn").disabled = stepIdx === S.plan.steps.length - 1;
  const c = (S.checks || {})[String(st.n)];
  if (c && c.tries && c.tries.length) showCheck(c.tries[c.tries.length - 1]); else $("checkResult").classList.add("hidden");
  if (live.last && live.last.step !== st.n) { live.last = null; drawLive(null); liveSay("liveAim", ""); }
  if ($("handsFree").checked && !$("stepCard").classList.contains("locked")) play();
}

// Waiting steps ("let the engine cool 10 minutes"): a visible countdown the owner can start, stop and forget about.
let timerHandle = null;
function fmtClock(sec) { const m = Math.floor(sec / 60), r = sec % 60; return `${m}:${String(r).padStart(2, "0")}`; }
function stopTimer() { if (timerHandle) { clearInterval(timerHandle); timerHandle = null; } }
function setupTimer(st) {
  stopTimer();
  const box = $("stepTimer"); if (!box) return;
  const mins = Number(st.wait_minutes) || 0;
  box.classList.toggle("hidden", mins <= 0);
  if (mins <= 0) return;
  $("timerLabel").textContent = t("waitFor").replace("{n}", mins);
  $("timerClock").textContent = fmtClock(mins * 60);
  $("timerBtn").textContent = t("timerStart"); $("timerBtn").dataset.state = "idle";
  $("timerBtn").onclick = () => {
    if (timerHandle) { stopTimer(); $("timerBtn").textContent = t("timerStart"); $("timerBtn").dataset.state = "idle"; $("timerClock").textContent = fmtClock(mins * 60); return; }
    const end = Date.now() + mins * 60000;
    $("timerBtn").textContent = t("timerStop"); $("timerBtn").dataset.state = "running";
    timerHandle = setInterval(() => {
      const left = Math.max(0, Math.round((end - Date.now()) / 1000));
      $("timerClock").textContent = fmtClock(left);
      if (left <= 0) {
        stopTimer(); $("timerBtn").textContent = t("timerStart"); $("timerBtn").dataset.state = "idle";
        $("timerClock").textContent = t("timerDone");
        if (navigator.vibrate) navigator.vibrate([300, 150, 300]);
        if (window.speechSynthesis) { const u = new SpeechSynthesisUtterance(t("timerDone")); u.lang = lang === "en" ? "en-US" : "id-ID"; speechSynthesis.speak(u); }
      }
    }, 500);
  };
}

function play() {
  const st = S.plan.steps[stepIdx], f = (S.audio || {})[String(st.n)];
  voice.quietUntil = Date.now() + 1500;  // hands-free: don't take the guide's own voice as a command
  if (f) { $("player").src = S.files_base + f; $("player").play().catch(() => {}); return; }
  if (window.speechSynthesis) { // browser voice fallback (no server TTS)
    const u = new SpeechSynthesisUtterance(st.voice_text || st.instruction); u.lang = lang === "en" ? "en-US" : "id-ID";
    u.onend = () => { voice.quietUntil = Date.now() + 800; };
    speechSynthesis.cancel(); speechSynthesis.speak(u);
  }
}

function showCheck(r) {
  $("checkResult").classList.remove("hidden");
  $("checkResult").innerHTML = `<p class="${r.passed ? "pass" : "fail"}">${esc(r.passed ? t("pass") : t("fail"))}</p><p>${esc(r.observation)}</p>`
    + (r.correction ? `<p><b>→</b> ${esc(r.correction)}</p>` : "") + (r.escalate_hint ? `<p class="caution">${esc(r.escalate_hint)}</p>` : "")
    + (r.fallback ? `<p class="small fbNote">${esc(t("fbNote"))}</p>` : "");
}

function renderOutcome() {
  const box = $("outcome"); if (!box || !S) return;
  const oc = S.outcome || {}, r = oc.result || "";
  box.classList.toggle("hidden", !S.plan);
  if ($("trialBox")) $("trialBox").classList.toggle("hidden", !trialLabel());
  $("fixedBtn").setAttribute("aria-pressed", String(r === "fixed")); $("proBtn").setAttribute("aria-pressed", String(r === "pro"));
  $("outcomeMsg").textContent = r === "fixed" ? t("fixedThanks") + (oc.saved_idr ? ` ${t("save")} ${rupiah(oc.saved_idr)}.` : "") : r === "pro" ? t("proThanks") : "";
}
// Trial mode for the impact study: open the app once with ?trial=T1 (kept on this phone); outcomes then carry
// the tester label and the minutes the owner reports (scripts/impact_report.py aggregates them).
function trialLabel() {
  try {
    const q = new URLSearchParams(location.search).get("trial");
    if (q !== null) { if (q) localStorage.setItem("tc_trial", q.slice(0, 40)); else localStorage.removeItem("tc_trial"); }
    return localStorage.getItem("tc_trial") || "";
  } catch (_) { return ""; }
}
async function sendOutcome(result) {
  if (!S || !S.id) return;
  const fd = new FormData(); fd.append("result", result);
  const tl = trialLabel();
  if (tl) {
    fd.append("tester", tl);
    const m = parseInt(($("trialMinutes") || {}).value, 10);
    if (m >= 0 && m <= 600) fd.append("minutes", String(m));
  }
  try {
    const r = await fetch(`/api/sessions/${S.id}/outcome`, { method: "POST", body: fd });
    const j = await r.json();
    if (!r.ok) { $("outcomeMsg").textContent = "⚠️ " + (j.detail || r.statusText); return; }
    S = j; setGarageOutcome(S.id, result, (S.outcome || {}).saved_idr); renderOutcome(); renderAgentLog(S, "agent");
    if (result === "pro") showHandoff("handoff");
  } catch (err) { $("outcomeMsg").textContent = "⚠️ " + netMsg(err); }
}

// "Check my step": send one photo of the current step, show pass / correction, move on after a pass.
async function checkPhoto(f) {
  const st = S.plan.steps[stepIdx], fd = new FormData(); fd.append("photo", f, f.name || "check.jpg");
  $("checkResult").classList.remove("hidden"); $("checkResult").textContent = t("checking");
  try {
    const r = await fetch(`/api/sessions/${S.id}/steps/${st.n}/check`, { method: "POST", body: fd });
    const j = await r.json();
    if (!r.ok) { $("checkResult").textContent = j.detail; return null; }
    S = await fetchSession(S.id); showCheck(j); renderVerified(); renderAgentLog(S, "agent");
    if (j.passed && stepIdx < S.plan.steps.length - 1) setTimeout(() => { stepIdx++; renderStep(); }, 1500);
    return j;
  } catch (err) { $("checkResult").textContent = "⚠️ " + netMsg(err); return null; }
}

/* ---------------- live guide: SAM 3.1 highlight over the live rear camera ----------------
   About one small frame per second goes to /track; the answer (normalised boxes + outline of this step's part)
   is drawn on a canvas over the video. No camera (old phone, denied, http) -> the photo button keeps working. */
const LIVE_MS = 1000, LIVE_SIDE = 640;
const live = { stream: null, timer: null, busy: false, last: null, n: 0 };
const liveName = () => { const p = live.last; return (p && p.name) || ""; };
function liveSay(key, name) { if ($("liveState")) $("liveState").textContent = t(key).replace("{name}", name || "…"); }
async function openLive() {
  if (!$("live")) return;
  const md = typeof navigator !== "undefined" && navigator.mediaDevices;
  $("live").classList.remove("hidden"); liveSay("liveStart");
  if (!md || typeof md.getUserMedia !== "function") { liveFallback(); return; }
  try {
    live.stream = await md.getUserMedia({ video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 } }, audio: false });
  } catch (_) { live.stream = null; liveFallback(); return; }
  const v = $("liveVideo"); v.srcObject = live.stream; try { await v.play(); } catch (_) { /* autoplay attribute */ }
  $("liveBtn").setAttribute("aria-pressed", "true");
  live.last = null; live.timer = setInterval(liveTick, LIVE_MS); liveTick();
}
function liveFallback() {
  liveSay("liveNoCam");
  if ($("liveVideo")) $("liveVideo").classList.add("hidden");
  if ($("liveCheck")) $("liveCheck").classList.add("hidden");
}
function closeLive() {
  if (live.timer) { clearInterval(live.timer); live.timer = null; }
  if (live.stream) { live.stream.getTracks().forEach((tr) => tr.stop()); live.stream = null; }
  live.last = null; live.busy = false;
  if ($("live")) $("live").classList.add("hidden");
  if ($("liveBtn")) $("liveBtn").setAttribute("aria-pressed", "false");
  if ($("liveVideo")) $("liveVideo").classList.remove("hidden");
  if ($("liveCheck")) $("liveCheck").classList.remove("hidden");
  drawLive(null);
}
function grabFrame(maxSide, quality) {
  const v = $("liveVideo"); if (!v || !v.videoWidth) return Promise.resolve(null);
  const k = Math.min(1, maxSide / Math.max(v.videoWidth, v.videoHeight));
  const c = document.createElement("canvas"); c.width = Math.round(v.videoWidth * k); c.height = Math.round(v.videoHeight * k);
  const ctx = c.getContext && c.getContext("2d"); if (!ctx) return Promise.resolve(null);
  ctx.drawImage(v, 0, 0, c.width, c.height);
  return new Promise((res) => c.toBlob((b) => res(b), "image/jpeg", quality));
}
async function liveTick() {
  if (live.busy || !live.stream || !S || !S.plan) return;
  live.busy = true;
  try {
    const blob = await grabFrame(LIVE_SIDE, 0.7); if (!blob) return;
    const st = S.plan.steps[stepIdx], fd = new FormData(); fd.append("frame", blob, "frame.jpg");
    const r = await fetch(`/api/sessions/${S.id}/steps/${st.n}/track`, { method: "POST", body: fd });
    if (r.status === 429) return;  // throttled: the next tick tries again
    const j = await r.json(); if (!r.ok) { if ($("liveState")) $("liveState").textContent = "⚠️ " + (j.detail || r.statusText); return; }
    if (j.step !== S.plan.steps[stepIdx].n) return;  // the owner moved to another step meanwhile
    applyTrack(j);
  } catch (err) { if ($("liveState")) $("liveState").textContent = "⚠️ " + netMsg(err);
  } finally { live.busy = false; }
}
function applyTrack(j) {
  live.last = j; live.n++;
  drawLive(j);
  if (!j.component_id) liveSay("liveNoPart");
  else if (j.found) liveSay("liveFound", (j.label ? j.label + ". " : "") + j.name);
  else liveSay(j.frames_used ? "liveLost" : "liveAim", j.name);
  if (j.limit_reached && live.timer) { clearInterval(live.timer); live.timer = null; liveSay("liveLimit"); }
}
function drawLive(j) {
  const c = $("liveCanvas"), v = $("liveVideo"); if (!c || !c.getContext) return;
  const w = (v && v.clientWidth) || c.clientWidth || 640, h = (v && v.clientHeight) || c.clientHeight || 480;
  c.width = w; c.height = h;
  const g = c.getContext("2d"); if (!g) return;
  g.clearRect(0, 0, w, h);
  if (!j || !j.found) return;
  g.lineWidth = 4; g.strokeStyle = "#ff7a00"; g.fillStyle = "rgba(255,122,0,0.30)";
  const poly = j.polygon || [];
  if (poly.length > 2) {
    g.beginPath(); poly.forEach(([x, y], i) => (i ? g.lineTo(x * w, y * h) : g.moveTo(x * w, y * h))); g.closePath(); g.fill(); g.stroke();
  }
  const b = (j.boxes || [])[0];
  if (b) {
    g.setLineDash([10, 6]); g.strokeRect(b.x1 * w, b.y1 * h, (b.x2 - b.x1) * w, (b.y2 - b.y1) * h); g.setLineDash([]);
    const tag = (j.label ? j.label + ". " : "") + (j.name || "");
    g.font = "bold 18px sans-serif"; const tw = g.measureText(tag).width + 16;
    const ty = b.y1 * h >= 30 ? b.y1 * h - 30 : Math.min(h - 28, b.y2 * h + 2), tx = Math.max(0, Math.min(b.x1 * w, w - tw));
    g.fillStyle = "#ff7a00"; g.fillRect(tx, ty, tw, 28); g.fillStyle = "#fff"; g.fillText(tag, tx + 8, ty + 20);
  }
}
async function liveCheckNow() {
  if (!live.stream) { const inp = $("stepPhoto"); if (inp) inp.click(); return; }
  const blob = await grabFrame(1600, 0.85);
  if (!blob) return;
  await checkPhoto(new File([blob], "live-check.jpg", { type: "image/jpeg" }));
}

function renderVerified() {
  const n = S.plan.steps.filter((st) => ((S.checks || {})[String(st.n)] || {}).passed).length;
  $("verifiedCount").textContent = `✅ ${n}/${S.plan.steps.length} ${t("verified")}`;
}

function setupResult() {
  on("prevBtn", "click", () => { if (stepIdx > 0) { stepIdx--; renderStep(); } });
  on("nextBtn", "click", () => { if (stepIdx < S.plan.steps.length - 1) { stepIdx++; renderStep(); } });
  on("playBtn", "click", play);
  on("handsFree", "change", (e) => setHandsFree(e.target.checked));
  on("mechBtn", "click", () => showHandoff("handoff"));
  on("pttBtn", "click", pushToTalk);
  if ($("player")) $("player").addEventListener("ended", () => { voice.quietUntil = Date.now() + 800; });
  on("fixedBtn", "click", () => sendOutcome("fixed"));
  on("proBtn", "click", () => sendOutcome("pro"));
  on("stepPhoto", "change", async (e) => {
    const f0 = e.target.files[0]; if (!f0) return;
    const f = await shrinkImage(f0); e.target.value = "";
    await checkPhoto(f);
  });
  on("liveBtn", "click", () => (live.stream ? closeLive() : openLive()));
  on("liveClose", "click", closeLive);
  on("liveCheck", "click", liveCheckNow);
  on("stuckBtn", "click", async () => {
    const fd = new FormData(); fd.append("report", $("stuckText").value.trim());
    $("stuckBtn").disabled = true; $("stuckMsg").textContent = t("working");
    try {
      const r = await fetch(`/api/sessions/${S.id}/replan`, { method: "POST", body: fd });
      const j = await r.json();
      if (!r.ok) { $("stuckMsg").textContent = "⚠️ " + (j.detail || r.statusText); return; }
      S = j;
      if (S.status === "ready") { stepIdx = 0; render(S); $("stuckMsg").textContent = t("newPlan"); $("stuckText").value = ""; toTop(); }
      else { $("stuckMsg").textContent = "⛔ " + (S.stop_reason || S.error || ""); showHandoff("handoff"); }
    } catch (err) { $("stuckMsg").textContent = "⚠️ " + netMsg(err);
    } finally { $("stuckBtn").disabled = false; }
  });
  on("shareBtn", "click", async () => {
    const url = replayOn() ? location.origin + "/?replay=1" : location.origin + "/guide/" + S.id;  // a recording has no shared guide page
    const dx = (S && S.diagnosis) || {}, c = (dx.causes || [])[S.cause_index || 0] || (dx.causes || [])[0];
    const text = [S.object_report && S.object_report.object, c && c.title].filter(Boolean).join(": ");  // the link preview card shows the rest
    if (navigator.share) {
      try {
        const cr = await fetch(`/api/sessions/${S.id}/card.png`);
        if (cr.ok && navigator.canShare) {
          const files = [new File([await cr.blob()], "tukang-copilot.png", { type: "image/png" })];
          if (navigator.canShare({ files })) { await navigator.share({ title: "Tukang Copilot", text, url, files }); return; }
        }
      } catch (e) { if (e && e.name === "AbortError") return; }
      try { await navigator.share({ title: "Tukang Copilot", text, url }); return; } catch (_) {}
    }
    try { await navigator.clipboard.writeText(url); alert(t("copied")); } catch (_) { prompt("Link", url); }
  });
  on("eraseBtn", "click", () => {
    if (!S || !S.id || !confirm(t("eraseAsk"))) return;
    const id = S.id;
    fetch(`/api/sessions/${encodeURIComponent(id)}`, { method: "DELETE" }).catch(() => null).then(() => {
      try { localStorage.setItem(GARAGE_KEY, JSON.stringify(loadGarage().filter((e) => e && e.id !== id))); } catch (_) {}
      alert(t("erased")); freshStart();
    });
  });
  on("againBtn", "click", freshStart);
}

window.SAFETY_BASE = {
  id: ["Cabut steker / matikan mesin dan tunggu dingin sebelum mulai.", "Pakai sarung tangan dan kacamata bila ada serpihan, bensin, atau cairan."],
  jv: ["Copot steker / pateni mesin lan enteni adhem sadurunge miwiti.", "Nganggo sarung tangan lan kacamata yen ana pecahan, bensin, utawa cairan."],
  en: ["Unplug it / switch the engine off and let it cool before you start.", "Wear gloves and eye protection around shards, fuel or liquids."],
};

/* ---------------- hands-free voice loop ----------------
   Steps are read aloud (server MP3 or the browser voice). With SpeechRecognition the phone keeps listening for
   commands; without it a push-to-talk button sends a short clip to /command (same ASR as the description).
   parseCommand mirrors api/voice.py: same word lists (api/tests/test_voice.py checks both on the same cases). */
/* VOICE_WORDS:start */const VOICE_WORDS = {"id":{"broken":["masih rusak","tetap rusak","masih mati","tetap mati","masih belum","tidak berhasil","nggak berhasil","gak berhasil","belum berhasil","rencana lain","masih bocor","masih netes"],"stop":["berhenti","stop","matikan suara","cukup","diam"],"back":["kembali","mundur","sebelumnya","balik"],"repeat":["ulang","ulangi","sekali lagi","apa tadi","bacakan lagi"],"check":["cek","periksa","foto","cekrek","lihat"],"next":["lanjut","terus","berikutnya","selanjutnya","oke","sudah","beres"]},"jv":{"broken":["isih rusak","tetep rusak","isih mati","tetep mati","ora kasil","durung kasil","rencana liya","isih bocor","isih netes"],"stop":["mandheg","mandeg","wis cukup","meneng","stop"],"back":["bali","mbalik","sadurunge","sakdurunge","mundur"],"repeat":["baleni","maneh","sepisan maneh","ulang","ulangi"],"check":["priksa","periksa","cek","foto","delokna"],"next":["terus","lanjut","sabanjure","wis","oke","rampung"]},"en":{"broken":["still broken","not working","doesn't work","does not work","didn't work","did not work","still dead","another plan","still leaking","still dripping"],"stop":["stop","quit","be quiet","stop listening","that's enough"],"back":["back","go back","previous","last step"],"repeat":["repeat","again","say again","say that again","read it again"],"check":["check","verify","photo","take a photo","look"],"next":["next","continue","go on","done","okay","ok","carry on"]}};/* VOICE_WORDS:end */
const VOICE_ORDER = ["broken", "stop", "back", "repeat", "check", "next"], VOICE_NEG = ["jangan", "ojo", "aja", "don't", "do not", "not"];
function normCmd(text) {
  return String(text || "").toLowerCase().replace(/\u2019/g, "'").replace(/[^\p{L}\p{N}_' ]+/gu, " ").split(/\s+/).filter(Boolean).join(" ").slice(0, 200);
}
function hitCmd(text, word) {
  const words = text.split(" "), ws = word.split(" ");
  for (let i = 0; i + ws.length <= words.length; i++) {
    if (ws.every((x, k) => words[i + k] === x)) { if (!(i > 0 && VOICE_NEG.includes(words[i - 1]))) return true; }
  }
  return false;
}
function parseCommand(text, lg) {
  const tx = normCmd(text); if (!tx) return null;
  const langs = (VOICE_WORDS[lg] ? [lg] : []).concat(Object.keys(VOICE_WORDS).filter((x) => x !== lg));
  for (const l of langs) for (const c of VOICE_ORDER) if (VOICE_WORDS[l][c].some((w) => hitCmd(tx, w))) return c;
  return null;
}

const SR_LANG = { id: "id-ID", jv: "jv-ID", en: "en-US" };
const voice = { on: false, rec: null, ptt: null, quietUntil: 0 };
const srCtor = () => (typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition)) || null;
function guideSpeaking() {
  return Date.now() < voice.quietUntil || (window.speechSynthesis && speechSynthesis.speaking) || ($("player") && $("player").src && !$("player").paused);
}
function setHandsFree(onb) {
  voice.on = !!onb;
  if ($("handsFree")) $("handsFree").checked = voice.on;
  if ($("voiceBar")) $("voiceBar").classList.toggle("hidden", !voice.on);
  document.body.classList.toggle("handsfree", voice.on);
  if (voice.on) { startListening(); if (S && S.plan && !$("stepCard").classList.contains("locked")) play(); }
  else { stopListening(); if ($("voiceState")) $("voiceState").textContent = t("vOff"); }
}
function pttMode(msgKey) {
  if ($("pttBtn")) $("pttBtn").classList.remove("hidden");
  if ($("voiceDot")) $("voiceDot").classList.remove("on");
  if ($("voiceState")) $("voiceState").textContent = t(msgKey);
}
function startListening() {
  if ($("voiceHelp")) $("voiceHelp").textContent = t("vHelp");
  const C = srCtor();
  if (!C) { pttMode("vNoSR"); return; }
  try {
    const r = new C();
    r.lang = SR_LANG[lang] || "id-ID"; r.continuous = true; r.interimResults = false; r.maxAlternatives = 3;
    r.onresult = (ev) => {
      if (guideSpeaking()) return;
      const res = ev.results[ev.results.length - 1]; if (!res) return;
      let heard = "", cmd = null;
      for (let i = 0; i < res.length && !cmd; i++) { heard = heard || res[i].transcript; cmd = parseCommand(res[i].transcript, lang); if (cmd) heard = res[i].transcript; }
      doCommand(cmd, String(heard).trim());
    };
    r.onerror = (e) => { if (e && /not-allowed|service-not-allowed|audio-capture/.test(e.error || "")) { voice.rec = null; pttMode("vNoSR"); } };
    r.onend = () => { if (voice.on && voice.rec === r) setTimeout(() => { if (voice.on && voice.rec === r) { try { r.start(); } catch (_) { /* already running */ } } }, 300); };
    voice.rec = r; r.start();
    if ($("voiceDot")) $("voiceDot").classList.add("on");
    if ($("pttBtn")) $("pttBtn").classList.add("hidden");
    if ($("voiceState")) $("voiceState").textContent = t("vListening");
  } catch (_) { voice.rec = null; pttMode("vNoSR"); }
}
function stopListening() {
  const r = voice.rec; voice.rec = null;
  if (r) { try { r.abort ? r.abort() : r.stop(); } catch (_) { /* ended */ } }
  if (voice.ptt && voice.ptt.state === "recording") voice.ptt.stop();
  if ($("voiceDot")) $("voiceDot").classList.remove("on");
  if ($("pttBtn")) $("pttBtn").classList.add("hidden");
}
function doCommand(cmd, heard) {
  const vs = $("voiceState");
  if (!cmd) { if (vs) vs.textContent = t("vUnknown").replace("{text}", heard || "…"); return null; }
  if (vs) vs.textContent = heard ? t("vHeard").replace("{text}", heard) : "";
  if (cmd === "stop") { setHandsFree(false); return cmd; }
  if (!S || !S.plan || $("stepCard").classList.contains("locked")) return null;
  if (cmd === "next") { if (stepIdx < S.plan.steps.length - 1) { stepIdx++; renderStep(); } else play(); }
  else if (cmd === "back") { if (stepIdx > 0) { stepIdx--; renderStep(); } else play(); }
  else if (cmd === "repeat") play();
  else if (cmd === "check") { if (live.stream) liveCheckNow(); else if ($("liveBtn")) openLive(); else if ($("stepPhoto")) $("stepPhoto").click(); }
  else if (cmd === "broken") { if ($("stuckBtn")) $("stuckBtn").click(); }
  return cmd;
}
// Push-to-talk fallback: one short clip per command, transcribed on the server (POST /command).
async function pushToTalk() {
  if (voice.ptt && voice.ptt.state === "recording") { voice.ptt.stop(); return; }
  let stream;
  try { stream = await navigator.mediaDevices.getUserMedia({ audio: true }); } catch (_) { if ($("voiceState")) $("voiceState").textContent = t("micErr"); return; }
  const parts = [], mr = new MediaRecorder(stream); voice.ptt = mr;
  mr.ondataavailable = (e) => e.data.size && parts.push(e.data);
  mr.onstop = async () => {
    stream.getTracks().forEach((tr) => tr.stop());
    $("pttBtn").setAttribute("aria-pressed", "false"); $("pttBtn").textContent = t("ptt");
    const blob = new Blob(parts, { type: mr.mimeType || "audio/webm" });
    const ext = blob.type.includes("mp4") ? "m4a" : blob.type.includes("ogg") ? "ogg" : "webm";
    const fd = new FormData(); fd.append("audio", blob, "command." + ext);
    try {
      const r = await fetch(`/api/sessions/${S.id}/command`, { method: "POST", body: fd });
      const j = await r.json();
      if (!r.ok) { $("voiceState").textContent = "⚠️ " + (j.detail || r.statusText); return; }
      doCommand(j.command, j.text);
    } catch (err) { $("voiceState").textContent = "⚠️ " + netMsg(err); }
  };
  mr.start(); $("pttBtn").setAttribute("aria-pressed", "true"); $("pttBtn").textContent = t("pttRec");
  setTimeout(() => mr.state === "recording" && mr.stop(), 4000);
}

/* ---------------- My garage (localStorage only, no account, SPEC v2) ---------------- */
const GARAGE_KEY = "tc_garage", GARAGE_MAX = 20;
function loadGarage() { try { const g = JSON.parse(localStorage.getItem(GARAGE_KEY) || "[]"); return Array.isArray(g) ? g : []; } catch (_) { return []; } }
function saveGarage(s) {
  if (!s || !s.id || document.body.dataset.sid) return; // never store someone else's shared guide
  const steps = ((s.plan || {}).steps || []), checks = s.checks || {};
  const entry = { id: s.id, object: (s.object_report || {}).object || "", fix: (s.plan || {}).cause_title || "",
    level: (s.safety || {}).level || (s.diagnosis || {}).safety_level || "", status: s.status,
    verified: steps.filter((st) => (checks[String(st.n)] || {}).passed).length, total: steps.length, outcome: (s.outcome || {}).result || "", saved: Number((s.outcome || {}).saved_idr) || 0, at: Math.round((s.created || Date.now() / 1000) * 1000) };
  const g = [entry].concat(loadGarage().filter((e) => e && e.id !== s.id)).slice(0, GARAGE_MAX);
  try { localStorage.setItem(GARAGE_KEY, JSON.stringify(g)); } catch (_) {}
  renderGarage();
}
function setGarageOutcome(id, result, saved) {
  const g = loadGarage();
  g.forEach((e) => { if (e && e.id === id) { e.outcome = result; e.saved = Number(saved) || 0; } });
  try { localStorage.setItem(GARAGE_KEY, JSON.stringify(g)); } catch (_) {}
}
function renderGarage() {
  if (!$("garage")) return;
  const g = loadGarage();
  if ($("garageSaved")) {
    const fixed = g.filter((e) => e && e.outcome === "fixed"), sum = fixed.reduce((a, e) => a + (Number(e.saved) || 0), 0);
    $("garageSaved").textContent = sum > 0 ? `💰 ${t("savedTotal")} ${rupiah(sum)} ${t("savedFrom")} ${fixed.length} ${t("savedUnit")}` : "";
    $("garageSaved").classList.toggle("hidden", !(sum > 0));
  }
  $("garage").classList.toggle("hidden", !g.length || ($("capture") && $("capture").classList.contains("hidden")));
  $("garageList").innerHTML = g.map((e) => {
    const day = new Date(e.at).toLocaleDateString(lang === "en" ? "en-GB" : "id-ID", { day: "numeric", month: "short" });
    const lvl = ["green", "amber", "red"].includes(e.level) ? e.level : "";
    return `<li><a href="/guide/${encodeURIComponent(e.id)}">${esc(e.object || e.id)}</a> ` +
      (lvl ? `<span class="level ${lvl}">${esc(t(lvl))}</span> ` : "") + (e.outcome === "fixed" ? "🎉 " : "") +
      `<span class="muted small">${esc(day)}${e.total ? ` · ${e.verified}/${e.total} ✓` : ""}${e.fix ? " · " + esc(e.fix) : ""}</span></li>`;
  }).join("");
}

/* ---------------- agent log: "What the AI did" (v1.22) ----------------
   One line per agent decision from s.agent_log (api/pipeline/engine.py _event): what it perceived, decided,
   checked or handed off, and which tool did it. Every value is escaped; the log never holds the owner's words. */
const fillT = (key, d) => t(key).replace(/\{(\w+)\}/g, (_, k) => esc(d[k] ?? ""));
const AG_PHASE = { listen: "see", look: "see", segment: "see", gate: "guard", input_guard: "guard", plan_guard: "guard", diagnose: "think",
  ask: "ask", answer: "ask", plan: "plan", illustrate: "plan", check: "verify", replan: "replan", escalate: "handoff", outcome: "verify",
  fallback: "guard", retry: "think" };
const AG_ICON = { listen: "👂", look: "👁️", segment: "🎯", gate: "🛡️", input_guard: "🛡️", plan_guard: "🛡️", diagnose: "🧠", ask: "❓", answer: "💬",
  plan: "📋", illustrate: "🖼️", check: "📸", replan: "🔁", escalate: "🧑‍🔧", outcome: "🎉", fallback: "🧪", retry: "↻" };
const LOOP = ["see", "think", "ask", "plan", "guard", "verify", "replan", "handoff"];
function agentLine(e) {
  const k = e.kind;
  if (k === "gate") return e.ok ? t("ag_gate_ok") : fillT("ag_gate_stop", e);
  if (k === "plan_guard") return e.ok ? fillT("ag_guard_ok", { level: t(e.level) }) : t("ag_guard_stop");
  if (k === "illustrate") return fillT("ag_illustrate", e) + (e.redrawn ? fillT("ag_redrawn", e) : "");
  if (k === "check") return fillT(e.passed ? "ag_check_ok" : "ag_check_fail", e) + (e.escalate ? t("ag_check_esc") : "");
  if (k === "escalate") return t(e.reason === "exhausted" ? "ag_esc_exhausted" : "ag_esc_red");
  if (k === "outcome") return t(e.result === "fixed" ? "ag_outcome_fixed" : "ag_outcome_pro");
  return T.en["ag_" + k] !== undefined ? fillT("ag_" + k, e) : esc(k);
}
function renderAgentLog(s, boxId) {
  const box = $(boxId); if (!box) return;
  const ev = (s && s.agent_log) || [];
  box.classList.toggle("hidden", !ev.length);
  if (!ev.length) return;
  const seen = new Set(ev.map((e) => AG_PHASE[e.kind]));
  const loop = LOOP.map((p) => `<span class="lp${seen.has(p) ? " on" : ""}">${esc(t("lp_" + p))}</span>`).join("<span class=\"lpArrow\" aria-hidden=\"true\">→</span>");
  const rows = ev.map((e, i) => {
    const tool = e.model ? `<code class="tool">${esc(e.model)}</code>` : (["gate", "plan_guard", "input_guard"].includes(e.kind) ? `<code class="tool code">${esc(t("agCode"))}</code>` : "");
    const secs = e.ms >= 100 ? ` <span class="muted">${(e.ms / 1000).toFixed(1)}s</span>` : "";
    const line = `<span class="agT muted">${esc(Number(e.t || 0).toFixed(0))}s</span> <span aria-hidden="true">${AG_ICON[e.kind] || "•"}</span> ${agentLine(e)} ${tool}${secs}`;
    return `<li class="ag ${esc(AG_PHASE[e.kind] || "")}">${agTarget(e, boxId) ? `<button type="button" class="agGo" data-i="${i}" title="${esc(t("agJump"))}">${line}<span class="agArrow" aria-hidden="true">›</span></button>` : line}</li>`;
  }).join("");
  if (!box.dataset.go) {  // one delegated handler per log box: tap a line to see the stage, photo or step it is about
    box.dataset.go = "1";
    box.addEventListener("click", (ev) => {
      const btn = ev.target.closest && ev.target.closest(".agGo"); if (!btn) return;
      const e = ((S && S.agent_log) || [])[Number(btn.dataset.i)]; if (e) agGo(e, boxId);
    });
  }
  box.querySelector(".agLoop").innerHTML = loop;
  box.querySelector(".agList").innerHTML = rows;
}

/* ---------------- agent log lines link to what they are about (v1.23) ---------------- */
// Progress screen: the stage row (or the streamed result row). Result and guide pages: the photo, the causes, the
// safety list, or the exact step that was camera-checked (the step card jumps to it).
const AG_STAGE = { listen: "listen", gate: "gate", input_guard: "gate", look: "look", segment: "segment", diagnose: "diagnose",
  plan: "plan", replan: "plan", plan_guard: "safety", illustrate: "illustrate", ask: "question", answer: "question" };
const AG_RESULT = { listen: "dxSummary", gate: "safetyBadge", input_guard: "safetyBadge", look: "dxObject", segment: "partsWrap",
  diagnose: "dxCauses", ask: "dxCauses", answer: "dxCauses", plan: "stepCard", replan: "stepCard", plan_guard: "preflight",
  illustrate: "stepCard", check: "stepCard", escalate: "handoff", outcome: "outcome", fallback: "fallbackNote" };
function visible(el) { return !!(el && el.getClientRects().length && !el.closest(".hidden")); }
function agTarget(e, boxId) {
  if (boxId === "agentLive") {
    const k = e.kind === "fallback" ? e.stage : AG_STAGE[e.kind];
    if (!k) return null;
    if (k === "question") return $("question");
    return document.getElementById("lf-" + k) || document.getElementById("st-" + k);
  }
  if (e.kind === "check" && e.cause !== undefined && S && e.cause !== (S.cause_index || 0)) return null;  // a step of an earlier plan
  let id = AG_RESULT[e.kind];
  if (id === "preflight" && !visible($("preflight"))) id = "safetyBadge";
  if (id === "handoff" && !visible($("handoff"))) id = visible($("stopBox")) ? "stopBox" : "stuckBtn";
  if (id === "partsWrap" && !visible($("partsWrap"))) id = "dxCauses";
  return id ? $(id) : null;
}
let flashT = { id: "", until: 0 };
function flash(el) {
  if (!el) return;
  if (!el.id) el.id = "fl-" + Math.random().toString(36).slice(2, 8);
  document.querySelectorAll(".flash").forEach((x) => x.classList.remove("flash"));
  void el.offsetWidth; el.classList.add("flash");
  flashT = { id: el.id, until: Date.now() + 1800 };
  setTimeout(() => { if (flashT.id === el.id && Date.now() >= flashT.until - 50) el.classList.remove("flash"); }, 1800);
}
function reflash() {  // the stage list is redrawn on every update; keep a fresh highlight on it
  if (Date.now() < flashT.until) { const el = document.getElementById(flashT.id); if (el) el.classList.add("flash"); }
}
function agGo(e, boxId) {
  if (e.kind === "check" && boxId !== "agentLive" && S && S.plan && Array.isArray(S.plan.steps)) {
    const i = S.plan.steps.findIndex((x) => x.n === e.step);
    if (i >= 0 && i !== stepIdx) { stepIdx = i; renderStep(); }
  }
  const el = agTarget(e, boxId); if (!el) return;
  const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (el.scrollIntoView) el.scrollIntoView({ block: "center", behavior: reduce ? "auto" : "smooth" });
  if (!el.hasAttribute("tabindex") && !/^(BUTTON|A|INPUT|TEXTAREA|SELECT)$/.test(el.tagName)) el.setAttribute("tabindex", "-1");
  try { el.focus({ preventScroll: true }); } catch (_) { /* old browsers */ }
  flash(el);
}

/* ---------------- progress: partial results stream in (v1.23) ---------------- */
// Each stage's result shows up the moment it is saved (SSE, or the polling fallback): what the AI saw, the photo
// with SAM 3.1's outlines, the top cause, the step count. Rows are only appended or updated, never rebuilt, so a
// row animates once and the screen does not jump.
function partialRows(s) {
  const st = s.stages || {}, rows = [], rep = s.object_report, dx = s.diagnosis;
  if (rep && rep.object && st.look && st.look.status === "done") {
    const comps = (rep.components || []).map((c) => `<span class="chip sm">${esc(c.name)}</span>`).join("");
    rows.push(["look", `${esc(fillRaw("pv_seen", { object: rep.object }))}${comps ? `<div class="lfChips">${comps}</div>` : ""}`]);
  }
  if (s.parts_image && st.segment && st.segment.status === "done") {
    const pf = Array.isArray(s.parts_found) ? s.parts_found : Object.values(s.parts || {});
    const found = pf.filter((p) => p && p.found).length;
    rows.push(["segment", `${esc(fillRaw("pv_parts", { found, of: pf.length }))}<img class="lfImg" src="${esc((s.files_base || `/files/${s.id}/`) + s.parts_image)}" alt="${esc(t("pv_img"))}" width="320" height="240" loading="eager">`]);
  }
  if (dx && dx.causes && dx.causes[0] && st.diagnose && st.diagnose.status === "done") {
    const lvl = dx.safety_level ? ` <span class="level ${esc(dx.safety_level)}">${esc(t(dx.safety_level))}</span>` : "";
    rows.push(["diagnose", esc(fillRaw("pv_cause", { cause: dx.causes[0].title, conf: dx.causes[0].confidence })) + lvl]);
  }
  const nSteps = s.plan_steps || (s.plan && s.plan.steps && s.plan.steps.length) || 0;
  if (nSteps && st.plan && st.plan.status === "done") rows.push(["plan", esc(fillRaw("pv_steps", { n: nSteps }))]);
  return rows;
}
function fillRaw(key, vals) { return t(key).replace(/\{(\w+)\}/g, (m, k) => (vals[k] !== undefined ? String(vals[k]) : m)); }
function renderPartial(s) {
  const box = $("liveFind"); if (!box) return;
  const list = box.querySelector(".lfList");
  if (box.dataset.sid !== String(s.id || "")) { list.innerHTML = ""; box.dataset.sid = String(s.id || ""); }
  const rows = partialRows(s);
  box.classList.toggle("hidden", !rows.length);
  for (const [k, html] of rows) {
    let li = list.querySelector(`li[data-k="${k}"]`);
    if (!li) { li = document.createElement("li"); li.dataset.k = k; li.className = "pop"; li.id = "lf-" + k; list.appendChild(li); }
    if (li.dataset.h !== html) { li.innerHTML = html; li.dataset.h = html; }
  }
}

/* ---------------- progress: model per stage + elapsed time ---------------- */
// Fixed stage notes come from the server in English; show them in the UI language (model text passes through).
const NOTE_KEY = { typed: "note_typed", "safety stop": "note_stop", "photo is enough": "note_photo", "browser voice": "note_browser", "no visible components": "note_nocomp" };
function stageNote(note) {
  const n = String(note || ""), m = /^(\d+) steps$/.exec(n);
  return m ? t("note_steps").replace("{n}", m[1]) : NOTE_KEY[n] ? t(NOTE_KEY[n]) : n;
}
const STAGE_TOOL = { listen: "listen", look: "look", segment: "segment", diagnose: "diagnose", plan: "plan", illustrate: "illustrate" };
function stageTool(s, k) {
  const m = s.models || {};
  if (k === "listen" && s.lang === "jv" && m.listen_javanese) return m.listen_javanese;
  if (STAGE_TOOL[k]) return m[STAGE_TOOL[k]] || "";
  return k === "narrate" ? "edge-tts" : t("agCode");
}
let progT0 = 0, progTimer = null;
function tickElapsed() {
  const el = $("elapsed"); if (!el) return;
  const running = S && ["created", "running"].includes(S.status) && !$("progress").classList.contains("hidden");
  el.textContent = running ? "⏱ " + t("elapsed").replace("{n}", String(Math.round((Date.now() - progT0) / 1000))) : "";
  if (!running && progTimer) { clearInterval(progTimer); progTimer = null; }
}
function startElapsed() { progT0 = Date.now(); if (progTimer) clearInterval(progTimer); progTimer = setInterval(tickElapsed, 1000); tickElapsed(); }

/* ---------------- 1-tap guided demo (v1.22) ---------------- */
// The tip bar is a small pill in the corner, never a full-width sheet over the main button. It opens wide for the
// first tips, collapses to a 💡 chip by itself once the first step has been checked, and the owner can fold or
// close it at any time. A new tip after a manual fold stays folded until tapped.
const tour = { on: false, collapsed: false, userSet: false, key: "" };
try { tour.on = sessionStorage.getItem("tc_tour") === "1"; } catch (_) { /* private mode */ }
function setTour(v) {
  tour.on = v; tour.collapsed = false; tour.userSet = false; tour.key = "";
  try { v ? sessionStorage.setItem("tc_tour", "1") : sessionStorage.removeItem("tc_tour"); } catch (_) {}
  updateTour();
}
function toggleTour() { tour.collapsed = !tour.collapsed; tour.userSet = true; updateTour(); }
function updateTour() {
  const bar = $("tourBar"); if (!bar) return;
  let key = "";
  if (tour.on && S) {
    if (S.status === "needs_answer") key = "tourAsk";
    else if (["created", "running"].includes(S.status)) key = "tourProgress";
    else if (S.status === "ready" && S.plan) {
      const unlocked = !$("stepCard") || !$("stepCard").hasAttribute("inert");
      const passed = Object.values(S.checks || {}).some((c) => c && c.passed);
      key = !unlocked ? "tourResult" : passed ? "tourStuck" : "tourCheck";
    }
  }
  // auto-collapse after the first step check (pass or fail), unless the owner chose otherwise
  const checked = !!(S && S.checks && Object.keys(S.checks).length);
  if (checked && !tour.userSet) tour.collapsed = true;
  tour.key = key;
  bar.classList.toggle("hidden", !key);
  bar.classList.toggle("collapsed", !!key && tour.collapsed);
  if (!key) return;
  $("tourText").textContent = t(key);
  const tg = $("tourToggle");
  if (tg) { tg.setAttribute("aria-expanded", String(!tour.collapsed)); tg.setAttribute("aria-label", t(tour.collapsed ? "tourTip" : "tourHide")); tg.title = tg.getAttribute("aria-label"); }
  const x = $("tourClose"); if (x) { x.setAttribute("aria-label", t("tourClose")); x.title = t("tourClose"); }
}
async function sampleCheck(kind) {
  if (!S || !S.sample) return;
  try {
    const r = await fetch(`/api/demo/check-photo/${kind}?sample=${encodeURIComponent(S.sample)}`);
    if (!r.ok) throw new Error(r.statusText);
    const blob = await r.blob();
    await checkPhoto(new File([blob], `sample-${kind}.jpg`, { type: "image/jpeg" }));
  } catch (e) { $("checkResult").classList.remove("hidden"); $("checkResult").textContent = "⚠️ " + netMsg(e); }
  updateTour();
}
function setupDemo() {
  on("demoBtn", "click", async () => {
    setTour(true);
    if (await useReplay()) { await window.TCReplay.start(lang); wakeNote(false); await health(); }
    submit("motor");
  });
  on("tourClose", "click", () => setTour(false));
  on("tourToggle", "click", toggleTour);
  on("sampleBad", "click", () => sampleCheck("dark"));
  on("sampleGood", "click", () => sampleCheck("ok"));
  document.querySelectorAll("#quickAns button").forEach((b) => b.addEventListener("click", () => {
    $("answerText").value = t(b.dataset.q); sendAnswer();
  }));
  if ($("preList")) $("preList").addEventListener("change", () => setTimeout(updateTour, 0));
}

// "/" on the server; the page's own path in the static judge build (it may live under a GitHub Pages sub-path).
function homePath() { return window.TC_STATIC ? location.pathname : "/"; }

/* ---------------- laptop view (v1.25) ---------------- */
// At >= 1024 px the page shows the app in a phone frame plus a side panel (web/style.css). The QR code encodes the
// page's own address so a judge on a laptop can carry on with a phone; the encoder (web/vendor/qrcode.js, MIT,
// Kazuhiko Arase) is fetched only on wide screens, so phones never download it.
const DESK_MQ = "(min-width: 1024px)";
const isDesk = () => typeof window.matchMedia === "function" && window.matchMedia(DESK_MQ).matches;
function qrTarget() {
  const u = new URL(location.href); u.hash = "";
  return u.toString();
}
function drawQr() {
  const box = $("qrBox"); if (!box || box.dataset.done || typeof window.qrcode !== "function") return;
  const url = qrTarget();
  try {
    const q = window.qrcode(0, "M"); q.addData(url); q.make();
    box.innerHTML = q.createSvgTag({ cellSize: 4, margin: 2, scalable: true });
    box.dataset.done = "1"; box.setAttribute("aria-label", "QR: " + url);
  } catch (_) { box.classList.add("hidden"); }
  if ($("qrUrl")) $("qrUrl").textContent = url.replace(/^https?:\/\//, "").replace(/\/$/, "");
  const local = location.protocol === "file:" || /^(localhost|127\.|0\.0\.0\.0|\[::1\])/.test(location.hostname);
  if ($("qrLocal")) $("qrLocal").classList.toggle("hidden", !local);
}
function loadQr() {
  if (!$("qrBox") || !isDesk()) return;
  if (typeof window.qrcode === "function") { drawQr(); return; }
  if (document.getElementById("qrLib")) return;
  const sc = document.createElement("script"); sc.id = "qrLib"; sc.src = (window.TC_STATIC ? "" : "/") + "static/vendor/qrcode.js"; sc.onload = drawQr;
  document.head.appendChild(sc);
}
function setupDesk() {
  if (!$("side")) return;
  on("sideDemo", "click", () => { const b = $("demoBtn"); if (b && !$("capture").classList.contains("hidden")) b.click(); else location.href = location.pathname + location.search; });
  document.querySelectorAll("[data-setlang]").forEach((b) => b.addEventListener("click", () => {
    const sel = $("lang"); if (!sel) return;
    sel.value = b.dataset.setlang; sel.dispatchEvent(new Event("change"));
  }));
  loadQr();
  if (typeof window.matchMedia === "function") {
    const mq = window.matchMedia(DESK_MQ);
    if (mq.addEventListener) mq.addEventListener("change", loadQr);
  }
}
function markLang() { document.querySelectorAll("[data-setlang]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.setlang === lang))); }

/* ---------------- phone Back button (v1.25.1) ---------------- */
// Starting a repair pushes "#<id>" so Back goes to the first screen (not out of the site, which lost the place) and
// Forward comes back to the same repair. Anything running for the repair (stream, timers, camera, voice) is stopped.
// A clean first screen: step back past the pushed "#<id>" entry when there is one (no duplicate history entry), then reload.
function freshStart() {
  if (history.state && history.state.tc) { window.addEventListener("popstate", () => location.reload(), { once: true }); history.back(); }
  else { history.replaceState(null, "", homePath()); location.reload(); }
}
function onBack() {
  const id = location.hash.length > 1 ? location.hash.slice(1) : "";
  if (es) { es.close(); es = null; }
  if (progTimer) { clearInterval(progTimer); progTimer = null; }
  try { stopTimer(); closeLive(); if (window.speechSynthesis) speechSynthesis.cancel(); } catch (_) { /* nothing was running */ }
  if (!id) { show("capture"); return; }
  show("progress"); startElapsed(); follow(id);
}
window.addEventListener("popstate", () => { if (!document.body.dataset.sid || document.body.dataset.sid.startsWith("{{")) onBack(); });

/* ---------------- boot ---------------- */
document.addEventListener("DOMContentLoaded", () => {
  setupOffline(); applyLang(); health(); setupResult(); setupDemo(); setupDesk();
  const shared = document.body.dataset.sid;
  if (shared && !shared.startsWith("{{")) { // read-only /guide/<id> page
    on("lang", "change", (e) => { lang = e.target.value; applyLang(); });
    fetchSession(shared).then((s) => { S = s; lang = s.lang; applyLang(); render(s); });
    return;
  }
  setupCapture(); renderGarage();
  on("garageClear", "click", () => {
    loadGarage().forEach((e) => { if (e && e.id) fetch(`/api/sessions/${encodeURIComponent(e.id)}`, { method: "DELETE" }).catch(() => null); }); // best effort: erase on the server too
    localStorage.removeItem(GARAGE_KEY); renderGarage();
  });
  if (location.hash.startsWith("#replay-")) history.replaceState(null, "", location.pathname + location.search);  // a recording does not survive a reload
  else if (location.hash.length > 1) { show("progress"); startElapsed(); follow(location.hash.slice(1)); }
});

// PWA: install to home screen. The worker only caches the app shell; it fails quietly when sw.js is absent.
if ("serviceWorker" in navigator && location.protocol !== "file:" && !window.TC_STATIC) {  // the static judge build has no worker
  window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
}

// Keyboard open (text field focused): move the tip bar to the top of the screen.
document.addEventListener("focusin", (e) => {
  const el = e.target;
  if (el && (el.tagName === "TEXTAREA" || (el.tagName === "INPUT" && !["file", "checkbox", "radio", "button"].includes(el.type)))) document.body.classList.add("typing");
});
document.addEventListener("focusout", () => document.body.classList.remove("typing"));
