# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Hazime Sendo
"""
Reproduce every numerical claim of the paper from a clone of this repository
(no installation needed) and write a reproducibility log.

    python3 scripts/reproduce_all.py --quick   # smoke test, a few seconds
    python3 scripts/reproduce_all.py           # full run, about 1 minute
    python3 scripts/reproduce_all.py --out DIR # full run, output to DIR
    python3 scripts/reproduce_all.py --help

The full run writes its output to results/ and the log to
results/reproducibility_log.md. The quick run writes to a temporary
directory and leaves results/ untouched.
"""
import argparse
import contextlib
import datetime
import hashlib
import io
import os
import platform
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from audit_horizon import __version__          # noqa: E402
from audit_horizon.verify import main as verify  # noqa: E402

DATA = os.path.join(ROOT, "data", "paper_values.json")
RESULTS = os.path.join(ROOT, "results")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description="Reproduce every numerical claim of the paper and compare it "
                    "with the values printed there (data/paper_values.json).")
    ap.add_argument("--quick", action="store_true",
                    help="smoke test with small sizes (a few seconds); writes to a "
                         "temporary directory and never touches results/")
    ap.add_argument("--out", metavar="DIR", default=RESULTS,
                    help="output directory of the full run (default: results/ of "
                         "this repository, which holds the reference outputs)")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.quick:
        return verify(quick=True, paper_values=DATA)

    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    started = datetime.datetime.now(datetime.timezone.utc)
    t0 = time.time()
    buf = io.StringIO()

    class Tee(io.TextIOBase):
        def write(self, s):
            sys.__stdout__.write(s)
            buf.write(s)
            return len(s)

    with contextlib.redirect_stdout(Tee()):
        status = verify(quick=False, out=out, paper_values=DATA)
    elapsed = time.time() - t0

    lines = buf.getvalue().splitlines()
    checks = [l for l in lines if l.startswith("[PASS]") or l.startswith("[FAIL]")]
    n_pass = sum(l.startswith("[PASS]") for l in checks)
    outputs = sorted(f for f in os.listdir(out)
                     if f.endswith((".json", ".txt")) and not f.startswith("reproducibility"))
    log = [
        "# Reproducibility log",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| audit-horizon version | {__version__} |",
        f"| Run started (UTC) | {started.strftime('%Y-%m-%d %H:%M:%S')} |",
        f"| Wall-clock time | {elapsed:.0f} s |",
        f"| Python | {platform.python_version()} ({platform.python_implementation()}) |",
        f"| Platform | {platform.system()} {platform.release()} ({platform.machine()}) |",
        "| Third-party packages | none |",
        f"| Reference values | data/paper_values.json (sha256 {sha256(DATA)[:16]}…) |",
        f"| Result | {'ALL CHECKS PASSED' if status == 0 else 'SOME CHECKS FAILED'} ({n_pass}/{len(checks)} checks) |",
        "",
        "## Checks",
        "",
        "```",
        *checks,
        "```",
        "",
        "## Output files (sha256)",
        "",
        "Timing fields (`microseconds_per_formula`) differ between runs; all other content is deterministic.",
        "",
        "| File (in the output directory) | sha256 |",
        "|---|---|",
        *[f"| {f} | `{sha256(os.path.join(out, f))}` |" for f in outputs],
        "",
    ]
    with open(os.path.join(out, "reproducibility_log.md"), "w") as fh:
        fh.write("\n".join(log))
    print(f"Reproducibility log written to {os.path.join(out, 'reproducibility_log.md')}")
    return status


if __name__ == "__main__":
    sys.exit(main())
