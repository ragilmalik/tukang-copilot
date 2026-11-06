"""Test helper: the owner token of a repair. The web API returns it once at creation; tests that
act as the owner read it back from the stored session and send it the way the app does (X-Owner-Token header).

OwnerClient is a TestClient that acts as the owner's phone on the routes that change a repair or spend on it
(answer, retry, step check, live guide, voice command, still broken), the way web/app.js sends ownerHeaders().
It never adds the token to outcome or erase, so the tests that prove a shared-link viewer gets 403 there keep
sending (or leaving out) the header themselves. Tests that prove the 403 on the other routes use a plain
TestClient."""
import re
from typing import Any

from fastapi.testclient import TestClient

from api.pipeline import engine

OWNED = re.compile(r"^(?:https?://[^/]+)?/api/sessions/([A-Za-z0-9]+)/(?:answer|retry|replan|command|steps/\d+/(?:check|track))$")


def owner(sid: str) -> dict[str, str]:
    return {"X-Owner-Token": str(engine.load(sid).get("owner_token") or "")}


class OwnerClient(TestClient):
    def request(self, method: str, url: Any, *args: Any, **kw: Any) -> Any:
        m = OWNED.match(str(url))
        if m and method.upper() == "POST":
            hdrs = dict(kw.get("headers") or {})
            if not any(k.lower() == "x-owner-token" for k in hdrs):
                try:
                    tok = engine.load(m.group(1)).get("owner_token")
                except (FileNotFoundError, ValueError):
                    tok = None
                if tok:
                    hdrs["X-Owner-Token"] = str(tok)
                    kw["headers"] = hdrs
        return super().request(method, url, *args, **kw)
