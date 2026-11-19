"""Kern, Least Core, Nukleolus und Shapley-Wert eines Kostenspiels (c[S] für alle Koalitionen S als Bitmasken, c[0] = 0).

Überschuss einer Koalition S bei der Aufteilung x: e(S, x) = x(S) - c(S) mit x(S) = Σ_{i in S} x_i. Positiv heißt: S zahlt mehr, als sie allein führe, und würde austreten.
- Kern: alle Überschüsse echter Koalitionen <= 0 und x(N) = c(N). Er kann leer sein.
- Additiver Least-Core-Wert ε*: kleinstes ε mit x(S) <= c(S) + ε für alle echten Koalitionen S und x(N) = c(N). Kern nicht leer genau dann, wenn ε* <= 0.
- Multiplikativer Least-Core-Wert ρ*: kleinstes ρ mit x(S) <= ρ c(S). Kern nicht leer genau dann, wenn ρ* <= 1.
- Nukleolus (Schmeidler 1969): die Aufteilung, die den größten Überschuss minimiert, dann den zweitgrößten usw.; hier per Folge linearer Programme (Maschler, Peleg, Shapley 1979),
  mit der Technik der Kern-Demo (nur linear unabhängige Fesseln). Er ist eindeutig und liegt im Kern, wenn der Kern nicht leer ist.
- Shapley-Wert: mittlerer Beitrag c(S ∪ {i}) - c(S) über alle Reihenfolgen. Er liegt nicht immer im Kern.
Gleichstände: Ein Überschuss gilt erst oberhalb von TOL als positiv (blockierend); den Least-Core-Wert gibt das LP auf Rundung genau zurück."""

import math

import numpy as np

import stg_constants as C
from stg_game import incidence


def proper_incidence(n: int) -> np.ndarray:
    """Inzidenz der echten nichtleeren Koalitionen (Masken 1 bis 2^n - 2), Zeile k gehört zur Maske k + 1."""
    return incidence(n)[1:-1]


def excess(x: np.ndarray, c: np.ndarray, n: int) -> np.ndarray:
    """Überschüsse x(S) - c(S) der echten nichtleeren Koalitionen (Index k = Maske k + 1)."""
    return proper_incidence(n) @ np.asarray(x, dtype=float) - c[1:-1]


def least_core(c: np.ndarray, n: int, mult: bool = False) -> tuple[float, np.ndarray]:
    """(Wert, x): additiver ε* (mult = False) oder multiplikativer ρ* (mult = True, braucht c > 0) mit einer zugehörigen Aufteilung x. n = 1: es gibt keine echte Koalition,
    der Wert ist -inf (der Kern ist {c(N)})."""
    from scipy.optimize import linprog

    if n == 1:
        return float("-inf"), np.array([c[-1]])
    S = proper_incidence(n)
    cs = c[1:-1]
    a_ub = np.hstack([S, -(cs[:, None] if mult else np.ones((len(cs), 1)))])
    b_ub = np.zeros(len(cs)) if mult else cs
    res = linprog(np.r_[np.zeros(n), 1.0], A_ub=a_ub, b_ub=b_ub, A_eq=[np.r_[np.ones(n), 0.0]], b_eq=[c[-1]], bounds=[(None, None)] * (n + 1), method="highs")
    if res.status != 0:
        raise RuntimeError(res.message)
    return float(res.x[-1]), res.x[:n]


def is_core_empty(c: np.ndarray, n: int) -> bool:
    """Kern leer genau dann, wenn ε* > TOL."""
    return least_core(c, n)[0] > C.TOL


def shapley(c: np.ndarray, n: int) -> np.ndarray:
    """Shapley-Wert: φ_i = Σ_{S ohne i} |S|! (n - |S| - 1)! / n! · (c(S ∪ {i}) - c(S)), vektorisiert über die Koalitionen."""
    masks = np.arange(1 << n)
    pop = ((masks[:, None] >> np.arange(n)[None, :]) & 1).sum(axis=1)
    fact = np.array([math.factorial(k) for k in range(n + 1)], dtype=float)
    phi = np.zeros(n)
    for i in range(n):
        without = masks[((masks >> i) & 1) == 0]
        weight = fact[pop[without]] * fact[n - pop[without] - 1] / fact[n]
        phi[i] = float((weight * (c[without | (1 << i)] - c[without])).sum())
    return phi


def nucleolus(c: np.ndarray, n: int) -> np.ndarray:
    """Nukleolus per Folge linearer Programme: je Stufe das kleinste ε für die noch freien Koalitionen; Koalitionen, die an jedem Optimum der Stufe gleich eng sind,
    werden mit ihrem Überschuss festgeschrieben (nur linear unabhängige als Gleichung, sonst meldet HiGHS die Fläche als unzulässig). Ende, sobald die festen Gleichungen x bestimmen."""
    from scipy.optimize import linprog

    if n == 1:
        return np.array([c[-1]])
    M = proper_incidence(n)
    rhs = c[1:-1]
    grand = c[-1]
    remaining = np.ones(len(rhs), dtype=bool)
    rows, vals = [], []
    x = np.full(n, grand / n)
    for _ in range(len(rhs) + 1):
        idx = np.flatnonzero(remaining)
        if len(idx) == 0:
            break
        a_eq = np.array([np.r_[np.ones(n), 0.0]] + [np.r_[r, 0.0] for r in rows])
        b_eq = np.array([grand] + vals)
        res = linprog(np.r_[np.zeros(n), 1.0], A_ub=np.hstack([M[idx], -np.ones((len(idx), 1))]), b_ub=rhs[idx], A_eq=a_eq, b_eq=b_eq,
                      bounds=[(None, None)] * (n + 1), method="highs")
        if res.status != 0:
            raise RuntimeError(res.message)
        eps, x = float(res.x[-1]), res.x[:n]
        slack = M[idx] @ x - rhs[idx]
        candidates = [k for k, s in zip(idx, slack) if s >= eps - C.TOL]
        face_eq = np.array([np.ones(n)] + rows)
        face_b = np.array([grand] + vals)
        newly = []
        for k in candidates:                              # an jedem Optimum der Stufe gleich eng? Überschuss von k über die Fläche minimieren
            r2 = linprog(M[k], A_ub=M[idx], b_ub=rhs[idx] + eps + C.TOL, A_eq=face_eq, b_eq=face_b, bounds=[(None, None)] * n, method="highs")
            if r2.status == 0 and M[k] @ r2.x - rhs[k] >= eps - 10 * C.TOL:
                newly.append(k)
        if not newly:
            newly = candidates[:1]
        for k in newly:
            if np.linalg.matrix_rank(np.array([np.ones(n)] + rows + [M[k]]), tol=1e-9) > len(rows) + 1:
                rows.append(M[k])
                vals.append(rhs[k] + eps)
            remaining[k] = False
        if np.linalg.matrix_rank(np.array([np.ones(n)] + rows), tol=1e-9) >= n:
            x = np.linalg.lstsq(np.array([np.ones(n)] + rows), np.array([grand] + vals), rcond=None)[0]
            break
    return x
