"""Test helper: the owner token of a repair (1.27.0, backlog Q14). The web API returns it once at creation; tests that
act as the owner read it back from the stored session and send it the way the app does (X-Owner-Token header)."""
from api.pipeline import engine


def owner(sid: str) -> dict[str, str]:
    return {"X-Owner-Token": str(engine.load(sid).get("owner_token") or "")}
