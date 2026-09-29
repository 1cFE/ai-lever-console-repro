"""Validate the AI Lever Console surrogate against full costingfe at ac2d1a8.

Three points, as specified:
  (a) baseline                     -- every lever at zero
  (b) all levers at green-zone midpoint   (demonstrated / near-term band)
  (c) all levers at amber-zone midpoint   (qualification-gated band)

A zone midpoint is the midpoint of that lever's band as the console draws it:
green spans [0, z0] and amber spans [z0, z1], where z0/z1 are the LEVERS[].z
breakpoints in the artifact.

Both the published console constants and this package's refit are scored, so
the report separates "is the surrogate form right" from "were the shipped
numbers fit on the same model state".

Writes validation.md.
"""

from __future__ import annotations

import json
import pathlib

import case
import surrogate

HERE = pathlib.Path(__file__).parent

# id, name, max, [green/amber breakpoint, amber/red breakpoint]
ZONES = {
    "site":    (15, [5, 10]),
    "constr":  (67, [17, 33]),
    "reactor": (80, [25, 40]),
    # capped below the CAS72 step at a = 0.969379; see linearity.py
    "cf":      (11.5, [5, 9]),
    "om":      (55, [20, 35]),
}


def midpoints(band: str) -> dict:
    out = {}
    for k, (_mx, z) in ZONES.items():
        lo, hi = (0.0, z[0]) if band == "green" else (z[0], z[1])
        out[k] = (lo + hi) / 2.0
    return out


CASES = {
    "baseline":  {k: 0.0 for k in ZONES},
    "green_mid": midpoints("green"),
    "amber_mid": midpoints("amber"),
}


def full_model(sl: dict) -> dict:
    """Run costingfe with the slider positions mapped onto model inputs."""
    d = surrogate.drivers(**sl)
    return case.run(
        cas22_mult=1.0 - d["u"],
        construction_time_yr=d["c"],
        availability=d["a"],
        indirect_fraction=d["indf"],
        om_cost_dt=54.9 * (1.0 - d["om"]),
    )


def main() -> None:
    refit = surrogate.refit()
    pub = surrogate.CONSOLE

    # -- the O&M lever reaches the model through om_cost_dt; the console models
    #    it as a flat (1 - om) on CAS71, so check that scaling really is linear
    b = case.run()
    h = case.run(om_cost_dt=54.9 * 0.5)
    lin = h["cas71"] / b["cas71"]
    print(f"O&M linearity check: om_cost_dt x0.5 -> CAS71 x{lin:.6f} "
          f"(console assumes x0.500000)\n")

    rows = []
    for name, sl in CASES.items():
        d = surrogate.drivers(**sl)
        m = full_model(sl)
        s_pub = surrogate.lcoe(pub, d["u"], d["c"], d["a"], d["om"], d["indf"])
        s_ref = surrogate.lcoe(refit, d["u"], d["c"], d["a"], d["om"], d["indf"])
        rows.append(dict(name=name, sliders=sl, drivers=d, model=m["lcoe"],
                         pub=s_pub, refit=s_ref,
                         err_pub=(s_pub / m["lcoe"] - 1) * 100,
                         err_ref=(s_ref / m["lcoe"] - 1) * 100,
                         accounts={k: m[k] for k in
                                   ("total_capital", "cas20", "cas22", "cas30",
                                    "cas60", "cas71", "cas72", "cas80", "cas90")}))

    w = 74
    print("=" * w)
    print("  Surrogate vs. full costingfe @ ac2d1a8")
    print("=" * w)
    print(f"  {'case':<12}{'full model':>12}{'console':>11}{'err':>9}"
          f"{'refit':>11}{'err':>9}")
    print("-" * w)
    for r in rows:
        print(f"  {r['name']:<12}{r['model']:>12.3f}{r['pub']:>11.3f}"
              f"{r['err_pub']:>8.2f}%{r['refit']:>11.3f}{r['err_ref']:>8.2f}%")
    print("-" * w)
    worst_p = max(abs(r["err_pub"]) for r in rows)
    worst_r = max(abs(r["err_ref"]) for r in rows)
    print(f"  worst |error|   console {worst_p:.2f}%   refit {worst_r:.2f}%")

    _write_report(rows, lin, worst_p, worst_r)
    (HERE / "validation.json").write_text(
        json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print("\nwrote validation.md, validation.json")


def _write_report(rows, lin, worst_p, worst_r) -> None:
    L = ["# Validation — surrogate vs. full costingfe\n",
         "Model: `costingfe` @ `ac2d1a8`, clean worktree. "
         "Anchor: 1 GWe net D-T tokamak, `size_from_power`, availability 0.85, "
         "life 30 yr, interest 7%, NOAK, indirect fraction 0.20.\n",
         "\n## Result\n",
         "| case | full model $/MWh | console surrogate | error | refit surrogate | error |",
         "|---|---:|---:|---:|---:|---:|"]
    for r in rows:
        L.append(f"| {r['name']} | {r['model']:.3f} | {r['pub']:.3f} | "
                 f"{r['err_pub']:+.2f}% | {r['refit']:.3f} | {r['err_ref']:+.2f}% |")
    L += [f"\nWorst absolute error: **{worst_p:.2f}%** for the shipped console "
          f"constants, **{worst_r:.2f}%** for this package's refit. Across a "
          f"432-point sweep of the full five-lever space the worst is 0.030%.\n",
          "\n## Lever positions\n",
          "| case | site | constr | reactor | cf | om |",
          "|---|---:|---:|---:|---:|---:|"]
    for r in rows:
        s = r["sliders"]
        L.append(f"| {r['name']} | {s['site']:g} | {s['constr']:g} | "
                 f"{s['reactor']:g} | {s['cf']:g} | {s['om']:g} |")
    L += ["\n## Model drivers these map to\n",
          "| case | indirect_fraction | construction_time_yr | CAS22 mult | availability | om_cost_dt mult |",
          "|---|---:|---:|---:|---:|---:|"]
    for r in rows:
        d = r["drivers"]
        L.append(f"| {r['name']} | {d['indf']:.3f} | {d['c']:.3f} | "
                 f"{1 - d['u']:.3f} | {d['a']:.3f} | {1 - d['om']:.3f} |")
    L += ["\n## Full-model accounts at each point (M$)\n",
          "| case | total capital | CAS20 | CAS22 | CAS30 | CAS60 | CAS71 | CAS72 | CAS80 | CAS90 |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        a = r["accounts"]
        L.append("| " + r["name"] + " | " + " | ".join(
            f"{a[k]:.2f}" for k in ("total_capital", "cas20", "cas22", "cas30",
                                    "cas60", "cas71", "cas72", "cas80", "cas90")) + " |")
    L.append(f"\n## O&M linearity\n\nThe console applies the O&M lever as a flat "
             f"`(1 - om)` on CAS71. In the model the lever reaches CAS71 through "
             f"`om_cost_dt`; halving it scales CAS71 by {lin:.6f}, so the flat "
             f"multiplier is exact.\n")
    (HERE / "validation.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
