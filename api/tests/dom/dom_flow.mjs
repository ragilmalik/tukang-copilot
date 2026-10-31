// Headless DOM check of the real web/app.js (jsdom, no browser needed).
// Usage: node dom_flow.mjs <base-url>   (jsdom found via NODE_PATH or JSDOM_DIR)
// Prints one JSON line {ok, checks:[{name, ok, detail}]}; exit code 1 on failure.
import { createRequire } from "node:module";
const base = process.argv[2];
const require = createRequire((process.env.JSDOM_DIR || process.cwd()) + "/");
const { JSDOM, VirtualConsole } = require("jsdom");

const checks = [];
const check = (name, ok, detail = "") => checks.push({ name, ok: !!ok, detail: String(detail).slice(0, 200) });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function until(fn, ms = 20000) { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (fn()) return true; await sleep(150); } return false; }

function nodeFetch(url, opts = {}) {
  const u = new URL(url, base);
  const o = { ...opts };
  if (o.body && typeof o.body.entries === "function" && !(o.body instanceof URLSearchParams)) {
    const fd = new FormData(); for (const [k, v] of o.body.entries()) fd.append(k, typeof v === "string" ? v : String(v));
    o.body = fd;
  }
  return fetch(u, o);
}

async function run(lang, sample) {
  const errors = [];
  const vc = new VirtualConsole(); vc.on("jsdomError", (e) => errors.push(String(e.message || e)));
  const dom = await JSDOM.fromURL(base + "/", {
    runScripts: "dangerously", resources: "usable", pretendToBeVisual: true, virtualConsole: vc,
    beforeParse(w) { w.fetch = nodeFetch; w.localStorage.setItem("tc_lang", lang); w.scrollTo = () => {}; },
  });
  const w = dom.window, d = w.document;
  await until(() => d.readyState === "complete");
  await sleep(300);
  check(`${lang}: demo badge`, await until(() => !d.getElementById("modeBadge").classList.contains("hidden"), 5000));
  check(`${lang}: html lang attribute`, d.documentElement.lang === lang, d.documentElement.lang);
  check(`${lang}: pickers reachable by keyboard`, ["photoBox", "videoBox", "stepPhotoLabel"].every((i) => d.getElementById(i).tabIndex === 0));
  check(`${lang}: mic button has aria-pressed`, d.getElementById("micBtn").getAttribute("aria-pressed") === "false");
  const chip = d.querySelector('#cats .chip[data-cat="pump"]');
  chip.click();
  check(`${lang}: category chip aria-pressed toggles`, chip.getAttribute("aria-pressed") === "true"
    && d.querySelector('#cats .chip[data-cat="motor"]').getAttribute("aria-pressed") === "false");
  chip.click();
  d.getElementById("photoBox").dispatchEvent(new w.KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  const viaDemo = sample === "motor" && lang === "en";  // the 1-tap demo button runs the motor sample with the tour
  check(`${lang}: 1-tap demo button translated`, !/demoBtn/.test(d.getElementById("demoBtn").textContent) && d.getElementById("demoBtn").textContent.length > 8);
  if (viaDemo) d.getElementById("demoBtn").click(); else d.querySelector(`button.sample[data-sample="${sample}"]`).click();
  if (viaDemo) check(`${lang}: tour bar shows a tip`, await until(() => !d.getElementById("tourBar").classList.contains("hidden") && d.getElementById("tourText").textContent.length > 10, 8000));
  const shown = (id) => !d.getElementById(id).classList.contains("hidden");
  if (sample === "rice") {  // red safety stop: no repair steps, a stop box with a service-centre card
    const stopped = await until(() => shown("stopBox"));
    check(`${lang}/${sample}: red stop box shown`, stopped);
    check(`${lang}/${sample}: no result page on red stop`, !shown("result"));
    check(`${lang}/${sample}: stop box has text`, d.getElementById("stopBox").textContent.trim().length > 40, d.getElementById("stopBox").textContent);
    check(`${lang}/${sample}: stop box has the bengkel hand-off`, await until(() => !!d.querySelector('#stopHandoff a[href^="https://wa.me/"]'), 5000));
    w.close(); return;
  }
  if (sample === "motor") {  // the agent asks one follow-up question first
    const asked = await until(() => shown("question"));
    check(`${lang}/${sample}: follow-up question shown`, asked && d.getElementById("questionText").textContent.length > 3);
    const qa = [...d.querySelectorAll("#quickAns button")].map((b) => b.textContent.trim());
    check(`${lang}/${sample}: quick answers translated`, qa.length === 3 && qa.every((x) => x && !/^q[A-Z]/.test(x)), qa.join("|"));
    const live = d.getElementById("agentLive");
    check(`${lang}/${sample}: live agent log explains the question`, live && !live.classList.contains("hidden") && /60/.test(live.textContent) && !/ag_|lp_|\{/.test(live.textContent), live && live.textContent);
    check(`${lang}/${sample}: progress shows the model per stage`, /muse-spark-1\.3/.test(d.getElementById("stageList").textContent) && /sam-3\.1/.test(d.getElementById("stageList").textContent));
    if (asked) { d.getElementById("answerText").value = "Busi basah, motor sempat kehujanan"; d.getElementById("answerBtn").click(); }
  }
  const ready = await until(() => shown("result"));
  check(`${lang}/${sample}: result shown`, ready, d.getElementById("formErr").textContent);
  if (ready) {
    check(`${lang}/${sample}: diagnosis text`, d.getElementById("dxObject").textContent.trim().length > 2);
    check(`${lang}/${sample}: steps rendered`, d.getElementById("stepText").textContent.trim().length > 5);
    // "Before you start": steps stay locked until every box is ticked, and the ticks survive a re-render
    const pre = d.getElementById("preflight"), card = d.getElementById("stepCard");
    const boxes = Array.from(d.querySelectorAll("#preList input"));
    check(`${lang}/${sample}: preflight shown with boxes`, pre && !pre.classList.contains("hidden") && boxes.length >= 1, boxes.length);
    check(`${lang}/${sample}: preflight text translated`, !/preTitle|preLocked|preReady|undefined/.test(pre.textContent), pre.textContent);
    check(`${lang}/${sample}: steps locked until ticked`, card.classList.contains("locked") && card.hasAttribute("inert"));
    boxes.slice(0, -1).forEach((b) => { b.checked = true; b.dispatchEvent(new w.Event("change")); });
    check(`${lang}/${sample}: still locked with one box open`, boxes.length === 1 || card.classList.contains("locked"));
    boxes.forEach((b) => { b.checked = true; b.dispatchEvent(new w.Event("change")); });
    check(`${lang}/${sample}: steps unlock when all ticked`, !card.classList.contains("locked") && !card.hasAttribute("inert") && /^✅/.test(d.getElementById("preState").textContent), d.getElementById("preState").textContent);
    const tm = d.getElementById("stepTimer");
    if (sample === "motor") {  // step 1 asks the owner to wait 10 minutes: countdown visible, starts and stops
      check(`${lang}/${sample}: wait timer shown`, tm && !tm.classList.contains("hidden") && /10/.test(d.getElementById("timerLabel").textContent), tm && tm.textContent);
      check(`${lang}/${sample}: timer clock 10:00`, d.getElementById("timerClock").textContent === "10:00", d.getElementById("timerClock").textContent);
      check(`${lang}/${sample}: timer label translated`, !/waitFor|timerStart/.test(tm.textContent), tm.textContent);
      d.getElementById("timerBtn").click(); await sleep(1400);
      check(`${lang}/${sample}: timer counts down`, d.getElementById("timerBtn").dataset.state === "running" && d.getElementById("timerClock").textContent !== "10:00", d.getElementById("timerClock").textContent);
      d.getElementById("timerBtn").click();
      check(`${lang}/${sample}: timer stops and resets`, d.getElementById("timerBtn").dataset.state === "idle" && d.getElementById("timerClock").textContent === "10:00");
    } else {
      check(`${lang}/${sample}: no timer when no wait`, !tm || tm.classList.contains("hidden"));
    }
    const ag = d.getElementById("agent");
    check(`${lang}/${sample}: agent log card visible`, ag && !ag.classList.contains("hidden"));
    const agRows = d.querySelectorAll("#agent .agList li").length;
    check(`${lang}/${sample}: agent log rows >= 5`, agRows >= 5, agRows);
    check(`${lang}/${sample}: agent log has no raw keys or placeholders`, !/ag_|lp_|\{\w+\}|undefined/.test(ag.textContent), ag.textContent.slice(0, 300));
    check(`${lang}/${sample}: agent loop strip lights up`, d.querySelectorAll("#agent .agLoop .lp.on").length >= 4);
    const sc = d.getElementById("sampleCheckBox");
    check(`${lang}/${sample}: sample check photos offered on a sample repair`, sc && !sc.classList.contains("hidden") && !/sampleTry|sampleBad/.test(sc.textContent));
    const hood = d.getElementById("hood");
    check(`${lang}/${sample}: hood panel visible`, hood && !hood.classList.contains("hidden"));
    const rows = d.querySelectorAll("#hoodList li").length;
    check(`${lang}/${sample}: hood rows >= 5`, rows >= 5, rows);
    check(`${lang}/${sample}: hood names SAM`, /sam-3\.1/i.test(d.getElementById("hoodList").textContent));
    check(`${lang}/${sample}: no raw i18n keys in hood`, !/hs_/.test(d.getElementById("hoodList").textContent));
    const saveChip = d.getElementById("gSave");
    check(`${lang}/${sample}: shop price chip shown with rupiah`, saveChip && !saveChip.classList.contains("hidden") && /Rp\d/.test(saveChip.textContent) && !/undefined|shopCost/.test(saveChip.textContent), saveChip && saveChip.textContent);
    check(`${lang}/${sample}: PDF + workshop links`, (d.getElementById("workshopBtn") || {}).href !== undefined);
    check(`${lang}/${sample}: erase button has a translated label`, !!d.getElementById("eraseBtn") && !/^erase$/.test(d.getElementById("eraseBtn").textContent) && d.getElementById("eraseBtn").textContent.length > 8);
    check(`${lang}/${sample}: focus moved to result heading`, d.activeElement && d.activeElement.tagName === "H2", d.activeElement && d.activeElement.tagName);
    check(`${lang}/${sample}: safety badge`, d.getElementById("safetyBadge").textContent.trim().length > 0);
    // next step button moves on
    const before = d.getElementById("stepNo").textContent;
    d.getElementById("nextBtn").click(); await sleep(100);
    check(`${lang}/${sample}: next step`, d.getElementById("stepNo").textContent !== before || (d.getElementById("stepTitle").textContent.startsWith("1 / 1")));
    // outcome: "it works now" closes the loop and the garage tallies the saving
    const oc = d.getElementById("outcome");
    check(`${lang}/${sample}: outcome card visible and translated`, oc && !oc.classList.contains("hidden") && !/outcomeAsk|fixedBtn/.test(oc.textContent), oc && oc.textContent);
    d.getElementById("fixedBtn").click();
    check(`${lang}/${sample}: outcome fixed confirmed`, await until(() => d.getElementById("outcomeMsg").textContent.length > 5 && d.getElementById("fixedBtn").getAttribute("aria-pressed") === "true", 5000), d.getElementById("outcomeMsg").textContent);
    check(`${lang}/${sample}: outcome message has no raw keys`, !/fixedThanks|undefined/.test(d.getElementById("outcomeMsg").textContent), d.getElementById("outcomeMsg").textContent);
    const gar = JSON.parse(w.localStorage.getItem("tc_garage") || "[]");
    check(`${lang}/${sample}: garage entry marked fixed`, gar.length > 0 && gar[0].outcome === "fixed", JSON.stringify(gar[0]));
    // garage persisted?
    check(`${lang}/${sample}: no uncaught page errors`, errors.length === 0, errors.join(" | "));
  }
  w.close();
}

// shrinkImage: runs in the page with a stubbed canvas (jsdom has none): resizes, falls back to the original on any failure.
async function shrinkChecks() {
  const dom = await JSDOM.fromURL(base + "/", { runScripts: "dangerously", resources: "usable", pretendToBeVisual: true,
    beforeParse(w) { w.fetch = nodeFetch; w.scrollTo = () => {}; } });
  const w = dom.window, d = w.document;
  await until(() => d.readyState === "complete");
  await sleep(300);
  check("shrink: function exists", typeof w.shrinkImage === "function");
  const big = (n, type = "image/jpeg", name = "IMG_1.jpeg") => new w.File([new Uint8Array(n)], name, { type });
  const small = big(1000);
  check("shrink: small file untouched", (await w.shrinkImage(small)) === small);
  const notImg = big(900000, "application/pdf", "a.pdf");
  check("shrink: non-image untouched", (await w.shrinkImage(notImg)) === notImg);
  const orig = d.createElement.bind(d);
  let drawn = null;
  w.createImageBitmap = async () => ({ width: 4000, height: 3000, close() {} });
  d.createElement = (tag) => tag === "canvas" ? {
    width: 0, height: 0,
    getContext: () => ({ drawImage(_b, _x, _y, cw, ch) { drawn = [cw, ch]; } }),
    toBlob(cb, type) { cb(new w.Blob([new Uint8Array(200000)], { type })); },
  } : orig(tag);
  const f1 = big(3000000);
  const r1 = await w.shrinkImage(f1);
  check("shrink: resized to max side 1600", drawn && drawn[0] === 1600 && drawn[1] === 1200, JSON.stringify(drawn));
  check("shrink: smaller jpeg returned", r1 !== f1 && r1.size === 200000 && r1.type === "image/jpeg" && r1.name === "IMG_1.jpg", `${r1.size} ${r1.type} ${r1.name}`);
  d.createElement = (tag) => tag === "canvas" ? { width: 0, height: 0, getContext: () => ({ drawImage() {} }), toBlob(cb) { cb(new w.Blob([new Uint8Array(5000000)])); } } : orig(tag);
  const f2 = big(3000000);
  check("shrink: keeps original when result is not smaller", (await w.shrinkImage(f2)) === f2);
  d.createElement = (tag) => tag === "canvas" ? { getContext: () => null } : orig(tag);
  check("shrink: no 2d context falls back", (await w.shrinkImage(f2)) === f2);
  w.createImageBitmap = async () => { throw new Error("cannot decode HEIC"); };
  check("shrink: decode error falls back", (await w.shrinkImage(f2)) === f2);
  w.close();
}


// Hostile model output: every free-text string in a real session gets an HTML payload appended; the page must never run it.
async function xssChecks() {
  const fd = new FormData(); fd.append("language", "en"); fd.append("text", ""); fd.append("category", "other"); fd.append("sample", "pump");
  const id = (await (await fetch(base + "/api/sessions", { method: "POST", body: fd })).json()).id;
  let sess = null;
  for (let i = 0; i < 100 && !(sess && ["ready"].includes(sess.status)); i++) { sess = await (await fetch(`${base}/api/sessions/${id}`)).json(); await sleep(150); }
  const PAY = '<img src=x onerror="window.__pwn=1"><script>window.__pwn=2</script>';
  const poison = (v, key = "") => {
    if (typeof v === "string") return (v.includes(" ") || (v.length > 14 && !/^(\/|https?:)/.test(v))) && !/^(id|status|level|kind|stage|file|image)/.test(key) ? v + PAY : v;
    if (Array.isArray(v)) return v.map((x) => poison(x, key));
    if (v && typeof v === "object") return Object.fromEntries(Object.entries(v).map(([k, x]) => [k, poison(x, k)]));
    return v;
  };
  const bad = poison(sess);
  const errors = [];
  const vc = new VirtualConsole(); vc.on("jsdomError", (e) => errors.push(String(e.message || e)));
  const dom = await JSDOM.fromURL(`${base}/guide/${id}`, { runScripts: "dangerously", resources: "usable", pretendToBeVisual: true, virtualConsole: vc,
    beforeParse(w) {
      w.scrollTo = () => {};
      w.fetch = (url, o) => (String(url).endsWith(`/api/sessions/${id}`) && !(o && o.method) ? Promise.resolve(new Response(JSON.stringify(bad), { headers: { "content-type": "application/json" } })) : nodeFetch(url, o));
    } });
  const w = dom.window, d = w.document;
  await until(() => d.readyState === "complete");
  const shown = await until(() => d.getElementById("stepText").textContent.length > 5, 8000);
  check("xss: guide page rendered hostile session", shown);
  check("xss: no injected script ran", w.__pwn === undefined, w.__pwn);
  check("xss: no injected img/script elements", d.querySelectorAll("img[src='x'], script:not([src])").length === 0, d.querySelectorAll("img[src='x']").length);
  check("xss: payload shown as text", d.body.textContent.includes("<img src=x"));
  w.close();
}

// Live guide + hands-free + hand-off on a ready pump repair (jsdom has no camera, no canvas, no speech).
async function featureChecks(lang) {
  const vc = new VirtualConsole(); vc.on("jsdomError", () => {});
  const dom = await JSDOM.fromURL(base + "/", { runScripts: "dangerously", resources: "usable", pretendToBeVisual: true, virtualConsole: vc,
    beforeParse(w) { w.fetch = nodeFetch; w.localStorage.setItem("tc_lang", lang); w.scrollTo = () => {}; } });
  const w = dom.window, d = w.document;
  await until(() => d.readyState === "complete");
  await sleep(300);
  d.querySelector('button.sample[data-sample="pump"]').click();
  const ready = await until(() => !d.getElementById("result").classList.contains("hidden"));
  check(`${lang}/live: result ready`, ready);
  if (!ready) { w.close(); return; }
  Array.from(d.querySelectorAll("#preList input")).forEach((b) => { b.checked = true; b.dispatchEvent(new w.Event("change")); });
  // live guide without a camera: falls back to the photo flow with a translated message
  d.getElementById("liveBtn").click();
  await until(() => d.getElementById("liveState").textContent.length > 10, 3000);
  const ls = d.getElementById("liveState").textContent;
  check(`${lang}/live: no-camera fallback message`, ls.length > 20 && !/liveNoCam|undefined/.test(ls) && !d.getElementById("live").classList.contains("hidden"), ls);
  w.applyTrack({ step: 1, component_id: "c1", name: "PLUG-X", label: 1, found: true, boxes: [{ x1: 0.4, y1: 0.2, x2: 0.6, y2: 0.3, confidence: 0.9 }], polygon: [[0.4, 0.2], [0.6, 0.2], [0.6, 0.3]], frames_used: 1, limit_reached: false });
  check(`${lang}/live: found text names the part`, /1\. PLUG-X/.test(d.getElementById("liveState").textContent), d.getElementById("liveState").textContent);
  w.applyTrack({ step: 1, component_id: "c1", name: "PLUG-X", found: false, boxes: [], polygon: [], frames_used: 3, limit_reached: true });
  check(`${lang}/live: limit message`, !/liveLimit/.test(d.getElementById("liveState").textContent) && d.getElementById("liveState").textContent.length > 20);
  d.getElementById("liveClose").click();
  check(`${lang}/live: close hides the live box`, d.getElementById("live").classList.contains("hidden"));
  // hands-free without SpeechRecognition: listening bar + push-to-talk fallback, translated
  const hf = d.getElementById("handsFree");
  hf.checked = true; hf.dispatchEvent(new w.Event("change"));
  const vs = () => d.getElementById("voiceState").textContent;
  check(`${lang}/voice: bar shown with push-to-talk fallback`, !d.getElementById("voiceBar").classList.contains("hidden") && !d.getElementById("pttBtn").classList.contains("hidden") && vs().length > 20 && !/vNoSR/.test(vs()), vs());
  check(`${lang}/voice: help line translated`, d.getElementById("voiceHelp").textContent.length > 20 && !/vHelp/.test(d.getElementById("voiceHelp").textContent));
  const word = { id: "lanjut", jv: "terus", en: "next" }[lang];
  const n0 = d.getElementById("stepNo").textContent;
  check(`${lang}/voice: parseCommand in page`, w.parseCommand(word, lang) === "next" && w.parseCommand({ id: "masih rusak", jv: "isih rusak", en: "still broken" }[lang], lang) === "broken");
  w.doCommand(w.parseCommand(word, lang), word);
  check(`${lang}/voice: next command moves a step`, d.getElementById("stepNo").textContent !== n0, d.getElementById("stepNo").textContent);
  w.doCommand("back", "back");
  check(`${lang}/voice: back command returns`, d.getElementById("stepNo").textContent === n0);
  w.doCommand(null, "blabla");
  check(`${lang}/voice: unknown text explained`, /blabla/.test(vs()) && !/vUnknown/.test(vs()), vs());
  w.doCommand("stop", "stop");
  check(`${lang}/voice: stop turns hands-free off`, !hf.checked && d.getElementById("voiceBar").classList.contains("hidden"));
  // with a (fake) SpeechRecognition: continuous listening in the right language, red dot, results become commands
  let fake = null;
  w.webkitSpeechRecognition = class { constructor() { fake = this; this.started = 0; } start() { this.started++; } stop() {} abort() {} };
  hf.checked = true; hf.dispatchEvent(new w.Event("change"));
  check(`${lang}/voice: recognition started in ${lang}`, fake && fake.started === 1 && fake.continuous === true && fake.lang === { id: "id-ID", jv: "jv-ID", en: "en-US" }[lang], fake && fake.lang);
  check(`${lang}/voice: listening dot on, no push-to-talk`, d.getElementById("voiceDot").classList.contains("on") && d.getElementById("pttBtn").classList.contains("hidden"));
  await sleep(1700);  // past the guide's own read-aloud window
  const n1 = d.getElementById("stepNo").textContent;
  fake.onresult({ results: [[{ transcript: word }]] });
  check(`${lang}/voice: spoken word moves a step`, d.getElementById("stepNo").textContent !== n1 && /«/.test(vs()), vs());
  fake.onend();
  await sleep(400);
  check(`${lang}/voice: listening restarts after the browser stops it`, fake.started === 2, fake.started);
  w.doCommand("stop", "");
  // bengkel hand-off on request
  d.getElementById("mechBtn").click();
  const ho = d.getElementById("handoff");
  check(`${lang}/handoff: card shown on request`, await until(() => !ho.classList.contains("hidden"), 5000));
  check(`${lang}/handoff: WhatsApp + Maps + PDF links`, !!ho.querySelector('a[href^="https://wa.me/?text="]') && !!ho.querySelector('a[href*="google.com/maps/search"]') && !!ho.querySelector('a[href$="/report.pdf"]'), ho.innerHTML.slice(0, 200));
  check(`${lang}/handoff: translated`, !/hoWa|hoMaps|hoSub|undefined/.test(ho.textContent), ho.textContent);
  w.close();
}

async function offlineChecks() {
  for (const lang of ["id", "jv", "en"]) {
    const vc = new VirtualConsole(); vc.on("jsdomError", () => {});
    const dom = await JSDOM.fromURL(base + "/", {
      runScripts: "dangerously", resources: "usable", pretendToBeVisual: true, virtualConsole: vc,
      beforeParse(w) {
        w.fetch = (url, o) => (String(url).includes("/api/health") ? nodeFetch(url, o) : Promise.reject(new TypeError("Failed to fetch")));
        w.localStorage.setItem("tc_lang", lang); w.scrollTo = () => {};
      },
    });
    const w = dom.window, d = w.document;
    await until(() => d.readyState === "complete");
    await sleep(300);
    const bar = d.getElementById("offlineBar");
    check(`${lang}: offline bar exists and starts hidden`, bar && bar.classList.contains("hidden"));
    Object.defineProperty(w.navigator, "onLine", { value: false, configurable: true });
    w.dispatchEvent(new w.Event("offline"));
    check(`${lang}: offline bar shows when phone goes offline`, !bar.classList.contains("hidden") && bar.textContent.length > 20, bar.textContent);
    Object.defineProperty(w.navigator, "onLine", { value: true, configurable: true });
    w.dispatchEvent(new w.Event("online"));
    check(`${lang}: offline bar hides again`, bar.classList.contains("hidden"));
    d.querySelector('button.sample[data-sample="faucet"]').click();
    await until(() => d.getElementById("formErr").textContent.length > 0, 4000);
    const msg = d.getElementById("formErr").textContent;
    check(`${lang}: network failure gives friendly text`, msg.length > 20 && !/failed to fetch/i.test(msg), msg);
    check(`${lang}: start button usable again`, d.getElementById("goBtn").disabled === false);
    w.close();
  }
}

try {
  await offlineChecks();
  await shrinkChecks();
  await xssChecks();
  for (const l of ["id", "jv", "en"]) await featureChecks(l);
  await run("id", "faucet");
  await run("jv", "pump");
  await run("en", "motor");
  await run("en", "rice");
  await run("jv", "tire");
} catch (e) { check("script error", false, e.stack || e); }
const ok = checks.every((c) => c.ok);
console.log(JSON.stringify({ ok, checks }));
process.exit(ok ? 0 : 1);
