# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Hazime Sendo
"""audit_horizon: verification code for the paper

  H. Sendo, "Self-audit horizons of finitely axiomatized theories:
  non-accumulation of finite reflection and the cost of external verification".

Modules
  languages      formula counts and singularity analysis for L(c,k,m)
  saturation     linear-time saturation audit for fragments of Robinson's Q
  horizons       external self-audit horizons of saturation audits
  finite_models  exhaustive check that {Q1, Q2} has no small model
  verify         reproduce and check every numerical claim of the paper

Quick start
  >>> from audit_horizon import Language
  >>> L = Language.named("LQ")          # language of Robinson's Q
  >>> L.case, round(L.base, 6)
  ('iii', 3.828427)
"""
from .languages import Language, LANGUAGES
from .horizons import (external_horizon, external_horizon_asymptotic,
                       symbols_per_decade)

__version__ = "1.0.0"
__all__ = ["Language", "LANGUAGES", "external_horizon", "external_horizon_asymptotic",
           "symbols_per_decade", "__version__"]
