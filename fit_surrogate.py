"""Fit the AI Lever Console surrogate coefficients from the 6-point DOE.

This script only derives coefficients. It does NOT test them: every form here
is fit from two DOE points, and two points always fit a line exactly, so any
residual it could report at those points is zero by construction and means
nothing. The real tests -- fit from the endpoints, score against interior points
the fit never saw -- are in linearity.py. Run that before trusting a form.

It also prints each refitted coefficient against the constant shipped in the
live console, because the console was fit in an earlier session whose DOE
outputs no longer exist; the drift column is the evidence that this package
reproduces it.

Writes surrogate_coefficients.json.
"""

from __future__ import annotations

import json
import pathlib

HERE = pathlib.Path(__file__).parent

from surrogate import LEGACY as PUBLISHED  # the 11 Aug fit, for comparison


def main() -> None:
    runs = {r["id"]: r for r in
            json.loads((HERE / "doe_results.json").read_text(encoding="utf-8"))}
    P1, P2, P3, P4, P5, P6 = (runs[k] for k in ("P1", "P2", "P3", "P4", "P5", "P6"))

    fit = {}

    # -- CAS20 (total direct cost), the base the indirect fraction multiplies
    fit["cas20_a"] = P1["cas20"]
    fit["cas20_b"] = P1["cas20"] - P2["cas20"]

    # -- total capital on the model's own identity:
    #       overnight(u,c,indf) = A(u) + indf * CAS20(u) * (c/6) * insurance
    #       TC                  = overnight * (1 + f_IDC(c))
    #    A(u) is the overnight cost stripped of everything proportional to the
    #    indirect fraction, and is linear in u.  Only P1 and P2 are needed.
    ins = PUBLISHED["insurance"]
    a0 = P1["overnight_cost"] - 0.20 * P1["cas20"] * (6.0 / 6.0) * ins
    a1 = P2["overnight_cost"] - 0.20 * P2["cas20"] * (6.0 / 6.0) * ins
    fit["A_a"] = a0
    fit["A_b"] = a0 - a1

    # legacy linear-in-c interpolation, reported only to compare with the
    # constants the 11 Aug fit shipped; the exact form above replaces it
    fit["tc6_a"] = P1["total_capital"]
    fit["tc6_b"] = P1["total_capital"] - P2["total_capital"]
    fit["tc2_a"] = P3["total_capital"]
    fit["tc2_b"] = P3["total_capital"] - P4["total_capital"]

    # -- CAS71 fixed O&M: linear in construction time, flat in u and in a
    fit["c71_a"] = P3["cas71"]                                  # value at c = 2
    fit["c71_b"] = (P1["cas71"] - P3["cas71"]) / (6.0 - 2.0)    # per year

    # -- CAS72 scheduled replacement: linear in availability, proportional to
    #    (1 - u) -- P2 drives CAS22 to zero and CAS72 goes to zero with it
    fit["c72_a"] = P1["cas72"]
    fit["c72_b"] = (P5["cas72"] - P1["cas72"]) / (0.95 - 0.85)
    # CAS72 steps once inside the cf lever's range: above this capacity factor
    # one more in-vessel replacement fits into the 30-yr life.  A line cannot
    # represent a step, so the surrogate carries it explicitly.  Located by
    # bisection and measured against the sub-threshold fit; see linearity.py.
    fit["c72_a_thresh"] = 0.969379
    fit["c72_step"] = 6.3100

    # -- CAS80 fuel: linear in availability
    fit["c80_a"] = P1["cas80"]
    fit["c80_b"] = (P5["cas80"] - P1["cas80"]) / (0.95 - 0.85)

    # -- capital recovery factor, read straight off the model
    fit["CRF"] = P1["cas90"] / P1["total_capital"]

    # -- the site lever is a closed form, not a fit:
    #       dTC/d(indf) = CAS20(u) * (c/6) * (1 + f_IDC(c)) * insurance
    #    P6 is the only run that moves the indirect fraction, so it is a pure
    #    check point.  f_IDC is costingfe's CAS60 interest-during-construction.
    fit["insurance"] = PUBLISHED["insurance"]
    fit["idc_rate"] = PUBLISHED["idc_rate"]
    i, c = fit["idc_rate"], 6.0
    f_idc = ((1 + i) ** c - 1) / (i * c) - 1
    g_closed = fit["cas20_a"] * (c / 6.0) * (1 + f_idc) * fit["insurance"]
    g_doe = (P1["total_capital"] - P6["total_capital"]) / (0.20 - 0.10)

    print("=" * 74)
    print("  Exact-form coefficients (what the console now ships)")
    print("=" * 74)
    for k in ("A_a", "A_b", "cas20_a", "cas20_b", "c71_a", "c71_b",
              "c72_a", "c72_b", "c80_a", "c80_b", "CRF"):
        print(f"  {k:<14}{fit[k]:>14.4f}")
    print()
    print("=" * 74)
    print("  Legacy linear-in-c fit vs. what the 11 Aug console shipped")
    print("=" * 74)
    print(f"  {'coefficient':<14}{'refit':>14}{'published':>14}{'drift':>12}")
    print("-" * 74)
    for k in ("tc6_a", "tc6_b", "tc2_a", "tc2_b", "cas20_a", "cas20_b",
              "c71_a", "c71_b", "c72_a", "c72_b", "c80_a", "c80_b", "CRF"):
        r, p = fit[k], PUBLISHED[k]
        print(f"  {k:<14}{r:>14.4f}{p:>14.4f}{(r / p - 1) * 100:>11.3f}%")
    print("-" * 74)
    print(f"  dTC/d(indf), closed form   {g_closed:>12.2f}")
    print(f"  dTC/d(indf), from DOE P6   {g_doe:>12.2f}"
          f"   ({(g_closed / g_doe - 1) * 100:+.3f}%)")

    # -- NOT a linearity check: tc2_b is DEFINED as P3 - P4, so predicting P4
    #    from it is an identity and tests nothing.  Real held-out tests, on
    #    points no coefficient was fit to, live in linearity.py -- run that.
    print("-" * 74)
    print(f"  P3 CAS80          actual {P3['cas80']:9.4f}  "
          f"predicted {fit['c80_a']:9.4f}   "
          f"({(fit['c80_a'] / P3['cas80'] - 1) * 100:+.3f}%)  "
          f"<- the one term the surrogate neglects (see README)")
    print("  linearity of the fitted forms: run linearity.py (held-out points)")

    # -- calibration factor: the surrogate's own baseline vs. the model's
    from surrogate import lcoe_raw
    raw = lcoe_raw(fit, u=0.0, c=6.0, a=0.85, om=0.0, indf=0.20)
    # anchor on the model's own baseline, not the legacy rounded 108.89
    fit["BASE"] = P1["lcoe"]
    fit["KCAL"] = P1["lcoe"] / raw
    print("-" * 74)
    print(f"  uncalibrated surrogate at baseline   {raw:8.4f} $/MWh")
    print(f"  full model at baseline               {P1['lcoe']:8.4f} $/MWh")
    print(f"  console anchor (BASE)                {PUBLISHED['BASE']:8.4f} $/MWh")
    print(f"  calibration factor KCAL              {fit['KCAL']:8.6f}"
          f"   (published {PUBLISHED['KCAL']:.6f})")

    (HERE / "surrogate_coefficients.json").write_text(
        json.dumps({"refit": fit, "published": PUBLISHED}, indent=2) + "\n",
        encoding="utf-8")
    print("\nwrote surrogate_coefficients.json")


if __name__ == "__main__":
    main()
