"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Schwelle und jede Zahl im Text steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zahlen oder Zeilen, nicht Seeds. Jedes Preset und die Ränder laufen zusätzlich in `test_presets.py` durch."""

import stg_allocations as AL
import stg_constants as C
import stg_evaluation as ev
from stg_allocations import Kennzahlen


def test_number_formats_use_the_decimal_comma_and_no_negative_zero():
    assert ev.de(1234.5678, 2) == "1234,57" and ev.de(-0.0004, 2) == "0,00" and ev.de(-2.5, 1) == "-2,5"
    assert ev.pct(0.0327, 2) == "3,27 %" and ev.num(33600) == "33.600" and ev.count_text(122, 33600) == "122 von 33.600" and ev.count_text(7, 400) == "7 von 400"


# ---- Kernfrage ---------------------------------------------------------------------------------------------------------------------------


def test_core_verdict_empty_names_eps_share_gap_and_price():
    kind, text = ev.verdict_core(7.735, 236.6, 1.0516, 11.6, 3)
    assert kind == "warning" and "Der Kern ist leer" in text
    assert "ε* = 7,735" in text and "3,27 % von c(N) = 236,60" in text and "1,0516" in text and "Zuschuss von 11,600" in text


def test_core_verdict_thresholds_at_plus_and_minus_tolerance():
    assert ev.verdict_core(C.TOL, 100.0, 1.0, 0.0, 4)[0] == "info"                    # genau an der Toleranz: nicht leer
    assert ev.verdict_core(C.TOL * 1.01, 100.0, 1.0, 0.0, 4)[0] == "warning"
    assert ev.verdict_core(-C.TOL, 100.0, 1.0, 0.0, 4)[0] == "info"                   # ohne Spielraum bis einschließlich -TOL
    assert ev.verdict_core(-C.TOL * 1.01, 100.0, 1.0, 0.0, 4)[0] == "success"


def test_core_verdict_without_slack_and_with_slack_texts():
    _, text = ev.verdict_core(0.0, 450.0, 1.0, 0.0, 6)
    assert "keinen Spielraum" in text and "ε* = 0,000" in text and "1,0000" in text
    kind, text = ev.verdict_core(-5.5, 100.0, 1.0, 0.0, 8)
    assert kind == "success" and "ε* = -5,500" in text and "mindestens 5,500" in text


def test_core_verdict_for_a_single_customer():
    kind, text = ev.verdict_core(float("-inf"), 7.0, 1.0, 0.0, 1)
    assert kind == "info" and "einzigen Kunden" in text


def test_gap_verdict_agreement_and_disagreement():
    kind, text = ev.verdict_gap(True, True, 1.0516, 236.6, 225.0)
    assert kind == "success" and "**leer**" in text and "bestätigt" in text and "größer als 1" in text and "236,600" in text and "225,000" in text
    kind, text = ev.verdict_gap(False, False, 1.0, 50.0, 50.0)
    assert kind == "success" and "**nicht leer**" in text and "gleich 1" in text
    kind, text = ev.verdict_gap(True, False, 1.0, 50.0, 50.0)
    assert kind == "warning" and "widerspricht" in text and "Rechenrauschen" in text


# ---- Was wählen --------------------------------------------------------------------------------------------------------------------------


def _kz(e, rho, blocking=1):
    return Kennzahlen(e, rho, blocking, 1)


def test_choice_verdict_empty_core_names_best_by_excess_and_by_ratio():
    kz = {AL.NUKLEOLUS: _kz(3.0, 1.02), AL.SHAPLEY: _kz(9.0, 1.05), AL.DUAL_LUECKE: _kz(4.0, 1.01), AL.PROPORTIONAL: _kz(20.0, 1.2), AL.GLEICH: _kz(30.0, 1.3)}
    kind, text = ev.verdict_choice(kz, 3.0, 300.0, True)
    assert kind == "info" and "kleinste größte Überschuss ist 3,000 (1,00 % von c(N)) bei Nukleolus" in text and "ε* = 3,000" in text
    assert "1,0100 bei Dual × Lücke" in text


def test_choice_verdict_empty_core_with_all_rules_equal_says_so():
    kz = {nm: _kz(20.0, 1.0667) for nm in AL.RULES}
    kind, text = ev.verdict_choice(kz, 20.0, 400.0, True)
    assert kind == "info" and "für alle 5 Aufteilungen gleich" in text and "5,00 % von c(N)" in text and "nichts" in text


def test_choice_verdict_nonempty_core_lists_inside_and_outside():
    kz = {AL.NUKLEOLUS: _kz(-5.0, 0.9), AL.SHAPLEY: _kz(0.9, 1.01, 2), AL.DUAL_LUECKE: _kz(0.0, 0.95), AL.PROPORTIONAL: _kz(31.0, 1.2, 9), AL.GLEICH: _kz(43.0, 1.3, 7)}
    kind, text = ev.verdict_choice(kz, -5.0, 200.0, False)
    assert kind == "info" and "Im Kern liegen: Nukleolus, Dual × Lücke." in text
    assert "Außerhalb liegen: Shapley, proportional, gleich" in text and "am größten ist der Überschuss bei gleich mit 43,000 (21,50 % von c(N)), bei 7 blockierenden Koalitionen" in text


def test_choice_verdict_nonempty_core_edge_cases_all_inside_and_none_inside():
    inside = {nm: _kz(-1.0, 0.9, 0) for nm in AL.RULES}
    assert ev.verdict_choice(inside, -1.0, 100.0, False)[0] == "success"
    outside = {nm: _kz(1.0, 1.1, 3) for nm in AL.RULES}
    _, text = ev.verdict_choice(outside, -1.0, 100.0, False)
    assert "Keine der gezeigten Aufteilungen liegt im Kern." in text


# ---- Experimente -------------------------------------------------------------------------------------------------------------------------


def test_raster_verdict_names_counts_and_all_most_affected_cells():
    kind, text = ev.verdict_raster(122, 33600, 41, 84, [(6, 6, 100), (8, 8, 100)], 7, 400, 0.0143)
    assert kind == "info" and "122 von 33.600 Instanzen leer (0,36 %)" in text and "41 von 84 Zellen" in text
    assert "n = 6, m = 6, f = 100 und n = 8, m = 8, f = 100 mit je 7 von 400 (1,75 %)" in text and "1,43 % von c(N)" in text and "selten und der Effekt klein" in text


def test_triangle_verdict_names_the_ranges_and_counts_mixed_cells():
    rows = [dict(sigma=0, f=30, empty=400, total=400), dict(sigma=0, f=73, empty=400, total=400), dict(sigma=0, f=80, empty=0, total=400),
            dict(sigma=5, f=30, empty=380, total=400), dict(sigma=5, f=80, empty=1, total=400), dict(sigma=20, f=100, empty=0, total=400)]
    kind, text = ev.verdict_triangle(rows)
    assert kind == "info" and "bei f = 30, 73 in allen Instanzen leer und bei f = 80 in keiner" in text and "f = 73,2" in text
    assert "in 2 von 3 Zellen" in text and "zwischen 0 und 400" in text


def test_shapley_verdict_sums_over_the_fixed_costs():
    rows = [dict(f=10, by_k={1: (3, 4), 2: (1, 5)}), dict(f=30, by_k={1: (2, 2), 2: (0, 7), 3: (0, 1)})]
    kind, text = ev.verdict_shapley_k(rows)
    assert kind == "info" and "k = 1: 5 von 6; k = 2: 1 von 12; k = 3: 0 von 1" in text
    assert "meist" not in text and "selten" not in text                                  # nur die Zählung, kein Urteilswort


def _summary():
    s = {nm: dict(e_mean=m, rho_mean=r, best_e=be, best_rho=br) for nm, m, r, be, br in (
        (AL.NUKLEOLUS, 0.0049, 1.0103, 40, 0), (AL.SHAPLEY, 0.0278, 1.0485, 0, 0), (AL.DUAL_LUECKE, 0.0061, 1.0073, 0, 40), (AL.PROPORTIONAL, 0.07, 1.13, 0, 0), (AL.GLEICH, 0.086, 1.18, 0, 0))}
    s["_n"] = 40
    return s


def test_allocation_verdict_names_best_rules_and_shapley():
    kind, text = ev.verdict_allocations(_summary())
    assert kind == "info" and "In 40 Instanzen mit leerem Kern hat Nukleolus den kleinsten größten Überschuss (im Mittel 0,49 % von c(N), in 40 von 40 Instanzen der beste)" in text
    assert "kleinste Verhältnis x(S)/c(S) hat Dual × Lücke (im Mittel 1,0073, in 40 von 40 der beste)" in text and "Shapley-Wert liegt bei 2,78 %" in text


def test_ring_verdict_counts_empty_odd_rings_and_formula_rows():
    rows = [dict(n=5, f=50, gap=1.0667, rel_eps=0.05, formula_ok=True), dict(n=6, f=50, gap=1.0, rel_eps=0.0, formula_ok=True),
            dict(n=7, f=100, gap=1.03, rel_eps=0.02, formula_ok=False), dict(n=9, f=1, gap=1.0, rel_eps=0.0, formula_ok=True)]
    kind, text = ev.verdict_ring(rows)
    assert kind == "info" and "Bei 2 von 3 ungeraden Ringen" in text and "stimmen in 3 von 4 Zeilen" in text and "5,00 % (n = 5, f = 50)" in text


def test_large_verdict_counts_cells_with_and_without_empty_cores():
    rows = [dict(n=20, phi=3, empty=1, total=100), dict(n=20, phi=25, empty=0, total=100), dict(n=30, phi=10, empty=9, total=100)]
    kind, text = ev.verdict_large(rows)
    assert kind == "info" and "In 2 von 3 Zellen" in text and "in 1 wurde in 100 Instanzen keiner gezählt" in text and "9 von 100 bei n = 30 und f = 10 · n (9,0 %)" in text
