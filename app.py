"""Standortspiel: wann ist eine Aufteilung der Fixkosten stabil? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Kunden teilen die Fixkosten von Standorten und die Wege zum nächsten offenen Standort. Gezeigt werden der Kern (per LP), die Ganzzahligkeitslücke als Grund für einen leeren Kern,
fünf Aufteilungen und sechs Experimente.

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import stg_allocations as AL
import stg_constants as C
import stg_data as D
import stg_evaluation as ev
import stg_scenario as S
import stg_visualization as V
from stg_layout import dunkles_design, kopf_css
from stg_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from stg_texts import ASSUMPTIONS_MARKDOWN

st.set_page_config(page_title="Standortspiel – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner="Rechne Koalitionen, Kern, Nukleolus und Relaxierung …")
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False)
def _hand():
    return ev.analyse_instance(S.hand_triangle())


@st.cache_data(show_spinner=False)
def _raster():
    return D.load_raster()


@st.cache_data(show_spinner=False)
def _allocation_study():
    return D.load_allocations()


def _timed(fn, *args):
    t0 = time.perf_counter()
    result = fn(*args)
    return result, time.perf_counter() - t0


@st.cache_data(show_spinner=False)
def _e1_live(n, m, f):
    return _timed(ev.raster_cell, n, m, f)


@st.cache_data(show_spinner=False)
def _e2():
    return _timed(lambda: [ev.triangle_cell(sg, f) for sg in C.DREIECK_SIGMA for f in C.DREIECK_F])


@st.cache_data(show_spinner=False)
def _e3():
    return _timed(lambda: [ev.shapley_by_open(f) for f in C.E3_F])


@st.cache_data(show_spinner=False)
def _e5():
    return _timed(lambda: [ev.ring_row(n, f) for f in (10, 25, 50) for n in (3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 21)])


@st.cache_data(show_spinner=False)
def _e6():
    return _timed(lambda: [ev.large_cell(n, C.M_GROSS_MAX, phi) for n in C.E6_N for phi in C.E6_PHI])


def run_block(key, label, compute, current=None):
    """Teure Zusatzansicht erst auf Klick: der Knopf merkt sich, dass gerechnet werden soll (bei `current` nur für diese Einstellung); das Ergebnis kommt aus dem Zwischenspeicher."""
    if st.button(label, key=f"run_{key}"):
        st.session_state[f"done_{key}"] = current if current is not None else True
    if st.session_state.get(f"done_{key}") != (current if current is not None else True):
        return None
    with st.spinner("Rechne …"):
        result, seconds = compute()
    st.caption(f"Gerechnet in {ev.de(seconds, 1)} s (beim ersten Aufruf; danach aus dem Zwischenspeicher).")
    return result


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in stg_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🏭 Standortspiel – wann ist eine Aufteilung der Fixkosten stabil?")
st.markdown(
    """
Mehrere **Kunden** teilen sich die Fixkosten von **Standorten**: jeder offene Standort kostet Fixkosten, und jeder Kunde zahlt den Weg zum nächsten offenen Standort. Jede Gruppe von Kunden (**Koalition**)
könnte auch allein die für sie billigste Standortmenge öffnen. Eine Aufteilung der Gesamtkosten liegt im **Kern**, wenn keine Koalition dabei mehr zahlt, als sie allein müsste.

Die Frage dieses Stücks: Gibt es so eine Aufteilung immer? **Nein, der Kern kann leer sein**, und die Demo zeigt **warum**: genau dann, wenn eine halb geöffnete Lösung (die Relaxierung) billiger ist als jede ganzzahlige,
also die **Ganzzahligkeitslücke** größer als 1 ist. Die Demo gehört zur Linie [Koalitionen und Teilen](https://sebastianhanisch.net/konzepte-koalitionen-teilen.html).
Nukleolus und Least Core zeigt die Demo `kern-demo` bei Touren, die Lücke beim Optimieren die Demo `standortplanung-demo`; hier geht es um die Erklärung des leeren Kerns und um die Wahl, wenn er leer ist.
Fixkosten und Lagen sind **Modellannahmen**, keine Daten und keine Beratung.

Wer die Idee zuerst ohne Fachbegriffe verstehen will, öffnet **💬 In einfachen Worten**. Weiter unten: das **Kernfrage**-Verdikt, zwei Abschnitte zu Lücke und Aufteilungen, sechs **🔬 Experimente**, **🚧 Wo die Annahmen enden** und die Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und **📐 Mathematische Formulierung**.
"""
)

# erklaerseite:einfach:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/standortspiel-erklaert.json, nicht von Hand ändern)
with st.expander("💬 In einfachen Worten"):
    st.markdown(
        """
Kunden teilen sich die Fixkosten eines oder mehrerer Standorte, und jeder zahlt zusätzlich seinen Weg zum nächsten geöffneten Standort. Die Demo fragt, ob es eine Aufteilung gibt, bei der keine Gruppe lieber allein einen eigenen Standort betreiben würde. Eine solche Aufteilung heißt **Kern**. Der Kern ist **genau dann leer**, wenn eine Lösung mit halb geöffneten Standorten billiger wäre als jede Lösung mit ganzen Standorten. Die Demo zeigt, in welchen Lagen das vorkommt (Dreieck, ungerade Ringe), wie oft es in Zufallslagen vorkommt und welche Aufteilung man bei leerem Kern wählen kann. **Fixkosten und Lagen sind Modellannahmen, keine Daten und keine Beratung.**

[Ausführlich und verständlich erklärt, mit Fachteil](https://sebastianhanisch.net/standortspiel-erklaert.html)
        """
    )
# erklaerseite:einfach:end

with st.expander("So funktioniert ein Standortspiel", expanded=True):
    st.markdown(
        """
1. **Koalitionswert.** c(S) ist der billigste Weg, die Kunden der Gruppe S zu bedienen: man wählt eine Standortmenge, zahlt deren Fixkosten und für jeden Kunden den Weg zum nächsten gewählten Standort. Die App zählt alle Standortmengen auf.
2. **Aufteilung.** Jeder Kunde zahlt einen Anteil x_i, die Anteile summieren sich zu c(N), den Kosten der großen Koalition aller Kunden.
3. **Kern.** x liegt im Kern, wenn keine echte Koalition S zusammen mehr als c(S) zahlt: x(S) ≤ c(S).
4. **Wenn es keinen Kern gibt,** bleibt die Frage, welche Aufteilung am wenigsten schlecht ist. Dafür gibt es die Begriffe der Tabelle.
        """
    )
    st.markdown(
        """
| Begriff | Bedeutung | In der App berechnet als |
|---|---|---|
| **Kern** | Aufteilungen, bei denen keine Koalition mehr zahlt, als sie allein müsste | LP über alle 2^n − 2 echten Koalitionen |
| **Least-Core-Wert ε\\*** | größter Überschuss x(S) − c(S), den man bei bester Aufteilung nicht unterschreiten kann; positiv heißt Kern leer | LP: kleinstes ε mit x(S) ≤ c(S) + ε |
| **Nukleolus** | die Aufteilung, die den größten Überschuss minimiert, dann den zweitgrößten und so weiter | Folge von LP (Maschler, Peleg, Shapley) |
| **Ganzzahligkeitslücke** | c(N) geteilt durch den Wert der Relaxierung, in der Standorte halb offen sein dürfen | LP mit n·m + m Variablen |
| **Multiplikativer Least-Core-Wert ρ\\*** | kleinster Faktor ρ, mit dem alle echten Koalitionen x(S) ≤ ρ · c(S) einhalten; ρ\\* ≤ 1 heißt Kern nicht leer. Bei leerem Kern ist ρ\\* die Ganzzahligkeitslücke | LP: kleinstes ρ mit x(S) ≤ ρ · c(S); angezeigt wird max(ρ\\*, 1) |
| **Preis der Stabilität (Zuschuss)** | kleinster Betrag Δ, den ein Dritter übernehmen müsste, damit die Kunden nur c(N) − Δ aufteilen und ein Kern entsteht; bei nichtleerem Kern 0 | c(N) minus Wert der Relaxierung |
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Lage**")
    lage = st.selectbox(
        "Lage der Kunden und Standorte", C.LAGEN, key="lage_select",
        help="Zufall: gleichverteilt im Quadrat 100 × 100. Zwei Ballungen: die Kunden liegen um zwei Zentren. Ring: Kunden im Abstand s auf einem Kreis, die Standorte in den Kantenmitten (n = 3 ist das Dreieck).",
    )
    ring = lage == C.LAGE_RING
    n = st.slider("Kunden n", *bounds("n_slider"), key="n_slider", help="Wie viele Kunden (Spieler) es gibt. Die Zahl der Koalitionen wächst mit 2^n.")
    m = st.slider(
        "Standorte m", *bounds("m_slider"), key="m_slider", disabled=ring,
        help="Zahl der möglichen Standorte bei Zufallslagen. Beim Ring gibt es genau n Standorte (die Kantenmitten); dort ist der Regler ausgeschaltet.",
    )
    st.markdown("**Fixkosten**")
    f = st.slider("Fixkosten f je Standort", *bounds("f_slider"), key="f_slider", help="Kosten, einen Standort zu öffnen. Die Wege liegen im Quadrat 100 × 100 (Ring: Abstand s).")
    fixmode = st.selectbox("Fixkosten der Standorte", C.FIX_MODI, key="fix_select", help="Einheitlich: alle Standorte kosten f. Ungleich: je Standort ein Zufallswert zwischen 0,5 f und 1,5 f.")
    st.markdown("**Ring**")
    s = st.slider("Abstand s benachbarter Kunden", *bounds("s_slider"), key="s_slider", disabled=not ring, help="Nur beim Ring: Abstand benachbarter Kunden. Die Standorte liegen in den Kantenmitten, jeder Kunde hat also zwei Standorte im Weg s/2.")
    sigma = st.slider("Streuung σ der Positionen", *bounds("sigma_slider"), key="sigma_slider", disabled=not ring, help="Nur beim Ring: jede Koordinate wird um einen gleichverteilten Wert in [−σ, σ] gestört.")
    st.markdown("**Zufall**")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"lage_select": lage, "n_slider": int(n), "m_slider": int(m), "f_slider": int(f), "fix_select": fixmode, "s_slider": int(s), "sigma_slider": int(sigma), "seed_input": int(seed)})

settings = S.Settings(lage, int(n), int(m), int(f), fixmode, int(s), int(sigma), int(seed))
a = _analysis(settings)
n_eff, m_eff = a.inst.n, a.inst.m

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
c1, c2, c3 = st.columns(3)
c1.metric("Kosten der großen Koalition c(N)", ev.de(a.cn, 2), help="Billigste Standortmenge für alle Kunden zusammen: Fixkosten plus Wege.")
c2.metric("Relaxierung (LP)", ev.de(a.lp, 2), help="Wert, wenn Standorte zum Teil offen sein dürfen. Höchstens c(N).")
c3.metric("Ganzzahligkeitslücke c(N)/LP", ev.de(a.gap, 4), help="1 heißt: kein Unterschied zwischen ganzzahlig und halb offen.")
c4, c5, c6 = st.columns(3)
c4.metric("Kern", "leer" if a.core_empty else "nicht leer", help="Least-Core-LP über alle echten Koalitionen: leer, wenn ε* größer als 0 ist.")
c5.metric("Least-Core-Wert ε*", ev.de(a.eps, 3) if n_eff > 1 else "–", help="Kleinster größter Überschuss über alle Aufteilungen. Positiv: Kern leer. Null: Kern ohne Spielraum.")
c6.metric("Preis der Stabilität c(N) − LP", ev.de(a.subsidy, 3), help="Zuschuss: kleinster Betrag, den ein Dritter übernehmen müsste, damit die Kunden nur c(N) minus diesen Betrag aufteilen und ein Kern entsteht. Gleich c(N) − LP; bei nichtleerem Kern 0.")
left, right = st.columns([3, 2])
with left:
    st.plotly_chart(V.build_map(a), width="stretch", key="map_main")
    st.caption(
        f"Rot: offene Standorte der großen Koalition (Zahl: {a.k_open}, c(N) = {ev.de(a.cn, 2)}); graue Linien: Weg jedes Kunden zum nächsten offenen Standort. "
        f"Grau umrandet: mögliche Standorte, die in der großen Koalition geschlossen bleiben. Bei Gleichstand gewinnt die Standortmenge mit der kleineren Nummer."
    )
with right:
    st.markdown("**Koalitionen mit dem größten Überschuss** bei der Least-Core-Aufteilung (positiv: die Koalition würde austreten)")
    st.dataframe(ev.coalition_rows(a, 10), hide_index=True, width="stretch")
    with st.expander(f"Alle {2 ** n_eff - 2} echten Koalitionen"):
        st.dataframe(ev.coalition_rows(a), hide_index=True, width="stretch", height=300)
    st.caption("Die Least-Core-Aufteilung ist nicht eindeutig; die Tabelle zeigt die, die das LP liefert.")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Gibt es eine Aufteilung, bei der keine Gruppe austreten will?")
kind, text = ev.verdict_core(a.eps, a.cn, a.gap, a.subsidy, n_eff)
getattr(st, kind)(text)
kind, text = ev.verdict_gap(a.core_empty, a.gap_empty, a.gap, a.cn, a.lp)
getattr(st, kind)(text)

st.markdown("---")

# --- Warum leer ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Warum der Kern leer sein kann: die Ganzzahligkeitslücke")
st.markdown(
    """
Die **Relaxierung** darf Standorte halb öffnen und Kunden auf mehrere Standorte verteilen. Ihre **Duallösung** gibt jedem Kunden einen Preis v_i; die Preise summieren sich zum Wert der Relaxierung.
Zwei Aussagen (Beweisskizze im 📐-Expander): **(1)** Jede Aufteilung im Kern ist dual zulässig, also ist c(N) höchstens der Wert der Relaxierung, und der ist nie größer als c(N): im Kern gilt c(N) = LP.
**(2)** Ist c(N) = LP, dann liegen die Preise v selbst im Kern. Darum ist der Kern **genau dann leer, wenn c(N) größer als der Wert der Relaxierung ist**. Zwei Folgen: Der multiplikative Least-Core-Wert
ρ\\* (kleinstes ρ mit x(S) ≤ ρ c(S)) ist bei leerem Kern die Lücke selbst, und der **Preis der Stabilität** ist c(N) − LP. Das ist der **Zuschuss**: der kleinste Betrag Δ, den ein Dritter übernehmen müsste,
damit die Kunden nur c(N) − Δ aufteilen und ein Kern entsteht. Wer ihn zahlt, sagt das Modell nicht.
"""
)
g1, g2 = st.columns(2)
with g1:
    st.plotly_chart(V.build_costs(a), width="stretch", key="costs_chart")
    st.caption("Summe der Alleinkosten, c(N) ganzzahlig und Wert der Relaxierung dieser Instanz.")
with g2:
    st.plotly_chart(V.build_opened(a), width="stretch", key="opened_chart")
    st.caption("Wie die Relaxierung Standorte öffnet (eine Optimallösung, bei Gleichstand nicht eindeutig). Rot umrandet: ganzzahlig offene Standorte der großen Koalition.")
st.markdown(
    f"Diese Instanz: ρ\\* = {ev.de(a.rho_star, 4)} (mindestens 1 gesetzt), Lücke {ev.de(a.gap, 4)}, Preis der Stabilität {ev.de(a.subsidy, 3)} bei c(N) = {ev.de(a.cn, 2)} und LP = {ev.de(a.lp, 2)}."
)
group_table = ev.group_rows(a)
if group_table:
    st.markdown(
        "**Zwei oder mehr Standorte offen: die große Koalition zerfällt in Gruppen.** Jede Gruppe bedient sich bei einem eigenen Standort, und die Kosten der Gruppen summieren sich zu c(N). "
        "Dann muss im Kern jede Gruppe genau ihre Alleinkosten zahlen (x(Gruppe) ≤ c(Gruppe) bei Summe c(N)): der Kern hat keinen Spielraum, ε\\* ist mindestens 0."
    )
    st.dataframe(group_table, hide_index=True, width="stretch")
hand = _hand()
with st.expander("Das kleinste Beispiel von Hand: drei Kunden, drei Standorte"):
    st.markdown(
        "Standort F12 liegt für die Kunden 1 und 2 im Weg 0, für Kunde 3 im Weg 2 (entsprechend F13 und F23); jeder Standort kostet 2. "
        "Jeder Kunde und jedes Paar kann sich mit einem Standort für 2 bedienen, alle drei zusammen brauchen zwei Standorte (4) oder einen plus den Weg 2 (ebenfalls 4)."
    )
    st.dataframe([{"Kunde": f"K{i + 1}", "F12": ev.de(hand.inst.d[i, 0], 0), "F13": ev.de(hand.inst.d[i, 1], 0), "F23": ev.de(hand.inst.d[i, 2], 0)} for i in range(3)], hide_index=True)
    st.markdown(
        f"Jedes Paar zahlt allein {ev.de(float(hand.c[3]), 0)}, alle drei {ev.de(hand.cn, 0)}. Die Relaxierung öffnet jeden Standort halb und kommt auf {ev.de(hand.lp, 0)}; die Lücke ist {ev.de(hand.gap, 4)}. "
        f"Gäbe jeder Kunde gleich viel, {ev.de(hand.cn / 3, 4)}, zahlte ein Paar {ev.de(2 * hand.cn / 3, 4)} und wäre um {ev.de(2 * hand.cn / 3 - float(hand.c[3]), 4)} über seinen Alleinkosten. "
        f"Mehr als ε\\* = {ev.de(hand.eps, 4)} lässt sich dieser Überschuss durch keine Aufteilung drücken. Shapley-Wert und Nukleolus geben hier jedem Kunden {ev.de(hand.alloc[AL.SHAPLEY][0], 4)}."
    )
    kind, text = ev.verdict_core(hand.eps, hand.cn, hand.gap, hand.subsidy, 3)
    getattr(st, kind)(text)

st.markdown("---")

# --- Was wählen ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Was wählen? Fünf Aufteilungen im Vergleich")
st.markdown(
    "Ist der Kern leer, blockiert jede Aufteilung mindestens eine Koalition. Dann kommt es darauf an, **wie stark** und **wie viele**. Die Tabelle misst jede Aufteilung dieser Instanz: "
    "den größten Überschuss x(S) − c(S), das größte Verhältnis x(S)/c(S) und die Zahl der Koalitionen mit positivem Überschuss. Ist der Kern nicht leer, zeigt sie, welche Regeln im Kern liegen."
)
st.dataframe(ev.allocation_table(a), hide_index=True, width="stretch")
kind, text = ev.verdict_choice(a.kz, a.eps, a.cn, a.core_empty)
getattr(st, kind)(text)
st.plotly_chart(V.build_allocations(a), width="stretch", key="alloc_chart")
st.caption("Anteile der Kunden an c(N) bei den fünf Aufteilungen; die schwarzen Striche sind die Alleinkosten c({i}).")
st.markdown("**Die Verfahren in einem Satz**, mit dem Anteil von Kunde 1 in dieser Instanz als Beispiel:")
st.dataframe(
    [
        {"Verfahren": AL.NUKLEOLUS, "Regel": "minimiert den größten Überschuss, dann den zweitgrößten und so weiter", "Anteil von Kunde 1": ev.de(a.alloc[AL.NUKLEOLUS][0], 2)},
        {"Verfahren": AL.SHAPLEY, "Regel": "mittlerer Beitrag c(S ∪ {i}) − c(S) über alle Reihenfolgen, in denen die Kunden dazukommen", "Anteil von Kunde 1": ev.de(a.alloc[AL.SHAPLEY][0], 2)},
        {"Verfahren": AL.DUAL_LUECKE, "Regel": "Preis der Duallösung der Relaxierung mal Lücke c(N)/LP, summiert sich zu c(N)", "Anteil von Kunde 1": ev.de(a.alloc[AL.DUAL_LUECKE][0], 2)},
        {"Verfahren": AL.PROPORTIONAL, "Regel": "c(N) im Verhältnis der Alleinkosten c({i})", "Anteil von Kunde 1": ev.de(a.alloc[AL.PROPORTIONAL][0], 2)},
        {"Verfahren": AL.GLEICH, "Regel": "c(N)/n für jeden Kunden", "Anteil von Kunde 1": ev.de(a.alloc[AL.GLEICH][0], 2)},
    ],
    hide_index=True, width="stretch",
)
if n_eff > 1:
    rule = st.selectbox("Karte: blockierende Koalition dieser Aufteilung", list(a.kz), key="map_rule", help="Orange: die Koalition mit dem größten Überschuss bei der gewählten Aufteilung und die Standorte, die sie allein wählen würde.")
    k = a.kz[rule]
    if k.e_max > C.TOL:
        st.plotly_chart(V.build_map(a, k.worst), width="stretch", key="map_blocking")
        st.caption(
            f"Bei {rule} zahlt die Koalition {ev.names(k.worst, n_eff)} zusammen {ev.de(float((a.alloc[rule][[i for i in range(n_eff) if k.worst >> i & 1]]).sum()), 2)}, "
            f"allein käme sie mit den Standorten {ev.names(int(a.best[k.worst]), m_eff, 'S')} auf {ev.de(float(a.c[k.worst]), 2)}: Überschuss {ev.de(k.e_max, 3)}."
        )
    else:
        st.info(f"Bei {rule} gibt es keine blockierende Koalition: die Aufteilung liegt in dieser Instanz im Kern.")

st.markdown("---")

# --- E1 Raster ---------------------------------------------------------------------------------------------------------------------------

raster = _raster()
cells = raster["cells"]
st.subheader("🔬 Experiment 1: Wie oft ist der Kern in Zufallsinstanzen leer?")
st.caption(
    f"Vorgerechnet (data/raster_leere_kerne.json, Erzeuger `tools/make_data.py`): Zufall gleichverteilt, einheitliche Fixkosten, {len(cells)} Zellen aus Kundenzahl n ∈ {list(C.RASTER_N)}, Standortzahl m ∈ {list(C.RASTER_M)} "
    f"und Fixkosten f ∈ {list(C.RASTER_F)}, je Zelle {C.RASTER_BLOECKE} Blöcke zu {C.RASTER_PRO_BLOCK} Instanzen. Zahl im Feld: leere Kerne unter {C.RASTER_BLOECKE * C.RASTER_PRO_BLOCK}."
)
st.plotly_chart(V.build_raster(cells), width="stretch", key="raster_chart")
total = sum(c["total"] for c in cells)
empty = sum(c["empty"] for c in cells)
best_k = max(c["empty"] for c in cells)
tops = sorted((c["n"], c["m"], c["f"]) for c in cells if c["empty"] == best_k)
kind, text = ev.verdict_raster(empty, total, sum(c["empty"] > 0 for c in cells), len(cells), tops, best_k, cells[0]["total"], max(c["max_rel_eps"] for c in cells))
getattr(st, kind)(text)
st.markdown("**Eine Zelle live nachrechnen** (n, m und f der Seitenleiste, Zufall gleichverteilt, einheitliche Fixkosten, 400 Instanzen mit den Zufalls-Seeds der Rasterzelle; unabhängig von der Lage der Seitenleiste):")
live = run_block("e1", "▶️ Zelle rechnen", lambda: _e1_live(int(n), int(m), int(f)), current=(int(n), int(m), int(f)))
if live is not None:
    st.markdown(
        f"n = {live['n']}, m = {live['m']}, f = {live['f']}: Kern leer in {live['empty']} von {live['total']} Instanzen ({ev.pct(live['empty'] / live['total'])}), je Block {live['by_block']}; "
        f"Kern leer und Lücke größer als 1 stimmen in {live['agree']} von {live['total']} überein; größte Lücke {ev.de(live['max_gap'], 4)}."
    )

st.markdown("---")

# --- E2 Dreieck ------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Das Dreieck mit gestörten Positionen")
st.caption(
    f"Kunden an den Ecken eines Dreiecks mit Seite 100, Standorte in den Kantenmitten, Positionen je Koordinate um einen gleichverteilten Wert in [−σ, σ] gestört; je Zelle {C.DREIECK_INSTANZEN} Instanzen."
)
rows2 = run_block("e2", "▶️ Dreieck rechnen", _e2)
if rows2 is not None:
    st.plotly_chart(V.build_triangle(rows2), width="stretch", key="triangle_chart")
    kind, text = ev.verdict_triangle(rows2)
    getattr(st, kind)(text)

st.markdown("---")

# --- E3 Shapley -----------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Liegt der Shapley-Wert im Kern?")
st.caption(f"n = 6 Kunden, m = 4 Standorte, Fixkosten f ∈ {list(C.E3_F)}, je {C.E3_INSTANZEN} Instanzen; gezählt werden nur Instanzen mit nichtleerem Kern, getrennt nach der Zahl k offener Standorte der großen Koalition.")
rows3 = run_block("e3", "▶️ Shapley-Zählung rechnen", _e3)
if rows3 is not None:
    st.plotly_chart(V.build_shapley_k(rows3), width="stretch", key="shapley_chart")
    kind, text = ev.verdict_shapley_k(rows3)
    getattr(st, kind)(text)
    st.markdown(
        "Warum liegt der Shapley-Wert bei k ≥ 2 seltener im Kern als bei k = 1? Ist die große Koalition in Gruppen zerfallen, muss im Kern jede Gruppe genau ihre Alleinkosten zahlen (siehe oben). Der Shapley-Wert verteilt die Fixkosten des zweiten Standorts aber "
        "auch auf Kunden der ersten Gruppe; liegt er im Kern, dann nur, wenn er jeder Gruppe genau ihre Alleinkosten zuweist."
    )

st.markdown("---")

# --- E4 Aufteilungen -----------------------------------------------------------------------------------------------------------------

study = _allocation_study()
summ = study["summary"]
st.subheader("🔬 Experiment 4: Welche Aufteilung bei leerem Kern?")
st.caption(
    f"Vorgerechnet (data/aufteilungen_leerer_kern.json): {summ['_n']} Instanzen mit leerem Kern aus {len(C.E4_KONFIG)} Konfigurationen (n, m, f) = {list(C.E4_KONFIG)}, je {C.E4_PRO_KONFIG} Instanzen, "
    "alle fünf Aufteilungen. ε* ist im Mittel " + ev.pct(summ["_eps_mean"]) + " von c(N), im größten Fall " + ev.pct(summ["_eps_max"]) + "."
)
st.plotly_chart(V.build_allocation_study(summ), width="stretch", key="study_chart")
st.dataframe(
    [{"Aufteilung": nm, "Überschuss im Mittel (% von c(N))": ev.de(100 * summ[nm]["e_mean"], 2), "Vielfaches von ε* (Mittel der Einzelverhältnisse)": ev.de(summ[nm]["e_over_eps"], 2), "größtes Verhältnis im Mittel": ev.de(summ[nm]["rho_mean"], 4),
      "blockierende Koalitionen im Mittel": ev.de(summ[nm]["blocking_mean"], 1), "beste nach Überschuss": summ[nm]["best_e"], "beste nach Verhältnis": summ[nm]["best_rho"]} for nm in AL.RULES],
    hide_index=True, width="stretch",
)
kind, text = ev.verdict_allocations(summ)
getattr(st, kind)(text)

st.markdown("---")

# --- E5 Ring ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 5: Ring, ungerade und gerade")
st.caption("Ring mit Seite s = 100 und Fixkosten f ∈ {10, 25, 50}, n bis 21 Kunden. c(N) durch Aufzählung (bis 12 Standorte) oder gemischt-ganzzahlig, ε* aus der Drehsymmetrie (der Gleichanteil c(N)/n ist optimal); daneben die hergeleiteten Formeln.")
rows5 = run_block("e5", "▶️ Ringe rechnen", _e5)
if rows5 is not None:
    st.plotly_chart(V.build_ring(rows5), width="stretch", key="ring_chart")
    st.dataframe(
        [{"n": r["n"], "f": ev.de(r["f"], 0), "c(N)": ev.de(r["cn"], 2), "LP": ev.de(r["lp"], 2), "Lücke": ev.de(r["gap"], 5), "Lücke (Formel)": ev.de(r["gap_formula"], 5), "ε*": ev.de(r["eps"], 3),
          "ε* (Formel)": ev.de(r["eps_formula"], 3), "ε*/c(N) in %": ev.de(100 * r["rel_eps"], 3), "Formeln stimmen": "ja" if r["formula_ok"] else "nein"} for r in rows5],
        hide_index=True, width="stretch", height=300,
    )
    kind, text = ev.verdict_ring(rows5)
    getattr(st, kind)(text)

st.markdown("---")

# --- E6 Größer -----------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 6: Größere Instanzen ohne 2^n Bedingungen")
st.caption(
    f"Das Kriterium c(N) > LP braucht keine Koalitionstabelle: eine Aufzählung der Standortmengen (m = {C.M_GROSS_MAX}) und ein LP mit n·m + m Variablen. Zufall gleichverteilt, einheitliche Fixkosten f = φ · n, "
    f"n ∈ {list(C.E6_N)}, φ ∈ {list(C.E6_PHI)}, je Zelle {C.E6_INSTANZEN} Instanzen."
)
rows6 = run_block("e6", "▶️ Große Instanzen rechnen", _e6)
if rows6 is not None:
    st.plotly_chart(V.build_large(rows6), width="stretch", key="large_chart")
    kind, text = ev.verdict_large(rows6)
    getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Standorte ohne Kapazität** | Mit Kapazitätsgrenzen gilt die Herleitung „Kern leer genau dann, wenn Lücke größer als 1“ nicht mehr ohne Weiteres; hier nicht gerechnet. | `kapazitierte-standortplanung-demo` (Optimierung, kein Kostenteilen) |
| **Kunden nennen ihre Kosten wahrheitsgemäß, die Koalitionswerte sind bekannt** | Bei privaten Werten kommt es auf Anreize an, nicht nur auf die Aufteilung. | `moulin-demo` (Kostenteilung mit privaten Werten) |
| **Euklidische Wege, ein Kunde je Spieler** | Echte Netze sind nicht euklidisch; Dreieck und Ring sind Konstruktionen, keine Abbilder. | – |
| **Zufallsinstanzen klein und gleichverteilt** | Wie oft der Kern leer ist, wurde nur für n bis 8 gezählt; Experiment 6 prüft das Kriterium bis n = 30. | – |
| **Eine Aufteilung gilt für die ganze Gruppe** | Eine Wahl ohne Kern lässt Koalitionen übrig, die austreten wollen; wer das verhindert, ist nicht Teil des Modells. | – |
| **Der Kern ist die gesuchte Eigenschaft** | Andere Maße (Shapley-Wert, Nukleolus) beantworten andere Fragen; die Aufteilungen oben zeigen den Unterschied. | `shapley-demo`, `kern-demo` |
"""
)

st.markdown("---")

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(ASSUMPTIONS_MARKDOWN)

with st.expander("📐 Mathematische Formulierung"):
    # erklaerseite:lesehilfe:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/standortspiel-erklaert.json, nicht von Hand ändern)
    st.markdown(
        r"""
**Lesehilfe.** Gegeben sind $n$ Kunden, $m$ mögliche Standorte, Wege $d_{ij}$ und Fixkosten $f_j$. Gesucht ist, ob und wie sich die Kosten $c(N)$ der großen Koalition so aufteilen lassen, dass keine Koalition austritt.

| Symbol | Bedeutung |
|---|---|
| $N = \{1, \dots, n\}$ | Kunden (Spieler) |
| $J = \{1, \dots, m\}$ | mögliche Standorte |
| $d_{ij}$ | Weg von Kunde $i$ zu Standort $j$ |
| $f_j$ | Fixkosten von Standort $j$ |
| $c(S)$ | Kosten der Koalition $S \subseteq N$ bei bester eigener Standortmenge |
| $x$ | Aufteilung: $x_i$ ist der Anteil von Kunde $i$, $x(S) = \sum_{i \in S} x_i$ |
| $\varepsilon^*$, $\rho^*$ | additiver und multiplikativer Least-Core-Wert |
| $y_j$, $x_{ij}$ | Standort $j$ offen, Kunde $i$ bei Standort $j$ (in der Relaxierung Bruchteile) |
| $v_i$ | Preis von Kunde $i$ (Duallösung der Relaxierung) |
| $\mathrm{LP}$, $c(N)/\mathrm{LP}$ | Wert der Relaxierung, Ganzzahligkeitslücke |

[Schritt für Schritt erklärt, mit Herleitung und Literatur](https://sebastianhanisch.net/standortspiel-erklaert.html#fachleute)
        """
    )
    # erklaerseite:lesehilfe:end
    st.markdown(
        "**Weitere Begriffe** (zur Symboltabelle oben):\n\n"
        "- **Ganzzahligkeitslücke** c(N)/LP: Kosten der großen Koalition geteilt durch den Wert der Relaxierung, in der Standorte halb offen sein dürfen. Sie ist mindestens 1.\n"
        "- **ρ\\*** (multiplikativer Least-Core-Wert): das kleinste ρ, für das es eine Aufteilung mit x(N) = c(N) und x(S) ≤ ρ · c(S) für alle echten Koalitionen gibt. Der Kern ist nicht leer genau dann, wenn ρ\\* ≤ 1; "
        "bei leerem Kern ist ρ\\* = c(N)/LP, bei nichtleerem Kern höchstens 1. Die App zeigt max(ρ\\*, 1).\n"
        "- **Preis der Stabilität** (Zuschuss) Δ: das kleinste Δ ≥ 0, für das es eine Aufteilung mit x(N) = c(N) − Δ und x(S) ≤ c(S) für alle echten Koalitionen gibt; es ist c(N) − LP, bei nichtleerem Kern 0. "
        "Ein Rechenwert des Modells: wer den Zuschuss zahlt, sagt es nicht."
    )
    st.markdown("**Koalitionswert.** Eine Koalition wählt die billigste nichtleere Standortmenge O:")
    st.latex(r"c(S) = \min_{\emptyset \ne O \subseteq J} \Big( \sum_{j \in O} f_j + \sum_{i \in S} \min_{j \in O} d_{ij} \Big), \qquad c(\emptyset) = 0")
    st.markdown("**Kern.** Aufteilungen, bei denen keine echte Koalition mehr zahlt, als sie allein müsste:")
    st.latex(r"\mathrm{Kern} = \{\, x \in \mathbb{R}^N : x(N) = c(N),\ x(S) \le c(S)\ \text{für alle } \emptyset \ne S \subsetneq N \,\}")
    st.markdown("**Least Core.** Der additive Wert ε\\* ist das kleinste ε, für das alle echten Koalitionen mit Zuschlag ε passen; der Kern ist genau dann nicht leer, wenn ε\\* ≤ 0:")
    st.latex(r"\varepsilon^{*} = \min \{\, \varepsilon : x(N) = c(N),\ x(S) \le c(S) + \varepsilon\ \text{für alle } \emptyset \ne S \subsetneq N \,\}")
    st.markdown("**Relaxierung.** Standorte und Zuordnungen dürfen Bruchteile sein:")
    st.latex(r"\mathrm{LP} = \min \sum_{j \in J} f_j\, y_j + \sum_{i \in N} \sum_{j \in J} d_{ij}\, x_{ij}")
    st.latex(r"\text{so dass}\quad \sum_{j \in J} x_{ij} = 1\ \ (i \in N), \qquad x_{ij} \le y_j, \qquad 0 \le x_{ij}, y_j \le 1")
    st.markdown("**Dual.** Preise v_i je Kunde; die Zahlungsbereitschaft über die Wege darf die Fixkosten jedes Standorts nicht übersteigen:")
    st.latex(r"\mathrm{LP} = \max \sum_{i \in N} v_i \qquad \text{so dass}\quad \sum_{i \in N} \max(0,\, v_i - d_{ij}) \le f_j\ \ (j \in J)")
    st.markdown(
        "**Satz (hier hergeleitet, an Instanzen gemessen).** Der Kern ist genau dann nicht leer, wenn c(N) = LP. "
        "*Beweisskizze.* (⇒) Sei x im Kern und S_j = {i : x_i > d_ij}. Die Koalition S_j kann allein den Standort j öffnen, also gilt x(S_j) ≤ c(S_j) ≤ f_j + Σ_{i∈S_j} d_ij, das ist Σ_i max(0, x_i − d_ij) ≤ f_j. "
        "Damit ist x dual zulässig, und die schwache Dualität gibt c(N) = x(N) ≤ LP ≤ c(N). (⇐) Ist c(N) = LP, dann ist eine optimale Duallösung v mit Σ v_i = c(N) auf jede Koalition S eingeschränkt dual zulässig für die Relaxierung von S, "
        "also v(S) ≤ LP(S) ≤ c(S): v liegt im Kern. Aus demselben Schluss folgt, dass der kleinste Zuschuss c(N) − LP ist und dass bei leerem Kern ρ\\* = c(N)/LP gilt."
    )
    st.markdown("**Shapley-Wert** (mittlerer Beitrag über alle Reihenfolgen) und **Nukleolus** (Überschussvektor lexikografisch minimiert):")
    st.latex(r"\varphi_i = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!\,(n - |S| - 1)!}{n!}\,\big(c(S \cup \{i\}) - c(S)\big)")
    st.latex(r"\nu = \arg\operatorname{lexmin}_{x(N) = c(N)}\ \big(\text{Überschüsse } x(S) - c(S) \text{ absteigend sortiert}\big)")
    st.markdown("**Zerfall bei k ≥ 2 offenen Standorten.** Bedient die große Koalition die Gruppen S_1, …, S_k von je einem Standort aus, dann gilt c(N) = Σ_q c(S_q), und im Kern ist x(S_q) = c(S_q) für jede Gruppe.")
    st.markdown("**Ring** (n Kunden im Abstand s, Standorte in den Kantenmitten, ungerades n, einheitliche Fixkosten f; hergeleitet und nur im Bereich von Experiment 5 bestätigt):")
    st.latex(r"c(N) = \tfrac{n+1}{2}\, f + \tfrac{n}{2}\, s, \qquad \mathrm{LP} = \tfrac{n}{2}\,(f + s)")
    st.latex(r"\frac{c(N)}{\mathrm{LP}} = 1 + \frac{f}{n\,(f + s)}, \qquad \varepsilon^{*} = \frac{f\,(n-1)}{2n}")
    st.markdown("**Dreieck** (n = 3, Seite s, einheitliche Fixkosten f, ohne Störung; hergeleitet, Prüfung durch Halbierung im Test). Ab f = (√3 − 1)/2 · s ist ein Standort billiger als zwei:")
    st.latex(r"c(N) = f + s + \tfrac{\sqrt{3}}{2}\, s, \qquad \varepsilon^{*} = \tfrac{2}{3}\, c(N) - (f + s)")
    st.markdown(
        "Für f ≥ (√3 − 1)/2 · s (bei s = 100 ab f = 36,6) folgt aus den beiden Formeln: ε\\* > 0, der Kern also leer, genau für f < (√3 − 1) · s (bei s = 100 für f < 73,2). Darunter, für f < 36,6, sind zwei Standorte billiger als einer, "
        "und c(N) ist ein anderer Ausdruck; dort stützt sich die Aussage „Kern leer“ nicht auf diese Formeln, sondern auf die Messung: bei s = 100 ist der Kern in der Prüfung mit dem Least-Core-LP für f = 5, 10, 20, 30 und 36 leer."
    )
    st.markdown(
        "**Literatur.** M. X. Goemans, M. Skutella: *Cooperative facility location games*, CORE Discussion Paper 2000/14 (Université catholique de Louvain, 2000): nur Titel, Jahr und Zusammenfassung gelesen, nicht der Volltext. "
        "Kolen (Duallösungen als Kernpunkte) und der Begriff „cost of stability“: nicht geprüft. Nukleolus: D. Schmeidler 1969 („The nucleolus of a characteristic function game“); "
        "Maschler, Peleg, Shapley 1979 („Geometric properties of the kernel, nucleolus, and related solution concepts“); Titel und Jahre aus der README von `kern-demo` übernommen, hier nicht erneut geprüft."
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Koalitionen und Teilen: Macht und Aufteilung](https://sebastianhanisch.net/konzepte-koalitionen-teilen.html)."
)
