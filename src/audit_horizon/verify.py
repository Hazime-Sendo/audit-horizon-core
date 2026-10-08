# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Hazime Sendo
"""
Reproduce every numerical claim of the paper and compare it with the values
printed there.

    audit-horizon verify              # full run (about 1 minute, < 2 GB RAM)
    audit-horizon verify --quick      # smoke test (a few seconds)
    audit-horizon verify --out DIR    # write the output of the full run to DIR

The quick run writes to a temporary directory. Standard library only.
"""
import json
import math
import os
import tempfile
import time

from . import finite_models as finite_model_check
from . import languages as gf_analysis
from . import saturation as saturation_audit

# Values as printed in the paper. The reference copy is data/paper_values.json;
# the same values are embedded here so that an installed package works without
# the repository. tests/ checks that both copies agree.
PAPER_EMBEDDED = {
    "c_F": {"L1": 0.521243, "L2": 0.379710, "LQ": 0.189484},
    "b": {"L1": 1 + math.sqrt(2), "L2": 3.0, "LQ": 1 + 2 * math.sqrt(2)},
    "table2": {("L1", 400): 0.521602, ("L1", 3000): 0.521290,
               ("L2", 400): 0.370237, ("L2", 3000): 0.376513,
               ("LQ", 400): 0.188640, ("LQ", 2500): 0.189349},
    "table3": {"L1": (22, 2457228, 15504, 2.013, 2.03),
               "L2": (18, 5148468, 71382, 2.015, 1.06),
               "LQ": (14, 651252, 18883, 2.029, 1.01)},
    "remark_5_6": (66706, 71382),
    "refutation": (11, 26, 4),
}

_B = {"1+sqrt(2)": 1 + math.sqrt(2), "3": 3.0, "1+2*sqrt(2)": 1 + 2 * math.sqrt(2)}


def load_paper_values(path):
    """Read data/paper_values.json into the internal format."""
    with open(path) as fh:
        d = json.load(fh)
    return {
        "c_F": {k: v for k, v in d["c_F"].items() if not k.startswith("_")},
        "b": {k: _B[v] for k, v in d["b"].items() if not k.startswith("_")},
        "table2": {(r["language"], r["n"]): r["value"] for r in d["table2"]["rows"]},
        "table3": {r["language"]: (r["n"], r["U"], r["Th"], r["C_over_U"], r["excess_over_Th"])
                   for r in d["table3"]["rows"]},
        "remark_5_6": (d["remark_5_6"]["Q2_instances_in_Th_18_L2"], d["remark_5_6"]["Th_18_L2"]),
        "refutation": (d["refutation"]["width"], d["refutation"]["length"], d["refutation"]["lines"]),
    }


def check(label, ok):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    return ok


def main(quick=False, out=None, paper_values=None):
    """Run all checks; return 0 if every check passes, 1 otherwise.

    paper_values: path to data/paper_values.json (default: the embedded copy)."""
    PAPER = load_paper_values(paper_values) if paper_values else PAPER_EMBEDDED
    print("Reference values: " + (paper_values or "embedded copy"))
    if quick or out is None:  # never overwrite reference results by accident
        RESULTS = tempfile.mkdtemp(prefix="audit_horizon_")
    else:
        RESULTS = out
    os.makedirs(RESULTS, exist_ok=True)
    t0 = time.time()
    all_ok = True

    print("== 1. No finite models of {Q1, Q2} (Section 6.2) ==")
    rows = finite_model_check.check(5 if quick else 7)
    all_ok &= check("no model of size <= %d" % rows[-1][0], all(r[2] == 0 for r in rows))
    with open(os.path.join(RESULTS, "finite_model_check.json"), "w") as fh:
        json.dump([dict(domain_size=m, maps=t, models=f) for m, t, f in rows], fh, indent=1)

    print("\n== 2. Singularity analysis (Proposition 5.2, Theorem 5.3, Table 2) ==")
    for name, (c, k, m) in gf_analysis.LANGUAGES.items():
        sd = gf_analysis.singular_data(c, k, m)
        all_ok &= check(f"{name}: case ({sd['case']}), b={sd['b']:.6f}, c_F={sd['c_F']:.6f}",
                        abs(sd["b"] - PAPER["b"][name]) < 1e-9 and abs(sd["c_F"] - PAPER["c_F"][name]) < 5e-7)
    if quick:
        f = gf_analysis.formula_counts(400, *gf_analysis.LANGUAGES["L1"])
        sd = gf_analysis.singular_data(*gf_analysis.LANGUAGES["L1"])
        v = gf_analysis.normalized(f, 400, sd["rho"], sd["gamma"])
        all_ok &= check(f"L1 n=400 normalized count {v:.6f}", abs(v - PAPER["table2"][("L1", 400)]) < 5e-7)
    else:
        text, table = gf_analysis.report()
        with open(os.path.join(RESULTS, "gf_analysis.txt"), "w") as fh:
            fh.write(text + "\n")
        with open(os.path.join(RESULTS, "table2_constants.json"), "w") as fh:
            json.dump(table, fh, indent=1)
        for row in table:
            key = (row["language"], row["n"])
            if key in PAPER["table2"]:
                all_ok &= check(f"Table 2 {key}: {row['value']:.6f}",
                                abs(row["value"] - PAPER["table2"][key]) < 5e-7)

    print("\n== 3. Saturation audits (Lemma 5.1, Table 3) ==")
    sizes = {"L1": 14, "L2": 12, "LQ": 11} if quick else {"L1": 22, "L2": 18, "LQ": 14}
    for lang, nmax in sizes.items():
        res = saturation_audit.run(lang, nmax, verbose=False)
        with open(os.path.join(RESULTS, f"saturation_{lang}.json"), "w") as fh:
            json.dump(res, fh, indent=1)
        all_ok &= check(f"{lang}: Lemma 5.1 bounds hold for all n <= {nmax}",
                        all(r["lemma_5_1_holds"] for r in res["rows"]))
        all_ok &= check(f"{lang}: Con(n) certified for all n <= {nmax}",
                        all(r["consistent"] for r in res["rows"]))
        last = res["rows"][-1]
        if not quick:
            n, U, Th, cu, ex = PAPER["table3"][lang]
            all_ok &= check(f"Table 3 {lang} n={n}: |U|={last['U']:,} |Th|={last['Th']:,} "
                            f"C/U={last['C_over_U']:.3f} (C-2U)/Th={last['excess_over_Th']:.2f}",
                            last["n"] == n and last["U"] == U and last["Th"] == Th
                            and round(last["C_over_U"], 3) == cu and round(last["excess_over_Th"], 2) == ex)
        if not quick and lang == "L2":
            all_ok &= check(f"Remark 5.6: {last['negations']:,} of the {last['Th']:,} elements of Th_18 are "
                            "ground instances of not(0 = Sx)", (last["negations"], last["Th"]) == PAPER["remark_5_6"])
        iv = res["inconsistent_variant"] or dict(width=None, refutation_length=None, refutation_lines=None)
        all_ok &= check(f"{lang} + S0=SS0: contradiction at width {iv['width']}, refutation of length "
                        f"{iv['refutation_length']} with {iv['refutation_lines']} lines",
                        (iv["width"], iv["refutation_length"], iv["refutation_lines"]) == PAPER["refutation"])
        if not quick:
            a, c = res["rows"][-2], res["rows"][-1]
            g = gf_analysis.singular_data(*gf_analysis.LANGUAGES[lang])["gamma"]
            b = PAPER["b"][lang]
            corr = c["C"] / a["C"] * (c["n"] / (c["n"] - 1)) ** g
            all_ok &= check(f"{lang}: corrected ratio C_n/C_(n-1) = {corr:.3f} vs b = {b:.3f} (within 1%)",
                            abs(corr - b) / b < 0.01)

    print(f"\nOutput written to {RESULTS}")
    print(f"Total time {time.time() - t0:.0f}s. {'ALL CHECKS PASSED' if all_ok else 'SOME CHECKS FAILED'}")
    return 0 if all_ok else 1


