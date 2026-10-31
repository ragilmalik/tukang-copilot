/* Tukang Copilot phone web app. Plain JavaScript, no build step. Strings in id / jv / en. */
const $ = (id) => document.getElementById(id);
const T = {
  id: { hero: "Apa yang rusak?", heroSub: "Foto barangnya, ceritakan masalahnya, dapat panduan perbaikan langkah demi langkah.", takePhoto: "Ambil foto (1–3)",
        catMotor: "Motor", catPump: "Pompa air", catAppliance: "Elektronik rumah", catPlumbing: "Pipa/keran", catOther: "Lainnya",
        record: "Ketuk untuk bicara", stop: "Ketuk untuk berhenti", typeHere: "…atau ketik masalahnya di sini", go: "Periksa sekarang",
        samples: "Coba contoh:", sMotor: "motor mogok", sPump: "pompa tidak keluar air", sFaucet: "kran menetes", sRice: "rice cooker mati", sTire: "ban kempes",
        working: "Sedang memeriksa…", retry: "Coba lagi", answerHere: "Jawaban kamu", send: "Kirim", diagnosis: "Diagnosa", safetyFirst: "Keselamatan dulu",
        tools: "Alat", materials: "Suku cadang", listen: "Dengarkan", next: "Lanjut", handsFree: "Mode tangan bebas (bacakan otomatis)",
        done: "Selesai kalau:", outcomeAsk: "Sudah jalan lagi?", fixedBtn: "Sudah beres 🎉", proBtn: "Dibawa ke bengkel", fixedThanks: "Mantap! Perbaikan selesai.", proThanks: "Tidak apa-apa, membawa ke ahli itu pilihan yang aman. Laporan PDF bisa ditunjukkan ke mekanik.", savedTotal: "Total hemat", savedFrom: "dari", savedUnit: "perbaikan", preTitle: "Sebelum mulai, pastikan:", preLocked: "Centang semua dulu, baru langkah 1 terbuka.", preReady: "✅ Siap. Langkah 1 terbuka.", waitFor: "Tunggu {n} menit", timerStart: "Mulai pengatur waktu", timerStop: "Hentikan", timerDone: "Waktu tunggu selesai. Lanjut ke langkah berikutnya.", checkStep: "Cek langkah ini", liveGuide: "Panduan kamera langsung", liveCheck: "📸 Cek sekarang", liveClose: "Tutup kamera", liveStart: "Menyalakan kamera…", liveAim: "Arahkan kamera ke {name}", liveFound: "🎯 Ketemu {name}", liveLost: "Belum ketemu {name}. Gerakkan HP pelan-pelan.", liveNoPart: "Langkah ini tidak menunjuk bagian tertentu. Pakai Cek sekarang.", liveNoCam: "Kamera langsung tidak bisa dipakai di HP ini. Pakai tombol foto untuk cek langkah.", liveLimit: "Batas kamera langsung untuk perbaikan ini sudah habis. Pakai foto untuk cek langkah.", share: "Bagikan laporan", pdf: "Unduh laporan PDF", workshop: "Lembar bengkel (cetak besar)", hood: "Di balik layar: model yang dipakai", hs_listen: "Dengar suara", hs_gate: "Cek keselamatan teks", hs_look: "Lihat foto", hs_segment: "Tandai bagian", hs_diagnose: "Diagnosa", hs_plan: "Susun langkah", hs_safety: "Cek keselamatan rencana", hs_illustrate: "Gambar bantu", hs_narrate: "Suara pemandu", wa: "Kirim daftar belanja ke WhatsApp", buy: "Cari harga", garage: "Garasi saya", garageNote: "Riwayat perbaikan hanya disimpan di HP ini. Panduan bisa dibuka 24 jam.", garageClear: "Hapus riwayat", again: "Perbaiki barang lain", erase: "Hapus foto saya sekarang", eraseAsk: "Hapus foto, suara, dan panduan ini dari server sekarang?", erased: "Sudah dihapus dari server.",
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
        exhausted: "Sudah semua", newPlan: "Rencana baru siap.", photos: "foto", videoBtn: "🎥 Atau rekam video 5–10 detik", videoOk: "Video siap ✓ (3 gambar terbaik diambil otomatis)", videoBig: "Videonya terlalu besar. Rekam 5–10 detik saja." },
  en: { hero: "What's broken?", heroSub: "Snap it, say what's wrong, get a step-by-step repair guide.", takePhoto: "Take photos (1–3)",
        catMotor: "Motorbike", catPump: "Water pump", catAppliance: "Home appliance", catPlumbing: "Pipes/taps", catOther: "Other",
        record: "Tap to talk", stop: "Tap to stop", typeHere: "…or type the problem here", go: "Check it now",
        samples: "Try a sample:", sMotor: "bike won't start", sPump: "pump gives no water", sFaucet: "dripping tap", sRice: "dead rice cooker", sTire: "flat tyre",
        working: "Checking…", retry: "Try again", answerHere: "Your answer", send: "Send", diagnosis: "Diagnosis", safetyFirst: "Safety first",
        tools: "Tools", materials: "Parts", listen: "Listen", next: "Next", handsFree: "Hands-free mode (read steps aloud)",
        done: "Done when:", outcomeAsk: "Does it work again?", fixedBtn: "It works now 🎉", proBtn: "Took it to a mechanic", fixedThanks: "Great, repair done.", proThanks: "That is a safe choice. Show the PDF report to the mechanic.", savedTotal: "Total saved", savedFrom: "from", savedUnit: "repairs", preTitle: "Before you start, make sure:", preLocked: "Tick everything first to unlock step 1.", preReady: "✅ Ready. Step 1 is open.", waitFor: "Wait {n} minutes", timerStart: "Start timer", timerStop: "Stop", timerDone: "Waiting time is over. Go on to the next step.", checkStep: "Check this step", liveGuide: "Live camera guide", liveCheck: "📸 Check now", liveClose: "Close camera", liveStart: "Starting the camera…", liveAim: "Point the camera at the {name}", liveFound: "🎯 Found {name}", liveLost: "Can't see the {name} yet. Move the phone slowly.", liveNoPart: "This step does not point at one part. Use Check now.", liveNoCam: "The live camera is not available on this phone. Use the photo button to check the step.", liveLimit: "The live camera limit for this repair is used up. Use a photo to check the step.", share: "Share report", pdf: "Download PDF report", workshop: "Workshop sheets (large print)", hood: "Under the hood: models used", hs_listen: "Listen", hs_gate: "Text safety gate", hs_look: "Look at photo", hs_segment: "Mark parts", hs_diagnose: "Diagnose", hs_plan: "Plan steps", hs_safety: "Plan safety gate", hs_illustrate: "Helper diagram", hs_narrate: "Voice guide", wa: "Send shopping list to WhatsApp", buy: "Compare prices", garage: "My garage", garageNote: "Your repair history stays on this phone only. Guides open for 24 hours.", garageClear: "Clear history", again: "Fix something else", erase: "Delete my photos now", eraseAsk: "Delete the photos, voice and guide of this repair from the server now?", erased: "Deleted from the server.",
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
        exhausted: "All tried", newPlan: "New plan ready.", photos: "photos", videoBtn: "🎥 Or record a 5–10 s video", videoOk: "Video ready ✓ (the 3 sharpest frames are picked for you)", videoBig: "That video is too big. Record 5–10 seconds." },
};
// Basa Jawa (ngoko, as spoken around Semarang). Falls back to Bahasa Indonesia for any key not listed.
T.jv = Object.assign({}, T.id, {
  hero: "Apa sing rusak?", heroSub: "Foto barange, critakna masalahe, entuk pandhuan ndandani langkah demi langkah.", takePhoto: "Jupuk foto (1–3)",
  catMotor: "Motor", catPump: "Pompa banyu", catAppliance: "Elektronik omah", catPlumbing: "Pipa/kran", catOther: "Liyane",
  record: "Tutul kanggo ngomong", stop: "Tutul kanggo mandheg", typeHere: "…utawa ketik masalahe ing kene", go: "Priksa saiki",
  samples: "Jajal conto:", sMotor: "motor mogok", sPump: "pompa ora metu banyu", sFaucet: "kran netes", sRice: "rice cooker mati", sTire: "ban kempes",
  working: "Lagi dipriksa…", retry: "Jajal maneh", answerHere: "Wangsulanmu", send: "Kirim", diagnosis: "Diagnosa", safetyFirst: "Slamet dhisik",
  tools: "Piranti", materials: "Suku cadang", listen: "Rungokna", next: "Terus", handsFree: "Mode tanpa tangan (diwacakake otomatis)",
  done: "Rampung yen:", outcomeAsk: "Wis urip maneh?", fixedBtn: "Wis rampung 🎉", proBtn: "Digawa menyang bengkel", fixedThanks: "Apik! Ndandani rampung.", proThanks: "Ora apa-apa, digawa menyang ahli iku pilihan sing aman. Laporan PDF bisa dituduhake marang mekanik.", savedTotal: "Total irit", savedFrom: "saka", savedUnit: "ndandani", preTitle: "Sadurunge miwiti, priksa:", preLocked: "Centhang kabeh dhisik, banjur langkah 1 mbukak.", preReady: "✅ Siap. Langkah 1 wis mbukak.", waitFor: "Antosna {n} menit", timerStart: "Wiwiti pangetung wektu", timerStop: "Mandhegna", timerDone: "Wektu antosan wis rampung. Terus menyang langkah sabanjure.", checkStep: "Priksa langkah iki", liveGuide: "Pandhuan kamera langsung", liveCheck: "📸 Priksa saiki", liveClose: "Tutup kamera", liveStart: "Nguripake kamera…", liveAim: "Arahna kamera menyang {name}", liveFound: "🎯 Ketemu {name}", liveLost: "Durung ketemu {name}. Obahna HP alon-alon.", liveNoPart: "Langkah iki ora nuduhake perangan tartamtu. Enggo Priksa saiki.", liveNoCam: "Kamera langsung ora bisa dienggo ing HP iki. Enggo tombol foto kanggo mriksa langkah.", liveLimit: "Wates kamera langsung kanggo ndandani iki wis entek. Enggo foto kanggo mriksa langkah.", share: "Bagekna laporan", pdf: "Undhuh laporan PDF", workshop: "Lembar bengkel (cetak gedhe)", hood: "Ing mburi layar: model sing dipakai", hs_listen: "Rungokake swara", hs_gate: "Priksa slamet teks", hs_look: "Delok foto", hs_segment: "Tandhani bagean", hs_diagnose: "Diagnosa", hs_plan: "Nyusun langkah", hs_safety: "Priksa slamet rencana", hs_illustrate: "Gambar bantu", hs_narrate: "Swara panuntun", wa: "Kirim dhaptar blanja menyang WhatsApp", buy: "Golek rega", garage: "Garasiku",
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
  exhausted: "Wis kabeh dijajal", newPlan: "Rencana anyar wis siap.", photos: "foto", videoBtn: "🎥 Utawa rekam video 5–10 detik", videoOk: "Video siap ✓ (3 gambar paling cetha dijupuk otomatis)", videoBig: "Videone kegedhen. Rekam 5–10 detik wae.",
});

let lang = localStorage.getItem("tc_lang") || "id";
let videoFile = null;
let photoFiles = [], audioBlob = null, rec = null, chunks = [], S = null, stepIdx = 0, category = "", es = null;
const t = (k) => (T[lang] && T[lang][k] !== undefined ? T[lang][k] : T.id[k] !== undefined ? T.id[k] : k);
const rupiah = (n) => "Rp" + Number(n || 0).toLocaleString("id-ID");
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const on = (id, ev, fn) => $(id) && $(id).addEventListener(ev, fn);

function applyLang() {
  document.documentElement.lang = lang === "en" ? "en" : lang === "jv" ? "jv" : "id";
  document.querySelectorAll("[data-t]").forEach((el) => (el.textContent = t(el.dataset.t)));
  document.querySelectorAll("[data-tp]").forEach((el) => (el.placeholder = t(el.dataset.tp)));
  if ($("lang")) $("lang").value = lang;
  if (S) { renderProgress(S); if (S.plan) render(S); }
  if ($("garage") && !$("capture").classList.contains("hidden")) renderGarage();
  badges();
  if (window.__offlineRefresh) window.__offlineRefresh();
}

let HEALTH = null;
// Header badges: demo mode, and the open-weights brain (Muse Spark Open on Baseten) when it is really in use.
function badges() {
  if (!HEALTH) return;
  if (HEALTH.mode === "mock") { $("modeBadge").textContent = t("demo"); $("modeBadge").classList.remove("hidden"); }
  if (HEALTH.open_weights && $("owBadge")) { $("owBadge").textContent = "🔓 " + t("openW"); $("owBadge").classList.remove("hidden"); }
}

async function health() {
  try {
    const h = await (await fetch("/api/health")).json();
    HEALTH = h; badges();
  } catch (_) {}
}

/* Network trouble: friendly text instead of "Failed to fetch", plus a banner while the phone is offline. */
function netMsg(e) {
  const m = e && e.message ? String(e.message) : "";
  return (!e || e.name === "TypeError" || /failed to fetch|load failed|networkerror|network request/i.test(m) || (typeof navigator !== "undefined" && navigator.onLine === false)) ? t("netErr") : (m || t("netErr"));
}
function setupOffline() {
  const bar = $("offlineBar"); if (!bar) return;
  const upd = () => { bar.textContent = "📡 " + t("offline"); bar.classList.toggle("hidden", navigator.onLine !== false); };
  window.addEventListener("online", upd); window.addEventListener("offline", upd);
  window.__offlineRefresh = upd; upd();
}

/* ---------------- capture ---------------- */
function setupCapture() {
  on("lang", "change", (e) => { lang = e.target.value; localStorage.setItem("tc_lang", lang); applyLang(); });
  on("video", "change", (e) => {
    videoFile = e.target.files[0] || null;
    if (videoFile && videoFile.size > 40 * 1024 * 1024) { videoFile = null; $("formErr").textContent = t("videoBig"); return; }
    $("videoHint").textContent = videoFile ? t("videoOk") : "";
  });
  on("photo", "change", (e) => {
    photoFiles = [...e.target.files].slice(0, 3);
    if (photoFiles.length) {
      $("photoPreview").src = URL.createObjectURL(photoFiles[0]); $("photoPreview").classList.remove("hidden");
      $("photoHint").textContent = photoFiles.length > 1 ? `${photoFiles.length} ${t("photos")}` : "";
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
    history.replaceState(null, "", "#" + j.id);
    show("progress"); follow(j.id);
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
function show(which) {
  ["capture", "progress", "result"].forEach((s) => $(s) && $(s).classList.toggle("hidden", s !== which));
  // Move focus to the new section's heading so screen-reader and keyboard users land on it (not on first load).
  if (!firstShow) {
    const h = $(which) && $(which).querySelector("h1, h2");
    if (h) { h.tabIndex = -1; try { h.focus({ preventScroll: true }); } catch (_) { /* old browsers */ } }
  }
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
      const snap = JSON.parse(ev.data); S = Object.assign(S || {}, snap); renderProgress(S);
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
    `<li class="${esc(v.status)}">${esc(t("stages")[k] || k)}<span class="note">${esc(v.note || "")}</span></li>`).join("");
  if ($("progressStatus")) {  // short screen-reader status instead of re-announcing the whole list
    const run = Object.entries(s.stages).find(([, v]) => v.status === "running");
    const nDone = Object.values(s.stages).filter((v) => v.status === "done").length;
    $("progressStatus").textContent = run ? `${nDone}/${Object.keys(s.stages).length}: ${t("stages")[run[0]] || run[0]}` : "";
  }
  $("question").classList.toggle("hidden", s.status !== "needs_answer");
  if (s.status === "needs_answer") $("questionText").textContent = s.question;
  const stopped = ["stopped", "exhausted"].includes(s.status);
  $("stopBox").classList.toggle("hidden", !stopped);
  if (stopped) { renderStop(s); saveGarage(s); }
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
  $("jobErr").textContent = ""; $("answerText").value = ""; follow(S.id);
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
    + ` <a class="btn link" href="/api/sessions/${esc(s.id)}/report.pdf">📄 ${esc(t("pdf"))}</a></p>`
    + `<p class="small">${esc(t("emergency"))}</p>`;
}

/* ---------------- result + guided repair ---------------- */
function render(s) {
  if (!s || !s.plan) return;
  const rep = s.object_report || {}, dx = s.diagnosis || {}, plan = s.plan, base = s.files_base;
  if ($("pdfBtn")) $("pdfBtn").href = `/api/sessions/${s.id}/report.pdf`;
  if ($("workshopBtn")) $("workshopBtn").href = `/api/sessions/${s.id}/workshop.pdf`;
  saveGarage(s);
  $("dxObject").textContent = rep.object || ""; $("dxSummary").textContent = dx.problem_summary || "";
  const lvl = (s.safety || {}).level || dx.safety_level;
  $("safetyBadge").className = "level " + lvl; $("safetyBadge").textContent = t(lvl);
  $("safetyReason").textContent = dx.safety_reason || "";
  $("dxCauses").innerHTML = (dx.causes || []).map((c, i) => `<li${i === s.cause_index ? ' class="on"' : ""}><span class="pct">${c.confidence}%</span> ${esc(c.title)}<br><span class="muted small">${esc((c.evidence || []).join("; "))}</span></li>`).join("");
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
  renderHood(s);
  renderPreflight(s, dx);
  renderStep(); renderVerified(); renderOutcome();
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
  if (f) { $("player").src = S.files_base + f; $("player").play().catch(() => {}); return; }
  if (window.speechSynthesis) { // browser voice fallback (no server TTS)
    const u = new SpeechSynthesisUtterance(st.voice_text || st.instruction); u.lang = lang === "en" ? "en-US" : "id-ID";
    speechSynthesis.cancel(); speechSynthesis.speak(u);
  }
}

function showCheck(r) {
  $("checkResult").classList.remove("hidden");
  $("checkResult").innerHTML = `<p class="${r.passed ? "pass" : "fail"}">${esc(r.passed ? t("pass") : t("fail"))}</p><p>${esc(r.observation)}</p>`
    + (r.correction ? `<p><b>→</b> ${esc(r.correction)}</p>` : "") + (r.escalate_hint ? `<p class="caution">${esc(r.escalate_hint)}</p>` : "");
}

function renderOutcome() {
  const box = $("outcome"); if (!box || !S) return;
  const oc = S.outcome || {}, r = oc.result || "";
  box.classList.toggle("hidden", !S.plan);
  $("fixedBtn").setAttribute("aria-pressed", String(r === "fixed")); $("proBtn").setAttribute("aria-pressed", String(r === "pro"));
  $("outcomeMsg").textContent = r === "fixed" ? t("fixedThanks") + (oc.saved_idr ? ` ${t("save")} ${rupiah(oc.saved_idr)}.` : "") : r === "pro" ? t("proThanks") : "";
}
async function sendOutcome(result) {
  if (!S || !S.id) return;
  const fd = new FormData(); fd.append("result", result);
  try {
    const r = await fetch(`/api/sessions/${S.id}/outcome`, { method: "POST", body: fd });
    const j = await r.json();
    if (!r.ok) { $("outcomeMsg").textContent = "⚠️ " + (j.detail || r.statusText); return; }
    S = j; setGarageOutcome(S.id, result, (S.outcome || {}).saved_idr); renderOutcome();
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
    S = await fetchSession(S.id); showCheck(j); renderVerified();
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
      if (S.status === "ready") { stepIdx = 0; render(S); $("stuckMsg").textContent = t("newPlan"); $("stuckText").value = ""; window.scrollTo(0, 0); }
      else $("stuckMsg").textContent = "⛔ " + (S.stop_reason || S.error || "");
    } catch (err) { $("stuckMsg").textContent = "⚠️ " + netMsg(err);
    } finally { $("stuckBtn").disabled = false; }
  });
  on("shareBtn", "click", async () => {
    const url = location.origin + "/guide/" + S.id;
    if (navigator.share) { try { await navigator.share({ title: "Tukang Copilot", url }); return; } catch (_) {} }
    try { await navigator.clipboard.writeText(url); alert(t("copied")); } catch (_) { prompt("Link", url); }
  });
  on("eraseBtn", "click", () => {
    if (!S || !S.id || !confirm(t("eraseAsk"))) return;
    const id = S.id;
    fetch(`/api/sessions/${encodeURIComponent(id)}`, { method: "DELETE" }).catch(() => null).then(() => {
      try { localStorage.setItem(GARAGE_KEY, JSON.stringify(loadGarage().filter((e) => e && e.id !== id))); } catch (_) {}
      alert(t("erased")); history.replaceState(null, "", "/"); location.reload();
    });
  });
  on("againBtn", "click", () => { history.replaceState(null, "", "/"); location.reload(); });
}

window.SAFETY_BASE = {
  id: ["Cabut steker / matikan mesin dan tunggu dingin sebelum mulai.", "Pakai sarung tangan dan kacamata bila ada serpihan, bensin, atau cairan."],
  jv: ["Copot steker / pateni mesin lan enteni adhem sadurunge miwiti.", "Nganggo sarung tangan lan kacamata yen ana pecahan, bensin, utawa cairan."],
  en: ["Unplug it / switch the engine off and let it cool before you start.", "Wear gloves and eye protection around shards, fuel or liquids."],
};

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

/* ---------------- boot ---------------- */
document.addEventListener("DOMContentLoaded", () => {
  setupOffline(); applyLang(); health(); setupResult();
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
  if (location.hash.length > 1) { show("progress"); follow(location.hash.slice(1)); }
});

// PWA: install to home screen. The worker only caches the app shell; it fails quietly when sw.js is absent.
if ("serviceWorker" in navigator && location.protocol !== "file:") {
  window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
}
