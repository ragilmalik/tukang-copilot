"""The service worker's fetch handler, run in Node with a fake cache and network (1.33.1 audit).

Two faults it had up to 1.33.0:
- a server that answered with an error page (a 502 or 503 while a free host wakes up or redeploys) was shown as
  is, although the cached app was right there; only a network error fell back to the cache;
- when a script or style sheet was not in the cache and the network was down, the worker answered with the
  cached home page instead, so the browser got HTML where it asked for JavaScript or CSS.
Now a 5xx answer falls back to the cache like a network error, and the home page only stands in for page loads."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

SW = Path(__file__).resolve().parents[2] / "web" / "sw.js"
NODE = shutil.which("node")

HARNESS = r"""
const fs = require("fs"), vm = require("vm");
const [swPath, casesJson] = process.argv.slice(1);
const cases = JSON.parse(casesJson);
(async () => {
  const out = [];
  for (const c of cases) {
    const handlers = {};
    const store = new Map(Object.entries(c.cached || {}));  // pathname -> body
    const key = (r) => new URL(typeof r === "string" ? r : r.url, "https://app.test").pathname;
    const caches = {
      open: async () => ({ put: async () => {}, addAll: async () => {}, add: async () => {}, match: async () => undefined }),
      keys: async () => [], delete: async () => true,
      match: async (r) => (store.has(key(r)) ? new Response(store.get(key(r)), { status: 200, headers: { "x-from": "cache" } }) : undefined),
    };
    const fetch = async () => {
      if (c.net === "down") throw new TypeError("Failed to fetch");
      return new Response("net " + c.net, { status: c.net, headers: { "x-from": "net" } });
    };
    const self = { addEventListener: (t, f) => { handlers[t] = f; }, skipWaiting: () => {}, clients: { claim: () => {} } };
    const ctx = { self, caches, fetch, Response, URL, Promise, setTimeout, clearTimeout, location: { origin: "https://app.test" }, console };
    vm.runInNewContext(fs.readFileSync(swPath, "utf8"), ctx);
    let got = null;
    const ev = { request: { url: "https://app.test" + c.path, method: "GET", mode: c.mode || "cors" }, respondWith: (p) => { got = p; } };
    handlers.fetch(ev);
    if (!got) { out.push({ path: c.path, handled: false }); continue; }
    const r = await got;
    out.push({ path: c.path, type: r.type, status: r.status, from: r.headers.get("x-from"), body: r.type === "error" ? "" : await r.text() });
  }
  console.log(JSON.stringify(out));
})();
"""


def _run(cases: list[dict[str, object]]) -> list[dict[str, object]]:
    assert NODE, "node is needed for the service worker test (CI installs it for jsdom)"
    p = subprocess.run([NODE, "-e", HARNESS, str(SW), json.dumps(cases)], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    return list(json.loads(p.stdout.strip().splitlines()[-1]))


SHELL = {"/": "<html>shell</html>", "/static/app.js": "app()"}


def test_a_5xx_from_a_waking_server_shows_the_cached_app() -> None:
    got = _run([{"path": "/", "mode": "navigate", "net": 503, "cached": SHELL},
                {"path": "/static/app.js", "net": 502, "cached": SHELL}])
    assert [(g["status"], g["from"]) for g in got] == [(200, "cache"), (200, "cache")]
    assert got[1]["body"] == "app()"


def test_a_5xx_with_nothing_cached_is_passed_through() -> None:
    got = _run([{"path": "/", "mode": "navigate", "net": 503, "cached": {}}])
    assert (got[0]["status"], got[0]["from"]) == (503, "net")


def test_a_missing_script_is_never_answered_with_the_home_page() -> None:
    got = _run([{"path": "/static/style.css", "net": "down", "cached": SHELL},
                {"path": "/static/replay.js", "net": 503, "cached": SHELL}])
    assert got[0]["type"] == "error"  # a network error to the page, not HTML labelled as CSS
    assert (got[1]["status"], got[1]["from"]) == (503, "net")


def test_page_loads_still_fall_back_to_the_cached_home_page_offline() -> None:
    got = _run([{"path": "/?lang=jv", "mode": "navigate", "net": "down", "cached": SHELL}])
    assert (got[0]["status"], got[0]["body"]) == (200, "<html>shell</html>")


@pytest.mark.parametrize("status", [200, 404])
def test_a_working_server_answers_as_before(status: int) -> None:
    got = _run([{"path": "/static/app.js", "net": status, "cached": SHELL}])
    assert (got[0]["status"], got[0]["from"]) == (status, "net")


def test_api_and_files_are_never_handled() -> None:
    got = _run([{"path": "/api/sessions/abc", "net": 200, "cached": SHELL}, {"path": "/files/abc/photo1.jpg", "net": 200, "cached": SHELL}])
    assert [g["handled"] for g in got] == [False, False]
