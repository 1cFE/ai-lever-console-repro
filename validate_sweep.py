"""Reproducible sampled comparison with the pinned full cost model.

This checks numerical agreement, not plant accuracy or benefits from AI.
It is a finite grid, not an error bound over every possible slider setting.
Run with the same pinned model and dependencies as validate.py.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
import statistics
import subprocess

import costingfe
import surrogate
import validate

HERE = Path(__file__).resolve().parent
MODEL_COMMIT = "ac2d1a8d07d0d9cbe5f0ca6e88db2fcbf477c093"
GRID = {
    "site": [0.0, 7.5, 15.0],
    "constr": [0.0, 67.0 / 3, 134.0 / 3, 67.0],
    "reactor": [0.0, 40.0, 80.0],
    "cf": [0.0, 11.5 / 3, 23.0 / 3, 11.5],
    "om": [0.0, 27.5, 55.0],
}


def main() -> None:
    model_dir = Path(costingfe.__file__).resolve().parent
    commit = subprocess.check_output(
        ["git", "-C", str(model_dir), "rev-parse", "HEAD"], text=True
    ).strip()
    dirty = subprocess.check_output(
        ["git", "-C", str(model_dir), "status", "--porcelain", "--untracked-files=no"],
        text=True,
    ).strip()
    if commit != MODEL_COMMIT or dirty:
        raise SystemExit("Use a clean cost-model checkout at " + MODEL_COMMIT)

    rows = []
    for values in itertools.product(*GRID.values()):
        sliders = dict(zip(GRID, values))
        full = validate.full_model(sliders)["lcoe"]
        approx = surrogate.lcoe_from_sliders(surrogate.CONSOLE, **sliders)
        rows.append({
            "sliders": sliders,
            "full_model_usd_per_mwh": full,
            "surrogate_usd_per_mwh": approx,
            "relative_error_percent": (approx / full - 1) * 100,
        })
        if len(rows) % 72 == 0:
            print(f"Compared {len(rows)} of 432 points", flush=True)

    worst = max(rows, key=lambda row: abs(row["relative_error_percent"]))
    result = {
        "model_commit": commit,
        "surrogate_sha256": hashlib.sha256((HERE / "surrogate.py").read_bytes()).hexdigest(),
        "scope": "Numerical comparison at sampled points, not an engineering validation or a continuous error bound.",
        "grid_slider_units": GRID,
        "summary": {
            "point_count": len(rows),
            "maximum_absolute_relative_error_percent": abs(worst["relative_error_percent"]),
            "median_absolute_relative_error_percent": statistics.median(
                abs(row["relative_error_percent"]) for row in rows
            ),
            "maximum_absolute_difference_usd_per_mwh": max(
                abs(row["surrogate_usd_per_mwh"] - row["full_model_usd_per_mwh"])
                for row in rows
            ),
            "worst_relative_error_point": worst,
        },
        "points": rows,
    }
    (HERE / "sweep_validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["summary"], indent=2))
    print("Wrote sweep_validation.json")


if __name__ == "__main__":
    main()
