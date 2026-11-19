"""Relaxierung, Duallösung, Lücke."""

import numpy as np
import pytest

import stg_game as G
import stg_lp as L
from stg_scenario import Settings, make_instance


def test_hand_triangle_relaxation_value_is_three(hand):
    rel = L.lp_relaxation(hand.d, hand.fix)
    assert rel.value == pytest.approx(3.0, rel=1e-9)                                 # jeder Standort halb offen: 3 · 1/2 · 2
    assert rel.prices.sum() == pytest.approx(3.0, rel=1e-9)
    assert L.dual_violation(hand.d, hand.fix, rel.prices) <= 1e-9


def test_hand_triangle_integer_optimum_and_gap(hand):
    assert L.integer_optimum(hand.d, hand.fix)[0] == 4.0
    cn, lp, gap = L.gap(hand.d, hand.fix)
    assert cn == 4.0 and lp == pytest.approx(3.0, rel=1e-9) and gap == pytest.approx(4 / 3, rel=1e-9)
    assert L.core_empty_by_gap(hand.d, hand.fix)


def test_two_customers_have_no_gap(two):
    cn, lp, gap = L.gap(two.d, two.fix)
    assert cn == 13.0 and lp == pytest.approx(13.0) and gap == pytest.approx(1.0)
    assert not L.core_empty_by_gap(two.d, two.fix)


@pytest.mark.parametrize("seed", range(6))
def test_enumeration_equals_milp(seed):
    inst = make_instance(Settings(n=6, m=5, f=40, seed=seed))
    exact, _ = L.integer_optimum(inst.d, inst.fix)
    milp, proven = L.integer_optimum_milp(inst.d, inst.fix)
    assert proven and milp == pytest.approx(exact, rel=1e-9)


def test_relaxation_is_a_lower_bound_of_the_integer_optimum():
    for seed in range(10):
        inst = make_instance(Settings(n=7, m=5, f=60, seed=seed))
        assert L.lp_relaxation(inst.d, inst.fix).value <= L.integer_optimum(inst.d, inst.fix)[0] + 1e-9


def test_dual_violation_detects_a_price_that_is_too_high(hand):
    """Preise 4 je Kunde: Σ_i max(0, 4 - d_ij) = 4 + 4 + 2 = 10 > Fixkosten 2, Verletzung 8."""
    assert L.dual_violation(hand.d, hand.fix, np.array([4.0, 4.0, 4.0])) == pytest.approx(8.0)


def test_best_set_of_the_grand_coalition_matches_enumeration():
    inst = make_instance(Settings(n=5, m=4, f=30, seed=11))
    c, best = G.coalition_costs(inst.d, inst.fix)
    value, mask = L.integer_optimum(inst.d, inst.fix)
    assert value == pytest.approx(c[-1], rel=1e-12) and mask == best[-1]
