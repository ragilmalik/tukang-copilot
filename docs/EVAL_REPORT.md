# Fixture evaluation

Server: `http://127.0.0.1:8765`, mode **mock**, 2026-11-02 07:04 UTC.

The fixtures are labelled AI-generated sample photos, not real repairs. In mock mode this shows the pipeline and safety routing work; only a LIVE run on real photos gives accuracy numbers.

**10/10 photos met every expectation.** Total model cost: $0.000.

| Photo | Status | Safety | Category | Parts found | Steps | Asked | Secs | Result |
|---|---|---|---|---|---|---|---|---|
| sample_motor_plug_area.jpg | ready | amber | motor | 3/3 | 4 | yes | 6.9 | PASS |
| sample_motor_plug_closeup.jpg | ready | amber | motor | 2/3 | 4 | yes | 6.8 | PASS |
| sample_pump_overview.jpg | ready | amber | pump | 3/3 | 4 | no | 6.4 | PASS |
| sample_faucet_drip.jpg | ready | green | plumbing | 3/3 | 4 | no | 6.3 | PASS |
| sample_faucet_hose_clamp.jpg | ready | green | plumbing | 1/3 | 4 | no | 6.1 | PASS |
| sample_rice_cooker_front.jpg | stopped | red | appliance | 2/2 | 0 | no | 3.2 | PASS |
| sample_rice_cooker_base_open.jpg | stopped | red | appliance | 0/2 | 0 | no | 3.1 | PASS |
| sample_tire_flat_nail.jpg | ready | amber | motor | 3/3 | 4 | no | 8.0 | PASS |
| sample_tire_flat_nail_en.jpg | ready | amber | motor | 3/3 | 4 | no | 8.3 | PASS |
| sample_unknown_object.jpg | ready | amber | motor | 0/3 | 4 | yes | 7.4 | PASS |

Camera step checks:

| Photo | HTTP | Verdict returned | Result |
|---|---|---|---|
| sample_motor_step_cap_on.jpg | 200 | True | PASS |
| sample_pump_prime_plug.jpg | 200 | True | PASS |
| sample_faucet_step_dry.jpg | 200 | True | PASS |
| sample_tire_valve_check.jpg | 200 | True | PASS |
| sample_tire_nail_out.jpg | 200 | True | PASS |
