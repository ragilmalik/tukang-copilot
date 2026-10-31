"""Hands-free voice commands: map what the owner said (Bahasa Indonesia, Basa Jawa, English) to one command.

Pure function, no network. The phone does the same in JavaScript (parseCommand in web/app.js, same word
lists) when the browser has SpeechRecognition; phones without it send a short push-to-talk clip to
POST /api/sessions/{id}/command, which transcribes it and calls parse_command here.

Commands: next, back, repeat, check, broken (still broken -> re-plan), stop (leave hands-free mode).
Earlier commands in ORDER win, so "masih rusak" is "broken" even though it is spoken like "lanjut".
"""
from __future__ import annotations

import re

COMMANDS = ("broken", "stop", "back", "repeat", "check", "next")
ORDER = COMMANDS

# Keep in sync with VOICE_WORDS in web/app.js (api/tests/test_voice.py checks both against the same cases).
WORDS: dict[str, dict[str, list[str]]] = {
    "id": {
        "broken": ["masih rusak", "tetap rusak", "masih mati", "tetap mati", "masih belum", "tidak berhasil", "nggak berhasil",
                   "gak berhasil", "belum berhasil", "rencana lain", "masih bocor", "masih netes"],
        "stop": ["berhenti", "stop", "matikan suara", "cukup", "diam"],
        "back": ["kembali", "mundur", "sebelumnya", "balik"],
        "repeat": ["ulang", "ulangi", "sekali lagi", "apa tadi", "bacakan lagi"],
        "check": ["cek", "periksa", "foto", "cekrek", "lihat"],
        "next": ["lanjut", "terus", "berikutnya", "selanjutnya", "oke", "sudah", "beres"],
    },
    "jv": {
        "broken": ["isih rusak", "tetep rusak", "isih mati", "tetep mati", "ora kasil", "durung kasil", "rencana liya", "isih bocor", "isih netes"],
        "stop": ["mandheg", "mandeg", "wis cukup", "meneng", "stop"],
        "back": ["bali", "mbalik", "sadurunge", "sakdurunge", "mundur"],
        "repeat": ["baleni", "maneh", "sepisan maneh", "ulang", "ulangi"],
        "check": ["priksa", "periksa", "cek", "foto", "delokna"],
        "next": ["terus", "lanjut", "sabanjure", "wis", "oke", "rampung"],
    },
    "en": {
        "broken": ["still broken", "not working", "doesn't work", "does not work", "didn't work", "did not work", "still dead",
                   "another plan", "still leaking", "still dripping"],
        "stop": ["stop", "quit", "be quiet", "stop listening", "that's enough"],
        "back": ["back", "go back", "previous", "last step"],
        "repeat": ["repeat", "again", "say again", "say that again", "read it again"],
        "check": ["check", "verify", "photo", "take a photo", "look"],
        "next": ["next", "continue", "go on", "done", "okay", "ok", "carry on"],
    },
}
NEGATION = ["jangan", "ojo", "aja", "don't", "do not", "not"]


def _norm(text: str) -> str:
    t = (text or "").lower().replace("\u2019", "'")
    t = re.sub(r"[^\w' ]+", " ", t)
    return " ".join(t.split())[:200]


def _hit(text: str, word: str) -> bool:
    for m in re.finditer(r"(?:^| )(?=" + re.escape(word) + r"(?: |$))", text):
        before = text[: m.end()].split()
        if not (before and before[-1] in NEGATION):  # "jangan lanjut" / "don't stop" is not a command
            return True
    return False


def parse_command(text: str, lang: str = "id") -> str | None:
    """One of COMMANDS, or None when nothing (or only a negated command) was said.
    The owner's own language is tried first, then the other two (people mix languages)."""
    t = _norm(text)
    if not t:
        return None
    langs = [lang] if lang in WORDS else []
    langs += [x for x in WORDS if x not in langs]
    for lg in langs:
        for cmd in ORDER:
            if any(_hit(t, w) for w in WORDS[lg][cmd]):
                return cmd
    return None
