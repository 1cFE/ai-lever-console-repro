"""Regenerate the 6-point DOE the AI Lever Console surrogate is fit to.

The design is not arbitrary -- it is the minimum set that identifies every
coefficient in the surrogate, given that each response is exactly linear in its
driver (verified in fit_surrogate.py, which reports the residuals):

  P1  baseline                     u=0, c=6, a=0.85, indf=0.20
  P2  reactor capital to zero      u=1, c=6          -> slope of TC and CAS20 in u
  P3  fastest build                u=0, c=2          -> slope of TC and CAS71 in c
  P4  both                         u=1, c=2          -> the TC(u,c) bilinear corner
  P5  high availability            a=0.95            -> slope of CAS72 and CAS80 in a
  P6  low indirect fraction        indf=0.10         -> checks the closed-form dTC/d(indf)

u is the fractional CAS22 cut; the model is driven with cas22_mult = 1 - u.
P2 and P4 set CAS22 to exactly zero.  That is deliberately unphysical: it is a
slope-identification point, not a plant.  The console never evaluates past
u = 0.80, and the surrogate is only claimed over the lever ranges.

Writes doe_design.json and doe_results.{json,csv}.
"""

from __future__ import annotations

import csv
import json
import pathlib

import case

HERE = pathlib.Path(__file__).parent

DESIGN = [
    dict(id="P1", label="baseline",
         note="the anchor; also the u=0, c=6 corner",
         cas22_mult=1.0, changes={}),
    dict(id="P2", label="reactor capital -> 0",
         note="slope of total capital and CAS20 in u, at c=6",
         cas22_mult=0.0, changes={}),
    dict(id="P3", label="construction 2 yr",
         note="slope of total capital in c, and of CAS71 in c, at u=0",
         cas22_mult=1.0, changes={"construction_time_yr": 2.0}),
    dict(id="P4", label="reactor -> 0, construction 2 yr",
         note="the fourth corner of the TC(u,c) bilinear",
         cas22_mult=0.0, changes={"construction_time_yr": 2.0}),
    dict(id="P5", label="availability 0.95",
         note="slope of CAS72 and CAS80 in availability",
         cas22_mult=1.0, changes={"availability": 0.95}),
    dict(id="P6", label="indirect fraction 0.10",
         note="check point for the closed-form dTC/d(indirect_fraction)",
         cas22_mult=1.0, changes={"indirect_fraction": 0.10}),
]


def main() -> None:
    results = []
    for d in DESIGN:
        r = case.run(cas22_mult=d["cas22_mult"], **d["changes"])
        r["id"], r["label"], r["note"] = d["id"], d["label"], d["note"]
        results.append(r)
        print(f"{d['id']}  {d['label']:<32} "
              f"LCOE {r['lcoe']:8.4f}  TC {r['total_capital']:9.2f}  "
              f"CAS20 {r['cas20']:8.2f}  CAS71 {r['cas71']:7.4f}  "
              f"CAS72 {r['cas72']:7.4f}  CAS80 {r['cas80']:6.4f}")

    (HERE / "doe_design.json").write_text(
        json.dumps(DESIGN, indent=2) + "\n", encoding="utf-8")
    (HERE / "doe_results.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8")

    cols = ["id", "label"] + list(case.ACCOUNTS)
    with open(HERE / "doe_results.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in results:
            w.writerow([r[c] for c in cols])

    print(f"\nwrote doe_design.json, doe_results.json, doe_results.csv "
          f"({len(results)} runs)")


if __name__ == "__main__":
    main()
