"""Orakel-Tests (DEMO-PLAYBOOK §12): Kernroutinen gegen einen anderen Rechenweg, in unter 10 Sekunden.

Orakel: (1) Koalitionswerte gegen Schleifen im Test (itertools, kein Matrixprodukt), (2) Least Core des Dreiecks von Hand gegen Gittersuche, (3) „Kern leer genau dann, wenn
Lücke > 1“ gegen das Least-Core-LP über alle Koalitionen, mit gezielt gesuchten leeren Kernen, (4) multiplikativer Least-Core-Wert gegen c(N)/LP, (5) Preis der Stabilität als
eigenes LP gegen c(N) - LP, (6) Duallösung gegen jede Koalitionsbedingung, (7) Shapley gegen alle Reihenfolgen, (8) Nukleolus gegen die Kern-Demo und gegen seine Definition,
(9) Ring-Formeln gegen das volle LP und gegen das gemischt-ganzzahlige Programm, (10) Dreieck-Schwelle gegen Halbierung. Der Scratch-Lauf des Baus (mehr Instanzen) steht im README."""

import itertools
import sys
from pathlib import Path

import numpy as np
import pytest

import stg_constants as C
import stg_core as Co
import stg_evaluation as ev
import stg_game as G
import stg_lp as L
from stg_scenario import Settings, make_instance, ring_instance, triangle_instance, uniform_instance

ROOT = Path(__file__).resolve().parent.parent
EMPTY_SEEDS = (21, 169, 275, 527, 575, 900, 906, 1326, 1362, 1378, 1406)      # Zufall gleichverteilt, n = 6, m = 4, f = 60: leerer Kern (gesucht über die Seeds 1 bis 1500)
NONEMPTY_SEEDS = tuple(range(1, 15))


def _loop_costs(d, fix):
    """Unabhängige Fassung: für jede Koalition und jede Standortmenge in Schleifen, mit itertools."""
    n, m = d.shape
    out = [0.0] * (1 << n)
    for mask in range(1, 1 << n):
        customers = [i for i in range(n) if mask >> i & 1]
        out[mask] = min(
            sum(fix[j] for j in stations) + sum(min(d[i][j] for j in stations) for i in customers)
            for size in range(1, m + 1) for stations in itertools.combinations(range(m), size)
        )
    return np.array(out)


def _instances(seeds, n=6, m=4, f=60):
    return [uniform_instance(n, m, f, s) for s in seeds]


@pytest.mark.parametrize("n,m,f,seed", [(4, 3, 20, 1), (4, 4, 40, 2), (3, 4, 60, 3), (5, 3, 30, 4), (4, 2, 10, 5), (5, 4, 60, 6)])
def test_coalition_costs_equal_independent_loops(n, m, f, seed):
    inst = uniform_instance(n, m, f, seed)
    c, _ = G.coalition_costs(inst.d, inst.fix)
    assert c == pytest.approx(_loop_costs(inst.d, inst.fix), rel=1e-12, abs=1e-12)


def test_hand_triangle_least_core_by_grid_search(hand):
    """Gitter x1, x2 in Schritten 1/60 (x3 = 4 - x1 - x2): der kleinste größte Überschuss ist 2/3, das LP findet dasselbe."""
    c, _ = G.coalition_costs(hand.d, hand.fix)
    best = min(
        Co.excess(np.array([a / 60, b / 60, 4 - a / 60 - b / 60]), c, 3).max()
        for a in range(0, 241) for b in range(0, 241 - a)
    )
    assert best == pytest.approx(2 / 3, abs=1e-9)
    assert Co.least_core(c, 3)[0] == pytest.approx(best, abs=1e-9)


def test_core_is_empty_exactly_when_the_gap_is_positive():
    """Mit gezielt gesuchten leeren Kernen (11) und nichtleeren (14), dazu Ringe und Dreieck: Least-Core-LP über alle Koalitionen gegen c(N) > LP."""
    cases = _instances(EMPTY_SEEDS) + _instances(NONEMPTY_SEEDS) + [ring_instance(n, 50) for n in (4, 5, 6, 7)] + [triangle_instance(100, 50, 0, 1)]
    empty = 0
    for inst in cases:
        c, _ = G.coalition_costs(inst.d, inst.fix)
        by_lp = Co.least_core(c, inst.n)[0] > C.TOL
        by_gap = L.core_empty_by_gap(inst.d, inst.fix)
        assert by_lp == by_gap
        empty += by_lp
    assert empty == len(EMPTY_SEEDS) + 3                                          # Ring n = 5 und 7 und das Dreieck; die Ringe n = 4 und 6 haben einen Kern, ε* = 0


def test_multiplicative_least_core_equals_the_gap_when_it_exceeds_one():
    """ρ* (nur echte Koalitionen) ist bei leerem Kern genau c(N)/LP; bei nichtleerem Kern liegt es bei höchstens 1 (die große Koalition mit Faktor 1 gehört zur Dualbedingung)."""
    for inst in _instances(EMPTY_SEEDS[:6]) + _instances(NONEMPTY_SEEDS[:6]) + [ring_instance(5, 50), ring_instance(6, 50)]:
        c, _ = G.coalition_costs(inst.d, inst.fix)
        cn, lp, gap = L.gap(inst.d, inst.fix)
        rho = Co.least_core(c, inst.n, mult=True)[0]
        assert max(rho, 1.0) == pytest.approx(gap, rel=1e-6)


def _price_of_stability(c, n):
    """Kleinstes Δ >= 0 mit x(S) <= c(S) für alle echten Koalitionen und x(N) = c(N) - Δ (ein eigenes LP, ohne die Relaxierung)."""
    from scipy.optimize import linprog

    S = Co.proper_incidence(n)
    res = linprog(np.r_[np.zeros(n), 1.0], A_ub=np.hstack([S, np.zeros((len(S), 1))]), b_ub=c[1:-1], A_eq=[np.r_[np.ones(n), 1.0]], b_eq=[c[-1]],
                  bounds=[(None, None)] * n + [(0, None)], method="highs")
    return float(res.x[-1])


def test_price_of_stability_equals_cn_minus_lp():
    for inst in _instances(EMPTY_SEEDS[:6]) + _instances(NONEMPTY_SEEDS[:6]) + [ring_instance(5, 50), ring_instance(6, 50)]:
        c, _ = G.coalition_costs(inst.d, inst.fix)
        cn, lp, _ = L.gap(inst.d, inst.fix)
        assert _price_of_stability(c, inst.n) == pytest.approx(cn - lp, abs=1e-6)


def test_dual_prices_are_feasible_and_satisfy_every_coalition_constraint():
    for inst in _instances(range(1, 21)) + [ring_instance(5, 50)]:
        c, _ = G.coalition_costs(inst.d, inst.fix)
        rel = L.lp_relaxation(inst.d, inst.fix)
        assert rel.prices.sum() == pytest.approx(rel.value, rel=1e-9)
        assert L.dual_violation(inst.d, inst.fix, rel.prices) <= 1e-9
        assert Co.excess(rel.prices, c, inst.n).max() <= 1e-7                      # x(S) <= c(S) für jede echte Koalition


def test_shapley_equals_the_average_over_all_orders():
    inst = uniform_instance(5, 4, 40, 8)
    c, _ = G.coalition_costs(inst.d, inst.fix)
    phi = np.zeros(5)
    orders = list(itertools.permutations(range(5)))
    for order in orders:
        mask = 0
        for i in order:
            phi[i] += c[mask | (1 << i)] - c[mask]
            mask |= 1 << i
    assert Co.shapley(c, 5) == pytest.approx(phi / len(orders), rel=1e-9)


def _kn_core():
    kern = ROOT.parent / "kern-demo"
    if not (kern / "kn_core.py").exists():
        pytest.skip("kern-demo liegt nicht im Portfolio-Ordner")
    sys.path.insert(0, str(kern))
    try:
        import kn_core
    finally:
        sys.path.remove(str(kern))
    return kn_core


def test_nucleolus_equals_the_kern_demo_and_minimises_the_largest_excess():
    kn = _kn_core()
    for inst in _instances(EMPTY_SEEDS[:4]) + _instances(NONEMPTY_SEEDS[:3]):
        c, _ = G.coalition_costs(inst.d, inst.fix)
        x = Co.nucleolus(c, inst.n)
        assert x == pytest.approx(kn.nucleolus(c, inst.n)[0], abs=1e-6)
        assert x.sum() == pytest.approx(c[-1], rel=1e-9)
        assert Co.excess(x, c, inst.n).max() == pytest.approx(Co.least_core(c, inst.n)[0], abs=1e-6)   # der Nukleolus erreicht den Least-Core-Wert


@pytest.mark.parametrize("n,f", [(5, 10), (5, 25), (5, 50), (7, 10), (7, 50), (9, 25)])
def test_ring_formulas_against_full_lp_and_milp(n, f):
    inst = ring_instance(n, f)
    c, _ = G.coalition_costs(inst.d, inst.fix)
    gap_formula, eps_formula = ev.ring_formulas(n, f)
    assert Co.least_core(c, n)[0] == pytest.approx(eps_formula, rel=1e-6)
    assert L.integer_optimum_milp(inst.d, inst.fix)[0] / L.lp_relaxation(inst.d, inst.fix).value == pytest.approx(gap_formula, rel=1e-9)
    assert c[-1] == pytest.approx((n + 1) / 2 * f + n * 100 / 2, rel=1e-9)         # c(N) = (n + 1)/2 · f + n · s/2 im gemessenen Bereich


@pytest.mark.parametrize("n,f", [(4, 50), (6, 50), (8, 25)])
def test_even_rings_have_a_core_without_slack(n, f):
    inst = ring_instance(n, f)
    c, _ = G.coalition_costs(inst.d, inst.fix)
    assert Co.least_core(c, n)[0] == pytest.approx(0.0, abs=1e-6)
    assert not Co.is_core_empty(c, n)


@pytest.mark.parametrize("n,f", [(5, 50), (6, 50), (7, 25), (3, 25)])
def test_symmetric_least_core_equals_the_full_lp_on_rings(n, f):
    inst = ring_instance(n, f)
    c, _ = G.coalition_costs(inst.d, inst.fix)
    sym = ev.max_excess_equal_share(inst.d, inst.fix, c[-1] / n)
    assert max(Co.least_core(c, n)[0], 0.0) == pytest.approx(max(sym, 0.0), abs=1e-6)


def test_triangle_threshold_by_bisection():
    """Kern des Dreiecks (s = 100) leer genau für f unterhalb (√3 - 1) · s = 73,2: Halbierung über das Least-Core-LP."""
    def empty(f):
        inst = ring_instance(3, f, 100.0)
        return Co.least_core(G.coalition_costs(inst.d, inst.fix)[0], 3)[0] > C.TOL

    lo, hi = 40.0, 120.0
    assert empty(lo) and not empty(hi)
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if empty(mid) else (lo, mid)
    assert lo == pytest.approx(ev.triangle_threshold(100.0), abs=1e-3)
    assert all(empty(f) for f in (5.0, 10.0, 20.0, 30.0, 36.0))                       # unterhalb von f = 36,6 (zwei Standorte billiger als einer) ebenfalls leer


def test_triangle_closed_form_for_one_open_station():
    """f = 50, s = 100: c(N) = f + s + s√3/2 (ein Standort, der dritte Kunde geht den langen Weg), ε* = 2/3 c(N) - (f + s)."""
    inst = triangle_instance(100, 50, 0, 1)
    c, _ = G.coalition_costs(inst.d, inst.fix)
    assert c[-1] == pytest.approx(50 + 100 + 100 * 3 ** 0.5 / 2, rel=1e-12)
    assert Co.least_core(c, 3)[0] == pytest.approx(2 / 3 * c[-1] - 150, rel=1e-9)


def test_a_single_open_station_leaves_no_slack_in_the_core_when_two_are_open():
    """Sind in der großen Koalition k >= 2 Standorte offen, zerfällt sie in unabhängige Gruppen: c(N) = Σ c(S_q), also gilt im Kern x(S_q) = c(S_q) und ε* >= 0."""
    checked = 0
    for seed in range(1, 60):
        inst = make_instance(Settings(n=6, m=4, f=60, seed=seed))
        c, best = G.coalition_costs(inst.d, inst.fix)
        if G.popcount(best[-1]) < 2:
            continue
        checked += 1
        groups = G.assignment(inst.d, int(best[-1]))
        mask_of = {q: sum(1 << i for i in range(6) if groups[i] == q) for q in set(groups.tolist())}
        assert sum(c[mk] for mk in mask_of.values()) == pytest.approx(c[-1], rel=1e-9)
        assert Co.least_core(c, 6)[0] >= -1e-7
    assert checked >= 15
