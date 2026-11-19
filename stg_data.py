"""Vorgerechnete Messreihen (E1 Raster, E4 Aufteilungen bei leerem Kern) als JSON im Ordner data/ und ihr Erzeuger-Hash.

Die Raster-Reihe rechnet 33 600 Instanzen (rund zwei Minuten), die Aufteilungs-Reihe 40 Instanzen mit allen fünf Aufteilungen (rund eine halbe Minute): live zu teuer.
`tools/make_data.py` erzeugt die Dateien; `generator_hash()` ist der Hash über den Quelltext der Rechenmodule und steht in beiden Dateien.
`tests/test_data.py` vergleicht ihn mit dem aktuellen Stand und rechnet Stichproben neu: wer den Kern ändert, muss die Dateien neu erzeugen."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
GENERATOR_FILES = ("stg_rng.py", "stg_scenario.py", "stg_game.py", "stg_core.py", "stg_lp.py", "stg_allocations.py")
RASTER_FILE = DATA / "raster_leere_kerne.json"
ALLOCATION_FILE = DATA / "aufteilungen_leerer_kern.json"


def generator_hash() -> str:
    """SHA-256 über den Quelltext der Rechenmodule (Zeilenenden normalisiert, damit Windows und Linux denselben Hash bilden)."""
    h = hashlib.sha256()
    for name in GENERATOR_FILES:
        text = "\n".join((ROOT / name).read_text(encoding="utf-8").splitlines())
        h.update(name.encode("utf-8") + b"\0" + text.encode("utf-8") + b"\0")
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_raster() -> dict:
    return load_json(RASTER_FILE)


def load_allocations() -> dict:
    return load_json(ALLOCATION_FILE)
