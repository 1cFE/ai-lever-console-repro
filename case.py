"""Shared case runner for the AI Lever Console reproducibility package.

One place that knows how to build and solve the anchor machine, so the DOE,
the fit and the validation cannot drift apart.

Anchor (from the console footer): 1 GWe net D-T tokamak, size_from_power,
availability 0.85, life 30 yr, interest 7%, NOAK, indirect fraction 0.20.
Model: costingfe at commit ac2d1a8.
"""

from __future__ import annotations

import warnings

# physics.py divides by zero computing q_sci when p_input_eff is 0 on the
# NOAK ignited solve; the resulting inf is not used in any cost account.
warnings.filterwarnings("ignore", category=RuntimeWarning)

from costingfe import ConfinementConcept, CostModel, Fuel  # noqa: E402

# ---------------------------------------------------------------- the anchor
BASELINE = dict(
    net_electric_mw=1000.0,
    size_from_power=True,
    availability=0.85,
    lifetime_yr=30.0,
    interest_rate=0.07,
    noak=True,
    indirect_fraction=0.20,
    construction_time_yr=6.0,
)

# Accounts pulled out of every run.  cas90 / total_capital is the CRF; cas71,
# cas72 and cas80 are the three annual (non-capital) lines the surrogate fits.
ACCOUNTS = (
    "lcoe", "total_capital", "overnight_cost", "capital_per_kw",
    "cas10", "cas20", "cas21", "cas22", "cas23", "cas24", "cas25",
    "cas26", "cas27", "cas28", "cas30", "cas40", "cas50", "cas60",
    "cas70", "cas71", "cas72", "cas80", "cas90",
)

_MODEL = None


def model() -> CostModel:
    """One CostModel instance, reused: construction parses the concept YAML."""
    global _MODEL
    if _MODEL is None:
        _MODEL = CostModel(concept=ConfinementConcept.TOKAMAK, fuel=Fuel.DT)
    return _MODEL


def run(cas22_mult: float = 1.0, **changes) -> dict:
    """Solve the anchor with `changes` applied, plus an optional CAS22 scaling.

    cas22_mult is the console's "reactor capital" lever, expressed as the
    surrogate's u: cas22_mult = 1 - u.  It is applied through cost_overrides,
    which is the only route that also carries the cut through to CAS20, the
    indirect and IDC accounts stacked on it, and the CAS72 replacement line.

    NOTE: cost_overrides keys are UPPERCASE account codes ("CAS22", "C220103").
    Unlike **overrides, an unrecognised key is silently ignored rather than
    raising, so a lowercase key would leave the baseline value in force.
    """
    kw = dict(BASELINE)
    kw.update(changes)

    if cas22_mult != 1.0:
        base_cas22 = _solve(kw).cas22
        kw["cost_overrides"] = {"CAS22": float(base_cas22) * cas22_mult}

    c = _solve(kw)
    out = {k: float(getattr(c, k)) for k in ACCOUNTS}
    out["_inputs"] = {
        "cas22_mult": cas22_mult,
        **{k: v for k, v in kw.items() if k != "cost_overrides"},
    }
    return out


def _solve(kw: dict):
    kw = dict(kw)
    overrides = kw.pop("cost_overrides", None)
    return model().forward(cost_overrides=overrides, **kw).costs


def energy_mwh(availability: float) -> float:
    """Annual saleable energy, M MWh, on the surrogate's nameplate convention.

    The surrogate assumes exactly 1000 MWe net.  size_from_power actually lands
    a shade under that, which is the entire reason the console carries a
    calibration factor -- see README, "Why there is a calibration factor".
    """
    return 8760.0 * 1000.0 * availability / 1e6
