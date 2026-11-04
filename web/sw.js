// Tukang Copilot service worker: caches the app shell so the app opens fast and installs as a PWA, plus the RECORDED
// 1-tap demo (/static/replay/*: one saved demo-mode run, labelled on screen) so the demo plays even when the server
// sleeps (free Render tier, ~50 s to wake) or the phone is offline.
// API calls (/api/*), session files (/files/*) and guides are never cached: diagnosis needs the network,
// and user photos must not linger on the device (24 h retention lives on the server).
const CACHE = "tukang-shell-v18";  // bump on every release that changes the shell, so phones fetch the new app
const SHELL = ["/", "/static/style.css", "/static/app.js", "/static/replay.js", "/manifest.webmanifest",
               "/static/icons/icon-192.png", "/static/icons/icon-512.png", "/static/demo-thumb.jpg", "/static/replay/demo.json",
               "/static/fonts/barlow-400.woff2", "/static/fonts/barlow-600.woff2", "/static/fonts/barlow-condensed-700.woff2",
               "/static/fonts/barlow-condensed-800.woff2"];
const SHELL_WAIT_MS = 3500;  // a sleeping server: show the cached shell after this, keep refreshing it in the background

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then(async (c) => {
    await c.addAll(SHELL);
    try {  // the recorded demo's photos (best effort: a missing one never blocks the install)
      const d = await (await c.match("/static/replay/demo.json")).json();
      await Promise.all((d.assets || []).map((u) => c.add(u).catch(() => null)));
    } catch (_) { /* no recording shipped */ }
  }).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  if (url.pathname.startsWith("/static/replay/") && !url.pathname.endsWith(".json")) {
    // recorded photos never change between versions of the recording: cache first
    e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
    return;
  }
  if (!SHELL.includes(url.pathname)) return;  // network only for everything else
  // Network first (always fresh when online); the cached copy after SHELL_WAIT_MS or when offline.
  const net = fetch(e.request).then((r) => {
    if (r.ok) { const copy = r.clone(); caches.open(CACHE).then((c) => c.put(e.request, copy)); }
    return r;
  });
  const cached = () => caches.match(e.request, { ignoreSearch: true }).then((r) => r || caches.match("/"));
  e.respondWith(new Promise((resolve) => {
    let done = false;
    const finish = (r) => { if (!done && r) { done = true; resolve(r); } };
    const timer = setTimeout(() => cached().then(finish), SHELL_WAIT_MS);
    net.then((r) => { clearTimeout(timer); finish(r); })
      .catch(() => { clearTimeout(timer); cached().then((r) => (r ? finish(r) : finish(Response.error()))); });
  }));
});
