// Tukang Copilot service worker: caches ONLY the app shell so the app opens fast and installs as a PWA.
// API calls (/api/*), session files (/files/*) and guides are never cached: diagnosis needs the network,
// and user photos must not linger on the device (24 h retention lives on the server).
const CACHE = "tukang-shell-v1";
const SHELL = ["/", "/static/style.css", "/static/app.js", "/manifest.webmanifest",
               "/static/icons/icon-192.png", "/static/icons/icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  if (!SHELL.includes(url.pathname)) return;  // network only for everything else
  // Network first (always fresh when online), cache as offline fallback.
  e.respondWith(fetch(e.request)
    .then((r) => { const copy = r.clone(); caches.open(CACHE).then((c) => c.put(e.request, copy)); return r; })
    .catch(() => caches.match(e.request).then((r) => r || caches.match("/"))));
});
