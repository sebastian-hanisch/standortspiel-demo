"""Fünf Aufteilungen der Kosten c(N) und ihre Kennzahlen.

- Nukleolus: minimiert den größten Überschuss, dann den zweitgrößten usw. (nur bis N_NUKLEOLUS_MAX Kunden gerechnet).
- Shapley: mittlerer Beitrag über alle Reihenfolgen.
- Dual × Lücke: die Preise v der Duallösung der Relaxierung, mit der Lücke c(N)/LP auf c(N) hochskaliert. Eine Duallösung, bei Gleichstand nicht eindeutig; ihr Verhältnis
  x(S)/c(S) ist höchstens die Lücke (Approximationsidee von Goemans und Skutella, hier nur an Beispielen gemessen).
- Proportional: Anteil an c(N) im Verhältnis der Alleinkosten c({i}).
- Gleich: c(N)/n je Kunde.
Kennzahlen je Aufteilung x: größter Überschuss e_max = max_S x(S) - c(S), größtes Verhältnis ρ(x) = max_S x(S)/c(S), Zahl der blockierenden Koalitionen (Überschuss > TOL)."""

from dataclasses import dataclass

import numpy as np

import stg_constants as C
from stg_core import excess, nucleolus, proper_incidence, shapley
from stg_lp import lp_relaxation

NUKLEOLUS = "Nukleolus"
SHAPLEY = "Shapley"
DUAL_LUECKE = "Dual × Lücke"
PROPORTIONAL = "proportional"
GLEICH = "gleich"
RULES = (NUKLEOLUS, SHAPLEY, DUAL_LUECKE, PROPORTIONAL, GLEICH)


@dataclass(frozen=True)
class Kennzahlen:
    e_max: float       # größter Überschuss aller echten Koalitionen (<= TOL: im Kern)
    rho: float         # größtes Verhältnis x(S)/c(S)
    blocking: int      # Zahl der Koalitionen mit Überschuss > TOL
    worst: int         # Maske der Koalition mit dem größten Überschuss


def kennzahlen(x: np.ndarray, c: np.ndarray, n: int) -> Kennzahlen:
    if n == 1:
        return Kennzahlen(0.0, 1.0, 0, 1)
    e = excess(x, c, n)
    ratio = (proper_incidence(n) @ np.asarray(x, dtype=float)) / c[1:-1]
    return Kennzahlen(float(e.max()), float(ratio.max()), int((e > C.TOL).sum()), int(e.argmax()) + 1)


def dual_times_gap(d: np.ndarray, fix: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Preise der Duallösung mal Lücke c(N)/LP: summiert sich auf c(N). Ist die Lücke 1, liegt das Ergebnis im Kern."""
    rel = lp_relaxation(d, fix)
    return rel.prices * (c[-1] / rel.value)


def proportional(c: np.ndarray, n: int) -> np.ndarray:
    """c(N) im Verhältnis der Alleinkosten c({i})."""
    alone = np.array([c[1 << i] for i in range(n)])
    return c[-1] * alone / alone.sum()


def equal(c: np.ndarray, n: int) -> np.ndarray:
    return np.full(n, c[-1] / n)


def allocations(d: np.ndarray, fix: np.ndarray, c: np.ndarray, with_nucleolus: bool = True) -> dict[str, np.ndarray]:
    """Alle fünf Aufteilungen (den Nukleolus nur, wenn with_nucleolus)."""
    n = d.shape[0]
    out = {}
    if with_nucleolus:
        out[NUKLEOLUS] = nucleolus(c, n)
    out[SHAPLEY] = shapley(c, n)
    out[DUAL_LUECKE] = dual_times_gap(d, fix, c)
    out[PROPORTIONAL] = proportional(c, n)
    out[GLEICH] = equal(c, n)
    return out
