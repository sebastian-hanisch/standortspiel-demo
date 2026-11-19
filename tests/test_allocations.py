"""Die fünf Aufteilungen und ihre Kennzahlen."""

import itertools

import numpy as np
import pytest

import stg_allocations as AL
import stg_constants as C
import stg_evaluation as ev
import stg_game as G
import stg_scenario as S

EMPTY_PRESET = "Zufall mit leerem Kern"


def test_every_allocation_sums_to_the_cost_of_the_grand_coalition():
    for name in ("Standard (Zufall, n = 8, m = 6)", EMPTY_PRESET, "Fünferring"):
        a = ev.analyse(S.Settings(**C.PRESETS[name]))
        assert set(a.alloc) == set(AL.RULES)
        for rule, x in a.alloc.items():
            assert x.sum() == pytest.approx(a.cn, rel=1e-9), (name, rule)


def test_proportional_and_equal_on_the_two_customer_example(two):
    c, _ = G.coalition_costs(two.d, two.fix)
    assert AL.proportional(c, 2) == pytest.approx([13 * 11 / 23, 13 * 12 / 23], rel=1e-12)      # c(N) · c({i}) / Σ c({j})
    assert AL.equal(c, 2).tolist() == [6.5, 6.5]


def test_kennzahlen_on_the_hand_triangle(hand):
    c, _ = G.coalition_costs(hand.d, hand.fix)
    k = AL.kennzahlen(np.array([4 / 3] * 3), c, 3)
    assert k.e_max == pytest.approx(2 / 3, rel=1e-9) and k.rho == pytest.approx(4 / 3, rel=1e-9) and k.blocking == 3 and k.worst in (3, 5, 6)


def test_kennzahlen_of_an_allocation_in_the_core(two):
    c, _ = G.coalition_costs(two.d, two.fix)
    k = AL.kennzahlen(np.array([6.0, 7.0]), c, 2)
    assert k.e_max == pytest.approx(-5.0) and k.rho == pytest.approx(7 / 12) and k.blocking == 0 and k.worst == 1     # beide Überschüsse sind -5 (6 - 11, 7 - 12): bei Gleichstand gilt die kleinere Maske


def test_dual_times_gap_has_ratio_equal_to_the_gap_when_the_core_is_empty_and_is_in_the_core_otherwise():
    for name in (EMPTY_PRESET, "Dreieck (Ring mit n = 3)", "Fünferring"):
        a = ev.analyse(S.Settings(**C.PRESETS[name]))
        assert a.kz[AL.DUAL_LUECKE].rho == pytest.approx(a.gap, rel=1e-6), name
    a = ev.analyse(S.Settings(**C.PRESETS["Standard (Zufall, n = 8, m = 6)"]))
    assert a.gap == pytest.approx(1.0) and a.kz[AL.DUAL_LUECKE].e_max <= C.TOL


def test_nucleolus_minimises_the_largest_excess():
    a = ev.analyse(S.Settings(**C.PRESETS[EMPTY_PRESET]))
    assert a.kz[AL.NUKLEOLUS].e_max == pytest.approx(a.eps, abs=1e-6)
    assert all(a.kz[AL.NUKLEOLUS].e_max <= k.e_max + 1e-6 for k in a.kz.values())


def test_branch_test_each_pair_of_allocations_differs_on_an_empty_core_instance():
    """Zweig-Test (Nullspalten-Regel): auf der Zufallsinstanz mit leerem Kern unterscheiden sich alle zehn Paare der fünf Aufteilungen in mindestens einem Anteil um mehr als 0,01."""
    a = ev.analyse(S.Settings(**C.PRESETS[EMPTY_PRESET]))
    assert a.core_empty
    for r1, r2 in itertools.combinations(AL.RULES, 2):
        assert np.abs(a.alloc[r1] - a.alloc[r2]).max() > 0.01, (r1, r2)


def test_allocation_table_rows_are_formatted_with_the_decimal_comma():
    a = ev.analyse(S.Settings(**C.PRESETS["Standard (Zufall, n = 8, m = 6)"]))
    rows = ev.allocation_table(a)
    assert [r["Aufteilung"] for r in rows] == list(AL.RULES)
    assert next(r for r in rows if r["Aufteilung"] == AL.NUKLEOLUS)["im Kern"] == "ja"
    assert next(r for r in rows if r["Aufteilung"] == AL.GLEICH)["im Kern"] == "nein"
    assert all("." not in r["in % von c(N)"] for r in rows)


def test_coalition_rows_sort_the_largest_excess_first_and_group_rows_sum_to_the_grand_cost():
    a = ev.analyse(S.Settings(**C.PRESETS[EMPTY_PRESET]))
    rows = ev.coalition_rows(a)
    assert len(rows) == 2 ** 6 - 2 and len(ev.coalition_rows(a, 5)) == 5
    values = [float(r["Überschuss bei x(Least Core)"].replace(",", ".")) for r in rows]
    assert values == sorted(values, reverse=True) and values[0] == pytest.approx(a.eps, abs=1e-3)
    groups = ev.group_rows(a)
    assert a.k_open == 2 and len(groups) == 3 and groups[-1]["Standort"] == "Summe" and groups[-1]["c(Gruppe)"] == ev.de(a.cn, 2)
