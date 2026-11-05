"""Which step of a plan the labelled sample "after" photo actually shows.

Each sample scenario has one sample after-photo (samples/check_<sample>.jpg): the motorbike one is a close-up of the
spark plug cap pushed back onto the plug, the pump one shows the priming hole open, and so on. Checking that photo
against whatever step happens to be on screen is not a fair test: on "turn the key off" the model rightly says
"not quite", and the demo looks broken. So the "Sample photo" button checks the step the photo shows.

The plan comes from the live model, so the step number and wording change from run to run. The step is found by
plain keyword matching on each step's expected_state (what the camera should see when the step is done), in all
three languages:

  * the step must mention the photo's subject (plug cap / cop busi, nail / paku, ...)
  * each "done" word (pushed on, seated, no gap, rapat, nancep, ...) adds a point
  * each "undone" word (pulled off, lepas, ucul, ...) takes two points away: those steps show the part removed
  * the best score wins; on a tie the later step wins (an after-photo shows the job further along)

No positive score: the last step that mentions the subject without an "undone" word, else the plan's last step
(then "shows" is False and the UI does not claim the photo shows that step).
Matching is on whole words, case-insensitive. Pure function, no model calls, safe to run on every GET.
"""
from __future__ import annotations

import re
from typing import Any

# subject: words naming what the sample after-photo shows; done/undone: words that say the step ends in the state the
# photo shows, or in the opposite state. English, Indonesian and Javanese together: a plan is in one language, and
# the extra words never match the other languages.
SUBJECTS: dict[str, dict[str, tuple[str, ...]]] = {
    "motor": {  # check_motor.jpg: the spark plug cap pushed fully onto the plug
        "subject": ("plug cap", "spark plug cap", "cap", "cop busi", "cop", "tutup busi"),
        "done": ("pushed", "fully", "onto", "seated", "no gap", "clicks", "firmly", "rapat", "rapet", "mentok", "menutupi",
                 "nutupi", "menutup", "nutup", "penuh", "menempel", "nempel", "nancep", "terpasang", "kepasang", "tanpa celah", "tanpa sela",
                 "tidak ada celah", "ora ana celah", "klik"),
        "undone": ("off", "pulled", "removed", "lepas", "terlepas", "ucul", "copot", "dicopot", "dilepas"),
    },
    "pump": {  # check_pump.jpg: the priming plug undone, priming hole open
        "subject": ("priming hole", "priming plug", "priming", "pancingan", "lubang pancingan", "bolongan pancingan"),
        "done": ("open", "opened", "undone", "terbuka", "dibuka", "kebukak", "menga"),
        "undone": ("full", "overflowing", "refit", "tight", "penuh", "meluap", "kencang", "kenceng"),
    },
    "tire": {  # check_tire.jpg: the nail pulled out of the tread
        "subject": ("nail", "paku", "pakune"),
        "done": ("out", "removed", "keluar", "dicabut", "metu", "dicopot"),
        "undone": ("stuck", "menancap", "nancep"),
    },
    "faucet": {  # check_faucet.jpg: the spout dry, no drips
        "subject": ("spout", "faucet", "tap", "mulut kran", "kran", "cangkem kran"),
        "done": ("dry", "no drips", "no drip", "kering", "garing", "tidak ada tetesan", "ora ana tetesan"),
        "undone": ("dripping", "still drips", "netes", "menetes"),  # not bare "drips": "no drips" is the done state
    },
}


def _hits(text: str, words: tuple[str, ...]) -> int:
    return sum(1 for w in words if re.search(rf"(?<![\w-]){re.escape(w)}(?![\w-])", text))


def pick(sample: str, steps: list[dict[str, Any]]) -> dict[str, Any] | None:
    """{"n": step number, "shows": True when the step's expected state names what the photo shows (the UI then says
    so), False for the fallback (last step)}, or None when the plan has no steps."""
    if not steps:
        return None
    rule = SUBJECTS.get(sample)
    last = int(steps[-1].get("n") or len(steps))
    if not rule:
        return {"n": last, "shows": False}
    best: tuple[int, int] | None = None   # (score, n)
    plain: int | None = None              # last step naming the subject without an "undone" word
    for st in steps:
        text = str(st.get("expected_state") or "").lower()
        if not _hits(text, rule["subject"]):
            continue
        n = int(st.get("n") or 0)
        undone = _hits(text, rule["undone"])
        score = _hits(text, rule["done"]) - 2 * undone
        if score > 0 and (best is None or score >= best[0]):
            best = (score, n)
        if not undone:
            plain = n
    if best:
        return {"n": best[1], "shows": True}
    if plain is not None:
        return {"n": plain, "shows": True}
    return {"n": last, "shows": False}


def for_session(s: dict[str, Any]) -> dict[str, Any] | None:
    """pick() for a stored session: None unless it is a sample scenario with a plan."""
    sample = str(s.get("sample") or "")
    plan = s.get("plan")
    if not sample or not isinstance(plan, dict):
        return None
    steps = [st for st in plan.get("steps") or [] if isinstance(st, dict)]
    return pick(sample, steps)
