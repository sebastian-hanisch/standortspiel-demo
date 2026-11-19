"""Jede Zahl der README steht hier (exakt oder als Band) mit ihrer Voraussetzung.

Zufall kommt aus SplitMix64 (`stg_rng.py`); die Instanzen sind je Reihe fest (Seeds in `stg_scenario.py` und `stg_evaluation.py`). Ganze Zahlen (Zählungen leerer Kerne) stehen exakt;
Werte aus LP und Aufzählung (Least-Core-Wert, Lücke) als Band, weil HiGHS und die Summationsreihenfolge je Plattform in der letzten Stelle abweichen. Der Scratch-Lauf des Baus
(Orakel über 320 Instanzen) und die Laufzeiten stehen in der README als „Messung dieser README, nicht im Test“.

Zahl -> Test: Raster (E1) -> test_raster_*; Varianten -> test_variants_*; Dreieck (E2) -> test_triangle_*; Shapley nach k (E3) -> test_shapley_*, test_core_without_slack_*;
Aufteilungen (E4) -> test_allocation_study_*; Ring (E5) -> test_ring_*; große Instanzen (E6) -> test_large_*; Presets -> test_presets.py (Verdikte) und test_preset_numbers;
Handbeispiel -> test_hand_example_numbers."""

from functools import lru_cache

import pytest

import stg_allocations as AL
import stg_constants as C
import stg_core as Co
import stg_data as D
import stg_evaluation as ev
import stg_game as G
import stg_scenario as S


@pytest.fixture(scope="module")
def raster():
    return D.load_raster()["cells"]


@pytest.fixture(scope="module")
def study():
    return D.load_allocations()


@lru_cache(maxsize=None)
def _triangle():
    return [ev.triangle_cell(sg, f) for sg in C.DREIECK_SIGMA for f in C.DREIECK_F]


@lru_cache(maxsize=None)
def _shapley():
    return [ev.shapley_by_open(f) for f in C.E3_F]


@lru_cache(maxsize=None)
def _ring():
    return [ev.ring_row(n, f) for f in (10, 25, 50) for n in (3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 21)]


@lru_cache(maxsize=None)
def _large():
    return [ev.large_cell(n, C.M_GROSS_MAX, phi) for n in C.E6_N for phi in C.E6_PHI]


# ---- E1 Raster ------------------------------------------------------------------------------------------------------------------------------


def test_raster_totals(raster):
    """84 Zellen zu je 400 Instanzen (Zufall gleichverteilt, einheitliche Fixkosten, n in 5/6/8, m in 3/4/6/8): 33 600 Instanzen, davon 122 mit leerem Kern."""
    assert sum(c["total"] for c in raster) == 33600 and sum(c["empty"] for c in raster) == 122
    assert sum(c["empty"] > 0 for c in raster) == 41 and sum(c["empty"] == 0 for c in raster) == 43


def test_raster_empty_core_equals_positive_gap_in_every_instance(raster):
    assert sum(c["agree"] for c in raster) == 33600


def test_raster_most_affected_cells_and_largest_values(raster):
    top = max(c["empty"] for c in raster)
    assert top == 7 and sorted((c["n"], c["m"], c["f"]) for c in raster if c["empty"] == top) == [(6, 6, 100), (8, 8, 100)]
    assert max(c["empty"] / c["total"] for c in raster) == pytest.approx(0.0175)
    assert max(c["max_rel_eps"] for c in raster) == pytest.approx(0.0143, abs=5e-5)         # größter ε*/c(N) in einer Instanz mit leerem Kern: 1,43 %
    assert max(c["max_gap"] for c in raster) == pytest.approx(1.0219, abs=5e-5)


def test_raster_counts_by_fixed_cost(raster):
    by_f = {f: sum(c["empty"] for c in raster if c["f"] == f) for f in C.RASTER_F}
    assert by_f == {10: 1, 20: 5, 30: 7, 45: 26, 60: 43, 100: 32, 150: 8}                  # je 4 800 Instanzen


def test_raster_counts_by_customers_and_stations(raster):
    assert {n: sum(c["empty"] for c in raster if c["n"] == n) for n in C.RASTER_N} == {5: 31, 6: 31, 8: 60}
    assert {m: sum(c["empty"] for c in raster if c["m"] == m) for m in C.RASTER_M} == {3: 15, 4: 36, 6: 35, 8: 36}


def test_raster_probability_of_seeing_no_empty_core_in_a_cell():
    """§11a Punkt 4: bei einem Anteil von 122/33 600 liegt die Wahrscheinlichkeit, in 400 Instanzen keinen leeren Kern zu sehen, bei 0,23; 43 leere Zellen von 84 beweisen also keine Unmöglichkeit."""
    assert (1 - 122 / 33600) ** 400 == pytest.approx(0.2336, abs=5e-4)


def test_variants_do_not_change_the_rarity():
    """n = 6, m = 4, f = 30/60/100, je 400 Instanzen: Zufall gleichverteilt (0/3/1), ungleiche Fixkosten (0/3/3), zwei Ballungen (2/0/0): höchstens 3 von 400."""
    got = {}
    for lage, fix in ((C.LAGE_ZUFALL, C.FIX_EINHEITLICH), (C.LAGE_ZUFALL, C.FIX_STREUEND), (C.LAGE_BALLUNG, C.FIX_EINHEITLICH)):
        counts = []
        for f in (30, 60, 100):
            k = 0
            for i in range(400):
                inst = S.make_instance(S.Settings(lage, 6, 4, f, fix, 100, 0, 7_000_000 + 1000 * f + i))
                k += Co.least_core(G.coalition_costs(inst.d, inst.fix)[0], 6)[0] > C.TOL
            counts.append(int(k))
        got[(lage, fix)] = counts
    assert got == {(C.LAGE_ZUFALL, C.FIX_EINHEITLICH): [0, 3, 1], (C.LAGE_ZUFALL, C.FIX_STREUEND): [0, 3, 3], (C.LAGE_BALLUNG, C.FIX_EINHEITLICH): [2, 0, 0]}


# ---- E2 Dreieck -----------------------------------------------------------------------------------------------------------------------------


def test_triangle_counts_by_noise_and_fixed_cost():
    """Leere Kerne unter 400 Dreiecken je Zelle (σ = 0/5/10/20 gleichverteilte Störung je Koordinate; f = 30/60/73/80/100)."""
    rows = _triangle()
    got = {sg: [next(r["empty"] for r in rows if r["sigma"] == sg and r["f"] == f) for f in C.DREIECK_F] for sg in C.DREIECK_SIGMA}
    assert got == {0: [400, 400, 400, 0, 0], 5: [400, 380, 37, 1, 0], 10: [350, 205, 37, 3, 0], 20: [93, 70, 29, 4, 0]}


def test_triangle_threshold_without_noise_is_between_73_and_74():
    assert ev.triangle_threshold(100.0) == pytest.approx(73.2, abs=0.05)
    rows = {(r["sigma"], r["f"]): r["empty"] for r in _triangle()}
    assert rows[(0, 73)] == 400 and rows[(0, 80)] == 0


# ---- E3 Shapley nach Zahl offener Standorte ----------------------------------------------------------------------------------------------


def test_shapley_in_core_by_number_of_open_stations():
    """n = 6, m = 4, f = 10/30/60/100, je 150 Instanzen, nur nichtleerer Kern: (Shapley im Kern, Instanzen) je k."""
    tot = {}
    for r in _shapley():
        for k, (a, b) in r["by_k"].items():
            t = tot.setdefault(k, [0, 0])
            t[0] += a
            t[1] += b
    assert tot == {1: [160, 224], 2: [42, 268], 3: [21, 96], 4: [3, 9]}
    assert sum(r["nonempty"] for r in _shapley()) == 597 and sum(r["in_core"] for r in _shapley()) == 226


def test_shapley_with_two_open_stations_at_f_60_is_never_in_the_core_in_these_77_instances():
    r = next(r for r in _shapley() if r["f"] == 60)
    assert r["by_k"][2] == (0, 77) and r["by_k"][1] == (41, 72)


def test_core_without_slack_when_two_or_more_stations_are_open():
    """Bei k >= 2 und nichtleerem Kern ist ε* = 0 (Toleranz 1e-7) in allen 373 Instanzen; bei k = 1 hat der Kern in allen 224 Spielraum (ε* < 0)."""
    stat = {}
    for f in C.E3_F:
        for i in range(C.E3_INSTANZEN):
            inst = S.uniform_instance(6, 4, f, ev.e3_seed(f, i))
            c, best = G.coalition_costs(inst.d, inst.fix)
            eps = Co.least_core(c, 6)[0]
            if eps > C.TOL:
                continue
            k = G.popcount(best[-1])
            row = stat.setdefault(min(k, 2), [0, 0])
            row[0] += 1
            row[1] += abs(eps) <= C.TOL
    assert stat == {1: [224, 0], 2: [373, 373]}


# ---- E4 Aufteilungen bei leerem Kern ---------------------------------------------------------------------------------------------------------


def test_allocation_study_means_in_percent_of_the_total_cost(study):
    s = study["summary"]
    got = {nm: round(100 * s[nm]["e_mean"], 2) for nm in AL.RULES}
    assert got == {AL.NUKLEOLUS: 0.49, AL.SHAPLEY: 2.78, AL.DUAL_LUECKE: 0.61, AL.PROPORTIONAL: 7.01, AL.GLEICH: 8.62}
    assert round(100 * s["_eps_mean"], 2) == 0.49 and round(100 * s["_eps_max"], 2) == 1.38 and round(s["_gap_mean"], 4) == 1.0073 and s["_n"] == 40


def test_allocation_study_multiples_of_eps_ratios_and_blocking(study):
    s = study["summary"]
    assert s[AL.NUKLEOLUS]["e_over_eps"] == pytest.approx(1.0, abs=1e-6)
    assert round(s[AL.SHAPLEY]["e_over_eps"], 1) == 53.1 and round(s[AL.DUAL_LUECKE]["e_over_eps"], 2) == 1.27
    assert {nm: round(s[nm]["rho_mean"], 4) for nm in AL.RULES} == {AL.NUKLEOLUS: 1.0103, AL.SHAPLEY: 1.0485, AL.DUAL_LUECKE: 1.0073, AL.PROPORTIONAL: 1.1329, AL.GLEICH: 1.1785}
    assert {nm: round(s[nm]["blocking_mean"], 1) for nm in AL.RULES} == {AL.NUKLEOLUS: 6.1, AL.SHAPLEY: 6.3, AL.DUAL_LUECKE: 10.2, AL.PROPORTIONAL: 18.4, AL.GLEICH: 25.0}


def test_allocation_study_best_counts_and_dual_ratio_equals_the_gap(study):
    s = study["summary"]
    assert s[AL.NUKLEOLUS]["best_e"] == 40 and s[AL.DUAL_LUECKE]["best_rho"] == 40
    assert sum(s[nm]["best_e"] for nm in AL.RULES) == 40 and sum(s[nm]["best_rho"] for nm in AL.RULES) == 40
    assert all(r[AL.DUAL_LUECKE]["rho"] == pytest.approx(r["gap"], rel=1e-6) for r in study["rows"])           # in allen 40 Instanzen
    assert max(r["eps_rel"] for r in study["rows"]) < 0.02


# ---- E5 Ring ----------------------------------------------------------------------------------------------------------------------------------


def test_ring_preset_numbers():
    """Dreieck (s = 100, f = 50): c(N) 236,60, LP 225,00, ε* 7,735 (3,27 %); Fünferring: 400, 375, 20 (5,00 %); Sechserring: 450, 450, ε* = 0."""
    d = {n: ev.ring_row(n, 50) for n in (3, 5, 6)}
    assert (d[3]["cn"], d[3]["lp"], d[3]["eps"], d[3]["rel_eps"]) == pytest.approx((236.60, 225.00, 7.735, 0.0327), abs=0.005, rel=2e-3)
    assert (d[5]["cn"], d[5]["lp"], d[5]["eps"], d[5]["rel_eps"]) == pytest.approx((400.0, 375.0, 20.0, 0.05), rel=1e-6)
    assert (d[6]["cn"], d[6]["lp"], d[6]["eps"]) == pytest.approx((450.0, 450.0, 0.0), abs=1e-6)


def test_ring_table_formula_rows_and_relative_eps():
    """36 Zeilen (n = 3, 4, …, 11, 13, 15, 21; f = 10/25/50): die Formeln stimmen in 35, nicht beim Dreieck mit f = 50; ε*/c(N) bei n = 21 liegt bei 0,41/0,90/1,49 %, der größte Wert bei n = 5, f = 50 (5,00 %)."""
    rows = _ring()
    assert len(rows) == 36 and sum(r["formula_ok"] for r in rows) == 35
    assert [(r["n"], r["f"]) for r in rows if not r["formula_ok"]] == [(3, 50)]
    assert [round(100 * r["rel_eps"], 2) for r in rows if r["n"] == 21] == [0.41, 0.90, 1.49]
    top = max(rows, key=lambda r: r["rel_eps"])
    assert (top["n"], top["f"], round(100 * top["rel_eps"], 2)) == (5, 50, 5.0)
    odd, even = [r for r in rows if r["n"] % 2], [r for r in rows if r["n"] % 2 == 0]
    assert len(odd) == 24 and all(r["gap"] > 1 + 1e-9 for r in odd)                          # alle 24 ungeraden Ringe: Lücke größer als 1, Kern leer
    assert len(even) == 12 and all(abs(r["gap"] - 1) < 1e-9 and r["eps"] < 1e-6 for r in even)   # alle 12 geraden: Lücke 1, ε* = 0


def test_ring_formula_range_on_the_full_grid():
    """Raster n = 3, …, 11 und f = 5/10/25/50/75/100/150/200 (s = 100): die Formeln stimmen für ungerades n >= 5 nur bis f = 50 (n = 5) bzw. 75 (n = 7, 9, 11), für gerades n außer n = 6 und 10 bei f = 200."""
    failing = {}
    for n in range(3, 12):
        for f in (5, 10, 25, 50, 75, 100, 150, 200):
            if not ev.ring_row(n, f)["formula_ok"]:
                failing.setdefault(n, []).append(f)
    assert failing == {3: [50, 75, 100, 150, 200], 5: [75, 100, 150, 200], 6: [200], 7: [100, 150, 200], 9: [100, 150, 200], 10: [200], 11: [100, 150, 200]}


# ---- E6 Große Instanzen ------------------------------------------------------------------------------------------------------------------------


def test_large_counts_of_empty_cores():
    """m = 12, f = φ · n, φ = 3/6/10/15/25, je 100 Instanzen: n = 20 (1/1/1/3/0), n = 30 (4/2/9/1/0), zusammen 22 von 1 000; bei φ = 25 keine in den 200 Instanzen."""
    rows = _large()
    got = {n: [next(r["empty"] for r in rows if r["n"] == n and r["phi"] == phi) for phi in C.E6_PHI] for n in C.E6_N}
    assert got == {20: [1, 1, 1, 3, 0], 30: [4, 2, 9, 1, 0]}
    assert sum(r["empty"] for r in rows) == 22 and sum(r["total"] for r in rows) == 1000
    assert max(r["max_gap"] for r in rows) == pytest.approx(1.0136, abs=5e-5)


# ---- Handbeispiel und Presets ---------------------------------------------------------------------------------------------------------------


def test_hand_example_numbers():
    a = ev.analyse_instance(S.hand_triangle())
    assert (a.cn, a.lp, a.gap, a.eps, a.rho_star, a.subsidy) == pytest.approx((4.0, 3.0, 4 / 3, 2 / 3, 4 / 3, 1.0), rel=1e-9)
    assert a.alloc[AL.SHAPLEY] == pytest.approx([4 / 3] * 3) and a.alloc[AL.NUKLEOLUS] == pytest.approx([4 / 3] * 3, abs=1e-6)


def test_preset_numbers():
    """Zufall mit leerem Kern (n = 6, m = 4, f = 60, Zufalls-Seed 1362): ε* = 1,38 % von c(N); Shapley-Preset (Zufalls-Seed 182): zwei Standorte, Shapley-Überschuss 18,14."""
    a = ev.analyse(S.Settings(**C.PRESETS["Zufall mit leerem Kern"]))
    assert a.core_empty and round(100 * a.eps / a.cn, 2) == 1.38
    b = ev.analyse(S.Settings(**C.PRESETS["Zufall: Shapley außerhalb des Kerns"]))
    assert b.k_open == 2 and b.kz[AL.SHAPLEY].e_max == pytest.approx(18.14, abs=0.005)
    s = ev.analyse(S.Settings(**C.PRESETS["Standard (Zufall, n = 8, m = 6)"]))
    assert not s.core_empty and s.eps == pytest.approx(-5.538, abs=0.0005)
