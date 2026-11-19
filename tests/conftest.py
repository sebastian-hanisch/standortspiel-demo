"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stg_scenario import hand_triangle, instance_from_tables  # noqa: E402


@pytest.fixture
def hand():
    """Das Dreieck von Hand: Kunden 1, 2, 3, Standorte F12, F13, F23 mit Fixkosten 2, Wege 0 oder 2.
    Von Hand: Einzel- und Paarkosten 2 (der gemeinsame Standort), alle drei 4 (zwei Standorte, oder einer plus der Weg 2), LP 3 (jeder Standort halb offen),
    ε* = 2/3, ρ* = 4/3, Preis der Stabilität 1, Shapley = Nukleolus = 4/3 je Kunde."""
    return hand_triangle()


@pytest.fixture
def two():
    """Zwei Kunden an einem Standort (Fixkosten 10, Wege 1 und 2): c = 11, 12, 13; Shapley = Nukleolus = 6 und 7; ε* = -5."""
    return instance_from_tables([[1.0], [2.0]], [10.0], "Zwei Kunden")
