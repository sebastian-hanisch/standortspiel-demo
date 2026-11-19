"""Der kopierte Baustein: `stg_rng.py` ist eine wörtliche Kopie von `ab-test-demo/abt_rng.py` (SplitMix64, Portfolio-Konvention).

Solange das Original im Portfolio-Ordner liegt, wird Zeile für Zeile verglichen; sonst gilt die Prüfsumme des Textes (Zeilenenden normalisiert), die beim Kopieren
bestimmt wurde. Ändert sich das Original, gehört die Änderung dorthin und die Kopie wird neu gezogen, nicht hier ergänzt."""

import ast
import hashlib
from pathlib import Path

import numpy as np
import pytest

from stg_rng import SplitMix64, uniform_block

ROOT = Path(__file__).resolve().parent.parent
RNG_SOURCE = ("ab-test-demo", "abt_rng.py")
COPY_SHA256 = "7ff588c02bcc96a1798c49ffb4e4b99decf7780eb8f119e8b2ba3af6fc88db48"   # Prüfsumme von abt_rng.py beim Kopieren (2026-11-18), ohne die Kopfzeile der Kopie


def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def test_rng_copy_is_verbatim_apart_from_the_header():
    folder, original = RNG_SOURCE
    source = ROOT.parent / folder / original
    mine = _lines(ROOT / "stg_rng.py")
    assert mine[0].startswith(f"# Wörtliche Kopie von {folder}/{original}")
    if not source.exists():
        pytest.skip("Original liegt nicht im Portfolio-Ordner")
    assert mine[1:] == _lines(source), "die Kopie weicht vom Original ab: Änderungen gehören ins Original, danach neu kopieren"


def test_copy_has_the_pinned_checksum():
    body = "\n".join(_lines(ROOT / "stg_rng.py")[1:]).encode("utf-8")
    assert hashlib.sha256(body).hexdigest() == COPY_SHA256


def test_copied_generator_has_the_documented_stream():
    """SplitMix64 mit Seed 0: die bekannten ersten Werte der Konvention (Vigna)."""
    rng = SplitMix64(0)
    assert [rng.next() for _ in range(3)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4, 0x06C45D188009454F]


def test_block_equals_the_scalar_stream():
    for seed in (0, 1, 35, 2 ** 63 + 5):
        rng = SplitMix64(seed)
        assert np.array_equal(uniform_block(seed, 100), np.array([rng.uniform() for _ in range(100)]))


def test_rng_module_has_no_other_imports_than_numpy_and_math():
    tree = ast.parse("\n".join(_lines(ROOT / "stg_rng.py")[1:]))
    names = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert names == {"math", "numpy"}


def test_the_demo_draws_no_findings_from_random_or_numpy_random():
    """Kein `random` und kein `numpy.random` im Kern: aller Zufall der Instanzen kommt aus SplitMix64 (`stg_presets.py` nutzt `random` nur für den Zufalls-Seed-Knopf)."""
    for path in ROOT.glob("stg_*.py"):
        if path.name in ("stg_presets.py", "stg_rng.py"):
            continue
        text = path.read_text(encoding="utf-8")
        assert "import random" not in text and "numpy.random" not in text and "np.random" not in text, path.name
