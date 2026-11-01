"""The Javanese PDF speaks Javanese (it used to fall back to Indonesian for most labels), and no language shows
the English "rules in code" tag in the under-the-hood list."""
from api.render.report_pdf import LABELS

# Words that are the same in Indonesian and Basa Jawa, so an identical label is fine.
SAME = {"object", "problem", "status", "ok", "todo", "minutes", "st_diagnose", "parts", "green", "steps", "st_illustrate"}


def test_all_three_languages_have_the_same_label_keys() -> None:
    assert set(LABELS["id"]) == set(LABELS["jv"]) == set(LABELS["en"])


def test_javanese_labels_are_not_indonesian_leftovers() -> None:
    same = sorted(k for k in LABELS["id"] if LABELS["jv"][k] == LABELS["id"][k] and k not in SAME)
    assert not same, f"still Indonesian in the Javanese PDF: {same}"


def test_javanese_safety_words_match_the_app() -> None:
    assert (LABELS["jv"]["green"], LABELS["jv"]["amber"], LABELS["jv"]["red"]) == ("AMAN", "ATI-ATI", "MANDHEG")


def test_rules_in_code_tag_is_localized() -> None:
    assert LABELS["en"]["code_tool"] == "rules in code"
    assert LABELS["id"]["code_tool"] == "aturan di kode"
    assert LABELS["jv"]["code_tool"] == "aturan ing kode"
