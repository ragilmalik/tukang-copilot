/* Tukang Copilot: RECORDED demo replay (v1.24).
   A free Render server sleeps and needs ~50 s to wake, and a judge on bad Wi-Fi may have no server at all. When the
   server does not answer in time (or the page is opened with ?replay=1), the 1-tap demo plays a RECORDED demo-mode run
   from /static/replay/demo.json instead: the same screens, agent log, SAM-marked photo, step checks and re-plan, with a
   "Recorded demo" badge on screen. No server, no model calls, nothing new is computed. Your own photos still need the
   live server, and the replay says so. Regenerate the recording with: python scripts/record_replay.py
   This file only answers /api/* calls while the replay is switched on; otherwise it does nothing. */
(function () {
  "use strict";
  const BASE = "/static/replay/";
  const realFetch = window.fetch ? window.fetch.bind(window) : null;
  const RealES = window.EventSource;
  const R = { on: false, data: null, L: null, lang: "id", cur: null, phase: "", tick: 900 };
  const tr = (k, fb) => (typeof window.tcT === "function" ? window.tcT(k) : fb || k);
  const clone = (o) => JSON.parse(JSON.stringify(o));
  const json = (obj, status) => new Response(JSON.stringify(obj), { status: status || 200, headers: { "Content-Type": "application/json" } });
  const nope = (key) => json({ detail: tr(key), replay: true }, 503);

  function forced() {
    try { return new URLSearchParams(location.search).get("replay") === "1"; } catch (_) { return false; }
  }

  async function load() {
    if (R.data) return R.data;
    const r = await realFetch(BASE + "demo.json");
    if (!r.ok) throw new Error("no recording");
    const d = await r.json();
    if (!d || d.kind !== "recorded-demo" || !d.langs) throw new Error("bad recording");
    R.data = d;
    return d;
  }

  // Apply one recorded action ("delta": set / merge / append) to the current session, so actions can be replayed in
  // any order: a second photo on the same step adds a try instead of replacing the first one.
  function apply(delta, opts) {
    const s = R.cur;
    Object.entries(delta.set || {}).forEach(([k, v]) => { s[k] = clone(v); });
    Object.entries(delta.append || {}).forEach(([k, v]) => { s[k] = (Array.isArray(s[k]) ? s[k] : []).concat(clone(v)); });
    Object.entries(delta.merge || {}).forEach(([k, v]) => {
      const box = s[k] && typeof s[k] === "object" ? s[k] : (s[k] = {});
      Object.entries(v).forEach(([kk, rec]) => {
        const old = box[kk];
        if (k === "checks" && old && rec && typeof rec === "object") {
          box[kk] = { ...clone(rec), tries: (old.tries || []).concat(clone(rec.tries || [])), fails: (old.fails || 0) + (rec.passed ? 0 : 1) };
        } else box[kk] = clone(rec);
      });
    });
    if (opts && opts.checksUsed) s.checks_used = (R.usedChecks = (R.usedChecks || 0) + 1);
  }

  async function formOf(init) {
    const b = init && init.body;
    return b && typeof b.get === "function" ? b : null;
  }

  async function handle(url, init) {
    const method = ((init && init.method) || "GET").toUpperCase();
    const L = R.L, path = url.pathname;
    if (path === "/api/health" || path === "/health") {
      return json({ ok: true, mode: "replay", version: R.data.recorded_with, models: R.data.models, open_weights: false, demo_fallback: false, meta_api_key: false });
    }
    let m;
    if (path === "/api/sessions" && method === "POST") {
      const fd = await formOf(init);
      if (!fd || fd.get("sample") !== R.data.sample) return nope("rpOnlyDemo");
      R.cur = null; R.phase = "ask"; R.usedChecks = 0;
      return json({ id: L.sid });
    }
    if ((m = path.match(/^\/api\/demo\/check-photo\/(ok|dark)$/))) return realFetch(BASE + `check_${m[1]}.jpg`);
    if (!(m = path.match(/^\/api\/sessions\/([^/]+)(\/.*)?$/))) return nope("rpNoLive");
    const sid = decodeURIComponent(m[1]), rest = m[2] || "";
    if (sid !== L.sid) return json({ detail: "Session not found" }, 404);
    if (rest === "" && method === "DELETE") { R.cur = null; return json({ id: sid, deleted: true }); }
    if (rest === "" && method === "GET") return R.cur ? json(R.cur) : json({ detail: "Session not found" }, 404);
    if (rest === "/answer" && method === "POST") { R.phase = "ready"; return json({ ok: true }); }
    if (rest === "/retry" && method === "POST") return json({ ok: true });
    if (rest === "/handoff") return json(L.handoff);
    if (rest === "/card.png") return realFetch(BASE + `card-${R.lang}.png`);
    if ((m = rest.match(/^\/steps\/(\d+)\/check$/)) && method === "POST") {
      const fd = await formOf(init), f = fd && fd.get("photo");
      const kind = f && f.name && (f.name.match(/^sample-(ok|dark)\./) || [])[1];
      if (!kind) return nope("rpOwnPhoto");   // a recording cannot look at a new photo: never fake a pass
      const rec = ((L.checks[String(R.cur.cause_index || 0)] || {})[m[1]] || {})[kind];
      if (!rec) return nope("rpNoLive");
      apply(rec.delta, { checksUsed: true });
      const c = (R.cur.checks || {})[m[1]] || {};
      const lim = R.data.max_check_fails || 2;
      return json({ ...clone(rec.response), fails: c.fails || 0, escalate: (c.fails || 0) >= lim }, rec.status);
    }
    if (rest === "/replan" && method === "POST") {
      if ((R.cur.cause_index || 0) > 0 || !L.replan) return nope("rpNoMore");
      apply(L.replan);
      return json(R.cur);
    }
    if (rest === "/outcome" && method === "POST") {
      const fd = await formOf(init), res = fd && String(fd.get("result") || "");
      if (!L.outcome[res]) return json({ detail: "bad result" }, 422);
      apply(L.outcome[res]);
      return json(R.cur);
    }
    return nope("rpNoLive");  // live camera guide, voice commands: need the real server
  }

  function shimFetch(input, init) {
    let url;
    try { url = new URL(typeof input === "string" ? input : input.url, location.href); } catch (_) { return realFetch(input, init); }
    if (!R.on || url.origin !== location.origin || !/^\/(api\/|health$)/.test(url.pathname)) return realFetch(input, init);
    return handle(url, init).catch(() => nope("rpNoLive"));
  }

  // EventSource stand-in: plays the recorded progress snapshots one by one (about one stage per tick).
  function ReplayES(url) {
    this.readyState = 0; this.url = String(url); this.onmessage = null; this.onerror = null; this._t = [];
    const m = this.url.match(/\/api\/sessions\/([^/]+)\/events/);
    const part = R.phase === "ready" ? R.L.ready : R.L.ask;
    if (!m || decodeURIComponent(m[1]) !== R.L.sid) { this._t.push(setTimeout(() => this.onerror && this.onerror(new Event("error")), 0)); return; }
    this.readyState = 1;
    part.snaps.forEach((snap, i) => this._t.push(setTimeout(() => {
      if (this.readyState === 2) return;
      if (i === part.snaps.length - 1) R.cur = clone(part.session);  // the full session is there once the stream settles
      if (this.onmessage) this.onmessage({ data: JSON.stringify(snap) });
    }, R.tick * (i + 1))));
  }
  ReplayES.prototype.close = function () { this.readyState = 2; this._t.forEach(clearTimeout); };
  ReplayES.prototype.addEventListener = function () {};

  function ES(url, cfg) {
    if (R.on && /\/api\/sessions\/[^/]+\/events/.test(String(url))) return new ReplayES(url);
    return new RealES(url, cfg);
  }

  async function start(lang) {
    if (R.on) return true;
    if (!realFetch) return false;
    try { await load(); } catch (_) { return false; }
    R.lang = R.data.langs[lang] ? lang : "id";
    R.L = R.data.langs[R.lang];
    R.on = true;
    window.fetch = shimFetch;
    if (RealES) window.EventSource = ES;
    else window.EventSource = ReplayES;
    if (document.body) document.body.classList.add("replay");
    return true;
  }

  // Links (PDF report) are not fetch calls: app.js asks for the recorded copy while the replay is on.
  function href(p) {
    if (!R.on) return p;
    if (/\/report\.pdf$/.test(p)) return BASE + `report-${R.lang}.pdf`;
    if (/\/workshop\.pdf$/.test(p)) return BASE + `report-${R.lang}.pdf`;
    return p;
  }

  window.TCReplay = { start, forced, href, active: () => R.on, lang: () => R.lang, _state: R };
})();
