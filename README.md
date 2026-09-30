# AI Lever Console — reproducibility package

Source and numerical checks for the **AI Lever Console**, a hypothetical plant-cost scenario tool.

[Open the console](https://ai.1cf.energy/). You can also download `console.html` and open it directly in a browser. It has no external runtime dependencies.

The colored bands organize assumed changes and possible mechanisms. They are not measurements of AI savings, probabilities or engineering limits. The preset names describe the size of the assumed changes. Their numerical settings are unchanged from the original console.

## Model version and boundary

| | |
|---|---|
| Library | `costingfe` |
| Commit | `ac2d1a8d07d0d9cbe5f0ca6e88db2fcbf477c093` (`ac2d1a8`) |
| Concept | D-T tokamak, `ConfinementConcept.TOKAMAK`, `Fuel.DT` |
| Sizing | `size_from_power=True`, `net_electric_mw=1000.0` |
| Economics | availability 0.85, life 30 yr, interest 7%, NOAK, indirect fraction 0.20, construction 6 yr |
| Baseline LCOE | **108.8711 $/MWh** |
| Overnight / total capital | 7096.73 / 8460.83 M$ |

**Boundary: plant-gate LCOE for approximately 1 GWe net output, before AI adoption costs.** It is
`(CAS90 + CAS70 + CAS80) / (8760 · P_net · availability)` — capital recovery,
O&M, scheduled replacement and fuel. It excludes grid interconnection beyond
the plant fence, transmission, storage, curtailment, carbon or capacity
revenue, and computing, data preparation, integration, qualification, training and maintenance costs of AI adoption. The chosen inputs do not establish their joint feasibility or the additional contribution from AI beyond ordinary NOAK improvement. Two plants
with the same number here can have very different delivered costs.

## Surrogate accuracy

Compared with full `costingfe` at three points (see `validation.md`):

| case | full model $/MWh | surrogate | error |
|---|---:|---:|---:|
| baseline | 108.871 | 108.871 | +0.0000% |
| all levers at green-zone midpoint | 92.015 | 92.013 | −0.0019% |
| all levers at amber-zone midpoint | 67.737 | 67.740 | +0.0047% |

A reproducible 432-point grid covering all five slider dimensions found a maximum relative difference of **0.03364%** and a median of **0.00912%**. The grid and every comparison are saved in `sweep_validation.json`; run `validate_sweep.py` to regenerate them. These are sampled checks, not a guaranteed error bound over the continuous slider ranges. Numerical agreement with the cost model does not validate the plant assumptions or benefits attributed to AI.

> **These figures are for the rebuilt surrogate.** The version fit on 11 Aug and
> shipped until now scored 0.58% at the amber midpoint and **1.03%** worst-case,
> from two defects this package found and fixed — see *What was wrong* below.

## What was wrong

Two defects in the 11 Aug surrogate, both found by scoring the fitted forms
against **held-out** points the fit never saw (`linearity.py`). Neither is
visible from the fit residuals, because every form is fit from two points and
two points always fit a line exactly.

**1. Total capital was linearly interpolated in construction time.** The DOE
probed only `c=2` and `c=6` and the surrogate straight-lined between them, but
interest during construction is nonlinear in `c`, so the fit was pinned at both
ends and drifted to **+0.71%** in the middle — exactly where the sliders sit.

Fixed by dropping the interpolation for the model's own identity:

    overnight(u, c, indf) = A(u) + indf * CAS20(u) * (c/6) * 1.015
    TC                    = overnight * (1 + f_IDC(c))

CAS30 is the only account carrying `c` into overnight (plus the construction
insurance stacked on it), and CAS60 is exactly `f_IDC(c)` on the whole overnight
cost. This matches the full-model capital calculation to the displayed precision at checked points, and it folds
the site lever in natively — the separate `dTC/d(indf)` correction is gone.

**2. CAS72 is not continuous, and the old fit straight-lined through a step.**
At availability **0.969379** one more in-vessel replacement fits into the 30-yr
life and CAS72 jumps **+6.31 M$/yr (+11%)**. That threshold sits *inside* the
console's capacity-factor lever, which reaches 0.97 — so the top of the lever
was wrong by ~1% of LCOE, the worst error anywhere in the space. The surrogate
now carries the step explicitly.

This discontinuity comes from the model's discrete replacement schedule. It does not establish a physical availability limit or imply that a particular control technology is required.

**The lever is capped below it.** The capacity-factor slider now stops at
+11.5 pts (availability 0.965), the largest half-point detent under the
threshold, so the tool stays entirely inside the continuous regime. Past the
step the slider moves the number the *wrong way* — +11.5 → +12 raised LCOE by
$0.28/MWh — which is a real model result but not what this tool is for. The step
stays in `buckets()` as a guard in case the ceiling is ever raised.

## What the rebuild moved

Nothing in the console's prose depends on a number that changed: capital is
still ~84% of LCOE at baseline, O&M still ~9%, CAS22 still ~$4.1B/GWe, CAS71
still ~$76M/yr. Only the displayed LCOE moved, and only slightly — the old
surrogate ran high, so every figure came down:

| | old | new | Δ |
|---|---:|---:|---:|
| Green-zone median | 92.22 | 91.99 | −0.23 |
| Green-zone midpoint | 92.26 | 92.01 | −0.25 |
| Amber-zone median | 68.11 | 67.73 | −0.38 |
| Amber-zone midpoint | 68.13 | 67.74 | −0.39 |
| "Reasonable" preset | 77.60 | 77.25 | −0.35 |
| "Optimistic" preset | 56.64 | 56.30 | −0.34 |
| "Heroic" preset | 38.97 | 38.96 | −0.00 |

Zone statistics are over a 7-point grid per lever within each band
(16,807 combinations), capacity factor capped at +11.5.

### What is exact, and what is not

Run `linearity.py` for the evidence. Exact (held-out error 0.0000%):

- total capital in `u`, `c` and the indirect fraction, on the identity above;
- CAS72 ∝ `(1 − u)` and CAS71 ∝ `(1 − om)`.

Not exact, and left alone as negligible:

- CAS72 vs availability is very slightly concave; the linear fit is worst at
  `a=0.90`, off **0.126%** on an account worth ~$6.8/MWh, so ~$0.009/MWh;
- CAS80 (fuel) has a weak construction-time dependence the fit ignores (8.2% on
  CAS80 at `c=2`). CAS80 is $0.10/MWh, so the omission is worth **$0.008/MWh**.

## Why there is a calibration factor

The console carries `KCAL = 1.0014319`. It is not a fudge to hide fit error.
The surrogate divides by a nameplate `8760 × 1000 MW × a`, but `size_from_power`
actually lands at ~998.6 MWe net, so the surrogate's denominator is ~0.14% too
large at every point. `KCAL` restores it and pins the surrogate to the model's
own baseline, 108.8711 $/MWh. (The 11 Aug version carried `108.89 / 108.74`,
anchoring to a rounded 108.89 rather than the model value.)

## Provenance: this DOE is a reconstruction

The original DOE script and outputs from the 11 Aug 2026 session in which the
console was built **no longer exist** — the working directory and its scratch
files are gone. This package regenerates the DOE from scratch at `ac2d1a8`,
using the design that uniquely identifies the coefficients the console shipped.

That it *is* the original design is well evidenced: driving CAS22 to zero gives
total capital 2316.33 M$ against the console's `tc6(1) = 8462.5 − 6145.9 =
2316.6`, and every other shipped constant falls out of the same six runs.
`fit_surrogate.py` prints refit against shipped:

| | refit | shipped | drift |
|---|---:|---:|---:|
| `tc6_a` | 8460.83 | 8462.5 | −0.020% |
| `tc6_b` | 6144.50 | 6145.9 | −0.023% |
| `cas20_b` (≈ baseline CAS22) | 4146.30 | 4147.3 | −0.024% |
| `c71_a` | 70.1530 | 70.15 | +0.004% |
| `c72_a` | 50.9606 | 50.97 | −0.018% |
| `CRF` | 0.080586 | 0.08059 | −0.004% |

Every capital coefficient is uniformly ~0.02% below the shipped value, which
says the original was fit on a *very slightly* different model state, not a
different design. The direction and uniformity rule out a structural
difference. Both sets are scored in `validation.md`; they agree to 0.001 $/MWh.

Three shipped constants trace directly to named model inputs rather than to the
fit: `indirect_fraction: 0.20`, `reference_construction_time: 6.0`, and the
`1.015` in the site-lever closed form is `construction_insurance_frac: 0.015`.

## Contents

```
README.md                   this file
LEVER_MAPPING.md            each console lever -> costingfe input(s)
validation.md               surrogate vs. full model, the three cases
baseline.json               baseline inputs + solved accounts
inputs/                     the two input files, verbatim at ac2d1a8
  steady_state_tokamak.yaml   concept defaults (the D-T tokamak baseline)
  costing_constants.yaml      global cost coefficients
case.py                     shared case runner -- the anchor lives here
run_doe.py                  regenerates the 6-point DOE
doe_design.json             the design, with why each point exists
doe_results.json/.csv       the six runs, full CAS ladder each
fit_surrogate.py            derives the coefficients, scores them vs. shipped
surrogate_coefficients.json refit + shipped, side by side
surrogate.py                line-for-line Python port of the console's JS
console.html                standalone console page, served from this repository
validate.py                 the three-point validation
validation.json             machine-readable validation output
validate_sweep.py            reproducible 432-point sampled comparison
sweep_validation.json        grid, model pin, coefficients hash and every comparison
linearity.py                held-out tests of each fitted form
linearity.md                their results -- what is exact, what is not
```

## The 6-point DOE

Each point exists to identify specific coefficients; nothing is redundant.

| id | point | identifies |
|---|---|---|
| P1 | baseline | anchor; `A(u=0)` and CAS20, CAS71, CAS72, CAS80, CRF |
| P2 | CAS22 → 0 | `A(u=1)` and the CAS20 slope in `u` |
| P3 | construction 2 yr | slope of CAS71 in `c` |
| P4 | both | *now redundant* — held out as a validation point |
| P5 | availability 0.95 | slope of CAS72 and CAS80 in `a` |
| P6 | indirect fraction 0.10 | *now redundant* — held out as a validation point |

The exact-TC rebuild needs only P1, P2, P3 and P5. P4 and P6 were required by
the old linear-in-`c` interpolation; they are kept in the design and have become
free held-out validation points, which is strictly better than spending them on
the fit. The capacity-factor step at `a=0.969379` is located by bisection in
`linearity.py` rather than by a DOE point, because a step cannot be fit from
corner runs.

P2 and P4 set CAS22 to exactly zero. That is deliberately unphysical — it is a
slope-identification point, not a plant. The console never evaluates past
`u = 0.80`. The validation checks specified points inside the lever ranges.

## How to rerun

Use a clean checkout of [1costingFE](https://github.com/1cFE/1costingfe) at the pinned commit. Other revisions or local changes can give different results. For an existing clone, create an isolated worktree:

```bash
cd /path/to/1costingfe
git worktree add --detach /tmp/wt-ac2d1a8 ac2d1a8
```

Then, from this folder:

```bash
export WT=/tmp/wt-ac2d1a8
export PYTHONPATH="$WT/src"

uv run --no-project --with numpy --with pydantic --with pyyaml python run_doe.py
uv run --no-project --with numpy --with pydantic --with pyyaml python fit_surrogate.py
uv run --no-project --with numpy --with pydantic --with pyyaml python validate.py
uv run --no-project --with numpy --with pydantic --with pyyaml python linearity.py
uv run --no-project --with numpy --with pydantic --with pyyaml python validate_sweep.py
```

Run the first three in that order: the fit reads `doe_results.json`, and the
validation reads `surrogate_coefficients.json`. `linearity.py` runs its own points using `case.py`. `validate_sweep.py` compares the existing console coefficients against the pinned full model and checks that the model checkout is clean.

Only three runtime dependencies are needed (`numpy`, `pydantic`, `pyyaml`).
Do **not** add `jax`: the backend auto-selects it if importable and a single
forward run goes from ~0.7 s to ~37 s, for identical results. If you are using
the library's own venv, force it off with `COSTINGFE_BACKEND=numpy`.

Expect one harmless `RuntimeWarning: divide by zero` from `physics.py` — it is
`q_sci` on the ignited solve, and no cost account reads it. `case.py` suppresses it.

## Rebuilding the console from this package

`surrogate.py` is a faithful port of the console's JavaScript, and
`surrogate_coefficients.json` holds both coefficient sets. To update the
console, replace the constants at the top of its `<script>` with the `refit`
block and re-derive `KCAL` from the new baseline — but note that the shipped and
refit coefficients agree to 0.001 $/MWh, so there is no accuracy reason to.

## Hosting and scenario labels

Cloudflare Pages serves the standalone console at [ai.1cf.energy](https://ai.1cf.energy/). Configure the build command as `mkdir -p dist && cp console.html dist/index.html` and the output directory as `dist`. Only the public console HTML is deployed. The source and numerical checks remain in this repository; no article drafts or editorial history are included.

The source and reproduction links are visible in the console footer. The scenario bands retain the original numerical breakpoints, while replacing claims of demonstrated percentage savings and regulatory or physical floors with explicit conditions. The site slider displays the remaining nominal indirect fraction as a percentage of direct cost. Its explanations use that same value without rounding away half points.
