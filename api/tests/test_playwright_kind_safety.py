"""1.29.9: what the phone says to do first depends on the kind of thing being fixed.

- A red stop on a pump or a rice cooker used to say "switch it off and unplug it / close the gas / stop the engine".
  Appliances and pumps now get an unplug list; gas, house wiring and brakes keep their own lists.
- "Safety first" on the guide said "switch the engine off" for a dripping tap. Each kind now has its own two lines.
"""
import pytest

pytest.importorskip("playwright.sync_api")
from api.tests.test_playwright_smoke import page, server  # noqa: E402,F401  (pytest fixtures)


def _stop(page, category, lang="en", gate=None):
    page.goto(page.base + f"/?lang={lang}")
    page.wait_for_selector("#modeBadge:not(.hidden)")
    log = [{"kind": "gate", "ok": False, "category": gate}] if gate else []
    page.evaluate("([c, log]) => renderStop({status: 'stopped', id: 'x', object_report: {object: 'thing', category: c}, agent_log: log})",
                  [category, log])
    return page.inner_text("#stopBox")


@pytest.mark.parametrize("lang,must", [("en", "Unplug it from the wall socket"), ("id", "Cabut steker dari stopkontak"),
                                       ("jv", "Copot steker saka stopkontak")])
def test_pump_red_stop_says_unplug_in_every_language(page, lang, must):
    box = _stop(page, "pump", lang)
    assert must in box


def test_motor_red_stop_keeps_the_general_list(page):
    box = _stop(page, "motor")
    assert "stop the engine" in box and "Unplug it from the wall socket" not in box


def test_gas_gate_wins_over_the_kind(page):
    box = _stop(page, "appliance", gate="gas")
    assert "Close the regulator" in box and "Unplug it from the wall socket" not in box


def _guide(page, sample, lang="en"):
    page.goto(page.base + f"/?lang={lang}")
    page.click(f'button.sample[data-sample="{sample}"]')
    page.wait_for_selector("#question:not(.hidden), #result:not(.hidden)", timeout=20000)
    if page.is_visible("#question"):
        page.fill("#answerText", "no fuel smell")
        page.click("#answerBtn")
        page.wait_for_selector("#result:not(.hidden)", timeout=20000)
    return page.inner_text("#gSafety")


def test_tap_safety_talks_about_the_stop_valve_not_the_engine(page):
    lines = _guide(page, "faucet")
    assert "Close the stop valve" in lines and "engine" not in lines


def test_pump_safety_says_unplug_and_dry_hands(page):
    lines = _guide(page, "pump")
    assert "Unplug the pump" in lines and "engine" not in lines


def test_motor_safety_in_javanese(page):
    lines = _guide(page, "motor", "jv")
    assert "Pateni mesin, copot kuncine" in lines
