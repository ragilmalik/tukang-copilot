/* Tukang Copilot phone web app. Plain JavaScript, no build step. Strings in id / jv / en. */
const $ = (id) => document.getElementById(id);
const T = {
  id: { hero: "Apa yang rusak?", heroSub: "Foto barangnya, ceritakan masalahnya, dapat panduan perbaikan langkah demi langkah.", takePhoto: "Ambil foto (1–3)",
        catMotor: "Motor", catPump: "Pompa air", catAppliance: "Elektronik rumah", catPlumbing: "Pipa/keran", catOther: "Lainnya",
        record: "Ketuk untuk bicara", stop: "Ketuk untuk berhenti", typeHere: "…atau ketik masalahnya di sini", go: "Periksa sekarang",
        samples: "Coba contoh:", sMotor: "motor mogok", sPump: "pompa tidak keluar air", sFaucet: "kran menetes", sRice: "rice cooker mati",
        working: "Sedang memeriksa…", answerHere: "Jawaban kamu", send: "Kirim", diagnosis: "Diagnosa", safetyFirst: "Keselamatan dulu",
        tools: "Alat", materials: "Suku cadang", listen: "Dengarkan", next: "Lanjut", handsFree: "Mode tangan bebas (bacakan otomatis)",
        done: "Selesai kalau:", checkStep: "Cek langkah ini", share: "Bagikan laporan", pdf: "Unduh laporan PDF", garage: "Garasi saya", garageNote: "Riwayat perbaikan hanya disimpan di HP ini. Panduan bisa dibuka 24 jam.", garageClear: "Hapus riwayat", again: "Perbaiki barang lain",
        stuck: "Masih rusak, coba rencana lain", stuckHere: "Apa yang terjadi? (mis. sudah dicoba, tetap mati)",
        needPhoto: "Ambil atau unggah foto dulu.", needDesc: "Ceritakan masalahnya (suara atau ketik).",
        footer: "Hanya untuk perbaikan ringan. Untuk gas, listrik rumah, atau tegangan tinggi, panggil teknisi.",
        stages: { listen: "Mendengarkan", gate: "Cek keselamatan awal", look: "Melihat foto", segment: "Menandai bagian (SAM 3.1)", diagnose: "Mendiagnosa",
                  plan: "Menyusun langkah", safety: "Cek keselamatan rencana", illustrate: "Menggambar diagram", narrate: "Menyiapkan suara" },
        diff: "Kesulitan", min: "menit", est: "perkiraan", copied: "Tautan disalin", openW: "Penalaran: Muse Spark Open (open weights)", demo: "Mode demo: jawaban contoh, tanpa biaya API.",
        green: "AMAN", amber: "HATI-HATI", red: "STOP", pass: "✅ Langkah ini beres", fail: "⚠️ Belum pas", checking: "Memeriksa foto…",
        verified: "langkah terverifikasi kamera", recording: "Merekam…", recorded: "Suara terekam ✓", micErr: "Mikrofon tidak bisa dipakai. Ketik saja masalahnya.",
        exhausted: "Sudah semua", newPlan: "Rencana baru siap.", photos: "foto" },
  en: { hero: "What's broken?", heroSub: "Snap it, say what's wrong, get a step-by-step repair guide.", takePhoto: "Take photos (1–3)",
        catMotor: "Motorbike", catPump: "Water pump", catAppliance: "Home appliance", catPlumbing: "Pipes/taps", catOther: "Other",
        record: "Tap to talk", stop: "Tap to stop", typeHere: "…or type the problem here", go: "Check it now",
        samples: "Try a sample:", sMotor: "bike won't start", sPump: "pump gives no water", sFaucet: "dripping tap", sRice: "dead rice cooker",
        working: "Checking…", answerHere: "Your answer", send: "Send", diagnosis: "Diagnosis", safetyFirst: "Safety first",
        tools: "Tools", materials: "Parts", listen: "Listen", next: "Next", handsFree: "Hands-free mode (read steps aloud)",
        done: "Done when:", checkStep: "Check this step", share: "Share report", pdf: "Download PDF report", garage: "My garage", garageNote: "Your repair history stays on this phone only. Guides open for 24 hours.", garageClear: "Clear history", again: "Fix something else",
        stuck: "Still broken, try another plan", stuckHere: "What happened? (e.g. tried it, still dead)",
        needPhoto: "Take or upload a photo first.", needDesc: "Describe the problem (voice or text).",
        footer: "Light repairs only. For gas, house wiring, or high voltage, call a professional.",
        stages: { listen: "Listening", gate: "First safety check", look: "Looking at the photo", segment: "Finding the parts (SAM 3.1)", diagnose: "Diagnosing",
                  plan: "Planning steps", safety: "Plan safety check", illustrate: "Drawing diagrams", narrate: "Preparing voice" },
        diff: "Difficulty", min: "min", est: "est.", copied: "Link copied", openW: "Reasoning: Muse Spark Open (open weights)", demo: "Demo mode: sample answers, no API cost.",
        green: "SAFE", amber: "CAUTION", red: "STOP", pass: "✅ Step looks right", fail: "⚠️ Not quite", checking: "Checking photo…",
        verified: "steps verified by camera", recording: "Recording…", recorded: "Voice recorded ✓", micErr: "Microphone unavailable. Please type the problem.",
        exhausted: "All tried", newPlan: "New plan ready.", photos: "photos" },
};
T.jv = Object.assign({}, T.id, { pdf: "Unduh laporan PDF", garage: "Garasiku", garageNote: "Riwayat ndandani mung disimpen ing HP iki. Pandhuan bisa dibukak 24 jam.", garageClear: "Busak riwayat", sPump: "pompa ora metu banyu", hero: "Apa sing rusak?", heroSub: "Foto barange, critakna masalahe, entuk pandhuan ndandani.", go: "Priksa saiki",
  record: "Tutul kanggo ngomong", next: "Terus", stuck: "Isih rusak, jajal rencana liya", checkStep: "Priksa langkah iki" });

let lang = localStorage.getItem("tc_lang") || "id";
let photoFiles = [], audioBlob = null, rec = null, chunks = [], S = null, stepIdx = 0, category = "", es = null;
const t = (k) => (T[lang] && T[lang][k] !== undefined ? T[lang][k] : T.id[k] !== undefined ? T.id[k] : k);
const rupiah = (n) => "Rp" + Number(n || 0).toLocaleString("id-ID");
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const on = (id, ev, fn) => $(id) && $(id).addEventListener(ev, fn);

function applyLang() {
  document.documentElement.lang = lang === "en" ? "en" : "id";
  document.querySelectorAll("[data-t]").forEach((el) => (el.textContent = t(el.dataset.t)));
  document.querySelectorAll("[data-tp]").forEach((el) => (el.placeholder = t(el.dataset.tp)));
  if ($("lang")) $("lang").value = lang;
  if (S) { renderProgress(S); if (S.plan) render(S); }
  if ($("garage") && !$("capture").classList.contains("hidden")) renderGarage();
  badges();
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

/* ---------------- capture ---------------- */
function setupCapture() {
  on("lang", "change", (e) => { lang = e.target.value; localStorage.setItem("tc_lang", lang); applyLang(); });
  on("photo", "change", (e) => {
    photoFiles = [...e.target.files].slice(0, 3);
    if (photoFiles.length) {
      $("photoPreview").src = URL.createObjectURL(photoFiles[0]); $("photoPreview").classList.remove("hidden");
      $("photoHint").textContent = photoFiles.length > 1 ? `${photoFiles.length} ${t("photos")}` : "";
    }
  });
  document.querySelectorAll("#cats .chip").forEach((b) => b.addEventListener("click", () => {
    category = category === b.dataset.cat ? "" : b.dataset.cat;
    document.querySelectorAll("#cats .chip").forEach((x) => x.classList.toggle("on", x.dataset.cat === category));
  }));
  on("micBtn", "click", toggleRec);
  on("goBtn", "click", () => submit(""));
  document.querySelectorAll(".sample").forEach((b) => b.addEventListener("click", () => submit(b.dataset.sample)));
  on("answerBtn", "click", sendAnswer);
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
      $("micBtn").classList.remove("rec"); $("micBtn").innerHTML = "🎙️ " + esc(t("record")); $("recState").textContent = t("recorded");
    };
    rec.start(); $("micBtn").classList.add("rec"); $("micBtn").innerHTML = "⏹️ " + esc(t("stop")); $("recState").textContent = t("recording");
    setTimeout(() => rec && rec.state === "recording" && rec.stop(), 60000); // spec: max 60 s
  } catch (_) { $("formErr").textContent = t("micErr"); }
}

async function submit(sample) {
  $("formErr").textContent = "";
  const text = $("text").value.trim();
  if (!sample && !photoFiles.length) return ($("formErr").textContent = t("needPhoto"));
  if (!sample && !text && !audioBlob) return ($("formErr").textContent = t("needDesc"));
  const fd = new FormData();
  fd.append("language", lang); fd.append("text", sample ? "" : text); fd.append("category", category);
  if (sample) fd.append("sample", sample);
  else photoFiles.forEach((f, i) => fd.append("photos", f, f.name || `photo${i + 1}.jpg`));
  if (audioBlob && !sample) {
    const ext = audioBlob.type.includes("mp4") ? "m4a" : audioBlob.type.includes("ogg") ? "ogg" : "webm";
    fd.append("audio", audioBlob, "voice." + ext);
  }
  $("goBtn").disabled = true;
  try {
    const r = await fetch("/api/sessions", { method: "POST", body: fd });
    const j = await r.json();
    if (!r.ok) throw new Error(j.detail || r.statusText);
    history.replaceState(null, "", "#" + j.id);
    show("progress"); follow(j.id);
  } catch (e) { $("formErr").textContent = e.message; }
  finally { $("goBtn").disabled = false; }
}

function show(which) {
  ["capture", "progress", "result"].forEach((s) => $(s) && $(s).classList.toggle("hidden", s !== which));
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
  $("question").classList.toggle("hidden", s.status !== "needs_answer");
  if (s.status === "needs_answer") $("questionText").textContent = s.question;
  const stopped = ["stopped", "exhausted"].includes(s.status);
  $("stopBox").classList.toggle("hidden", !stopped);
  if (stopped) { $("stopBox").textContent = "⛔ " + (s.stop_reason || ""); saveGarage(s); }
  $("jobErr").textContent = s.status === "error" ? s.error : "";
}

async function sendAnswer() {
  const v = $("answerText").value.trim(); if (!v) return;
  const fd = new FormData(); fd.append("text", v);
  await fetch(`/api/sessions/${S.id}/answer`, { method: "POST", body: fd });
  $("answerText").value = ""; follow(S.id);
}

/* ---------------- result + guided repair ---------------- */
function render(s) {
  if (!s || !s.plan) return;
  const rep = s.object_report || {}, dx = s.diagnosis || {}, plan = s.plan, base = s.files_base;
  if ($("pdfBtn")) $("pdfBtn").href = `/api/sessions/${s.id}/report.pdf`;
  saveGarage(s);
  $("dxObject").textContent = rep.object || ""; $("dxSummary").textContent = dx.problem_summary || "";
  const lvl = (s.safety || {}).level || dx.safety_level;
  $("safetyBadge").className = "level " + lvl; $("safetyBadge").textContent = t(lvl);
  $("safetyReason").textContent = dx.safety_reason || "";
  $("dxCauses").innerHTML = (dx.causes || []).map((c, i) => `<li${i === s.cause_index ? ' class="on"' : ""}><span class="pct">${c.confidence}%</span> ${esc(c.title)}<br><span class="muted small">${esc((c.evidence || []).join("; "))}</span></li>`).join("");
  if (s.parts_image) {
    $("partsWrap").classList.remove("hidden"); $("partsImg").src = base + s.parts_image;
    $("partsList").innerHTML = Object.values(s.parts || {}).map((p) => `<li>${p.label}. ${esc(p.name)}${p.found ? "" : " (?)"}</li>`).join("");
  }
  $("gTitle").textContent = plan.cause_title;
  $("gDiff").textContent = `${t("diff")} ${dx.difficulty}/5`; $("gTime").textContent = `⏱ ${dx.minutes_estimate} ${t("min")}`;
  $("gCost").textContent = `💰 ${t("est")} ${rupiah(dx.cost_estimate_idr)}`;
  $("gSafety").innerHTML = (window.SAFETY_BASE[lang] || []).map((x) => `<li>${esc(x)}</li>`).join("");
  const li = (i) => `<li>${esc(i.name)} <span class="muted small">${i.est_price_idr ? rupiah(i.est_price_idr) : ""}</span></li>`;
  $("gTools").innerHTML = (dx.tools || []).map(li).join(""); $("gMats").innerHTML = (dx.parts || []).map(li).join("");
  $("gDone").textContent = plan.done_check || ""; $("gPro").textContent = plan.when_to_call_pro ? "🧑‍🔧 " + plan.when_to_call_pro : "";
  $("disclaimer").textContent = (s.safety || {}).disclaimer || "";
  const uniq = [...new Set(Object.values(s.models || {}))];
  $("models").textContent = "Meta models: " + uniq.join(" · ");
  renderStep(); renderVerified();
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
  $("stepImg").src = stepImage(st); $("stepImg").alt = st.instruction; $("stepImg").classList.remove("hidden");
  $("prevBtn").disabled = stepIdx === 0; $("nextBtn").disabled = stepIdx === S.plan.steps.length - 1;
  const c = (S.checks || {})[String(st.n)];
  if (c && c.tries && c.tries.length) showCheck(c.tries[c.tries.length - 1]); else $("checkResult").classList.add("hidden");
  if ($("handsFree").checked) play();
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

function renderVerified() {
  const n = S.plan.steps.filter((st) => ((S.checks || {})[String(st.n)] || {}).passed).length;
  $("verifiedCount").textContent = `✅ ${n}/${S.plan.steps.length} ${t("verified")}`;
}

function setupResult() {
  on("prevBtn", "click", () => { if (stepIdx > 0) { stepIdx--; renderStep(); } });
  on("nextBtn", "click", () => { if (stepIdx < S.plan.steps.length - 1) { stepIdx++; renderStep(); } });
  on("playBtn", "click", play);
  on("stepPhoto", "change", async (e) => {
    const f = e.target.files[0]; if (!f) return;
    const st = S.plan.steps[stepIdx], fd = new FormData(); fd.append("photo", f, f.name || "check.jpg");
    $("checkResult").classList.remove("hidden"); $("checkResult").textContent = t("checking");
    const r = await fetch(`/api/sessions/${S.id}/steps/${st.n}/check`, { method: "POST", body: fd });
    const j = await r.json(); e.target.value = "";
    if (!r.ok) { $("checkResult").textContent = j.detail; return; }
    S = await fetchSession(S.id); showCheck(j); renderVerified();
    if (j.passed && stepIdx < S.plan.steps.length - 1) setTimeout(() => { stepIdx++; renderStep(); }, 1500);
  });
  on("stuckBtn", "click", async () => {
    const fd = new FormData(); fd.append("report", $("stuckText").value.trim());
    $("stuckBtn").disabled = true; $("stuckMsg").textContent = t("working");
    try {
      const r = await fetch(`/api/sessions/${S.id}/replan`, { method: "POST", body: fd });
      S = await r.json();
      if (S.status === "ready") { stepIdx = 0; render(S); $("stuckMsg").textContent = t("newPlan"); $("stuckText").value = ""; window.scrollTo(0, 0); }
      else $("stuckMsg").textContent = "⛔ " + (S.stop_reason || S.error || "");
    } finally { $("stuckBtn").disabled = false; }
  });
  on("shareBtn", "click", async () => {
    const url = location.origin + "/guide/" + S.id;
    if (navigator.share) { try { await navigator.share({ title: "Tukang Copilot", url }); return; } catch (_) {} }
    try { await navigator.clipboard.writeText(url); alert(t("copied")); } catch (_) { prompt("Link", url); }
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
    verified: steps.filter((st) => (checks[String(st.n)] || {}).passed).length, total: steps.length, at: Math.round((s.created || Date.now() / 1000) * 1000) };
  const g = [entry].concat(loadGarage().filter((e) => e && e.id !== s.id)).slice(0, GARAGE_MAX);
  try { localStorage.setItem(GARAGE_KEY, JSON.stringify(g)); } catch (_) {}
  renderGarage();
}
function renderGarage() {
  if (!$("garage")) return;
  const g = loadGarage();
  $("garage").classList.toggle("hidden", !g.length || ($("capture") && $("capture").classList.contains("hidden")));
  $("garageList").innerHTML = g.map((e) => {
    const day = new Date(e.at).toLocaleDateString(lang === "en" ? "en-GB" : "id-ID", { day: "numeric", month: "short" });
    const lvl = ["green", "amber", "red"].includes(e.level) ? e.level : "";
    return `<li><a href="/guide/${encodeURIComponent(e.id)}">${esc(e.object || e.id)}</a> ` +
      (lvl ? `<span class="level ${lvl}">${esc(t(lvl))}</span> ` : "") +
      `<span class="muted small">${esc(day)}${e.total ? ` · ${e.verified}/${e.total} ✓` : ""}${e.fix ? " · " + esc(e.fix) : ""}</span></li>`;
  }).join("");
}

/* ---------------- boot ---------------- */
document.addEventListener("DOMContentLoaded", () => {
  applyLang(); health(); setupResult();
  const shared = document.body.dataset.sid;
  if (shared && !shared.startsWith("{{")) { // read-only /guide/<id> page
    on("lang", "change", (e) => { lang = e.target.value; applyLang(); });
    fetchSession(shared).then((s) => { S = s; lang = s.lang; applyLang(); render(s); });
    return;
  }
  setupCapture(); renderGarage();
  on("garageClear", "click", () => { localStorage.removeItem(GARAGE_KEY); renderGarage(); });
  if (location.hash.length > 1) { show("progress"); follow(location.hash.slice(1)); }
});

// PWA: install to home screen. The worker only caches the app shell; it fails quietly when sw.js is absent.
if ("serviceWorker" in navigator && location.protocol !== "file:") {
  window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
}
