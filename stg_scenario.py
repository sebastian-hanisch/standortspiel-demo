"""Szenario: Kunden, mögliche Standorte, Wege und Fixkosten.

Eine Instanz besteht aus der Wegetabelle d[i, j] (Kunde i zu Standort j) und den Fixkosten fix[j]. Kunde i zahlt den Weg zum nächsten offenen Standort,
jeder offene Standort zahlt seine Fixkosten. Der Zufall kommt aus SplitMix64 (`stg_rng.py`): aus dem Zufalls-Seed entsteht ein Block gleichverteilter Zahlen
mit festen Abschnitten (Kunden, Standorte, Fixkosten, Störungen, Ballungswahl), dessen Aufteilung nur von (n, m) abhängt, nicht von der Lage.
Die Störung des Rings ist gleichverteilt in [-sigma, sigma] je Koordinate (keine Normalverteilung: kein math.log, kein math.cos, auf jeder Plattform dieselben Zahlen)."""

import math
from dataclasses import dataclass

import numpy as np

import stg_constants as C
from stg_rng import uniform_block


@dataclass(frozen=True)
class Settings:
    lage: str = C.LAGE_ZUFALL
    n: int = C.DEFAULT_N
    m: int = C.DEFAULT_M
    f: int = C.DEFAULT_F
    fix: str = C.FIX_EINHEITLICH
    s: int = C.DEFAULT_S
    sigma: int = C.DEFAULT_SIGMA
    seed: int = C.DEFAULT_SEED


@dataclass(eq=False)
class Instance:
    """Wegetabelle und Fixkosten; die Koordinaten sind nur für die Karte da (None bei Instanzen aus einer Wegetabelle)."""
    d: np.ndarray
    fix: np.ndarray
    pk: np.ndarray | None = None
    ps: np.ndarray | None = None
    name: str = ""

    @property
    def n(self) -> int:
        return self.d.shape[0]

    @property
    def m(self) -> int:
        return self.d.shape[1]


def instance_from_tables(d, fix, name: str = "") -> Instance:
    return Instance(np.asarray(d, dtype=float), np.asarray(fix, dtype=float), None, None, name)


def distances(pk: np.ndarray, ps: np.ndarray) -> np.ndarray:
    """Euklidische Wege (n, m) zwischen Kundenorten und Standorten."""
    return np.sqrt(((pk[:, None, :] - ps[None, :, :]) ** 2).sum(axis=2))


def ring_positions(n: int, s: float) -> tuple[np.ndarray, np.ndarray]:
    """Ring: n Kunden auf einem Kreis, benachbarte im Abstand s; Standort j liegt in der Mitte der Strecke zwischen Kunde j und Kunde j + 1.
    Jeder Kunde hat also zwei Standorte im Weg s/2; n = 3 ist das gleichseitige Dreieck."""
    radius = s / (2.0 * math.sin(math.pi / n))
    ang = 2.0 * math.pi * np.arange(n) / n
    pk = np.stack([radius * np.cos(ang), radius * np.sin(ang)], axis=1)
    mid = ang + math.pi / n
    ps = np.stack([radius * math.cos(math.pi / n) * np.cos(mid), radius * math.cos(math.pi / n) * np.sin(mid)], axis=1)
    return pk, ps


def stations_count(lage: str, n: int, m: int) -> int:
    """Beim Ring gibt es genau n Standorte (die Kantenmitten), sonst m."""
    return n if lage == C.LAGE_RING else m


def make_instance(st: Settings) -> Instance:
    """Deterministisch aus den Einstellungen: gleiche Eingabe, gleiche Instanz (SplitMix64 mit dem Zufalls-Seed)."""
    n, m = st.n, stations_count(st.lage, st.n, st.m)
    u = uniform_block(st.seed, 2 * n + 2 * m + m + 2 * n + 2 * m + n)
    o = 0
    u_cust = u[o:o + 2 * n].reshape(n, 2); o += 2 * n
    u_stat = u[o:o + 2 * m].reshape(m, 2); o += 2 * m
    u_fix = u[o:o + m]; o += m
    u_noise_c = u[o:o + 2 * n].reshape(n, 2); o += 2 * n
    u_noise_s = u[o:o + 2 * m].reshape(m, 2); o += 2 * m
    u_pick = u[o:o + n]
    if st.lage == C.LAGE_RING:
        pk, ps = ring_positions(n, float(st.s))
        pk = pk + (2.0 * u_noise_c - 1.0) * st.sigma
        ps = ps + (2.0 * u_noise_s - 1.0) * st.sigma
    elif st.lage == C.LAGE_BALLUNG:
        centres = np.array(C.BALLUNG_ZENTREN)
        pk = centres[(u_pick >= 0.5).astype(int)] + (2.0 * u_noise_c - 1.0) * C.BALLUNG_BREITE
        ps = u_stat * C.AREA
    else:
        pk = u_cust * C.AREA
        ps = u_stat * C.AREA
    fix = np.full(m, float(st.f)) if st.fix == C.FIX_EINHEITLICH else float(st.f) * (0.5 + u_fix)
    return Instance(distances(pk, ps), fix, pk, ps)


def uniform_instance(n: int, m: int, f: float, seed: int) -> Instance:
    """Zufallslage gleichverteilt mit einheitlichen Fixkosten: die Instanz der Raster-Experimente."""
    return make_instance(Settings(C.LAGE_ZUFALL, n, m, int(f), C.FIX_EINHEITLICH, C.DEFAULT_S, 0, seed))


def raster_seed(n: int, m: int, f: int, block: int, i: int) -> int:
    """Zufalls-Seed der Raster-Instanz (Zelle n, m, f; Block 0 bis 3; laufende Nummer i < 1000): jede Zelle zieht ihre eigenen Instanzen."""
    return (((n * 16 + m) * 4096 + f) * 8 + block) * 1000 + i


def ring_instance(n: int, f: float, s: float = 100.0) -> Instance:
    """Ring ohne Störung (die Formeln der Lehrseite gelten hier)."""
    pk, ps = ring_positions(n, s)
    return Instance(distances(pk, ps), np.full(n, float(f)), pk, ps, f"Ring n = {n}")


def triangle_instance(s: float, f: float, sigma: float, seed: int) -> Instance:
    """Dreieck mit Streuung (Ring mit n = 3): Experiment E2."""
    return make_instance(Settings(C.LAGE_RING, 3, 3, int(f), C.FIX_EINHEITLICH, int(s), int(sigma), seed))


# Das kleinste Beispiel von Hand: drei Kunden, drei Standorte F12, F13, F23 (Fixkosten 2). Standort Fij liegt für die Kunden i und j im Weg 0, für den dritten im Weg 2.
# Zeilen = Kunden 1, 2, 3; Spalten = F12, F13, F23.
HAND_TRIANGLE_D = ((0.0, 0.0, 2.0), (0.0, 2.0, 0.0), (2.0, 0.0, 0.0))
HAND_TRIANGLE_FIX = (2.0, 2.0, 2.0)


def hand_triangle() -> Instance:
    """Das Dreieck von Hand: Wege 0 oder 2, Fixkosten 2 je Standort."""
    return instance_from_tables(HAND_TRIANGLE_D, HAND_TRIANGLE_FIX, "Dreieck von Hand")
