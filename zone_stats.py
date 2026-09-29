"""Old vs new surrogate across the console's zones and presets."""
import itertools
import statistics as st

ZONES = {"site": (15, [5, 10]), "constr": (67, [17, 33]),
         "reactor": (80, [25, 40]), "cf": (12, [5, 9]), "om": (55, [20, 35])}
KEYS = list(ZONES)


def drivers(s):
    return dict(indf=(20 - s["site"]) / 100, c=6 * (1 - s["constr"] / 100),
                u=s["reactor"] / 100, a=0.85 + s["cf"] / 100, om=s["om"] / 100)


def fidc(c, i=0.07):
    return ((1 + i) ** c - 1) / (i * c) - 1


def old(s):
    d = drivers(s); u, c, a, om, indf = d["u"], d["c"], d["a"], d["om"], d["indf"]
    tc6, tc2 = 8462.5 - 6145.9 * u, 6590.6 - 4754.6 * u
    tc = tc2 + (tc6 - tc2) * (c - 2) / 4
    cas20 = 5397.5 - 4147.3 * u
    g = cas20 * (c / 6) * (1 + fidc(c)) * 1.015
    cap = 0.08059 * (tc + g * (indf - 0.20))
    c71 = (70.15 + 1.4475 * (c - 2)) * (1 - om)
    c72 = (1 - u) * (50.97 + 54.0 * (a - 0.85))
    c80 = 0.771 + 0.9 * (a - 0.85)
    E = 8760 * 1000 * a / 1e6
    return (cap + c71 + c72 + c80) / E * (108.89 / 108.74)


def new(s):
    d = drivers(s); u, c, a, om, indf = d["u"], d["c"], d["a"], d["om"], d["indf"]
    overnight = (6001.28 - 4312.15 * u) + indf * (5396.31 - 4146.30 * u) * (c / 6) * 1.015
    cap = 0.0805864 * overnight * (1 + fidc(c))
    c71 = (70.153 + 1.4457 * (c - 2)) * (1 - om)
    c72 = (1 - u) * (50.9606 + 53.944 * (a - 0.85) + (6.31 if a >= 0.969379 else 0))
    c80 = 0.7706 + 0.9066 * (a - 0.85)
    E = 8760 * 1000 * a / 1e6
    return (cap + c71 + c72 + c80) / E * 1.0014319


def band(zone, cf_max):
    out = {}
    for k, (_m, z) in ZONES.items():
        lo, hi = (0.0, z[0]) if zone == "green" else (z[0], z[1])
        out[k] = (lo, hi)
    return out


def sample(zone, cf_max, n=7):
    b = band(zone, cf_max)
    grids = []
    for k in KEYS:
        lo, hi = b[k]
        if k == "cf":
            hi = min(hi, cf_max)
        grids.append([lo + (hi - lo) * i / (n - 1) for i in range(n)])
    return [dict(zip(KEYS, combo)) for combo in itertools.product(*grids)]


print(f"{'zone':<8}{'stat':<10}{'old':>10}{'new':>10}{'delta':>10}")
print("-" * 48)
for zone in ("green", "amber"):
    pts = sample(zone, 11.5)
    o = [old(p) for p in pts]; nw = [new(p) for p in pts]
    for lbl, fn in (("median", st.median), ("mean", st.fmean),
                    ("min", min), ("max", max)):
        print(f"{zone:<8}{lbl:<10}{fn(o):>10.2f}{fn(nw):>10.2f}{fn(nw)-fn(o):>+10.2f}")
    mid = {k: (band(zone, 11.5)[k][0] + min(band(zone, 11.5)[k][1],
               11.5 if k == 'cf' else 1e9)) / 2 for k in KEYS}
    print(f"{zone:<8}{'midpoint':<10}{old(mid):>10.2f}{new(mid):>10.2f}"
          f"{new(mid)-old(mid):>+10.2f}")
    print("-" * 48)

PRESETS = {
    "reasonable": dict(reactor=25, constr=16.7, cf=5, om=20, site=5),
    "optimistic": dict(reactor=44, constr=41.7, cf=8, om=35, site=10),
    "heroic":     dict(reactor=65, constr=66.7, cf=11, om=50, site=14),
    "all-max":    dict(reactor=80, constr=67, cf=11.5, om=55, site=15),
}
print(f"{'preset':<12}{'old':>10}{'new':>10}{'delta':>10}")
print("-" * 42)
for k, v in PRESETS.items():
    print(f"{k:<12}{old(v):>10.2f}{new(v):>10.2f}{new(v)-old(v):>+10.2f}")
