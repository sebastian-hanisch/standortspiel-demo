"""Das Kostenspiel: Koalitionswerte c(S) eines Standortspiels.

c(S) ist der billigste Weg, die Kunden der Koalition S zu bedienen: man wählt eine nichtleere Standortmenge O, zahlt deren Fixkosten und für jeden Kunden in S den Weg
zum nächsten Standort in O. Koalitionen sind Bitmasken über die Kunden (Bit i gesetzt: Kunde i gehört dazu), Standortmengen Bitmasken über die Standorte.
Bei Gleichstand zwischen Standortmengen gewinnt die mit der kleineren Maske (`argmin` nimmt die erste kleinste Stelle); die Kosten c(S) selbst hängen davon nicht ab."""

import numpy as np


def location_sets(d: np.ndarray, fix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(Fsum, DM): Fsum[O] = Fixkosten der Standortmenge O, DM[O, i] = Weg von Kunde i zum nächsten Standort in O (inf für die leere Menge O = 0).

    Aufgebaut aus der Menge ohne ihr niedrigstes Bit, daher eine Schleife über die 2^m Mengen mit einer Vektoroperation je Menge."""
    n, m = d.shape
    full = 1 << m
    Fsum = np.zeros(full)
    DM = np.full((full, n), np.inf)
    for O in range(1, full):
        low = (O & -O).bit_length() - 1
        rest = O & (O - 1)
        Fsum[O] = Fsum[rest] + fix[low]
        DM[O] = np.minimum(DM[rest], d[:, low])
    return Fsum, DM


def incidence(n: int) -> np.ndarray:
    """Zeile S (Maske) = Inzidenzvektor der Koalition S, Form (2^n, n)."""
    masks = np.arange(1 << n)
    return ((masks[:, None] >> np.arange(n)[None, :]) & 1).astype(float)


def coalition_costs(d: np.ndarray, fix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(c, best): c[S] für alle 2^n Koalitionen (c[0] = 0) und die beste Standortmenge je Koalition (Maske, bei Gleichstand die kleinere)."""
    n, m = d.shape
    Fsum, DM = location_sets(d, fix)
    total = incidence(n) @ DM[1:].T + Fsum[1:][None, :]      # (2^n, 2^m - 1): Kosten jeder Koalition bei jeder Standortmenge
    best = total.argmin(axis=1)
    c = total[np.arange(1 << n), best]
    c[0] = 0.0
    return c, best + 1


def cost_of(S: int, d: np.ndarray, fix: np.ndarray) -> tuple[float, int]:
    """Kosten und beste Standortmenge einer einzelnen Koalition, in Schleifen (kein Matrixprodukt): die Regel in Worten, auch als Orakel der Tabelle."""
    n, m = d.shape
    customers = [i for i in range(n) if S >> i & 1]
    if not customers:
        return 0.0, 0
    best_value, best_set = float("inf"), 0
    for O in range(1, 1 << m):
        stations = [j for j in range(m) if O >> j & 1]
        value = sum(fix[j] for j in stations) + sum(min(d[i, j] for j in stations) for i in customers)
        if value < best_value:
            best_value, best_set = value, O
    return float(best_value), best_set


def popcount(x: int) -> int:
    return bin(int(x)).count("1")


def members(mask: int, count: int) -> list[int]:
    """Die gesetzten Bits einer Maske als Liste (0-basiert)."""
    return [i for i in range(count) if mask >> i & 1]


def assignment(d: np.ndarray, open_mask: int) -> np.ndarray:
    """Nächster offener Standort je Kunde (bei gleichem Weg der mit der kleineren Nummer)."""
    open_idx = members(open_mask, d.shape[1])
    return np.array(open_idx)[d[:, open_idx].argmin(axis=1)]
