# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Hazime Sendo
"""Fast tests (a few seconds). The full comparison with the paper is `audit-horizon verify`."""
import math

import pytest

import json
import os

from audit_horizon import Language, external_horizon, symbols_per_decade
from audit_horizon.finite_models import check as finite_check
from audit_horizon.saturation import run as audit


@pytest.mark.parametrize("name,case,b,gamma,cF", [
    ("L1", "i", 1 + math.sqrt(2), 1.5, 0.521243),
    ("L2", "ii", 3.0, 1.25, 0.379710),
    ("LQ", "iii", 1 + 2 * math.sqrt(2), 1.5, 0.189484),
])
def test_trichotomy_and_constants(name, case, b, gamma, cF):
    L = Language.named(name)
    assert L.case == case
    assert abs(L.base - b) < 1e-9
    assert L.gamma == gamma
    assert abs(L.c_F - cF) < 5e-7


def test_propositional_base():
    from audit_horizon.languages import propositional_counts
    f = propositional_counts(400, 2)
    ratio = f[400] / f[399] * (400 / 399) ** 1.5
    assert abs(ratio - (1 + 2 * math.sqrt(2))) < 1e-3


def test_exact_counts_match_table2_L1():
    from audit_horizon.languages import normalized
    L = Language.named("L1")
    v = normalized(L.formula_counts(400), 400, L.rho, L.gamma)
    assert abs(v - 0.521602) < 5e-7


def test_no_small_finite_model():
    assert all(found == 0 for _, _, found in finite_check(6))


@pytest.mark.parametrize("lang,nmax", [("L1", 13), ("L2", 12), ("LQ", 11)])
def test_saturation_audit(lang, nmax):
    res = audit(lang, nmax, verbose=False)
    assert all(r["lemma_5_1_holds"] and r["consistent"] for r in res["rows"])
    iv = res["inconsistent_variant"]
    assert (iv["width"], iv["refutation_length"], iv["refutation_lines"]) == (11, 26, 4)


def test_reference_values_match_embedded_copy():
    from audit_horizon.verify import PAPER_EMBEDDED, load_paper_values
    path = os.path.join(os.path.dirname(__file__), "..", "data", "paper_values.json")
    assert load_paper_values(path) == PAPER_EMBEDDED


def test_external_horizon():
    g, q = external_horizon(1e6, "LQ")
    assert 1 <= g <= q
    assert abs(symbols_per_decade("LQ") - 1.72) < 0.01
