"""End-to-end Smoke-Test via Streamlits AppTest: lädt app.py mit den Standardeinstellungen, klickt jeden Preset-Button, fährt jeden Regler an Minimum und Maximum,
setzt den Permalink und klickt jeden ▶️-Knopf der Experimente (eigene Tests unten: das Gerüst lässt ▶️-Knöpfe aus, weil sie dort Animationen starten).

Regler, die nur beim Ring wirken (Abstand s, Streuung σ), sind außerhalb des Rings deaktiviert; ihre Randwerte werden deshalb nach dem Laden eines Ring-Presets gesetzt."""

import os

import pytest
from streamlit.testing.v1 import AppTest

import stg_constants as C
import stg_presets as P

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
RING_PRESET = "Dreieck (Ring mit n = 3)"
RING_ONLY = ("s_slider", "sigma_slider")


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _widget(at, key):
    for kind in ("slider", "selectbox", "number_input"):
        try:
            return getattr(at.sidebar, kind)(key=key)
        except KeyError:
            continue
    raise AssertionError(key)


def test_app_loads_without_exception():
    at = _fresh_app()
    assert any("Der Kern" in m.value or "Kern" in m.value for m in at.markdown)
    assert len(at.metric) == 6


def test_every_non_experiment_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        if "▶️" in label:
            continue                                                               # die Experiment-Knöpfe prüfen die Tests unten einzeln
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


@pytest.mark.parametrize("state_key", list(P.SETTING_SPECS))
@pytest.mark.parametrize("edge", ["min", "max"])
def test_every_control_at_its_minimum_and_maximum_does_not_raise(state_key, edge):
    at = _fresh_app()
    if state_key in RING_ONLY:
        at.sidebar.button(key=f"preset_{RING_PRESET}").click().run(timeout=TIMEOUT)
    spec = P.SETTING_SPECS[state_key]
    widget = _widget(at, state_key)
    if spec.options is not None:
        value = spec.options[0] if edge == "min" else spec.options[-1]
    else:
        value = spec.lo if edge == "min" else spec.hi
    widget.set_value(value).run(timeout=TIMEOUT)
    assert not at.exception, (state_key, edge, [str(e) for e in at.exception])


@pytest.mark.parametrize("lage", C.LAGEN)
@pytest.mark.parametrize("edge", ["min", "max"])
def test_all_minima_and_all_maxima_together(lage, edge):
    at = _fresh_app()
    _widget(at, "lage_select").set_value(lage).run(timeout=TIMEOUT)
    for state_key, spec in P.SETTING_SPECS.items():
        if spec.options is not None:
            continue
        widget = _widget(at, state_key)
        if getattr(widget.proto, "disabled", False):
            continue                                                               # m beim Ring, s und σ außerhalb des Rings
        widget.set_value(spec.lo if edge == "min" else spec.hi)
    _widget(at, "fix_select").set_value(C.FIX_STREUEND)
    at.run(timeout=TIMEOUT)
    assert not at.exception, (lage, edge, [str(e) for e in at.exception])


def test_the_regulators_that_only_work_for_the_ring_are_disabled_elsewhere_and_m_is_disabled_for_the_ring():
    at = _fresh_app()
    assert _widget(at, "s_slider").proto.disabled and _widget(at, "sigma_slider").proto.disabled and not _widget(at, "m_slider").proto.disabled
    at.sidebar.button(key=f"preset_{RING_PRESET}").click().run(timeout=TIMEOUT)
    assert not _widget(at, "s_slider").proto.disabled and not _widget(at, "sigma_slider").proto.disabled and _widget(at, "m_slider").proto.disabled


def test_permalink_sets_the_controls_and_clamps_to_the_bounds():
    at = AppTest.from_file(APP_PATH)
    at.query_params["lage"] = C.LAGE_RING
    at.query_params["n"] = "5"
    at.query_params["f"] = "9999"                                                  # über der Grenze: wird auf F_MAX begrenzt
    at.query_params["fix"] = "unbekannt"                                           # kein Eintrag der Auswahl: ignoriert
    at.query_params["seed"] = "17"
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert _widget(at, "lage_select").value == C.LAGE_RING and _widget(at, "n_slider").value == 5
    assert _widget(at, "f_slider").value == C.F_MAX and _widget(at, "fix_select").value == C.FIX_EINHEITLICH and _widget(at, "seed_input").value == 17


def _click(at, label_part):
    button = next(b for b in at.button if label_part in b.label)
    button.click().run(timeout=TIMEOUT)
    assert not at.exception, (label_part, [str(e) for e in at.exception])


@pytest.mark.parametrize("label,heading", [
    ("Zelle rechnen", "Kern leer in"), ("Dreieck rechnen", "Ohne Streuung"), ("Shapley-Zählung", "Der Shapley-Wert liegt"),
    ("Ringe rechnen", "ungeraden Ringen"), ("Große Instanzen", "Zellen (n, f/n)"),
])
def test_every_experiment_button_runs_and_shows_its_verdict(label, heading):
    at = _fresh_app()
    _click(at, label)
    texts = " ".join(e.value for kind in (at.markdown, at.info, at.warning, at.success) for e in kind)
    assert heading in texts
