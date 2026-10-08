# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Hazime Sendo
"""
Generating-function analysis for saturation audits (Section 5 of the paper).

Language L(c, k, m): c constants, k unary and m binary function symbols,
equality as the only predicate, connectives "not" (unary) and "->" (binary),
Polish notation, length = number of symbols.

    T = c z + k z T + m z T^2        (terms)
    A = z T^2                        (atomic formulas t = s)
    F = A + z F + z F^2              (formulas)
    Delta(z) = (1 - z)^2 - 4 z A(z),  F = ((1 - z) - sqrt(Delta)) / (2 z)

This module computes
  * exact counts f(n) = [z^n] F(z) with Python integers,
  * the dominant singularity rho, the base b = 1/rho and the case (i)/(ii)/(iii)
    of Proposition 5.2 (trichotomy),
  * the constants c_F of Theorem 5.3 in closed form,
  * the numerical checks reported in Table 2 of the paper.

Standard library only.
"""
import math
from dataclasses import dataclass

LANGUAGES = {
    "L1": (1, 1, 0),   # {0, S}
    "L2": (1, 1, 1),   # {0, S, +}
    "LQ": (1, 1, 2),   # {0, S, +, *}  (language of Robinson's Q)
}


# ---------------------------------------------------------------- exact counts
def term_counts(nmax, c, k, m):
    t = [0] * (nmax + 1)
    for s in range(1, nmax + 1):
        v = c if s == 1 else 0
        if s >= 2:
            v += k * t[s - 1]
        if m:
            v += m * sum(t[i] * t[s - 1 - i] for i in range(1, s - 1))
        t[s] = v
    return t


def formula_counts(nmax, c, k, m, atoms=None):
    """f(s) for s = 0..nmax. If `atoms` is given (list), it replaces A."""
    if atoms is None:
        t = term_counts(nmax, c, k, m)
        atoms = [0] * (nmax + 1)
        for s in range(3, nmax + 1):
            atoms[s] = sum(t[i] * t[s - 1 - i] for i in range(1, s - 1))
    f = [0] * (nmax + 1)
    for s in range(1, nmax + 1):
        f[s] = atoms[s] + (f[s - 1] if s >= 2 else 0) \
               + sum(f[i] * f[s - 1 - i] for i in range(1, s - 1))
    return f


def propositional_counts(nmax, a):
    atoms = [0] * (nmax + 1)
    atoms[1] = a
    return formula_counts(nmax, 0, 0, 0, atoms=atoms)


def log_int(v):
    """Natural logarithm of a (possibly huge) positive integer."""
    if v < 1e300:
        return math.log(v)
    shift = v.bit_length() - 64
    return math.log(v >> shift) + shift * math.log(2)


# ------------------------------------------------------------ analytic objects
def T_value(z, c, k, m):
    if m == 0:
        return c * z / (1 - k * z)
    d = (1 - k * z) ** 2 - 4 * m * c * z * z
    return ((1 - k * z) - math.sqrt(d)) / (2 * m * z)


def T_prime(z, c, k, m):
    t = T_value(z, c, k, m)
    return (c + k * t + m * t * t) / (1 - k * z - 2 * m * z * t)


def A_value(z, c, k, m):
    return z * T_value(z, c, k, m) ** 2


def A_prime(z, c, k, m):
    t = T_value(z, c, k, m)
    return t * t + 2 * z * t * T_prime(z, c, k, m)


def Delta(z, c, k, m):
    return (1 - z) ** 2 - 4 * z * A_value(z, c, k, m)


def Delta_prime(z, c, k, m):
    return -2 * (1 - z) - 4 * A_value(z, c, k, m) - 4 * z * A_prime(z, c, k, m)


def F_value(z, c, k, m):
    return ((1 - z) - math.sqrt(Delta(z, c, k, m))) / (2 * z)


def rho_T(c, k, m):
    if m == 0:
        return 1.0 / k if k else math.inf
    return 1.0 / (k + 2 * math.sqrt(m * c))


def Phi(c, k, m):
    """Criterion of Proposition 5.2 (m >= 1)."""
    return (k + 2 * math.sqrt(m * c)) - (1 + 2 * math.sqrt(c / m))


def classify(c, k, m, tol=1e-12):
    if m == 0:
        return "i"
    p = Phi(c, k, m)
    return "i" if p < -tol else ("ii" if abs(p) <= tol else "iii")


def rho_Delta(c, k, m):
    """Unique zero of Delta on (0, min(1, rho_T)) by bisection (case i)."""
    lo, hi = 1e-12, min(1.0, rho_T(c, k, m)) * (1 - 1e-15)
    for _ in range(300):
        mid = (lo + hi) / 2
        if Delta(mid, c, k, m) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def singular_data(c, k, m):
    """Return dict with case, rho, b, gamma, c_F (Theorem 5.3)."""
    case = classify(c, k, m)
    out = {"case": case}
    if case == "i":
        r = rho_Delta(c, k, m)
        dp = Delta_prime(r, c, k, m)
        out.update(rho=r, gamma=1.5, c_F=math.sqrt(abs(dp) / r) / (4 * math.sqrt(math.pi)),
                   Delta_prime=dp)
        # Meir-Moon cross-check: G(z,y) = A(z) + z y + z y^2
        tau = (1 - r) / (2 * r)
        Gz = A_prime(r, c, k, m) + tau + tau * tau
        out.update(tau=tau, G_z=Gz, c_F_meir_moon=math.sqrt(Gz / (4 * math.pi)))
    else:
        r = rho_T(c, k, m)
        T0 = math.sqrt(c / m)
        dDT = -2 * k * (1 - k * r) - 8 * m * c * r
        t1 = math.sqrt(r * abs(dDT)) / (2 * m * r)
        a1 = 2 * r * T0 * t1
        out.update(rho=r, T0=T0, t1=t1, a1=a1, A0=r * T0 * T0)
        if case == "ii":
            out.update(gamma=1.25, c_F=math.sqrt(a1 / r) / abs(math.gamma(-0.25)))
        else:
            D0 = Delta(r, c, k, m)
            out.update(gamma=1.5, Delta_rho=D0,
                       c_F=a1 / (2 * math.sqrt(math.pi) * math.sqrt(D0)))
    out["b"] = 1 / out["rho"]
    return out


def L2_second_term():
    """Relative n^{-1/2} correction for L2 (Example 5.5(c)):
    f(n) 3^{-n} n^{5/4} = c_F + d n^{-1/2} + O(1/n)."""
    kappa = math.sqrt(8 * math.sqrt(3)) / 3
    return (3 * math.sqrt(3) / 8) * kappa / math.gamma(-0.75)


def normalized(f, n, rho, gamma):
    return math.exp(log_int(f[n]) + n * math.log(rho) + gamma * math.log(n))


# ---------------------------------------------------------------- A1 vs Q2 (L2)
def A1_constant(c, k, m, nterms=200):
    """Constant of the A1 instances: rho^2 F(rho^2) c_F (per length)."""
    sd = singular_data(c, k, m)
    x = sd["rho"] ** 2
    f = formula_counts(nterms, c, k, m)
    return x * sum(f[s] * x ** s for s in range(1, nterms + 1)) * sd["c_F"]


def crossover_L2():
    """Leading-order estimate of the length n beyond which the cumulative number
    of A1 instances exceeds the cumulative number of ground instances of
    forall x not(0 = Sx) in L2 (Remark 5.6)."""
    c, k, m = LANGUAGES["L2"]
    sd = singular_data(c, k, m)
    r = sd["rho"]
    cum = 1 / (1 - r)
    a1_cum = A1_constant(c, k, m) * cum                  # * 3^n n^{-5/4}
    # instances not(0 = S t) have length |t| + 4; terms ~ t1/(2 sqrt(pi)) 3^n n^{-3/2}
    q2_cum = sd["t1"] / (2 * math.sqrt(math.pi)) * r ** 4 * cum   # * 3^n n^{-3/2}
    n_cross = (q2_cum / a1_cum) ** 4
    return a1_cum, q2_cum, n_cross


# ------------------------------------------------------------------- reporting
def report(nmax_check=3000):
    lines = []
    P = lines.append
    P("== Trichotomy (Proposition 5.2) ==")
    for name, (c, k, m) in LANGUAGES.items():
        phi = "---" if m == 0 else f"{Phi(c, k, m):+.6f}"
        sd = singular_data(c, k, m)
        P(f"{name}: (c,k,m)=({c},{k},{m})  Phi={phi}  case ({sd['case']})  "
          f"rho={sd['rho']:.6f}  b={sd['b']:.6f}  gamma={sd['gamma']}  c_F={sd['c_F']:.6f}")
    P(f"propositional logic, a atoms: b = 1 + 2 sqrt(a); a=2 -> {1 + 2 * math.sqrt(2):.6f}")

    sd1 = singular_data(*LANGUAGES["L1"])
    P("\n== L1, case (i) ==")
    P(f"rho = sqrt(2)-1 = {math.sqrt(2) - 1:.9f} (computed {sd1['rho']:.9f})")
    P(f"Delta'(rho) = {sd1['Delta_prime']:.6f}  (-4 sqrt 2 = {-4 * math.sqrt(2):.6f})")
    P(f"c_F = sqrt(8+4 sqrt2)/(4 sqrt pi) = {math.sqrt(8 + 4 * math.sqrt(2)) / (4 * math.sqrt(math.pi)):.6f}")
    P(f"Meir-Moon: tau={sd1['tau']:.6f}  G_z={sd1['G_z']:.6f} (2+sqrt2={2 + math.sqrt(2):.6f})  "
      f"c_F={sd1['c_F_meir_moon']:.6f}")

    sd2 = singular_data(*LANGUAGES["L2"])
    d2 = L2_second_term()
    P("\n== L2, case (ii) ==")
    P(f"T0={sd2['T0']:.6f}  t1={sd2['t1']:.6f} (sqrt3)  a1={sd2['a1']:.6f} (2 sqrt3/3)")
    P(f"c_F = 12^(1/4)/|Gamma(-1/4)| = {12 ** 0.25 / abs(math.gamma(-0.25)):.6f}  (computed {sd2['c_F']:.6f})")
    P(f"second-order coefficient d = {d2:.6f}")

    sdq = singular_data(*LANGUAGES["LQ"])
    P("\n== LQ, case (iii) ==")
    P(f"T0={sdq['T0']:.6f} A0={sdq['A0']:.6f} a1={sdq['a1']:.6f} Delta(rho)={sdq['Delta_rho']:.6f} "
      f"c_F={sdq['c_F']:.6f}")

    P("\n== Table 2: normalized counts f(n) rho^n n^gamma ==")
    table = []
    for name, ns in (("L1", (100, 400, 1000, 2000, 3000)),
                     ("L2", (100, 400, 1000, 2000, 3000)),
                     ("LQ", (100, 400, 1000, 2500))):
        c, k, m = LANGUAGES[name]
        sd = singular_data(c, k, m)
        f = formula_counts(max(ns), c, k, m)
        for n in ns:
            v = normalized(f, n, sd["rho"], sd["gamma"])
            if name == "L2":
                pred = sd["c_F"] + d2 * n ** -0.5
                resid = (v - pred) * n
                P(f"{name} n={n:5d}  value={v:.6f}  prediction(with n^-1/2)={pred:.6f}  residual*n={resid:+.3f}")
            else:
                pred = sd["c_F"]
                resid = (v - pred) / pred * n
                P(f"{name} n={n:5d}  value={v:.6f}  prediction={pred:.6f}  rel.error*n={resid:+.3f}")
            table.append(dict(language=name, n=n, value=v, prediction=pred, residual_times_n=resid))
    f = formula_counts(1200, *LANGUAGES["L2"])
    P("L2 with the naive exponent gamma=3/2 (diverges): "
      + ", ".join(f"n={n}: {normalized(f, n, 1 / 3, 1.5):.2f}" for n in (50, 100, 200, 400, 800, 1200)))

    P("\n== A1 lower bound constant and crossover in L2 (Remark 5.6) ==")
    f1 = formula_counts(600, *LANGUAGES["L1"])
    for n in (100, 300, 600):
        a1n = sum(f1[i] * f1[n - 2 - 2 * i] for i in range(1, (n - 2) // 2) if n - 2 - 2 * i >= 1)
        P(f"L1: #A1 instances of length {n} / f({n}) = {math.exp(log_int(a1n) - log_int(f1[n])):.5f}")
    x = sd1["rho"] ** 2
    fL1 = formula_counts(200, *LANGUAGES["L1"])
    P(f"L1: predicted limit rho^2 F(rho^2) = {x * sum(fL1[s] * x ** s for s in range(1, 201)):.6f}")
    a1c = A1_constant(*LANGUAGES["L2"])
    a1_cum, q2_cum, n_cross = crossover_L2()
    P(f"L2: A1 instances per length ~ {a1c:.3e} * 3^n n^(-5/4); cumulative {a1_cum:.3e}")
    P(f"L2: ground instances of Q2 (cumulative) ~ {q2_cum:.3e} * 3^n n^(-3/2)")
    P(f"L2: leading-order crossover at n ~ {n_cross:.2e}")

    P("\n== Horizon extension per factor 10 of budget: log(10)/log(b) ==")
    for name, (c, k, m) in LANGUAGES.items():
        P(f"{name}: {math.log(10) / math.log(singular_data(c, k, m)['b']):.2f} symbols")
    return "\n".join(lines), table




# ---------------------------------------------------------------- object API
@dataclass(frozen=True)
class Language:
    """First-order language L(c, k, m) with equality, "not" and "->".

    >>> Language(1, 1, 2).case
    'iii'
    >>> round(Language(1, 1, 0).base, 6)
    2.414214
    """
    c: int
    k: int
    m: int

    @classmethod
    def named(cls, name):
        """One of "L1" = {0,S}, "L2" = {0,S,+}, "LQ" = {0,S,+,*}."""
        return cls(*LANGUAGES[name])

    @property
    def phi(self):
        """Criterion Phi of Proposition 5.2 (None if m = 0)."""
        return None if self.m == 0 else Phi(self.c, self.k, self.m)

    @property
    def case(self):
        """'i', 'ii' or 'iii' (Proposition 5.2)."""
        return classify(self.c, self.k, self.m)

    @property
    def singular(self):
        return singular_data(self.c, self.k, self.m)

    @property
    def rho(self):
        """Dominant singularity of the formula generating function."""
        return self.singular["rho"]

    @property
    def base(self):
        """Base b = 1/rho of the cost of saturation audits (Theorem 5.3)."""
        return self.singular["b"]

    @property
    def gamma(self):
        """Polynomial exponent: f(n) ~ c_F b^n n^(-gamma)."""
        return self.singular["gamma"]

    @property
    def c_F(self):
        """Asymptotic constant of Theorem 5.3."""
        return self.singular["c_F"]

    def formula_counts(self, nmax):
        """Exact numbers f(0), ..., f(nmax) of formulas of each length."""
        return formula_counts(nmax, self.c, self.k, self.m)

    def term_counts(self, nmax):
        """Exact numbers of terms of each length."""
        return term_counts(nmax, self.c, self.k, self.m)

    def asymptotic_count(self, n):
        """Leading-order approximation c_F b^n n^(-gamma) of f(n)."""
        return self.c_F * self.base ** n * n ** (-self.gamma)
