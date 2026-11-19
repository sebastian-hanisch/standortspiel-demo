"""Vorgerechnete Messreihen (data/*.json): Erzeuger-Hash, Parameter, Aufbau und Stichproben, die neu gerechnet werden.

Wer den Kern ändert (Quelltext der Rechenmodule), muss `tools/make_data.py` neu laufen lassen: sonst steht hier der Hash-Test rot. Zahlen, die live neu gerechnet werden,
vergleicht der Test exakt (ganze Zahlen) oder als Band (Anteile)."""

import pytest

import stg_allocations as AL
import stg_constants as C
import stg_data as D
import stg_evaluation as ev
from stg_scenario import uniform_instance


@pytest.fixture(scope="module")
def raster():
    return D.load_raster()


@pytest.fixture(scope="module")
def study():
    return D.load_allocations()


def test_both_files_carry_the_current_generator_hash(raster, study):
    assert raster["generator_hash"] == D.generator_hash() == study["generator_hash"]


def test_parameters_match_the_constants(raster, study):
    p = raster["params"]
    assert (tuple(p["n"]), tuple(p["m"]), tuple(p["f"]), p["blocks"], p["per_block"]) == (C.RASTER_N, C.RASTER_M, C.RASTER_F, C.RASTER_BLOECKE, C.RASTER_PRO_BLOCK)
    assert p["tol"] == C.TOL and p["gap_tol"] == C.GAP_TOL
    assert [tuple(k) for k in study["params"]["configs"]] == list(C.E4_KONFIG) and study["params"]["per_config"] == C.E4_PRO_KONFIG


def test_raster_has_every_cell_once_with_consistent_counts(raster):
    cells = raster["cells"]
    assert len(cells) == len(C.RASTER_N) * len(C.RASTER_M) * len(C.RASTER_F) == 84
    assert len({(c["n"], c["m"], c["f"]) for c in cells}) == 84
    for c in cells:
        assert c["total"] == C.RASTER_BLOECKE * C.RASTER_PRO_BLOCK and sum(c["by_block"]) == c["empty"] and 0 <= c["empty"] <= c["total"]


@pytest.mark.parametrize("n,m,f", [(5, 3, 45), (6, 4, 60), (6, 6, 100)])
def test_raster_cells_recompute_to_the_same_counts(raster, n, m, f):
    stored = next(c for c in raster["cells"] if (c["n"], c["m"], c["f"]) == (n, m, f))
    fresh = ev.raster_cell(n, m, f)
    assert fresh["by_block"] == stored["by_block"] and fresh["agree"] == stored["agree"]
    assert fresh["max_rel_eps"] == pytest.approx(stored["max_rel_eps"], rel=1e-6, abs=1e-9)


def test_allocation_rows_have_the_expected_shape_and_first_instance_recomputes(study):
    rows = study["rows"]
    assert len(rows) == len(C.E4_KONFIG) * C.E4_PRO_KONFIG == 40
    first = rows[0]
    fresh = ev.allocation_row(uniform_instance(first["n"], first["m"], first["f"], first["seed"]))
    assert fresh["eps_rel"] == pytest.approx(first["eps_rel"], rel=1e-6) and fresh["gap"] == pytest.approx(first["gap"], rel=1e-9)
    for name in AL.RULES:
        assert fresh[name]["e_rel"] == pytest.approx(first[name]["e_rel"], rel=1e-5, abs=1e-9) and fresh[name]["blocking"] == first[name]["blocking"]


def test_the_stored_seeds_are_the_first_empty_core_instances_of_their_configuration(study):
    n, m, f = C.E4_KONFIG[0]
    stored = [r["seed"] for r in study["rows"] if (r["n"], r["m"], r["f"]) == (n, m, f)]
    assert ev.find_empty_instances(n, m, f, 3) == stored[:3]


def test_summary_is_the_summary_of_the_rows(study):
    fresh = ev.allocation_summary(study["rows"])
    assert fresh.keys() == study["summary"].keys()
    for key, value in fresh.items():
        stored = study["summary"][key]
        if isinstance(value, dict):
            assert value == {k: pytest.approx(v, rel=1e-9) for k, v in stored.items()}
        else:
            assert value == pytest.approx(stored, rel=1e-9)
