# Reproducibility log

| Item | Value |
|---|---|
| audit-horizon version | 1.0.0 |
| Run started (UTC) | 2026-10-08 11:07:47 |
| Wall-clock time | 67 s |
| Python | 3.11.15 (CPython) |
| Platform | Linux 6.18.44-fc-v80 (x86_64) |
| Third-party packages | none |
| Reference values | data/paper_values.json (sha256 261abdb774a15831…) |
| Result | ALL CHECKS PASSED (26/26 checks) |

## Checks

```
[PASS] no model of size <= 7
[PASS] L1: case (i), b=2.414214, c_F=0.521243
[PASS] L2: case (ii), b=3.000000, c_F=0.379710
[PASS] LQ: case (iii), b=3.828427, c_F=0.189484
[PASS] Table 2 ('L1', 400): 0.521602
[PASS] Table 2 ('L1', 3000): 0.521290
[PASS] Table 2 ('L2', 400): 0.370237
[PASS] Table 2 ('L2', 3000): 0.376513
[PASS] Table 2 ('LQ', 400): 0.188640
[PASS] Table 2 ('LQ', 2500): 0.189349
[PASS] L1: Lemma 5.1 bounds hold for all n <= 22
[PASS] L1: Con(n) certified for all n <= 22
[PASS] Table 3 L1 n=22: |U|=2,457,228 |Th|=15,504 C/U=2.013 (C-2U)/Th=2.03
[PASS] L1 + S0=SS0: contradiction at width 11, refutation of length 26 with 4 lines
[PASS] L1: corrected ratio C_n/C_(n-1) = 2.400 vs b = 2.414 (within 1%)
[PASS] L2: Lemma 5.1 bounds hold for all n <= 18
[PASS] L2: Con(n) certified for all n <= 18
[PASS] Table 3 L2 n=18: |U|=5,148,468 |Th|=71,382 C/U=2.015 (C-2U)/Th=1.06
[PASS] Remark 5.6: 66,706 of the 71,382 elements of Th_18 are ground instances of not(0 = Sx)
[PASS] L2 + S0=SS0: contradiction at width 11, refutation of length 26 with 4 lines
[PASS] L2: corrected ratio C_n/C_(n-1) = 3.015 vs b = 3.000 (within 1%)
[PASS] LQ: Lemma 5.1 bounds hold for all n <= 14
[PASS] LQ: Con(n) certified for all n <= 14
[PASS] Table 3 LQ n=14: |U|=651,252 |Th|=18,883 C/U=2.029 (C-2U)/Th=1.01
[PASS] LQ + S0=SS0: contradiction at width 11, refutation of length 26 with 4 lines
[PASS] LQ: corrected ratio C_n/C_(n-1) = 3.850 vs b = 3.828 (within 1%)
```

## Output files (sha256)

Timing fields (`microseconds_per_formula`) differ between runs; all other content is deterministic.

| File (in the output directory) | sha256 |
|---|---|
| finite_model_check.json | `cae000d8701012fcc90ec461586590888848eb098a5c4271da9ab5ffd4c16814` |
| gf_analysis.txt | `d9f7ff9d4ca0147821513ce916f274a134ad9552c2ed211303d4b444719b0156` |
| saturation_L1.json | `60787c71b1612522cdba7db054fc88452b959bcc307fc9953cb0f82aa146861a` |
| saturation_L2.json | `1dee5fbdeca48b130d0956f7adf501cf75b80ab1ee4666037a2fe0264009a10c` |
| saturation_LQ.json | `abed6716d77bcbf1ab8baf1a52c71a131973d019ca925001ace60a99543e57dd` |
| table2_constants.json | `131732310be5b4f1bb3b1d8cec1a4aa4f1fbf5d4f2de8e31a9d5ad25e8af7dc8` |
