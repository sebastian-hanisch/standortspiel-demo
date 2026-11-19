"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): n = 1, n = 2, m = 1, Gleichstände, Reglerränder."""

import numpy as np
import pytest

import stg_constants as C
import stg_core as Co
import stg_evaluation as ev
import stg_game as G
import stg_lp as L
import stg_scenario as S


def test_single_customer_runs_through_every_routine():
    inst = S.instance_from_tables([[3.0, 5.0]], [10.0, 20.0])
    a = ev.analyse_instance(inst)
    assert a.cn == 13.0 and a.eps == float("-inf") and not a.core_empty and a.gap == pytest.approx(1.0)
    assert ev.coalition_rows(a) == [] and ev.group_rows(a) == []
    assert all(row["im Kern"] == "ja" for row in ev.allocation_table(a))
    assert ev.verdict_core(a.eps, a.cn, a.gap, a.subsidy, 1)[0] == "info"


def test_exactly_two_customers_is_the_smallest_game_with_a_proper_coalition(two):
    a = ev.analyse_instance(two)
    assert a.eps == pytest.approx(-5.0, rel=1e-9) and not a.core_empty
    assert a.alloc["Shapley"] == pytest.approx([6.0, 7.0]) and a.alloc["Nukleolus"] == pytest.approx([6.0, 7.0], abs=1e-6)
    assert len(ev.coalition_rows(a)) == 2


def test_two_customers_with_two_stations_that_each_prefer_their_own():
    inst = S.instance_from_tables([[0.0, 9.0], [9.0, 0.0]], [5.0, 5.0])
    c, best = G.coalition_costs(inst.d, inst.fix)
    assert c.tolist() == [0.0, 5.0, 5.0, 10.0] and G.popcount(best[3]) == 2        # zwei Standorte offen, Gruppen = Einzelne
    a = ev.analyse_instance(inst)
    assert a.k_open == 2 and a.eps == pytest.approx(0.0, abs=1e-9) and not a.core_empty    # kein Spielraum: jeder zahlt genau seine Alleinkosten
    assert [r["Gruppe"] for r in ev.group_rows(a)][:2] == ["K1", "K2"] and ev.group_rows(a)[-1]["c(Gruppe)"] == "10,00"


def test_single_station_has_no_gap_and_a_core():
    inst = S.make_instance(S.Settings(n=6, m=1, f=40, seed=3))
    a = ev.analyse_instance(inst)
    assert a.gap == pytest.approx(1.0) and not a.core_empty and a.k_open == 1


def test_identical_customers_get_identical_shares_and_stations_tie_to_the_smaller_index():
    d = np.tile([[4.0, 4.0]], (4, 1))                                              # beide Standorte gleich weit, gleiche Fixkosten
    inst = S.instance_from_tables(d, [10.0, 10.0])
    c, best = G.coalition_costs(inst.d, inst.fix)
    assert (best[1:] == 1).all()                                                   # Gleichstand zwischen den Standorten: kleinere Maske
    a = ev.analyse_instance(inst)
    for name, x in a.alloc.items():
        if name == "Dual × Lücke":
            assert x.sum() == pytest.approx(a.cn, rel=1e-9)                       # die Duallösung ist bei Gleichstand nicht eindeutig: HiGHS liefert hier [14, 4, 4, 4]
        else:
            assert x == pytest.approx([x[0]] * 4, abs=1e-6), name
    assert G.assignment(inst.d, 0b11).tolist() == [0, 0, 0, 0]


def test_equal_total_cost_in_two_ways_is_not_a_second_core_state(hand):
    """Dreieck von Hand: c(N) = 4 mit einem oder mit zwei Standorten; Kern leer in beiden Lesarten, Kosten und ε* hängen nicht an der gewählten Menge."""
    a = ev.analyse_instance(hand)
    assert a.cn == 4.0 and a.k_open == 1 and a.core_empty and a.eps == pytest.approx(2 / 3, rel=1e-9)


def test_slider_maximum_runs_through_and_is_consistent():
    """n = 10, m = 8 (Zufall) und Ring n = 10: alle Routinen laufen, ε* höchstens c(N), die Kriterien stimmen überein."""
    for settings in (S.Settings(n=C.N_MAX, m=C.M_MAX, f=C.F_MAX, seed=3), S.Settings(lage=C.LAGE_RING, n=C.N_MAX, f=C.F_MIN, sigma=C.SIGMA_MAX, seed=4),
                     S.Settings(lage=C.LAGE_BALLUNG, n=C.N_MAX, m=C.M_MAX, f=C.F_MIN, fix=C.FIX_STREUEND, seed=5)):
        a = ev.analyse(settings)
        assert a.inst.n == C.N_MAX and np.isfinite(a.eps) and a.eps <= a.cn and a.core_empty == a.gap_empty
        assert len(a.c) == 2 ** C.N_MAX and len(ev.coalition_rows(a)) == 2 ** C.N_MAX - 2


def test_slider_minimum_runs_through():
    for settings in (S.Settings(n=C.N_MIN, m=C.M_MIN, f=C.F_MIN, seed=0), S.Settings(lage=C.LAGE_RING, n=C.N_MIN, f=C.F_MAX, s=C.S_MIN, sigma=0, seed=0)):
        a = ev.analyse(settings)
        assert a.inst.n == C.N_MIN and a.core_empty == a.gap_empty


def test_all_fixed_costs_are_positive_so_ratios_are_defined():
    for fix in (C.FIX_EINHEITLICH, C.FIX_STREUEND):
        inst = S.make_instance(S.Settings(f=C.F_MIN, fix=fix, seed=0))
        assert (inst.fix > 0).all()
        c, _ = G.coalition_costs(inst.d, inst.fix)
        assert (c[1:] > 0).all()


def test_core_tolerance_for_the_empty_core():
    """ε* = (c12 - c1 - c2)/2: ein Wert von 0,5 TOL zählt als nicht leer, ein Wert von 2 TOL als leer."""
    assert not Co.is_core_empty(np.array([0.0, 1.0, 1.0, 2.0 + C.TOL]), 2)
    assert Co.is_core_empty(np.array([0.0, 1.0, 1.0, 2.0 + 4 * C.TOL]), 2)


def test_milp_path_for_more_stations_than_the_enumeration_limit():
    """Ring n = 13 hat 13 Standorte (mehr als die Aufzählung): gap() nimmt das gemischt-ganzzahlige Programm und trifft die Formel."""
    inst = S.ring_instance(13, 25)
    assert inst.m > C.M_ENUM_MAX
    cn, lp, gap = L.gap(inst.d, inst.fix)
    assert gap == pytest.approx(ev.ring_formulas(13, 25)[0], rel=1e-9)
