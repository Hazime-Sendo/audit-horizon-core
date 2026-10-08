# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Hazime Sendo
"""Exhaustive check that {Sx=Sy -> x=y, not 0=Sx} has no model of size <= MMAX.
Interpret 0 as element 0 and S as an arbitrary map on {0,...,m-1}."""
import sys
from itertools import product

def check(mmax):
    rows = []
    for m in range(1, mmax + 1):
        found = sum(1 for S in product(range(m), repeat=m) if len(set(S)) == m and 0 not in S)
        rows.append((m, m ** m, found))
    return rows

