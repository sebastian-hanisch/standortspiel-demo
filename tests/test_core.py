"""Kern, Least Core, Shapley und Nukleolus an den Handbeispielen."""

import numpy as np
import pytest

import stg_core as Co
import stg_game as G


def test_hand_triangle_least_core_and_ratio(hand):
    c, _ = G.coalition_costs(hand.d, hand.fix)
    eps, x = Co.least_core(c, 3)
    assert eps == pytest.approx(2 / 3, rel=1e-9)
    assert x.sum() == pytest.approx(4.0, rel=1e-12)
    assert Co.least_core(c, 3, mult=True)[0] == pytest.approx(4 / 3, rel=1e-9)
    assert Co.is_core_empty(c, 3)


def test_hand_triangle_shapley_and_nucleolus_are_four_thirds_each(hand):
    c, _ = G.coalition_costs(hand.d, hand.fix)
    assert Co.shapley(c, 3) == pytest.approx([4 / 3] * 3, rel=1e-9)
    assert Co.nucleolus(c, 3) == pytest.approx([4 / 3] * 3, rel=1e-6)


def test_two_customers(two):
    c, _ = G.coalition_costs(two.d, two.fix)
    assert Co.least_core(c, 2)[0] == pytest.approx(-5.0, rel=1e-9)                  # (c12 - c1 - c2) / 2 = (13 - 23) / 2
    assert Co.shapley(c, 2) == pytest.approx([6.0, 7.0], rel=1e-12)
    assert Co.nucleolus(c, 2) == pytest.approx([6.0, 7.0], rel=1e-6)
    assert not Co.is_core_empty(c, 2)


def test_single_customer_has_no_proper_coalition():
    c = np.array([0.0, 7.0])
    assert Co.least_core(c, 1)[0] == float("-inf")
    assert Co.shapley(c, 1).tolist() == [7.0] and Co.nucleolus(c, 1).tolist() == [7.0]
    assert not Co.is_core_empty(c, 1)


def test_excess_of_an_allocation(hand):
    c, _ = G.coalition_costs(hand.d, hand.fix)
    e = Co.excess([4 / 3] * 3, c, 3)
    single, pair = 4 / 3 - 2, 8 / 3 - 2                                          # Masken 1 bis 6: Kunde 1, 2, Paar 1+2, Kunde 3, Paar 1+3, Paar 2+3
    assert len(e) == 6 and e == pytest.approx([single, single, pair, single, pair, pair], rel=1e-9)


def test_shapley_is_efficient_and_symmetric():
    rng = np.random.default_rng(5)
    d = rng.uniform(1, 30, (5, 3))
    c, _ = G.coalition_costs(d, np.array([20.0, 25.0, 30.0]))
    assert Co.shapley(c, 5).sum() == pytest.approx(c[-1], rel=1e-9)
    c_sym, _ = G.coalition_costs(np.array([[2.0, 3.0], [2.0, 3.0], [2.0, 3.0]]), np.array([10.0, 10.0]))   # drei gleiche Kunden
    phi = Co.shapley(c_sym, 3)
    assert phi == pytest.approx([phi[0]] * 3, rel=1e-12)


def test_hand_triangle_is_not_submodular(hand):
    """Submodular hieße c(S ∪ T) + c(S ∩ T) <= c(S) + c(T); für S = {1, 2}, T = {1, 3} gilt c(123) + c(1) = 6 > 4 = c(12) + c(13). Fixkosten-Standortspiele sind also nicht submodular."""
    c, _ = G.coalition_costs(hand.d, hand.fix)
    s, t = 0b011, 0b101
    assert c[s | t] + c[s & t] == 6.0 and c[s] + c[t] == 4.0
