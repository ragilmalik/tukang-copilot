"""Loads the versioned prompt files in /prompts (one .md per stage; see docs/AI_PIPELINE.md)."""
from __future__ import annotations

import re
from functools import lru_cache

from .settings import ROOT

PROMPT_DIR = ROOT / "prompts"
LANG_NAME = {"id": "Bahasa Indonesia", "jv": "Javanese (basa Jawa, ngoko alus)", "en": "English"}


@lru_cache(maxsize=None)
def _raw(name: str) -> str:
    text = (PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8")
    return re.sub(r"^<!--.*?-->\s*", "", text, flags=re.S).strip()  # drop the header comment


def get(name: str, **kw: str) -> str:
    """Fill {placeholders}. Unknown braces are left alone so JSON examples survive."""
    text = _raw(name)
    for k, v in kw.items():
        text = text.replace("{" + k + "}", str(v))
    return text
