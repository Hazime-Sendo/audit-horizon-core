# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Hazime Sendo
"""Command-line interface: `audit-horizon <command>` or `python -m audit_horizon <command>`."""
import argparse
import json

from . import __version__


def _language(args):
    from .languages import Language
    if args.name:
        return Language.named(args.name)
    return Language(args.c, args.k, args.m)


def main(argv=None):
    p = argparse.ArgumentParser(prog="audit-horizon",
                                description="Verification code for 'Self-audit horizons of finitely axiomatized theories'.")
    p.add_argument("--version", action="version", version="%(prog)s " + __version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("verify", help="reproduce and check every numerical claim of the paper")
    v.add_argument("--quick", action="store_true", help="smoke test, a few seconds")
    v.add_argument("--out", help="directory for the output of the full run (default: a temporary directory)")

    lg = sub.add_parser("language", help="case, base, exponent and constant for a language L(c,k,m)")
    lg.add_argument("name", nargs="?", choices=["L1", "L2", "LQ"], help="a named language")
    lg.add_argument("-c", type=int, default=1, help="number of constants")
    lg.add_argument("-k", type=int, default=1, help="number of unary function symbols")
    lg.add_argument("-m", type=int, default=0, help="number of binary function symbols")

    au = sub.add_parser("audit", help="run the saturation audit for a fragment of Q")
    au.add_argument("lang", choices=["L1", "L2", "LQ"])
    au.add_argument("nmax", type=int)
    au.add_argument("--json", help="write the result to this file")

    hz = sub.add_parser("horizon", help="external horizon of the saturation audit for a budget R")
    hz.add_argument("budget", type=float, help="budget R (number of operations)")
    hz.add_argument("name", nargs="?", choices=["L1", "L2", "LQ"], default="LQ")
    hz.add_argument("-c", type=int, default=1)
    hz.add_argument("-k", type=int, default=1)
    hz.add_argument("-m", type=int, default=None)

    fm = sub.add_parser("finite-models", help="check that {Q1, Q2} has no model of size <= MMAX")
    fm.add_argument("mmax", type=int, nargs="?", default=7)

    args = p.parse_args(argv)

    if args.cmd == "verify":
        from .verify import main as run
        return run(quick=args.quick, out=args.out)

    if args.cmd == "language":
        L = _language(args)
        phi = "---" if L.phi is None else "%+.6f" % L.phi
        print("L(c=%d, k=%d, m=%d): Phi=%s  case (%s)  rho=%.6f  b=%.6f  gamma=%s  c_F=%.6f"
              % (L.c, L.k, L.m, phi, L.case, L.rho, L.base, L.gamma, L.c_F))
        return 0

    if args.cmd == "audit":
        from .saturation import run
        res = run(args.lang, args.nmax)
        if args.json:
            with open(args.json, "w") as fh:
                json.dump(res, fh, indent=1)
        return 0

    if args.cmd == "horizon":
        from .horizons import external_horizon, external_horizon_asymptotic
        from .languages import Language
        L = Language(args.c, args.k, args.m) if args.m is not None else Language.named(args.name)
        g, q = external_horizon(args.budget, L)
        print("budget R=%.3g, language L(%d,%d,%d): audited depth n with %d <= n <= %d "
              "(leading term log_b R = %.2f)" % (args.budget, L.c, L.k, L.m, g, q,
                                                  external_horizon_asymptotic(args.budget, L)))
        return 0

    if args.cmd == "finite-models":
        from .finite_models import check
        rows = check(args.mmax)
        for m, total, found in rows:
            print("domain size %d: %s maps S, models of Q1+Q2: %d" % (m, format(total, ","), found))
        return 0 if all(r[2] == 0 for r in rows) else 1
    return 2
