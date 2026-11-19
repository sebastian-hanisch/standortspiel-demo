"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben.

Beschriftungen sind Annotationen oder Hover-Texte; Karten haben gleichen Maßstab über `scaleanchor` mit automatischem Bereich (y umgekehrt, damit nach unten gezählt wird
wie im Plan), der Rand entsteht über zwei unsichtbare Marker an den Ecken (DEMO-PLAYBOOK §3)."""

import numpy as np
import plotly.graph_objects as go

import stg_allocations as AL
import stg_constants as C
import stg_game as G


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _de(x, nd=1):
    return f"{x:.{nd}f}".replace(".", ",")


def build_map(a, highlight_mask: int | None = None):
    """Karte: Kunden (K1, K2, …), Standorte (Quadrate), offene Standorte der großen Koalition rot mit Linien zu ihren Kunden.
    `highlight_mask`: Koalition, deren Kunden und beste Standorte orange umrandet werden (die blockierende Koalition)."""
    inst = a.inst
    pk, ps = inst.pk, inst.ps
    open_idx = G.members(a.open_mask, inst.m)
    fig = go.Figure()
    corners = np.vstack([pk, ps])
    lo, hi = corners.min(axis=0), corners.max(axis=0)
    pad = 0.08 * float((hi - lo).max() or 1.0)
    fig.add_trace(go.Scatter(x=[lo[0] - pad, hi[0] + pad], y=[lo[1] - pad, hi[1] + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    assigned = G.assignment(inst.d, a.open_mask)
    xs, ys = [], []
    for i, j in enumerate(assigned):
        xs += [pk[i, 0], ps[j, 0], None]
        ys += [pk[i, 1], ps[j, 1], None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="rgba(150,150,150,0.7)", width=1.5), hoverinfo="skip", name="Weg zum offenen Standort"))
    others = [j for j in range(inst.m) if j not in open_idx]
    if others:
        fig.add_trace(go.Scatter(x=ps[others, 0], y=ps[others, 1], mode="markers", marker=dict(symbol="square-open", size=13, color=C.COLOR_STANDORT, line=dict(width=2)),
                                 text=[f"Standort {j + 1}, Fixkosten {_de(inst.fix[j])}" for j in others], hovertemplate="%{text}<extra></extra>", name="möglicher Standort"))
    fig.add_trace(go.Scatter(x=ps[open_idx, 0], y=ps[open_idx, 1], mode="markers", marker=dict(symbol="square", size=15, color=C.COLOR_OFFEN),
                             text=[f"Standort {j + 1} (offen), Fixkosten {_de(inst.fix[j])}" for j in open_idx], hovertemplate="%{text}<extra></extra>", name="offener Standort (große Koalition)"))
    if highlight_mask:
        members = G.members(highlight_mask, inst.n)
        stations = G.members(int(a.best[highlight_mask]), inst.m)
        fig.add_trace(go.Scatter(x=pk[members, 0], y=pk[members, 1], mode="markers", marker=dict(symbol="circle-open", size=26, color=C.COLOR_BLOCK, line=dict(width=3)),
                                 hoverinfo="skip", name="blockierende Koalition"))
        fig.add_trace(go.Scatter(x=ps[stations, 0], y=ps[stations, 1], mode="markers", marker=dict(symbol="square-open", size=22, color=C.COLOR_BLOCK, line=dict(width=3)),
                                 hoverinfo="skip", name="deren Standorte allein"))
    fig.add_trace(go.Scatter(x=pk[:, 0], y=pk[:, 1], mode="markers", marker=dict(size=11, color=C.COLOR_KUNDE), name="Kunde",
                             text=[f"Kunde {i + 1}" for i in range(inst.n)], hovertemplate="%{text}<extra></extra>"))
    for i in range(inst.n):
        fig.add_annotation(x=pk[i, 0], y=pk[i, 1], text=f"K{i + 1}", showarrow=False, yshift=-16, font=dict(size=11), bgcolor="rgba(255,255,255,0.7)")
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, autorange="reversed", scaleanchor="x", scaleratio=1)
    return _base(fig, 420)


def build_costs(a):
    """Warum leer: die Kosten der großen Koalition ganzzahlig gegen die Relaxierung, daneben die Summe der Alleinkosten."""
    alone = float(sum(a.c[1 << i] for i in range(a.inst.n)))
    labels = ["Summe der Alleinkosten", "c(N) ganzzahlig", "Relaxierung (LP)"]
    values = [alone, a.cn, a.lp]
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=["rgba(150,150,150,0.7)", C.COLOR_OFFEN, C.COLOR_LINE], text=[_de(v) for v in values], textposition="outside",
                           hovertemplate="%{x}: %{y:.2f}<extra></extra>"))
    top = max(values)
    fig.update_yaxes(title_text="Kosten", range=[0, top * 1.15])
    return _base(fig, 320)


def build_opened(a):
    """Die Relaxierung öffnet Standorte zum Teil: Anteil y_j je Standort (eine optimale Lösung, bei Gleichstand nicht eindeutig); rot umrandet: ganzzahlig offen."""
    m = a.inst.m
    open_set = set(G.members(a.open_mask, m))
    labels = [f"S{j + 1}" for j in range(m)]
    fig = go.Figure(go.Bar(x=labels, y=a.opened, marker_color=[C.COLOR_LINE] * m, marker_line_color=[C.COLOR_OFFEN if j in open_set else "rgba(0,0,0,0)" for j in range(m)],
                           marker_line_width=3, hovertemplate="%{x}: y = %{y:.3f}<extra></extra>"))
    fig.update_yaxes(title_text="Anteil y offen", range=[0, 1.05])
    return _base(fig, 280)


def build_allocations(a):
    """Anteile der Kunden bei den fünf Aufteilungen (gruppierte Balken), dazu die Alleinkosten als Linie."""
    n = a.inst.n
    labels = [f"K{i + 1}" for i in range(n)]
    palette = {AL.NUKLEOLUS: "#2F6B65", AL.SHAPLEY: "#4c78a8", AL.DUAL_LUECKE: "#e08e0b", AL.PROPORTIONAL: "#8c6bb1", AL.GLEICH: "#999999"}
    fig = go.Figure()
    for name, x in a.alloc.items():
        fig.add_trace(go.Bar(x=labels, y=x, name=name, marker_color=palette[name], hovertemplate=f"{name}: %{{y:.2f}}<extra></extra>"))
    alone = [a.c[1 << i] for i in range(n)]
    fig.add_trace(go.Scatter(x=labels, y=alone, mode="markers", marker=dict(symbol="line-ew", size=16, color="black", line=dict(width=2)), name="Alleinkosten",
                             hovertemplate="Alleinkosten: %{y:.2f}<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Anteil an c(N)")
    return _base(fig, 380)


def build_raster(cells):
    """E1: Anteil leerer Kerne je Zelle (Zeilen: n und m, Spalten: Fixkosten f), Text = Zahl der leeren Kerne unter 400."""
    ns = sorted({c["n"] for c in cells})
    ms = sorted({c["m"] for c in cells})
    fs = sorted({c["f"] for c in cells})
    rows = [(n, m) for n in ns for m in ms]
    lookup = {(c["n"], c["m"], c["f"]): c for c in cells}
    z = [[100.0 * lookup[(n, m, f)]["empty"] / lookup[(n, m, f)]["total"] for f in fs] for n, m in rows]
    text = [[str(lookup[(n, m, f)]["empty"]) for f in fs] for n, m in rows]
    fig = go.Figure(go.Heatmap(z=z, x=[str(f) for f in fs], y=[f"n = {n}, m = {m}" for n, m in rows], text=text, texttemplate="%{text}", colorscale="Oranges", zmin=0,
                               colorbar=dict(title=dict(text="% leer", side="top"), nticks=4), hovertemplate="%{y}, f = %{x}: %{z:.2f} %<extra></extra>"))
    fig.update_xaxes(title_text="Fixkosten f", type="category")
    fig.update_yaxes(autorange="reversed", type="category")
    return _base(fig, 430)


def build_triangle(rows):
    """E2: Anteil leerer Kerne (in Prozent) über f, eine Linie je Streuung σ."""
    fig = go.Figure()
    for sigma in sorted({r["sigma"] for r in rows}):
        sel = [r for r in rows if r["sigma"] == sigma]
        fig.add_trace(go.Scatter(x=[r["f"] for r in sel], y=[100.0 * r["empty"] / r["total"] for r in sel], mode="lines+markers", name=f"σ = {sigma}",
                                 hovertemplate="f = %{x}: %{y:.1f} %<extra></extra>"))
    fig.update_xaxes(title_text="Fixkosten f (Seite s = 100)", type="category")
    fig.update_yaxes(title_text="Kern leer (%)", range=[0, 105])
    return _base(fig)


def build_shapley_k(rows):
    """E3: Anteil der Instanzen mit Shapley im Kern je Zahl k offener Standorte (Summe über die Fixkosten)."""
    tot: dict[int, list] = {}
    for r in rows:
        for k, (a, b) in r["by_k"].items():
            t = tot.setdefault(k, [0, 0])
            t[0] += a
            t[1] += b
    ks = sorted(tot)
    fig = go.Figure(go.Bar(x=[f"k = {k}" for k in ks], y=[100.0 * tot[k][0] / tot[k][1] for k in ks], marker_color=C.COLOR_LINE,
                           text=[f"{tot[k][0]} von {tot[k][1]}" for k in ks], textposition="outside", hovertemplate="%{x}: %{y:.1f} %<extra></extra>"))
    fig.update_yaxes(title_text="Shapley im Kern (%)", range=[0, 110])
    fig.update_xaxes(title_text="offene Standorte der großen Koalition")
    return _base(fig, 320)


def build_allocation_study(summary):
    """E4: mittlerer größter Überschuss je Aufteilung in Prozent von c(N), mit ε* als Linie."""
    names = list(AL.RULES)
    y = [100.0 * summary[nm]["e_mean"] for nm in names]
    fig = go.Figure(go.Bar(x=names, y=y, marker_color=C.COLOR_LINE, text=[_de(v, 2) + " %" for v in y], textposition="outside", hovertemplate="%{x}: %{y:.2f} %<extra></extra>"))
    fig.add_hline(y=100.0 * summary["_eps_mean"], line_dash="dash", line_color=C.COLOR_OFFEN, annotation_text="ε* (Mittel)", annotation_position="top left")
    fig.update_yaxes(title_text="größter Überschuss in % von c(N)", range=[0, max(y) * 1.2])
    return _base(fig, 340)


def build_ring(rows):
    """E5: Anteil ε*/c(N) in Prozent über die Kundenzahl n, eine Linie je Fixkosten f (gerade n: 0)."""
    fig = go.Figure()
    for f in sorted({r["f"] for r in rows}):
        sel = [r for r in rows if r["f"] == f]
        fig.add_trace(go.Scatter(x=[r["n"] for r in sel], y=[100.0 * r["rel_eps"] for r in sel], mode="lines+markers", name=f"f = {_de(f, 0)}",
                                 hovertemplate="n = %{x}: %{y:.2f} %<extra></extra>"))
    fig.update_xaxes(title_text="Kunden n auf dem Ring")
    fig.update_yaxes(title_text="ε* in % von c(N)")
    return _base(fig)


def build_large(rows):
    """E6: Anteil leerer Kerne je Kundenzahl n und Fixkosten f = φ · n."""
    fig = go.Figure()
    for n in sorted({r["n"] for r in rows}):
        sel = [r for r in rows if r["n"] == n]
        fig.add_trace(go.Bar(x=[f"φ = {r['phi']}" for r in sel], y=[100.0 * r["empty"] / r["total"] for r in sel], name=f"n = {n}", hovertemplate="%{x}: %{y:.1f} %<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Kern leer (%)")
    return _base(fig, 320)
