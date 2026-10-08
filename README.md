# audit-horizon-core

**Verification code for the paper**
*Self-audit horizons of finitely axiomatized theories: non-accumulation of finite reflection and the cost of external verification*
by Hazime Sendo (independent researcher, Japan).

 [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23238485.svg)](https://doi.org/10.5281/zenodo.23238485)
[![verify](https://github.com/Hazime-Sendo/audit-horizon-core/actions/workflows/verify.yml/badge.svg)](https://github.com/Hazime-Sendo/audit-horizon-core/actions/workflows/verify.yml)

This repository reproduces every numerical claim of the paper from first principles and compares each value with the value printed in the paper. The paper itself is not part of this repository.

## Repository layout

```
audit-horizon-core/
├── src/audit_horizon/          the verification code (standard library only)
│   ├── languages.py            formula counts and singularity analysis for L(c,k,m)
│   ├── saturation.py           linear-time saturation audit for fragments of Robinson's Q
│   ├── finite_models.py        exhaustive check that {Q1, Q2} has no small model
│   ├── horizons.py             external horizons of saturation audits
│   ├── verify.py               runs every check and compares with the paper
│   └── cli.py                  command-line interface
├── data/
│   └── paper_values.json       the values printed in the paper (reference for the checks)
├── scripts/
│   └── reproduce_all.py        entry point: full reproduction and reproducibility log
├── results/                    reference output of a full run, incl. reproducibility_log.md
├── tests/                      unit tests (pytest)
├── requirements.txt            runtime dependencies (none)
├── requirements-dev.txt        optional: pytest for the unit tests
├── pyproject.toml              optional installation as a package
├── CITATION.cff, .zenodo.json  citation and archive metadata
└── LICENSE                     Apache License 2.0
```

## Requirements

- Python 3.8 or later
- No third-party packages (see `requirements.txt`)
- About 1.5 GB of memory for the full run

## How to reproduce

From the root of a clone, without installing anything:

```bash
python3 scripts/reproduce_all.py --quick   # smoke test, a few seconds (results/ is left untouched)
python3 scripts/reproduce_all.py           # full run, about 1 minute
python3 scripts/reproduce_all.py --out DIR # full run into DIR (results/ is left untouched)
python3 scripts/reproduce_all.py --help    # options
```

The full run prints one `PASS`/`FAIL` line per numerical claim, writes its output to `results/`, writes `results/reproducibility_log.md`, and ends with `ALL CHECKS PASSED`.

Unit tests (optional):

```bash
python3 -m pip install -r requirements-dev.txt
PYTHONPATH=src python3 -m pytest
```

Optional installation as a command-line tool:

```bash
python3 -m pip install .
audit-horizon verify --quick
audit-horizon language LQ          # case, base, exponent and constant of a language L(c,k,m)
audit-horizon audit L1 16          # saturation audit of depth <= 16
audit-horizon horizon 1e9 LQ       # external horizon for a budget of 10^9 operations
```

## What is verified

| Claim in the paper | Code |
|---|---|
| Trichotomy for L(c,k,m); bases b = 1+√2, 3, 1+2√2 (Prop. 5.2, Thm. 5.3, Ex. 5.5) | `languages.singular_data` |
| Asymptotic constants c_F in closed form, normalized counts and error terms (Table 2, Sect. 6.1) | `languages.report` |
| Divergence of the naive exponent γ = 3/2 for L₂ (the correct exponent is 5/4) | `languages.report` |
| A1 constant and leading-order crossover in L₂ (Remark 5.6) | `languages.crossover_L2` |
| Operation counts 2\|U_n\| + \|Th_n\| ≤ C_n ≤ 2\|U_n\| + 3\|Th_n\| (Lemma 5.1) | `saturation.run` |
| \|U_n\|, \|Th_n\| and the ratios of Table 3 for fragments of Robinson's Q | `saturation.run` |
| Contradiction at width 11 and a refutation of length 26 for the variant with S0 = SS0 | `saturation.refutation` |
| {Q1, Q2} has no model of size ≤ 7 (Sect. 6.2) | `finite_models.check` |

The theorems of Sections 3 and 4 of the paper (internal horizons and horizons of towers of finite reflection) are asymptotic statements whose constants depend on the base theory. They are proved in the paper and are deliberately not evaluated numerically here.

## Reproducibility

`results/reproducibility_log.md` records the Python version, platform, run time, the result of every check and the SHA-256 of every output file of the reference run. All outputs are deterministic except the timing field `microseconds_per_formula`. A GitHub Actions workflow runs the unit tests and the smoke test on Python 3.8 (Ubuntu 22.04) and 3.12 (latest Ubuntu) on every push; the full reproduction can be started from the Actions tab.

## How to cite

Please cite the version archived on Zenodo (via its DOI) together with the paper. A machine-readable citation is in `CITATION.cff`.

## License

Apache License 2.0, see `LICENSE`.

## Contact

Please open an issue in this repository for questions about the code.
