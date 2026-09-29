"""Held-out tests of the surrogate's functional forms.

Every form in the surrogate is fit from two DOE points. Two points always fit a
line, so the fit residual at those points is zero by construction and proves
nothing. This script fits from the DOE endpoints and then scores the result
against interior points the fit never saw -- which is the only way to tell an
exact form from an assumed one.

It also answers a question the DOE design invites: P2 and P4 drive CAS22 to
zero, which is not a plant anyone would build and is outside the console's
0-80% slider range. Is a slope measured there the right slope inside the range?

Writes linearity.md.
"""

from __future__ import annotations

import pathlib

import case

HERE = pathlib.Path(__file__).parent

U_TEST = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
C_TEST = (2.0, 3.0, 4.0, 4.5, 5.0, 5.49, 6.0)
# NOTE: the console's cf lever reaches 0.97, so this must too. An earlier
# version of this test stopped at 0.95 and missed the step at 0.9694.
A_TEST = (0.85, 0.875, 0.90, 0.92, 0.95, 0.96, 0.965, 0.9694, 0.97)


def main() -> None:
    lines = ["# Held-out linearity tests\n",
             "Each form is fit from the DOE endpoints only; interior points are "
             "held out. A form is *exact* if the held-out error is zero.\n"]

    # ---------------------------------------------------- reactor capital (u)
    p0, p1 = case.run(cas22_mult=1.0), case.run(cas22_mult=0.0)
    a, b = p0["total_capital"], p0["total_capital"] - p1["total_capital"]
    print("--- total capital vs u   (fit from u=0, u=1; interior held out) ---")
    print(f"  {'u':>5}{'CAS22':>10}{'CAS20':>10}{'CAS60':>10}"
          f"{'TC':>10}{'predicted':>11}{'err':>10}")
    rows_u = []
    for u in U_TEST:
        r = case.run(cas22_mult=1.0 - u)
        pred = a - b * u
        err = (pred / r["total_capital"] - 1) * 100
        rows_u.append((u, r, pred, err))
        print(f"  {u:>5.2f}{r['cas22']:>10.2f}{r['cas20']:>10.2f}"
              f"{r['cas60']:>10.2f}{r['total_capital']:>10.2f}"
              f"{pred:>11.2f}{err:>9.4f}%")
    worst_u = max(abs(e) for _, _, _, e in rows_u)
    lines += ["\n## Reactor capital — total capital vs `u`\n",
              "Fit from `u=0` and `u=1`. The CAS22 override is a pure cost "
              "injection: it does not resize the machine, so every downstream "
              "account moves linearly with it.\n",
              "| u | CAS22 | CAS20 | CAS60 | TC | predicted | error |",
              "|---:|---:|---:|---:|---:|---:|---:|"]
    for u, r, pred, err in rows_u:
        lines.append(f"| {u:.2f} | {r['cas22']:.2f} | {r['cas20']:.2f} | "
                     f"{r['cas60']:.2f} | {r['total_capital']:.2f} | "
                     f"{pred:.2f} | {err:+.4f}% |")
    lines.append(f"\nWorst held-out error **{worst_u:.4f}%** — exact. Measuring "
                 "the slope at the unphysical `u=1` therefore gives the same "
                 "slope as measuring it anywhere inside the console's 0–80% "
                 "range. P2/P4 read as nonsense but cost no accuracy.\n")

    # ------------------------------------------------- construction time (c)
    q2, q6 = case.run(construction_time_yr=2.0), case.run()
    t2, t6 = q2["total_capital"], q6["total_capital"]
    print("\n--- total capital vs c   (surrogate interpolates LINEARLY) ---")
    print(f"  {'c':>5}{'CAS30':>10}{'CAS60':>10}{'TC':>10}"
          f"{'lin.interp':>12}{'err':>10}")
    rows_c = []
    for c in C_TEST:
        r = case.run(construction_time_yr=c)
        pred = t2 + (t6 - t2) * (c - 2.0) / 4.0
        err = (pred / r["total_capital"] - 1) * 100
        rows_c.append((c, r, pred, err))
        print(f"  {c:>5.2f}{r['cas30']:>10.2f}{r['cas60']:>10.2f}"
              f"{r['total_capital']:>10.2f}{pred:>12.2f}{err:>9.4f}%")
    worst_c = max(abs(e) for _, _, _, e in rows_c)
    lines += ["\n## Construction time — total capital vs `c`\n",
              "The surrogate straight-lines `TC` between `c=2` and `c=6`. The "
              "true response is convex, because CAS60 interest-during-"
              "construction is nonlinear in `c`. Pinned at both ends, worst in "
              "the middle — where the console's zones sit.\n",
              "| c (yr) | CAS30 | CAS60 | TC | linear interp | error |",
              "|---:|---:|---:|---:|---:|---:|"]
    for c, r, pred, err in rows_c:
        lines.append(f"| {c:.2f} | {r['cas30']:.2f} | {r['cas60']:.2f} | "
                     f"{r['total_capital']:.2f} | {pred:.2f} | {err:+.4f}% |")
    lines.append(f"\nWorst held-out error **{worst_c:.3f}%**. This is the form "
                 "the console shipped until it was rebuilt on the model's own "
                 "identity, `TC = overnight x (1 + f_IDC(c))`, which is exact. "
                 "The table is kept as the evidence for why it was changed: the "
                 "drift peaks in the middle, exactly where the sliders sit.\n")

    # ------------------------------------------------------- availability (a)
    r085, r095 = case.run(), case.run(availability=0.95)
    c72_a, c72_b = r085["cas72"], (r095["cas72"] - r085["cas72"]) / 0.10
    print("\n--- CAS72 vs availability   (linear fit a=0.85..0.95, "
          "plus the measured step at a>=0.969379) ---")
    print(f"  {'a':>6}{'CAS72':>10}{'predicted':>11}{'err':>10}")
    rows_a = []
    for av in A_TEST:
        r = case.run(availability=av)
        pred = (c72_a + c72_b * (av - 0.85)
                + (6.3100 if av >= 0.969379 else 0.0))
        err = (pred / r["cas72"] - 1) * 100
        rows_a.append((av, r, pred, err))
        print(f"  {av:>6.3f}{r['cas72']:>10.4f}{pred:>11.4f}{err:>9.4f}%")
    worst_a = max(abs(e) for _, _, _, e in rows_a)
    lines += ["\n## Capacity factor — CAS72 vs availability\n",
              "CAS72 is **not continuous**. At a = 0.969379 one more in-vessel "
              "replacement fits into the 30-yr life and the account jumps "
              "+6.31 M$/yr (+11%). That threshold sits *inside* the console's "
              "cf lever range, which reaches 0.97, so the surrogate carries the "
              "step explicitly; a straight line through it is wrong by ~1% of "
              "LCOE at the top of the lever.\n",
              "| a | CAS72 | predicted | error |", "|---:|---:|---:|---:|"]
    for av, r, pred, err in rows_a:
        lines.append(f"| {av:.3f} | {r['cas72']:.4f} | {pred:.4f} | {err:+.4f}% |")
    lines.append(f"\nWorst held-out error **{worst_a:.4f}%**.\n")

    print(f"\nworst held-out error:  u {worst_u:.4f}%   "
          f"c {worst_c:.3f}%   a {worst_a:.4f}%")
    (HERE / "linearity.md").write_text("\n".join(lines), encoding="utf-8")
    print("wrote linearity.md")


if __name__ == "__main__":
    main()
