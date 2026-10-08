# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Hazime Sendo
"""
External self-audit horizons of saturation audits (Section 5 of the paper).

The horizon of the saturation audit is computed exactly for a language
L(c,k,m), from the exact formula counts and the operation bounds
2|U_n| <= C_n <= 5|U_n| of Lemma 5.1.

The internal horizons (Proposition 3.2) and the horizons of towers of finite
reflection (Theorem 4.8, Corollary 4.9) are asymptotic theorems whose
constants depend on the base theory and on the formalization. They are proved
in the paper and are deliberately not evaluated here: a numerical evaluation
with chosen constants would not verify them.
"""
import math

from .languages import Language


def external_horizon(R, language, nmax=400):
    """Horizon of the linear-time saturation audit with budget R (Lemma 5.1).

    Returns (guaranteed, possible): the largest n with 5|U_n| <= R (the audit
    of depth n certainly fits in the budget) and the largest n with
    2|U_n| <= R (no audit of larger depth can fit).  |U_n| is computed
    exactly from the formula counts of `language` (a Language or a name)."""
    if isinstance(language, str):
        language = Language.named(language)
    f = language.formula_counts(nmax)
    guaranteed = possible = 0
    total = 0
    for n in range(1, nmax + 1):
        total += f[n]
        if 5 * total <= R:
            guaranteed = n
        if 2 * total <= R:
            possible = n
        else:
            break
    else:
        raise ValueError("budget too large for nmax=%d; increase nmax" % nmax)
    return guaranteed, possible


def external_horizon_asymptotic(R, language):
    """Leading term log_b R of Corollary 5.4."""
    if isinstance(language, str):
        language = Language.named(language)
    return math.log(R) / math.log(language.base)


def symbols_per_decade(language):
    """Extension of the external horizon when the budget grows by a factor 10."""
    if isinstance(language, str):
        language = Language.named(language)
    return math.log(10) / math.log(language.base)
