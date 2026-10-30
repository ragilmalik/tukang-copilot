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
  d.querySelector(`button.sample[data-sample="${sample}"]`).click();
  const shown = (id) => !d.getElementById(id).classList.contains("hidden");
  if (sample === "rice") {  // red safety stop: no repair steps, a stop box with a service-centre card
    const stopped = await until(() => shown("stopBox"));
    check(`${lang}/${sample}: red stop box shown`, stopped);
    check(`${lang}/${sample}: no result page on red stop`, !shown("result"));
    check(`${lang}/${sample}: stop box has text`, d.getElementById("stopBox").textContent.trim().length > 40, d.getElementById("stopBox").textContent);
    w.close(); return;
  }
  if (sample === "motor") {  // the agent asks one follow-up question first
    const asked = await until(() => shown("question"));
    check(`${lang}/${sample}: follow-up question shown`, asked && d.getElementById("questionText").textContent.length > 3);
    if (asked) { d.getElementById("answerText").value = "Busi basah, motor sempat kehujanan"; d.getElementById("answerBtn").click(); }
  }
  const ready = await until(() => shown("result"));
  check(`${lang}/${sample}: result shown`, ready, d.getElementById("formErr").textContent);
  if (ready) {
    check(`${lang}/${sample}: diagnosis text`, d.getElementById("dxObject").textContent.trim().length > 2);
    check(`${lang}/${sample}: steps rendered`, d.getElementById("stepText").textContent.trim().length > 5);
    const hood = d.getElementById("hood");
    check(`${lang}/${sample}: hood panel visible`, hood && !hood.classList.contains("hidden"));
    const rows = d.querySelectorAll("#hoodList li").length;
    check(`${lang}/${sample}: hood rows >= 5`, rows >= 5, rows);
    check(`${lang}/${sample}: hood names SAM`, /sam-3\.1/i.test(d.getElementById("hoodList").textContent));
    check(`${lang}/${sample}: no raw i18n keys in hood`, !/hs_/.test(d.getElementById("hoodList").textContent));
    check(`${lang}/${sample}: PDF + workshop links`, (d.getElementById("workshopBtn") || {}).href !== undefined);
    check(`${lang}/${sample}: safety badge`, d.getElementById("safetyBadge").textContent.trim().length > 0);
    // next step button moves on
    const before = d.getElementById("stepNo").textContent;
    d.getElementById("nextBtn").click(); await sleep(100);
    check(`${lang}/${sample}: next step`, d.getElementById("stepNo").textContent !== before || (d.getElementById("stepTitle").textContent.startsWith("1 / 1")));
    // garage persisted?
    check(`${lang}/${sample}: no uncaught page errors`, errors.length === 0, errors.join(" | "));
  }
  w.close();
}

try {
  await run("id", "faucet");
  await run("jv", "pump");
  await run("en", "motor");
  await run("en", "rice");
  await run("jv", "tire");
} catch (e) { check("script error", false, e.stack || e); }
const ok = checks.every((c) => c.ok);
console.log(JSON.stringify({ ok, checks }));
process.exit(ok ? 0 : 1);
