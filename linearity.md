# Held-out linearity tests

Each form is fit from the DOE endpoints only; interior points are held out. A form is *exact* if the held-out error is zero.


## Reactor capital — total capital vs `u`

Fit from `u=0` and `u=1`. The CAS22 override is a pure cost injection: it does not resize the machine, so every downstream account moves linearly with it.

| u | CAS22 | CAS20 | CAS60 | TC | predicted | error |
|---:|---:|---:|---:|---:|---:|---:|
| 0.00 | 4146.30 | 5396.31 | 1364.10 | 8460.83 | 8460.83 | +0.0000% |
| 0.20 | 3317.04 | 4567.05 | 1165.97 | 7231.93 | 7231.93 | -0.0000% |
| 0.40 | 2487.78 | 3737.79 | 967.84 | 6003.03 | 6003.03 | +0.0000% |
| 0.60 | 1658.52 | 2908.53 | 769.71 | 4774.13 | 4774.13 | +0.0000% |
| 0.80 | 829.26 | 2079.27 | 571.58 | 3545.23 | 3545.23 | +0.0000% |
| 1.00 | 0.00 | 1250.01 | 373.45 | 2316.33 | 2316.33 | -0.0000% |

Worst held-out error **0.0000%** — exact. Measuring the slope at the unphysical `u=1` therefore gives the same slope as measuring it anywhere inside the console's 0–80% range. P2/P4 read as nonsense but cost no accuracy.


## Construction time — total capital vs `c`

The surrogate straight-lines `TC` between `c=2` and `c=6`. The true response is convex, because CAS60 interest-during-construction is nonlinear in `c`. Pinned at both ends, worst in the middle — where the console's zones sit.

| c (yr) | CAS30 | CAS60 | TC | linear interp | error |
|---:|---:|---:|---:|---:|---:|
| 2.00 | 359.75 | 222.83 | 6589.26 | 6589.26 | +0.0000% |
| 3.00 | 539.63 | 469.13 | 7018.13 | 7057.15 | +0.5559% |
| 4.00 | 719.51 | 740.38 | 7471.96 | 7525.04 | +0.7104% |
| 4.50 | 809.45 | 885.85 | 7708.71 | 7758.99 | +0.6522% |
| 5.00 | 899.39 | 1038.15 | 7952.30 | 7992.94 | +0.5110% |
| 5.49 | 987.52 | 1194.23 | 8197.85 | 8222.21 | +0.2971% |
| 6.00 | 1079.26 | 1364.10 | 8460.83 | 8460.83 | +0.0000% |

Worst held-out error **0.710%**. This is the form the console shipped until it was rebuilt on the model's own identity, `TC = overnight x (1 + f_IDC(c))`, which is exact. The table is kept as the evidence for why it was changed: the drift peaks in the middle, exactly where the sliders sit.


## Capacity factor — CAS72 vs availability

CAS72 is **not continuous**. At a = 0.969379 one more in-vessel replacement fits into the 30-yr life and the account jumps +6.31 M$/yr (+11%). That threshold sits *inside* the console's cf lever range, which reaches 0.97, so the surrogate carries the step explicitly; a straight line through it is wrong by ~1% of LCOE at the top of the lever.

| a | CAS72 | predicted | error |
|---:|---:|---:|---:|
| 0.850 | 50.9606 | 50.9606 | +0.0000% |
| 0.875 | 52.3605 | 52.3092 | -0.0980% |
| 0.900 | 53.7257 | 53.6579 | -0.1263% |
| 0.920 | 54.7933 | 54.7367 | -0.1033% |
| 0.950 | 56.3551 | 56.3551 | +0.0000% |
| 0.960 | 56.8653 | 56.8945 | +0.0514% |
| 0.965 | 57.1184 | 57.1642 | +0.0801% |
| 0.969 | 63.7094 | 63.7116 | +0.0033% |
| 0.970 | 63.7476 | 63.7439 | -0.0058% |

Worst held-out error **0.1263%**.
