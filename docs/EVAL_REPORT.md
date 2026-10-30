# Fixture evaluation

Server: `http://127.0.0.1:8032`, mode **mock**, 2026-10-30 19:15 UTC.

The fixtures are labelled stand-ins, not real photos. In mock mode this shows the pipeline and safety routing work; only a LIVE run on real photos gives accuracy numbers.

**10/10 photos met every expectation.** Total model cost: $0.000.

| Photo | Status | Safety | Category | Parts found | Steps | Asked | Secs | Result |
|---|---|---|---|---|---|---|---|---|
| standin_motor_plug_area.jpg | ready | amber | motor | 3/3 | 4 | yes | 1.0 | PASS |
| standin_motor_plug_closeup.jpg | ready | amber | motor | 3/3 | 4 | yes | 1.0 | PASS |
| standin_pump_overview.jpg | ready | amber | pump | 3/3 | 4 | no | 0.5 | PASS |
| standin_faucet_drip.jpg | ready | green | plumbing | 3/3 | 4 | no | 0.5 | PASS |
| standin_faucet_hose_clamp.jpg | ready | green | plumbing | 3/3 | 4 | no | 0.5 | PASS |
| standin_rice_cooker_front.jpg | stopped | red | appliance | 2/2 | 0 | no | 0.5 | PASS |
| standin_rice_cooker_base_open.jpg | stopped | red | appliance | 2/2 | 0 | no | 0.5 | PASS |
| standin_tire_flat_nail.jpg | ready | amber | motor | 3/3 | 4 | no | 0.5 | PASS |
| standin_tire_flat_nail_en.jpg | ready | amber | motor | 3/3 | 4 | no | 0.5 | PASS |
| standin_unknown_object.jpg | ready | amber | motor | 3/3 | 4 | yes | 1.0 | PASS |

Camera step checks:

| Photo | HTTP | Verdict returned | Result |
|---|---|---|---|
| standin_motor_step_cap_on.jpg | 200 | True | PASS |
| standin_pump_prime_plug.jpg | 200 | True | PASS |
| standin_tire_valve_check.jpg | 200 | True | PASS |
