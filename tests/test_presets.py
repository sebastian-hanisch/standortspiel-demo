"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, und die erwartete Verdikt-Zeile je Preset (DEMO-PLAYBOOK §11a Punkt 7)."""

import pytest

import stg_allocations as AL
import stg_constants as C
import stg_evaluation as ev
import stg_presets as P
import stg_scenario as S


def _settings(name):
    return S.Settings(**C.PRESETS[name])


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_and_options():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            assert P.clamp_to_bounds(spec, preset[key]) == preset[key], (name, key)


def test_default_preset_equals_the_default_settings():
    assert _settings("Standard (Zufall, n = 8, m = 6)") == S.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


# Erwartete Verdikt-Zeile der Kernfrage je Preset: Art und tragende Wörter des Textes.
EXPECTED = {
    "Standard (Zufall, n = 8, m = 6)": ("success", "nicht leer"),
    "Dreieck (Ring mit n = 3)": ("warning", "leer"),
    "Fünferring": ("warning", "leer"),
    "Sechserring": ("info", "keinen Spielraum"),
    "Zufall mit leerem Kern": ("warning", "leer"),
    "Zufall: Shapley außerhalb des Kerns": ("info", "keinen Spielraum"),
}


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_each_preset_runs_through_with_the_expected_core_verdict(name):
    a = ev.analyse(_settings(name))
    kind, text = ev.verdict_core(a.eps, a.cn, a.gap, a.subsidy, a.inst.n)
    expected_kind, word = EXPECTED[name]
    assert kind == expected_kind and word in text
    assert ev.verdict_gap(a.core_empty, a.gap_empty, a.gap, a.cn, a.lp)[0] == "success"          # beide Kriterien stimmen überein
    assert ev.verdict_choice(a.kz, a.eps, a.cn, a.core_empty)[0] in ("info", "success")


def test_presets_state_in_their_help_what_the_measurement_shows():
    """Die Hilfetexte nennen den Kern-Zustand; er muss zur Messung passen (leer nur bei Dreieck, Fünferring und der gesuchten Instanz)."""
    empty = {name for name in C.PRESETS if ev.analyse(_settings(name)).core_empty}
    assert empty == {"Dreieck (Ring mit n = 3)", "Fünferring", "Zufall mit leerem Kern"}
    assert "Der Kern ist nicht leer" in C.PRESET_HELP["Standard (Zufall, n = 8, m = 6)"] and "leere Kern" in C.PRESET_HELP["Dreieck (Ring mit n = 3)"]
    assert "ungerade Ringe haben einen leeren Kern" in C.PRESET_HELP["Fünferring"] and "keinen Spielraum" in C.PRESET_HELP["Sechserring"]


def test_ring_presets_ignore_the_station_slider_and_have_symmetric_equal_allocations():
    """Beim Ring ist m wirkungslos (n Standorte); bei Fünfer- und Sechserring sind alle fünf Aufteilungen gleich (Drehsymmetrie), die Wahl der Regel ändert dort nichts."""
    for name in ("Fünferring", "Sechserring"):
        p = dict(C.PRESETS[name])
        a1, a2 = ev.analyse(S.Settings(**p)), ev.analyse(S.Settings(**{**p, "m": 2}))
        assert a1.cn == a2.cn and a1.inst.m == a2.inst.m == p["n"]
        e = [k.e_max for k in a1.kz.values()]
        assert max(e) - min(e) < 1e-6


def test_shapley_preset_has_two_open_stations_shapley_outside_and_nucleolus_inside():
    a = ev.analyse(_settings("Zufall: Shapley außerhalb des Kerns"))
    assert a.k_open == 2 and not a.core_empty
    assert a.kz[AL.SHAPLEY].e_max > 1.0 and a.kz[AL.NUKLEOLUS].e_max <= C.TOL and a.kz[AL.DUAL_LUECKE].e_max <= C.TOL

