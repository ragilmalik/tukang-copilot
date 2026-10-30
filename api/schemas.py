"""Data shapes. Pydantic models validate everything Muse Spark returns; their JSON Schemas are sent as
`response_format` (structured output, https://dev.meta.ai/docs/structured-output)."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

Lang = Literal["id", "jv", "en"]
Category = Literal["motor", "pump", "appliance", "plumbing", "other"]
SafetyLevel = Literal["green", "amber", "red"]


class Component(BaseModel):
    """A visible part of the object. `sam_phrase` is the short English noun phrase sent to SAM 3.1."""
    id: str
    name: str
    sam_phrase: str
    condition: str = ""
    # [x1, y1, x2, y2] as FRACTIONS (0..1) of the first photo's width/height; null if unsure.
    # A list (not a tuple) so the JSON Schema has no `prefixItems`.
    prompt_box: list[float] | None = Field(default=None, min_length=4, max_length=4)

    @field_validator("prompt_box")
    @classmethod
    def _box(cls, v: list[float] | None) -> list[float] | None:
        if v is None:
            return None
        x1, y1, x2, y2 = (max(0.0, min(1.0, float(c))) for c in v)
        x1, x2, y1, y2 = min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)
        return None if (x2 - x1 < 0.01 or y2 - y1 < 0.01) else [x1, y1, x2, y2]


class ObjectReport(BaseModel):
    """Stage 2 (Look): what the camera sees."""
    object: str
    brand_model_guess: str = ""
    category: Category
    components: list[Component] = Field(default_factory=list, max_length=5)
    visible_issues: list[str] = Field(default_factory=list)


class Cause(BaseModel):
    title: str
    confidence: int = Field(ge=0, le=100)
    evidence: list[str] = Field(default_factory=list)
    component_ids: list[str] = Field(default_factory=list)


class Item(BaseModel):
    name: str
    est_price_idr: int = 0


class Diagnosis(BaseModel):
    """Stage 4 (Diagnose)."""
    problem_summary: str
    causes: list[Cause] = Field(min_length=1, max_length=4)
    safety_level: SafetyLevel
    safety_reason: str = ""
    tools: list[Item] = Field(default_factory=list)
    parts: list[Item] = Field(default_factory=list)
    difficulty: int = Field(ge=1, le=5)
    minutes_estimate: int = Field(ge=1, le=600)
    follow_up_question: str = ""   # asked when the top cause is below 60% confidence

    @field_validator("causes")
    @classmethod
    def _sorted(cls, v: list[Cause]) -> list[Cause]:
        return sorted(v, key=lambda c: -c.confidence)

    @property
    def cost_estimate_idr(self) -> int:
        return sum(i.est_price_idr for i in self.parts)


class Step(BaseModel):
    n: int
    component_id: str = ""
    instruction: str
    why: str = ""
    expected_state: str           # what the camera should see when this step is done
    warnings: list[str] = Field(default_factory=list)
    voice_text: str = ""
    needs_diagram: bool = False   # True: the photo can't show it, so Muse Image draws a diagram
    diagram_prompt: str = ""      # English brief for Muse Image


class RepairPlan(BaseModel):
    """Stage 5 (Plan)."""
    cause_title: str
    steps: list[Step] = Field(min_length=1, max_length=10)
    done_check: str = ""
    when_to_call_pro: str = ""

    @field_validator("steps")
    @classmethod
    def _renumber(cls, v: list[Step]) -> list[Step]:
        for i, s in enumerate(v, 1):
            s.n = i
        return v


class StepCheck(BaseModel):
    """Stage 8 (Verify): did the user's new photo show the expected state?"""
    passed: bool
    observation: str
    correction: str = ""


class DiagramReview(BaseModel):
    ok: bool
    problems: list[str] = Field(default_factory=list)
    fix_prompt: str = ""


def json_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Pydantic -> plain JSON Schema with $defs inlined, so strict providers accept it."""
    schema = model.model_json_schema()
    defs = schema.pop("$defs", {})

    def inline(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                return inline(dict(defs[node["$ref"].split("/")[-1]]))
            return {k: inline(v) for k, v in node.items()}
        if isinstance(node, list):
            return [inline(x) for x in node]
        return node

    out: dict[str, Any] = inline(schema)
    return out
