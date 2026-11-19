"""Erzeugt data/raster_leere_kerne.json (E1) und data/aufteilungen_leerer_kern.json (E4).

Aufruf aus dem Demo-Ordner: <python> tools/make_data.py [raster|aufteilungen|alle]. Das Raster rechnet rund zwei bis drei Minuten, die Aufteilungen rund eine halbe."""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import stg_constants as C  # noqa: E402
import stg_data as D  # noqa: E402
import stg_evaluation as ev  # noqa: E402


def make_raster() -> None:
    t0 = time.perf_counter()
    cells = [ev.raster_cell(n, m, f) for n in C.RASTER_N for m in C.RASTER_M for f in C.RASTER_F]
    payload = dict(
        generator_hash=D.generator_hash(),
        params=dict(n=list(C.RASTER_N), m=list(C.RASTER_M), f=list(C.RASTER_F), blocks=C.RASTER_BLOECKE, per_block=C.RASTER_PRO_BLOCK, tol=C.TOL, gap_tol=C.GAP_TOL),
        cells=cells,
        seconds=round(time.perf_counter() - t0, 1),
    )
    D.DATA.mkdir(exist_ok=True)
    D.RASTER_FILE.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Raster: {sum(c['total'] for c in cells)} Instanzen, {sum(c['empty'] for c in cells)} leere Kerne, {payload['seconds']} s")


def make_allocations() -> None:
    t0 = time.perf_counter()
    study = ev.allocation_study()
    payload = dict(
        generator_hash=D.generator_hash(),
        params=dict(configs=[list(k) for k in C.E4_KONFIG], per_config=C.E4_PRO_KONFIG, tol=C.TOL),
        rows=study["rows"],
        summary=study["summary"],
        seconds=round(time.perf_counter() - t0, 1),
    )
    D.DATA.mkdir(exist_ok=True)
    D.ALLOCATION_FILE.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Aufteilungen: {len(study['rows'])} Instanzen, {payload['seconds']} s")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "alle"
    if what in ("raster", "alle"):
        make_raster()
    if what in ("aufteilungen", "alle"):
        make_allocations()
