"""Python port of the AI Lever Console surrogate, line for line.

The console ships this arithmetic as JavaScript (artifact 038598b6).  This
module is a faithful transcription so the validation can compare the *actual
console math* against the full model, not a re-derivation of it.

The JS, for reference:

    const CRF=0.0805864, KCAL=1.0014319, BASE=108.8711;
    function fIDC(c){const i=0.07;return (Math.pow(1+i,c)-1)/(i*c)-1;}
    function cas20of(u){return 5396.31-4146.30*u;}
    function Aof(u){return 6001.28-4312.15*u;}
    function TCadj(u,c,indf){
      const overnight=Aof(u)+indf*cas20of(u)*(c/6)*1.015;
      return overnight*(1+fIDC(c));}
    function buckets(u,c,a,om,indf){
      const cap=CRF*TCadj(u,c,indf), c71=(70.153+1.4457*(c-2))*(1-om);
      const c72=(1-u)*(50.9606+53.944*(a-0.85)+(a>=0.969379?6.3100:0));
      const c80=0.7706+0.9066*(a-0.85);
      const E=8760*1000*a/1e6;
      return {cap:cap/E*KCAL, om:c71/E*KCAL, rep:c72/E*KCAL, fuel:c80/E*KCAL};
    }

The old TC(u,c) linear interpolation it replaces, kept for reference:

    function TC(u,c){const tc6=8462.5-6145.9*u, tc2=6590.6-4754.6*u;
                     return tc2+(tc6-tc2)*(c-2)/4;}
    function TCadj(u,c,indf){const G=cas20of(u)*(c/6)*(1+fIDC(c))*1.015;
                             return TC(u,c)+G*(indf-0.20);}
"""

from __future__ import annotations

import json
import pathlib

HERE = pathlib.Path(__file__).parent

# The live console's constants, in the same shape fit_surrogate.py emits.
CONSOLE = {
    "CRF": 0.0805864,
    "KCAL": 1.0014319,
    "BASE": 108.8711,
    "A_a": 6001.28, "A_b": 4312.15,
    "cas20_a": 5396.31, "cas20_b": 4146.30,
    "c71_a": 70.153, "c71_b": 1.4457,
    "c72_a": 50.9606, "c72_b": 53.944,
    # CAS72 is not continuous: above this capacity factor the plant fits one
    # more in-vessel replacement into its 30-yr life, a discrete +6.31 M$/yr.
    "c72_a_thresh": 0.969379, "c72_step": 6.3100,
    "c80_a": 0.7706, "c80_b": 0.9066,
    "insurance": 1.015,
    "idc_rate": 0.07,
}

# The constants the console shipped before the exact-TC rebuild, kept so
# fit_surrogate.py can still show what the 11 Aug fit produced.
LEGACY = {
    "CRF": 0.08059, "KCAL": 108.89 / 108.74, "BASE": 108.89,
    "tc6_a": 8462.5, "tc6_b": 6145.9,
    "tc2_a": 6590.6, "tc2_b": 4754.6,
    "cas20_a": 5397.5, "cas20_b": 4147.3,
    "c71_a": 70.15, "c71_b": 1.4475,
    "c72_a": 50.97, "c72_b": 54.0,
    "c80_a": 0.771, "c80_b": 0.9,
    "insurance": 1.015, "idc_rate": 0.07,
}


def refit() -> dict:
    """The coefficients fit_surrogate.py derived from this package's own DOE."""
    blob = json.loads(
        (HERE / "surrogate_coefficients.json").read_text(encoding="utf-8"))
    return blob["refit"]


def _f_idc(k: dict, c: float) -> float:
    """costingfe's CAS60 interest-during-construction factor. Nonlinear in c."""
    i = k["idc_rate"]
    return ((1 + i) ** c - 1) / (i * c) - 1


def _cas20(k: dict, u: float) -> float:
    return k["cas20_a"] - k["cas20_b"] * u


def _a_of(k: dict, u: float) -> float:
    """Overnight cost minus the part proportional to the indirect fraction."""
    return k["A_a"] - k["A_b"] * u


def _tc_adj(k: dict, u: float, c: float, indf: float) -> float:
    """Total capital, on the model's own identity rather than an interpolation.

        overnight(u, c, indf) = A(u) + indf * CAS20(u) * (c/6) * insurance
        TC                    = overnight * (1 + f_IDC(c))

    CAS30 is the only account carrying c into overnight (plus the construction
    insurance stacked on it), and CAS60 is exactly f_IDC(c) on the whole
    overnight cost.  Reproduces full costingfe to 0.0000% over the lever ranges,
    where the previous linear-in-c interpolation drifted to +0.71%.
    """
    overnight = _a_of(k, u) + indf * _cas20(k, u) * (c / 6.0) * k["insurance"]
    return overnight * (1 + _f_idc(k, c))


def buckets(k: dict, u: float, c: float, a: float, om: float,
            indf: float, calibrated: bool = True) -> dict:
    """The four LCOE buckets, $/MWh."""
    kcal = k["KCAL"] if calibrated else 1.0
    cap = k["CRF"] * _tc_adj(k, u, c, indf)
    c71 = (k["c71_a"] + k["c71_b"] * (c - 2.0)) * (1.0 - om)
    c72 = (1.0 - u) * (k["c72_a"] + k["c72_b"] * (a - 0.85)
                       + (k["c72_step"] if a >= k["c72_a_thresh"] else 0.0))
    c80 = k["c80_a"] + k["c80_b"] * (a - 0.85)
    e = 8760.0 * 1000.0 * a / 1e6
    return {"cap": cap / e * kcal, "om": c71 / e * kcal,
            "rep": c72 / e * kcal, "fuel": c80 / e * kcal}


def lcoe(k: dict, u: float, c: float, a: float, om: float,
         indf: float, calibrated: bool = True) -> float:
    b = buckets(k, u, c, a, om, indf, calibrated)
    return b["cap"] + b["om"] + b["rep"] + b["fuel"]


def lcoe_raw(k: dict, u: float, c: float, a: float, om: float,
             indf: float) -> float:
    """Uncalibrated -- what the fitted forms give before KCAL is applied."""
    return lcoe(k, u, c, a, om, indf, calibrated=False)


# ------------------------------------------------------------- lever mapping
# Console slider value -> surrogate driver.  Mirrors lcoeOf() in the artifact.
def drivers(site: float, constr: float, reactor: float,
            cf: float, om: float) -> dict:
    """Slider positions (in the console's own units) -> model drivers."""
    return {
        "indf": (20.0 - site) / 100.0,      # site: percentage points off 20%
        "c": 6.0 * (1.0 - constr / 100.0),  # constr: % faster than 6 yr
        "u": reactor / 100.0,               # reactor: % of CAS22 cut
        "a": 0.85 + cf / 100.0,             # cf: availability points added
        "om": om / 100.0,                   # om: % of CAS71 cut
    }


def lcoe_from_sliders(k: dict, site: float, constr: float, reactor: float,
                      cf: float, om: float) -> float:
    d = drivers(site, constr, reactor, cf, om)
    return lcoe(k, d["u"], d["c"], d["a"], d["om"], d["indf"])
