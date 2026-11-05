"""Things the first real Meta runs (2026-11-05) taught me, pinned down so they stay fixed.

1. A plain structured-output call that thinks for more than about 20 s came back as 504 "upstream request deadline
   exceeded". chat_json now streams (stream=true) and reads the content deltas plus the usage chunk.
2. The constrained decoder skipped every field the schema did not list as required (no parts for SAM, no follow-up
   question, no diagram flag). json_schema() now lists every property as required, at every depth.
"""
from __future__ import annotations

import json
from typing import Any, Iterator

import pytest

from api import meta_client
from api.schemas import Diagnosis, DiagramReview, ObjectReport, RepairPlan, StepCheck, json_schema
from api.settings import settings


def _objects(node: Any) -> Iterator[dict[str, Any]]:
    if isinstance(node, dict):
        if node.get("type") == "object" and "properties" in node:
            yield node
        for v in node.values():
            yield from _objects(v)
    elif isinstance(node, list):
        for v in node:
            yield from _objects(v)


@pytest.mark.parametrize("cls", [ObjectReport, Diagnosis, RepairPlan, StepCheck, DiagramReview])
def test_every_property_is_required_at_every_depth(cls: Any) -> None:
    objs = list(_objects(json_schema(cls)))
    assert objs
    for o in objs:
        assert sorted(o["required"]) == sorted(o["properties"]), o.get("title")


def test_object_report_schema_requires_components_and_boxes() -> None:
    s = json_schema(ObjectReport)
    assert "components" in s["required"]
    comp = s["properties"]["components"]["items"]
    assert "prompt_box" in comp["required"] and "sam_phrase" in comp["required"]


class _Resp:
    def __init__(self, status: int, lines: list[str], ctype: str = "text/event-stream", body: str = "") -> None:
        self.status_code, self._lines, self.headers, self.text = status, lines, {"content-type": ctype}, body

    def __enter__(self) -> "_Resp":
        return self

    def __exit__(self, *a: Any) -> None:
        return None

    def read(self) -> bytes:
        return self.text.encode()

    def json(self) -> Any:
        return json.loads(self.text)

    def iter_lines(self) -> Iterator[str]:
        yield from self._lines


def _sse(content: str, usage: dict[str, int]) -> list[str]:
    mid = len(content) // 2
    return [
        "data: " + json.dumps({"choices": [{"delta": {"content": content[:mid]}}]}), "",
        "data: " + json.dumps({"choices": [{"delta": {"content": content[mid:]}}]}), "",
        "data: " + json.dumps({"choices": [{"delta": {}, "finish_reason": "stop"}], "usage": usage}), "",
        "data: [DONE]",
    ]


@pytest.fixture
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    waits: list[float] = []
    monkeypatch.setattr(meta_client.time, "sleep", waits.append)
    monkeypatch.setattr(settings, "meta_api_key", "test-key-not-real")
    return waits


def test_stream_chat_joins_deltas_and_keeps_usage(monkeypatch: pytest.MonkeyPatch, no_sleep: list[float]) -> None:
    sent: list[dict[str, Any]] = []

    def fake(method: str, url: str, **kw: Any) -> _Resp:
        sent.append(kw["json"])
        return _Resp(200, _sse('{"passed": true, "observation": "ok", "correction": ""}', {"prompt_tokens": 10, "completion_tokens": 5}))

    monkeypatch.setattr(meta_client.httpx, "stream", fake)
    out = meta_client.chat_json([{"role": "user", "content": "x"}], json_schema(StepCheck), "step_check")
    assert out == {"passed": True, "observation": "ok", "correction": ""}
    assert sent[0]["stream"] is True and sent[0]["stream_options"] == {"include_usage": True}


def test_stream_chat_retries_a_504_then_succeeds(monkeypatch: pytest.MonkeyPatch, no_sleep: list[float]) -> None:
    answers = [_Resp(504, [], "application/json", "upstream request deadline exceeded"),
               _Resp(200, _sse('{"ok": true, "problems": [], "fix_prompt": ""}', {"prompt_tokens": 1, "completion_tokens": 1}))]
    monkeypatch.setattr(meta_client.httpx, "stream", lambda *a, **k: answers.pop(0))
    assert meta_client.chat_json([], json_schema(DiagramReview), "diagram_review")["ok"] is True
    assert no_sleep == [2]


def test_stream_chat_gives_up_after_retries(monkeypatch: pytest.MonkeyPatch, no_sleep: list[float]) -> None:
    monkeypatch.setattr(meta_client.httpx, "stream", lambda *a, **k: _Resp(504, [], "application/json", "deadline"))
    with pytest.raises(meta_client.MetaAPIError, match="504"):
        meta_client.chat_json([], json_schema(DiagramReview), "diagram_review")
    assert no_sleep == [2, 4, 8]


def test_stream_chat_does_not_retry_a_400(monkeypatch: pytest.MonkeyPatch, no_sleep: list[float]) -> None:
    calls: list[int] = []

    def fake(*a: Any, **k: Any) -> _Resp:
        calls.append(1)
        return _Resp(400, [], "application/json", '{"error": "bad schema"}')

    monkeypatch.setattr(meta_client.httpx, "stream", fake)
    with pytest.raises(meta_client.MetaAPIError, match="400"):
        meta_client.chat_json([], json_schema(DiagramReview), "diagram_review")
    assert calls == [1] and no_sleep == []


def test_stream_error_event_is_an_error(monkeypatch: pytest.MonkeyPatch, no_sleep: list[float]) -> None:
    lines = ["data: " + json.dumps({"error": {"message": "overloaded"}})]
    monkeypatch.setattr(meta_client.httpx, "stream", lambda *a, **k: _Resp(200, lines))
    with pytest.raises(meta_client.MetaAPIError, match="overloaded"):
        meta_client.chat_json([], json_schema(DiagramReview), "diagram_review")


def test_plain_json_answer_is_still_read(monkeypatch: pytest.MonkeyPatch, no_sleep: list[float]) -> None:
    body = json.dumps({"choices": [{"message": {"content": '{"ok": false, "problems": ["x"], "fix_prompt": "y"}'}}],
                       "usage": {"prompt_tokens": 1, "completion_tokens": 1}})
    monkeypatch.setattr(meta_client.httpx, "stream", lambda *a, **k: _Resp(200, [], "application/json", body))
    assert meta_client.chat_json([], json_schema(DiagramReview), "diagram_review")["problems"] == ["x"]
