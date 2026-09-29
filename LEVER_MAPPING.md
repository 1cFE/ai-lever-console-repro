# Lever → costingfe input mapping

Each console lever, the surrogate driver it sets, and the `costingfe` input(s)
that driver moves. Model: `costingfe` @ `ac2d1a8`.

The console's slider units are not the model's units — the middle column is the
conversion, taken from `lcoeOf()` in the artifact and reproduced in
`surrogate.drivers()`.

| Console lever | Slider units (range, zone breaks) | → surrogate driver | → costingfe input(s) | How it reaches LCOE |
|---|---|---|---|---|
| **Site engineering & delivery** | % of CAPEX off the 20% baseline, 0–15, green ≤5, amber ≤10 | `indf = (20 − site)/100` | `indirect_fraction` (a `CostingConstants` float field, passed as a `forward()` kwarg) | `CAS30 = indirect_fraction × CAS20 × (T_constr / 6)`, then CAS60 IDC and the 1.5% construction insurance stack on top |
| **Construction time** | % faster than 6 yr, 0–67, green ≤17, amber ≤33 | `c = 6 × (1 − constr/100)` | `construction_time_yr` (popped from `**overrides` in `forward()`) | Three ways at once: CAS30 scales by `T/6`; CAS60 IDC scales by `f_IDC(T) = ((1+i)^T − 1)/(i·T) − 1`; CAS71 O&M carries a small per-year term |
| **Reactor capital** | % of CAS22 cut, 0–80, green ≤25, amber ≤40 | `u = reactor/100` | `cost_overrides={"CAS22": base_CAS22 × (1 − u)}` | CAS22 is the largest line in CAS20, so the cut propagates into CAS30, CAS60 and CAS90; CAS72 replacement is proportional to it and falls with it |
| **Capacity factor** | availability points added to 0.85, 0–12, green ≤5, amber ≤9 | `a = 0.85 + cf/100` | `availability` (a required `forward()` argument) | Raises the MWh denominator; also raises CAS72 (more throughput → more scheduled replacement) and CAS80 (more fuel) |
| **O&M** | % of CAS71 cut, 0–55, green ≤20, amber ≤35 | `om = om/100` | `om_cost_dt = 54.9 × (1 − om)` (a `CostingConstants` float field) | `annual_om = om_cost(fuel) × (P_net/1 GWe)^0.5`, levelized into CAS71. Verified exactly linear: halving `om_cost_dt` halves CAS71 |

## Notes that matter if you re-run this

- **`cost_overrides` keys are UPPERCASE** account codes (`"CAS22"`, `"C220103"`).
  Unlike `**overrides`, which raises `ValueError` on an unknown kwarg, an
  unrecognised `cost_overrides` key is **silently ignored** — a lowercase
  `"cas22"` leaves the baseline value in force and the run looks fine. This is
  the single easiest way to produce a wrong DOE.
- **CAS29/30/50/60/70/80/90 are derived and not overridable.** To move CAS30 you
  change `indirect_fraction` or `construction_time_yr`; to move CAS71 you change
  `om_cost_dt`. There is no direct override path for either.
- **The reactor lever is applied as an absolute override, not a multiplier.**
  `case.run()` solves the baseline once to read `CAS22`, then passes
  `base_CAS22 × (1 − u)`. Overriding CAS22 also rescales its `cas22_detail`
  sub-accounts proportionally.
- **`indirect_fraction` and `om_cost_dt` are costing *constants*, not concept
  YAML fields.** They are accepted as `forward()` kwargs because every
  `cc_float_fields()` entry is injected into the parameter dict.

## What the console does *not* map to a model input

The console's zone colours (green / amber / red) and the mechanism prose carry
no arithmetic — they classify how well-evidenced a lever position is, and never
enter the LCOE. Moving a slider within a zone changes the number; the zone
boundary only changes the text and the optimism chip.
