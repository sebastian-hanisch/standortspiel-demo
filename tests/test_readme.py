"""README und App sagen dasselbe: geteilter Text, Testzahl, genannte Testnamen, keine offenen Platzhalter."""

import re
import subprocess
import sys
from pathlib import Path

from stg_texts import ASSUMPTIONS_MARKDOWN

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_the_shared_assumptions_text_is_in_the_readme_verbatim():
    assert ASSUMPTIONS_MARKDOWN.strip() in README


def test_the_test_count_in_the_readme_matches_the_suite():
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "tests", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True, text=True, timeout=300).stdout
    collected = int(re.search(r"(\d+) tests? collected", out).group(1))
    stated = int(re.search(r"\*\*(\d+) Tests\*\*", README).group(1))
    assert stated == collected


def test_every_test_name_the_readme_cites_exists():
    sources = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "tests").glob("test_*.py"))
    cited = set(re.findall(r"`(test_[a-z0-9_]+)`", README))
    assert len(cited) >= 15
    for name in cited:
        assert re.search(rf"def {re.escape(name)}\b", sources), name


def test_readme_has_no_open_placeholders_except_the_live_link():
    todo_lines = [line for line in README.splitlines() if "TODO" in line]
    assert todo_lines == []
    assert "**[→ Demo live ausprobieren](https://sebastianhanisch-standortspiel-demo.streamlit.app/)**" in README


LINE_LINK = "[Koalitionen und Teilen](https://sebastianhanisch.net/konzepte-koalitionen-teilen.html)"
EXPLAINER_LINK = "https://sebastianhanisch.net/standortspiel-erklaert.html"


def test_readme_and_app_name_the_line_with_a_link_and_no_working_title():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert f"gehört zur Linie {LINE_LINK}" in README
    assert f"gehört zur Linie {LINE_LINK}" in app
    for name in ("README.md", "app.py", "stg_texts.py"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "Arbeitsname" not in text and "Stück der Linie" not in text, name


def test_readme_links_the_explainer_page_and_no_longer_announces_it_as_open():
    assert EXPLAINER_LINK in README
    assert "erst bei der Einbindung" not in README


def test_triangle_below_the_formula_range_is_stated_as_measured_in_readme_and_app():
    """Unterhalb von f = 36,6 gelten die Dreieck-Formeln nicht; die Aussage „Kern leer“ stützt sich dort auf die Messung (Halbierungstest prüft f = 5, 10, 20, 30, 36)."""
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    oracle = (ROOT / "tests" / "test_oracle_standortspiel.py").read_text(encoding="utf-8")
    assert "(5.0, 10.0, 20.0, 30.0, 36.0)" in oracle
    for text in (README, app):
        assert "f = 5, 10, 20, 30 und 36" in text and "36,6" in text
    assert "darunter ist er immer leer" not in app


def test_app_and_readme_define_rho_star_and_the_price_of_stability():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    for text in (README, app):
        assert "x(S) ≤ ρ · c(S)" in text
        assert "x(N) = c(N) − Δ" in text
    assert "Zuschuss" in app and "Δ" in app


def test_every_file_of_the_folder_is_in_the_file_table():
    for name in ("app.py", "stg_game.py", "stg_lp.py", "stg_core.py", "stg_allocations.py", "stg_evaluation.py", "stg_data.py", "stg_texts.py", "stg_rng.py", "tools/make_data.py"):
        assert (ROOT / name).exists() and f"`{name}`" in README, name
