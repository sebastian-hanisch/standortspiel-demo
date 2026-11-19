"""Koalitionswerte: Handbeispiele, Gleichstand-Regel, Hilfsfunktionen."""

import numpy as np

import stg_game as G


def test_hand_triangle_coalition_values(hand):
    c, best = G.coalition_costs(hand.d, hand.fix)
    assert c.tolist() == [0.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 4.0]                  # Maske 1 = Kunde 1, 3 = Kunden 1 und 2, 7 = alle
    assert c[0] == 0.0 and len(c) == 8


def test_ties_between_location_sets_take_the_smaller_mask(hand):
    """c(N) = 4 gilt für {F12} (2 + 0 + 0 + 2) und für {F12, F13} (4 + 0 + 0 + 0); die kleinere Maske 1 = {F12} gewinnt, und es ist ein einziger offener Standort."""
    one_station = 2.0 + 0.0 + 0.0 + 2.0
    two_stations = 2.0 + 2.0 + 0.0 + 0.0 + 0.0
    assert one_station == two_stations == G.cost_of(7, hand.d, hand.fix)[0] == 4.0
    c, best = G.coalition_costs(hand.d, hand.fix)
    assert best[7] == 1 and G.popcount(best[7]) == 1
    assert G.cost_of(7, hand.d, hand.fix)[1] == 1                                   # die Schleifenfassung entscheidet den Gleichstand genauso


def test_two_customers_at_one_station(two):
    c, _ = G.coalition_costs(two.d, two.fix)
    assert c.tolist() == [0.0, 11.0, 12.0, 13.0]


def test_cost_of_the_empty_coalition_is_zero(hand):
    assert G.cost_of(0, hand.d, hand.fix) == (0.0, 0)


def test_location_sets_hand_triangle(hand):
    Fsum, DM = G.location_sets(hand.d, hand.fix)
    assert Fsum.tolist() == [0.0, 2.0, 2.0, 4.0, 2.0, 4.0, 4.0, 6.0]
    assert np.isinf(DM[0]).all()
    assert DM[3].tolist() == [0.0, 0.0, 0.0]                                       # F12 und F13: jeder Kunde hat einen Standort im Weg 0
    assert DM[1].tolist() == [0.0, 0.0, 2.0]


def test_incidence_rows_are_the_bits():
    S = G.incidence(3)
    assert S.shape == (8, 3) and S[5].tolist() == [1.0, 0.0, 1.0] and S[0].tolist() == [0.0, 0.0, 0.0]


def test_members_and_popcount():
    assert G.members(0b10110, 5) == [1, 2, 4] and G.popcount(0b10110) == 3 and G.popcount(0) == 0


def test_assignment_goes_to_the_nearest_open_station_with_the_smaller_index_on_ties():
    d = np.array([[3.0, 1.0, 1.0], [0.0, 5.0, 5.0]])
    assert G.assignment(d, 0b110).tolist() == [1, 1]                                # Kunde 1: Standorte 1 und 2 gleich weit: der kleinere Index
    assert G.assignment(d, 0b111).tolist() == [1, 0]


def test_costs_never_decrease_when_a_customer_joins():
    """Monotonie: c(S) <= c(T) für S in T (jede Lösung für T bedient auch S)."""
    rng = np.random.default_rng(3)
    d = rng.uniform(1, 20, (5, 3))
    c, _ = G.coalition_costs(d, np.array([5.0, 8.0, 3.0]))
    for S in range(32):
        for i in range(5):
            assert c[S] <= c[S | (1 << i)] + 1e-12
