"""Szenario: Zufall aus SplitMix64, Lagen (Zufall, Ballung, Ring), Fixkosten, feste Seeds."""

import math

import numpy as np
import pytest

import stg_constants as C
import stg_scenario as S
from stg_rng import uniform_block


def _st(**kw):
    return S.Settings(**kw)


def test_same_settings_give_the_same_instance_and_other_seeds_differ():
    a, b, c = S.make_instance(_st(seed=5)), S.make_instance(_st(seed=5)), S.make_instance(_st(seed=6))
    assert np.array_equal(a.d, b.d) and np.array_equal(a.fix, b.fix)
    assert not np.array_equal(a.d, c.d)


def test_random_layout_is_taken_from_the_splitmix_block():
    """Kunden = die ersten 2n Zahlen des Blocks mal 100, Standorte = die nächsten 2m."""
    inst = S.make_instance(_st(n=4, m=3, seed=9))
    u = uniform_block(9, 2 * 4 + 2 * 3)
    assert inst.pk.ravel().tolist() == (u[:8] * 100).tolist() and inst.ps.ravel().tolist() == (u[8:14] * 100).tolist()
    assert inst.d.shape == (4, 3) and (inst.pk >= 0).all() and (inst.pk <= 100).all()


def test_distances_are_euclidean():
    inst = S.make_instance(_st(n=3, m=2, seed=2))
    assert inst.d[1, 0] == pytest.approx(math.hypot(*(inst.pk[1] - inst.ps[0])), rel=1e-12)


def test_fixed_costs_uniform_or_spread():
    uniform = S.make_instance(_st(f=60, m=6, seed=4))
    assert uniform.fix.tolist() == [60.0] * 6
    spread = S.make_instance(_st(f=60, m=6, fix=C.FIX_STREUEND, seed=4))
    assert (spread.fix >= 30.0).all() and (spread.fix < 90.0).all() and len(set(spread.fix.tolist())) == 6


@pytest.mark.parametrize("n", [3, 5, 8])
def test_ring_neighbours_have_distance_s_and_each_station_sits_between_two_customers(n):
    inst = S.make_instance(_st(lage=C.LAGE_RING, n=n, m=2, s=100, sigma=0))
    assert inst.d.shape == (n, n)                                                   # beim Ring gibt es n Standorte, der Regler m wirkt nicht
    for i in range(n):
        assert np.linalg.norm(inst.pk[i] - inst.pk[(i + 1) % n]) == pytest.approx(100.0, rel=1e-9)
        assert inst.d[i, i] == pytest.approx(50.0, rel=1e-9) and inst.d[(i + 1) % n, i] == pytest.approx(50.0, rel=1e-9)


def test_ring_with_three_customers_is_the_equilateral_triangle_with_height_below_the_far_station():
    inst = S.ring_instance(3, 50)
    assert inst.d[2, 0] == pytest.approx(100 * math.sqrt(3) / 2, rel=1e-9)         # Kunde 3 zum Standort zwischen 1 und 2: die Höhe


def test_ring_scales_with_the_side_length():
    assert S.make_instance(_st(lage=C.LAGE_RING, n=5, s=200)).d[0, 0] == pytest.approx(100.0, rel=1e-9)


def test_ring_noise_stays_inside_plus_minus_sigma_per_coordinate_and_is_zero_for_sigma_zero():
    base = S.make_instance(_st(lage=C.LAGE_RING, n=6, sigma=0, seed=3))
    noisy = S.make_instance(_st(lage=C.LAGE_RING, n=6, sigma=10, seed=3))
    assert np.abs(noisy.pk - base.pk).max() <= 10.0 and np.abs(noisy.ps - base.ps).max() <= 10.0
    assert np.abs(noisy.pk - base.pk).max() > 1.0                                  # die Störung wirkt


def test_clusters_put_every_customer_near_one_of_two_centres():
    inst = S.make_instance(_st(lage=C.LAGE_BALLUNG, n=10, seed=7))
    centres = np.array(C.BALLUNG_ZENTREN)
    dist = np.abs(inst.pk[:, None, :] - centres[None, :, :]).max(axis=2)             # Tschebyschow-Abstand zum Zentrum
    assert (dist.min(axis=1) <= C.BALLUNG_BREITE).all()
    assert len({int(dist[i].argmin()) for i in range(10)}) == 2                     # beide Ballungen kommen vor


def test_the_layout_choice_changes_the_instance():
    a = S.make_instance(_st(lage=C.LAGE_ZUFALL, seed=3)).d
    b = S.make_instance(_st(lage=C.LAGE_BALLUNG, seed=3)).d
    assert not np.array_equal(a, b)


def test_raster_seeds_are_distinct_across_cells_blocks_and_instances():
    seeds = {S.raster_seed(n, m, f, b, i) for n in C.RASTER_N for m in C.RASTER_M for f in C.RASTER_F for b in range(4) for i in range(100)}
    assert len(seeds) == len(C.RASTER_N) * len(C.RASTER_M) * len(C.RASTER_F) * 4 * 100


def test_hand_triangle_tables(hand):
    assert hand.d.tolist() == [[0.0, 0.0, 2.0], [0.0, 2.0, 0.0], [2.0, 0.0, 0.0]] and hand.fix.tolist() == [2.0, 2.0, 2.0]
    assert hand.pk is None and hand.n == 3 and hand.m == 3
