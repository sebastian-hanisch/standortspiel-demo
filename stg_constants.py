"""Konstanten: Regler-Grenzen, feste Annahmen, Toleranzen, Farben und Presets.

Rechenaufwand am Regler-Maximum (n = 10 Kunden, m = 8 Standorte; beim Ring m = n = 10):
- Koalitionstabelle: 2^n Koalitionen x (2^m - 1) Standortmengen, ein Matrixprodukt (1 024 x 1 023 beim Ring), O(2^n 2^m n).
- Kern-LP (Least Core): n + 1 Variablen, 2^n - 2 Zeilen (1 022), HiGHS.
- Shapley: 2^n x n Summanden, vektorisiert. Nukleolus: Folge von LP, bis zu 2^n - 2 Zeilen je Stufe (nur bis N_NUKLEOLUS_MAX, Laufzeit im Bau gemessen).
- Lücke und Duallösung: LP mit n m + m Variablen, ohne die 2^n Koalitionen (deshalb bis n = 30, m = 12 im Experiment E6)."""

N_MIN, N_MAX, DEFAULT_N = 3, 10, 8
M_MIN, M_MAX, DEFAULT_M = 2, 8, 6
F_MIN, F_MAX, DEFAULT_F = 5, 200, 60
S_MIN, S_MAX, DEFAULT_S = 40, 200, 100          # Ring: Abstand benachbarter Kunden
SIGMA_MIN, SIGMA_MAX, DEFAULT_SIGMA = 0, 30, 0   # Ring: Positionsstörung je Koordinate, gleichverteilt in [-sigma, sigma]
SEED_MAX, DEFAULT_SEED = 999999, 1
AREA = 100.0                                     # Zufallslagen: Quadrat [0, AREA]^2

LAGE_ZUFALL = "Zufall: gleichverteilt"
LAGE_BALLUNG = "Zufall: zwei Ballungen"
LAGE_RING = "Ring (n = 3: Dreieck)"
LAGEN = (LAGE_ZUFALL, LAGE_BALLUNG, LAGE_RING)
FIX_EINHEITLICH = "einheitlich f"
FIX_STREUEND = "ungleich: f aus [0,5 f; 1,5 f]"
FIX_MODI = (FIX_EINHEITLICH, FIX_STREUEND)
BALLUNG_ZENTREN = ((25.0, 25.0), (75.0, 75.0))
BALLUNG_BREITE = 15.0                            # Kunden einer Ballung: Zentrum + gleichverteilt in [-BALLUNG_BREITE, BALLUNG_BREITE]

TOL = 1e-7                                       # ein Überschuss oberhalb TOL zählt als blockierend, ein Least-Core-Wert oberhalb TOL als leerer Kern
GAP_TOL = 1e-7                                   # Kriterium ohne 2^n Bedingungen: c(N) - LP > GAP_TOL
N_NUKLEOLUS_MAX = 10                             # Nukleolus (LP-Folge) nur bis zu dieser Kundenzahl
N_SHAPLEY_MAX = 10
M_ENUM_MAX = 12                                  # Aufzählung aller Standortmengen bis zu dieser Standortzahl, darüber gemischt-ganzzahliges Programm
N_GROSS_MAX, M_GROSS_MAX = 30, 12                # Experiment E6
RING_N_MAX = 21                                  # Experiment E5

# Experiment E1: Raster (vorgerechnet in data/raster_leere_kerne.json), Zufall gleichverteilt, einheitliche Fixkosten
RASTER_N = (5, 6, 8)
RASTER_M = (3, 4, 6, 8)
RASTER_F = (10, 20, 30, 45, 60, 100, 150)
RASTER_BLOECKE, RASTER_PRO_BLOCK = 4, 100
# Experiment E2: Dreieck mit Streuung
DREIECK_SIGMA = (0, 5, 10, 20)
DREIECK_F = (30, 60, 73, 80, 100)
DREIECK_INSTANZEN = 400
# Experiment E3: Shapley im Kern nach Zahl offener Standorte (n = 6, m = 4)
E3_F = (10, 30, 60, 100)
E3_INSTANZEN = 150
# Experiment E4: Aufteilungen bei leerem Kern (vorgerechnet in data/aufteilungen_leerer_kern.json)
E4_KONFIG = ((6, 4, 60), (6, 4, 100), (7, 6, 60), (8, 6, 60), (8, 8, 45))
E4_PRO_KONFIG = 8
# Experiment E6: Kriterium bei großer Kundenzahl
E6_N = (20, 30)
E6_PHI = (3, 6, 10, 15, 25)
E6_INSTANZEN = 100

COLOR_KUNDE = "#2F6B65"
COLOR_OFFEN = "#c0392b"
COLOR_STANDORT = "rgba(150,150,150,0.9)"
COLOR_BLOCK = "#e08e0b"
COLOR_LINE = "#4c78a8"

PRESETS = {
    "Standard (Zufall, n = 8, m = 6)": dict(lage=LAGE_ZUFALL, n=8, m=6, f=60, fix=FIX_EINHEITLICH, s=DEFAULT_S, sigma=0, seed=DEFAULT_SEED),
    "Dreieck (Ring mit n = 3)": dict(lage=LAGE_RING, n=3, m=DEFAULT_M, f=50, fix=FIX_EINHEITLICH, s=100, sigma=0, seed=DEFAULT_SEED),
    "Fünferring": dict(lage=LAGE_RING, n=5, m=DEFAULT_M, f=50, fix=FIX_EINHEITLICH, s=100, sigma=0, seed=DEFAULT_SEED),
    "Sechserring": dict(lage=LAGE_RING, n=6, m=DEFAULT_M, f=50, fix=FIX_EINHEITLICH, s=100, sigma=0, seed=DEFAULT_SEED),
    "Zufall mit leerem Kern": dict(lage=LAGE_ZUFALL, n=6, m=4, f=60, fix=FIX_EINHEITLICH, s=DEFAULT_S, sigma=0, seed=1362),
    "Zufall: Shapley außerhalb des Kerns": dict(lage=LAGE_ZUFALL, n=6, m=4, f=60, fix=FIX_EINHEITLICH, s=DEFAULT_S, sigma=0, seed=182),
}
PRESET_HELP = {
    "Standard (Zufall, n = 8, m = 6)": "8 Kunden und 6 mögliche Standorte, zufällig im Quadrat 100 × 100, Fixkosten 60. Der Kern ist nicht leer.",
    "Dreieck (Ring mit n = 3)": "Drei Kunden an den Ecken eines Dreiecks mit Seite 100, drei Standorte in den Kantenmitten, Fixkosten 50: der kleinste leere Kern.",
    "Fünferring": "Fünf Kunden im Abstand 100 auf einem Kreis, fünf Standorte in den Kantenmitten, Fixkosten 50: ungerade Ringe haben einen leeren Kern.",
    "Sechserring": "Sechs Kunden auf dem Ring, sonst wie der Fünferring: der Kern ist nicht leer, hat aber keinen Spielraum (gerade Ringe).",
    "Zufall mit leerem Kern": "Eine gesuchte Zufallsinstanz mit 6 Kunden und 4 Standorten, deren Kern leer ist; der Effekt ist klein.",
    "Zufall: Shapley außerhalb des Kerns": "Eine gesuchte Zufallsinstanz mit nichtleerem Kern, in der zwei Standorte offen sind: der Shapley-Wert liegt außerhalb des Kerns, der Nukleolus darin.",
}
