"""Die Relaxierung des Standortproblems und die Ganzzahligkeitslücke.

Ganzzahlig: Standort j offen (y_j in {0, 1}), jeder Kunde zu genau einem offenen Standort. Relaxierung: y_j und die Zuordnung x_ij dürfen Bruchteile sein
(Standort halb offen, Kunde halb hier, halb dort). Der Wert der Relaxierung ist höchstens so groß wie der ganzzahlige c(N); der Quotient c(N) / LP ist die Lücke.
Die Duallösung der Relaxierung gibt jedem Kunden einen Preis v_i: Σ_i v_i = LP-Wert, und für jeden Standort j gilt Σ_i max(0, v_i - d_ij) <= f_j.
Daraus folgt x(S) <= c(S) für jede Koalition S (Beweisskizze im 📐-Expander): die Preise v liegen im Kern, wenn die Lücke 1 ist.
scipy wird erst in den Funktionen importiert (kürzerer Kaltstart), steht aber in requirements.txt."""

from dataclasses import dataclass

import numpy as np

import stg_constants as C
from stg_game import location_sets


@dataclass(frozen=True)
class Relaxation:
    value: float            # LP-Wert
    prices: np.ndarray      # Preise v_i (Duallösung der Zuordnungsgleichungen); eine Duallösung, bei Gleichstand nicht eindeutig
    opened: np.ndarray      # y_j der Primallösung (eine optimale, nicht eindeutig)


def lp_relaxation(d: np.ndarray, fix: np.ndarray) -> Relaxation:
    """LP-Relaxierung für alle Kunden: min Σ f_j y_j + Σ d_ij x_ij; Σ_j x_ij = 1; x_ij <= y_j; 0 <= x, y <= 1."""
    from scipy.optimize import linprog
    from scipy.sparse import coo_matrix

    n, m = d.shape
    nv = m + n * m
    cost = np.concatenate([fix, d.ravel()])
    rows_eq = np.repeat(np.arange(n), m)
    cols_eq = m + np.arange(n * m)
    a_eq = coo_matrix((np.ones(n * m), (rows_eq, cols_eq)), shape=(n, nv)).tocsr()
    r = np.arange(n * m)
    a_ub = coo_matrix((np.r_[np.ones(n * m), -np.ones(n * m)], (np.r_[r, r], np.r_[m + r, np.tile(np.arange(m), n)])), shape=(n * m, nv)).tocsr()
    res = linprog(cost, A_ub=a_ub, b_ub=np.zeros(n * m), A_eq=a_eq, b_eq=np.ones(n), bounds=(0, 1), method="highs")
    if res.status != 0:
        raise RuntimeError(res.message)
    return Relaxation(float(res.fun), np.asarray(res.eqlin.marginals, dtype=float), np.asarray(res.x[:m], dtype=float))


def integer_optimum(d: np.ndarray, fix: np.ndarray) -> tuple[float, int]:
    """Ganzzahliges Optimum der großen Koalition c(N) durch Aufzählung aller Standortmengen (m <= M_ENUM_MAX), ohne die 2^n Koalitionen. Liefert (Wert, Maske)."""
    Fsum, DM = location_sets(d, fix)
    total = Fsum[1:] + DM[1:].sum(axis=1)
    k = int(total.argmin())
    return float(total[k]), k + 1


def integer_optimum_milp(d: np.ndarray, fix: np.ndarray, time_limit: float = 120.0) -> tuple[float, bool]:
    """c(N) als gemischt-ganzzahliges Programm (scipy.optimize.milp, HiGHS) für mehr Standorte, als aufgezählt werden. Liefert (Wert, bewiesen optimal);
    bei Zeitgrenze ohne Beweis ist der Wert nur eine obere Schranke (bewiesen = False)."""
    from scipy.optimize import Bounds, LinearConstraint, milp
    from scipy.sparse import coo_matrix

    n, m = d.shape
    nv = m + n * m
    cost = np.concatenate([fix, d.ravel()])
    rows, cols, vals = [], [], []
    lo, hi = np.zeros(n + n * m), np.zeros(n + n * m)
    for i in range(n):                                  # Σ_j x_ij = 1
        rows += [i] * m
        cols += list(range(m + i * m, m + (i + 1) * m))
        vals += [1.0] * m
        lo[i] = hi[i] = 1.0
    for i in range(n):                                  # y_j - x_ij >= 0
        for j in range(m):
            r = n + i * m + j
            rows += [r, r]
            cols += [j, m + i * m + j]
            vals += [1.0, -1.0]
            hi[r] = np.inf
    a = coo_matrix((vals, (rows, cols)), shape=(n + n * m, nv)).tocsr()
    res = milp(cost, constraints=LinearConstraint(a, lo, hi), integrality=np.r_[np.ones(m), np.zeros(n * m)], bounds=Bounds(0, 1), options={"time_limit": time_limit})
    if res.x is None:
        raise RuntimeError(res.message)
    return float(res.fun), res.status == 0


def dual_violation(d: np.ndarray, fix: np.ndarray, v: np.ndarray) -> float:
    """Größte Verletzung der Dualbedingung: max_j (Σ_i max(0, v_i - d_ij) - f_j); höchstens 0 (bis auf Rundung) heißt dual zulässig."""
    return float((np.maximum(0.0, v[:, None] - d).sum(axis=0) - fix).max())


def gap(d: np.ndarray, fix: np.ndarray) -> tuple[float, float, float]:
    """(c(N), LP-Wert, Lücke c(N)/LP). Der Kern ist genau dann leer, wenn c(N) - LP > 0 (Toleranz GAP_TOL)."""
    cn = integer_optimum(d, fix)[0] if d.shape[1] <= C.M_ENUM_MAX else integer_optimum_milp(d, fix)[0]
    lp = lp_relaxation(d, fix).value
    return cn, lp, cn / lp if lp > 0 else 1.0


def core_empty_by_gap(d: np.ndarray, fix: np.ndarray) -> bool:
    """Kern leer ohne die 2^n Bedingungen: c(N) > LP (Toleranz GAP_TOL). Gilt für das unkapazitierte Standortspiel; gemessen, nicht hier bewiesen."""
    cn, lp, _ = gap(d, fix)
    return cn - lp > C.GAP_TOL
