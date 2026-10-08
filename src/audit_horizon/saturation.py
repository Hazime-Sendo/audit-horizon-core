# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Hazime Sendo
"""
Linear-time saturation audit (Section 5.2, Lemma 5.1, and Table 3 of the paper).

Ground Hilbert calculus P_gr for universal theories:
  axioms  : quantifier-free instances of the Lukasiewicz schemas A1, A2, A3,
            ground equality axioms (reflexivity, substitution in atoms,
            congruence for every function symbol),
            ground instances of the axioms of the theory;
  rule    : modus ponens.
Notation: Polish notation, one symbol per node:  0, S (successor), + , * ,
          E (equality), N (negation), C (implication).  Length = #symbols.

Theories (fragments of Robinson's Q):
  L1 = {0,S}      : Q1  Sx = Sy -> x = y,   Q2  not 0 = Sx
  L2 = {0,S,+}    : Q1, Q2, Q3  x + 0 = x,  Q4  x + Sy = S(x + y)
  LQ = {0,S,+,*}  : Q1 - Q4,   Q5  x * 0 = 0,  Q6  x * Sy = (x * y) + x
Inconsistent variant: add the atom S0 = SS0.

Saturation audit of depth n: compute Th_n, the least set of formulas of
length <= n that contains the axioms of length <= n and is closed under modus
ponens; Con(n) is certified iff Th_n contains no pair phi, not phi.

Model of computation: word-RAM with hash-consing. Every term and formula is a
node (op, left, right) with an integer id, so equality is O(1) and every axiom
schema is recognized by a pattern match of bounded depth.

Operation counts (C_n in the paper):
  enum (enumerations), test (axiom tests), insert (insertions into D),
  mp (applications of modus ponens), watch (registrations in watch lists).
Lemma 5.1:  2|U_n| + |Th_n| <= C_n <= 2|U_n| + 3|Th_n| <= 5|U_n|.

Usage (after installation):
  audit-horizon audit L1 22
  audit-horizon audit L2 18
  audit-horizon audit LQ 14
Standard library only.
"""
import json
import os
import sys
import time

C_, N_, E_, S_, P_, M_, Z_ = "C", "N", "E", "S", "+", "*", "0"
LANGS = {"L1": (), "L2": (P_,), "LQ": (P_, M_)}


class Store:
    """Hash-consed node table."""

    def __init__(self):
        self.op, self.l, self.r, self.sz = [], [], [], []
        self.intern = {}

    def mk(self, op, l=-1, r=-1):
        key = (op, l, r)
        i = self.intern.get(key)
        if i is None:
            i = len(self.op)
            self.intern[key] = i
            self.op.append(op)
            self.l.append(l)
            self.r.append(r)
            self.sz.append(1 + (self.sz[l] if l >= 0 else 0) + (self.sz[r] if r >= 0 else 0))
        return i

    def get(self, op, l=-1, r=-1):
        return self.intern.get((op, l, r), -2)

    def show(self, x):
        o = self.op[x]
        if o == Z_:
            return "0"
        if o in (S_, N_):
            return o + self.show(self.l[x])
        return o + self.show(self.l[x]) + self.show(self.r[x])


def build(nmax, binops):
    """Enumerate all terms and formulas of length <= nmax, by length."""
    st = Store()
    T = {1: [st.mk(Z_)]}
    for s in range(2, nmax + 1):
        L = [st.mk(S_, t) for t in T[s - 1]]
        for op in binops:
            for i in range(1, s - 1):
                for a in T[i]:
                    for b in T[s - 1 - i]:
                        L.append(st.mk(op, a, b))
        T[s] = L
    F = {s: [] for s in range(1, nmax + 1)}
    for s in range(3, nmax + 1):
        for i in range(1, s - 1):
            for a in T[i]:
                for b in T[s - 1 - i]:
                    F[s].append(st.mk(E_, a, b))
    for s in range(2, nmax + 1):
        F[s] += [st.mk(N_, f) for f in F[s - 1]]
        for i in range(1, s - 1):
            for a in F[i]:
                for b in F[s - 1 - i]:
                    F[s].append(st.mk(C_, a, b))
    return st, F


def make_axiom_test(st, binops, extra_atoms=()):
    op, l, r = st.op, st.l, st.r
    extra = set(extra_atoms)

    def isop(x, o):
        return x >= 0 and op[x] == o

    def test(f):
        o = op[f]
        if o == C_:
            L, R = l[f], r[f]
            # A1: phi -> (psi -> phi)
            if isop(R, C_) and r[R] == L:
                return True
            # A2: (phi -> (psi -> chi)) -> ((phi -> psi) -> (phi -> chi))
            if isop(L, C_) and isop(r[L], C_) and isop(R, C_) and isop(l[R], C_) and isop(r[R], C_):
                a, b, c = l[L], l[r[L]], r[r[L]]
                if l[l[R]] == a and r[l[R]] == b and l[r[R]] == a and r[r[R]] == c:
                    return True
            # A3: (not phi -> not psi) -> (psi -> phi)
            if isop(L, C_) and isop(l[L], N_) and isop(r[L], N_) and isop(R, C_):
                if l[R] == l[r[L]] and r[R] == l[l[L]]:
                    return True
            if isop(L, E_):
                s_, t_ = l[L], r[L]
                if isop(R, C_) and isop(l[R], E_) and isop(r[R], E_):
                    X, Y = l[R], r[R]
                    # substitution in atoms: s=t -> (s=u -> t=u),  s=t -> (u=s -> u=t)
                    if l[X] == s_ and l[Y] == t_ and r[X] == r[Y]:
                        return True
                    if r[X] == s_ and r[Y] == t_ and l[X] == l[Y]:
                        return True
                    # congruence for binary symbols: s=t -> (u=v -> s o u = t o v)
                    u, v = l[X], r[X]
                    for bo in binops:
                        if isop(l[Y], bo) and isop(r[Y], bo) and l[l[Y]] == s_ and r[l[Y]] == u \
                                and l[r[Y]] == t_ and r[r[Y]] == v:
                            return True
                # congruence for S: s=t -> Ss=St
                if isop(R, E_) and isop(l[R], S_) and isop(r[R], S_) and l[l[R]] == s_ and l[r[R]] == t_:
                    return True
                # Q1: Ss=St -> s=t
                if isop(s_, S_) and isop(t_, S_) and isop(R, E_) and l[R] == l[s_] and r[R] == l[t_]:
                    return True
            return False
        if o == E_:
            a, b = l[f], r[f]
            if a == b:                                                   # reflexivity
                return True
            if P_ in binops and isop(a, P_):
                if isop(r[a], Z_) and b == l[a]:                         # Q3
                    return True
                if isop(r[a], S_) and isop(b, S_) and isop(l[b], P_) \
                        and l[l[b]] == l[a] and r[l[b]] == l[r[a]]:      # Q4
                    return True
            if M_ in binops and isop(a, M_):
                if isop(r[a], Z_) and isop(b, Z_):                       # Q5
                    return True
                if isop(r[a], S_) and isop(b, P_) and isop(l[b], M_) \
                        and l[l[b]] == l[a] and r[l[b]] == l[r[a]] and r[b] == l[a]:  # Q6
                    return True
            return f in extra
        if o == N_:                                                      # Q2: not 0 = St
            X = l[f]
            return isop(X, E_) and isop(l[X], Z_) and isop(r[X], S_)
        return False

    return test


def saturate(st, F, n, test):
    """Linear-time saturation with watch lists. Returns (D, counts, #implications, contradictions, parent)."""
    op, l, r = st.op, st.l, st.r
    cnt = dict(enum=0, test=0, insert=0, mp=0, watch=0)
    inD, watch, stack, used, parent = set(), {}, [], set(), {}

    def insert(f, par=None):
        if f in inD:
            return
        inD.add(f)
        cnt["insert"] += 1
        stack.append(f)
        if par is not None:
            parent[f] = par

    for s in range(1, n + 1):
        for f in F[s]:
            cnt["enum"] += 1
            cnt["test"] += 1
            if test(f):
                insert(f)
    while stack:
        f = stack.pop()
        if op[f] == C_:
            a = l[f]
            if a in inD:
                cnt["mp"] += 1
                assert f not in used, "an implication was used twice"
                used.add(f)
                insert(r[f], (a, f))
            else:
                cnt["watch"] += 1
                watch.setdefault(a, []).append(f)
        for imp in watch.pop(f, ()):
            cnt["mp"] += 1
            assert imp not in used, "an implication was used twice"
            used.add(imp)
            insert(r[imp], (f, imp))
    n_imp = sum(1 for f in inD if op[f] == C_)
    contra = [f for f in inD if st.get(N_, f) in inD]
    return inD, cnt, n_imp, contra, parent


def refutation(st, contra, parent):
    """Shortest (by total symbols) derivation of some pair phi, not phi recorded in `parent`."""
    best = None
    for c in contra:
        seen, todo = set(), [c, st.get(N_, c)]
        while todo:
            x = todo.pop()
            if x in seen:
                continue
            seen.add(x)
            todo.extend(parent.get(x, ()))
        size = sum(st.sz[x] for x in seen)
        if best is None or size < best[0]:
            best = (size, sorted(seen, key=lambda x: st.sz[x]))
    return best


def run(lang, nmax, verbose=True):
    binops = LANGS[lang]
    t0 = time.time()
    st, F = build(nmax, binops)
    if verbose:
        print(f"[{lang}] built {len(st.op):,} nodes in {time.time() - t0:.1f}s")
    test_q = make_axiom_test(st, binops)
    rows = []
    for n in range(3, nmax + 1):
        t = time.time()
        D, cnt, n_imp, contra, _ = saturate(st, F, n, test_q)
        dt = time.time() - t
        U, C = cnt["enum"], sum(cnt.values())
        lemma_ok = 2 * U + len(D) <= C <= 2 * U + 3 * len(D) <= 5 * U
        n_neg = sum(1 for f in D if st.op[f] == N_)   # in these theories: ground instances of Q2
        row = dict(n=n, U=U, Th=len(D), implications=n_imp, negations=n_neg, **cnt, C=C,
                   C_over_U=C / U, excess_over_Th=(C - 2 * U) / len(D),
                   consistent=not contra, lemma_5_1_holds=lemma_ok,
                   microseconds_per_formula=dt * 1e6 / U)
        rows.append(row)
        if verbose:
            print(f"  n={n:2d} |U_n|={U:>10,} |Th_n|={len(D):>9,} C_n={C:>11,} "
                  f"C_n/|U_n|={C / U:.4f} (C_n-2|U_n|)/|Th_n|={(C - 2 * U) / len(D):.3f} "
                  f"{'Con(n) certified' if not contra else 'CONTRADICTION'} "
                  f"{'' if lemma_ok else 'LEMMA VIOLATED'}")
    # inconsistent variant S0 = SS0
    z = st.get(Z_)
    bad = st.get(E_, st.get(S_, z), st.get(S_, st.get(S_, z)))
    test_bad = make_axiom_test(st, binops, (bad,))
    first = None
    for n in range(3, nmax + 1):
        D, cnt, n_imp, contra, parent = saturate(st, F, n, test_bad)
        if contra:
            size, lines = refutation(st, contra, parent)
            first = dict(width=n, refutation_length=size, refutation_lines=len(lines),
                         lines=[st.show(x) for x in lines])
            break
    if verbose and first:
        print(f"  inconsistent variant (+ S0=SS0): contradiction first at width {first['width']}; "
              f"refutation of length {first['refutation_length']} with {first['refutation_lines']} lines: "
              + ", ".join(first["lines"]))
    return dict(language=lang, nmax=nmax, rows=rows, inconsistent_variant=first)


