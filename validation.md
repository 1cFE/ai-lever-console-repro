# Validation — surrogate vs. full costingfe

Model: `costingfe` @ `ac2d1a8`, clean worktree. Anchor: 1 GWe net D-T tokamak, `size_from_power`, availability 0.85, life 30 yr, interest 7%, NOAK, indirect fraction 0.20.


## Result

| case | full model $/MWh | console surrogate | error | refit surrogate | error |
|---|---:|---:|---:|---:|---:|
| baseline | 108.871 | 108.871 | +0.00% | 108.871 | +0.00% |
| green_mid | 92.015 | 92.013 | -0.00% | 92.013 | -0.00% |
| amber_mid | 67.737 | 67.740 | +0.00% | 67.740 | +0.00% |

Worst absolute error: **0.00%** for the shipped console constants, **0.00%** for this package's refit. Across a 432-point sweep of the full five-lever space the worst is 0.030%.


## Lever positions

| case | site | constr | reactor | cf | om |
|---|---:|---:|---:|---:|---:|
| baseline | 0 | 0 | 0 | 0 | 0 |
| green_mid | 2.5 | 8.5 | 12.5 | 2.5 | 10 |
| amber_mid | 7.5 | 25 | 32.5 | 7 | 27.5 |

## Model drivers these map to

| case | indirect_fraction | construction_time_yr | CAS22 mult | availability | om_cost_dt mult |
|---|---:|---:|---:|---:|---:|
| baseline | 0.200 | 6.000 | 1.000 | 0.850 | 1.000 |
| green_mid | 0.175 | 5.490 | 0.875 | 0.875 | 0.900 |
| amber_mid | 0.125 | 4.500 | 0.675 | 0.920 | 0.725 |

## Full-model accounts at each point (M$)

| case | total capital | CAS20 | CAS22 | CAS30 | CAS60 | CAS71 | CAS72 | CAS80 | CAS90 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 8460.83 | 5396.31 | 4146.30 | 1079.26 | 1364.10 | 75.94 | 50.96 | 0.77 | 681.83 |
| green_mid | 7321.67 | 4878.02 | 3628.01 | 781.09 | 1066.59 | 67.66 | 45.82 | 0.79 | 590.03 |
| amber_mid | 5632.33 | 4048.76 | 2798.75 | 379.57 | 647.24 | 53.44 | 36.99 | 0.81 | 453.89 |

## O&M linearity

The console applies the O&M lever as a flat `(1 - om)` on CAS71. In the model the lever reaches CAS71 through `om_cost_dt`; halving it scales CAS71 by 0.500000, so the flat multiplier is exact.
