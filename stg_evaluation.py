"""Kennzahlen, Verdikte und Messreihen des Standortspiels.

Die Verdikte sind reine Funktionen `verdict_*(…) -> (Art, Text)`: die App ruft `getattr(st, Art)(Text)`, `tests/test_verdicts.py` prüft Schwellen und jede Zahl im Text an handgesetzten Werten.
Die Messreihen (`raster_cell`, `triangle_cell`, `shapley_by_open`, `large_cell`, `ring_row`, `allocation_study`) sind Funktionen mit festen Zufalls-Seeds und liefern Zeilen,
die die App zeigt und `tests/test_claims.py` festschreibt."""

from dataclasses import dataclass

import numpy as np

import stg_allocations as AL
import stg_constants as C
import stg_game as G
import stg_lp as L
from stg_core import excess, least_core, shapley
from stg_scenario import Instance, Settings, make_instance, raster_seed, ring_instance, triangle_instance, uniform_instance


# ---- Zahlenformat (deutsches Dezimalkomma) ------------------------------------------------------------------------------------------------


def de(x: float, digits: int = 2) -> str:
    """Zahl mit Dezimalkomma; −0,00 wird zu 0,00."""
    s = f"{x:.{digits}f}"
    if float(s) == 0.0:
        s = f"{0.0:.{digits}f}"
    return s.replace(".", ",")


def pct(share: float, digits: int = 2) -> str:
    """Anteil (0,05 = 5 %) als Prozentangabe mit Dezimalkomma."""
    return f"{de(100.0 * share, digits)} %"


def num(k: int) -> str:
    """Ganzzahl mit Punkt als Tausendertrenner."""
    return f"{k:,}".replace(",", ".")


def count_text(k: int, total: int) -> str:
    return f"{num(k)} von {num(total)}"


# ---- Analyse einer Instanz ---------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Analysis:
    inst: Instance
    c: np.ndarray               # Koalitionswerte (Index = Maske)
    best: np.ndarray            # beste Standortmenge je Koalition
    cn: float                   # c(N)
    open_mask: int              # Standortmenge der großen Koalition
    k_open: int                 # Zahl der offenen Standorte der großen Koalition
    eps: float                  # additiver Least-Core-Wert ε*
    x_lc: np.ndarray            # eine Aufteilung zum Least-Core-Wert (nicht eindeutig)
    core_empty: bool            # ε* > TOL
    rho_star: float             # multiplikativer Least-Core-Wert ρ*
    lp: float                   # Wert der Relaxierung
    prices: np.ndarray          # Duallösung der Relaxierung
    opened: np.ndarray          # y_j einer Optimallösung der Relaxierung
    gap: float                  # c(N)/LP
    subsidy: float              # Cost of Stability c(N) - LP
    alloc: dict                 # Name -> Aufteilung
    kz: dict                    # Name -> Kennzahlen
    gap_empty: bool             # c(N) - LP > GAP_TOL (das Kriterium ohne 2^n Bedingungen)


def analyse_instance(inst: Instance) -> Analysis:
    n = inst.n
    c, best = G.coalition_costs(inst.d, inst.fix)
    eps, x_lc = least_core(c, n)
    rho = max(least_core(c, n, mult=True)[0], 1.0)       # ρ* gilt als Dualbedingung mit der großen Koalition (Faktor 1): mindestens 1
    rel = L.lp_relaxation(inst.d, inst.fix)
    alloc = AL.allocations(inst.d, inst.fix, c, with_nucleolus=n <= C.N_NUKLEOLUS_MAX)
    alloc[AL.DUAL_LUECKE] = rel.prices * (c[-1] / rel.value)
    kz = {name: AL.kennzahlen(x, c, n) for name, x in alloc.items()}
    return Analysis(inst, c, best, float(c[-1]), int(best[-1]), G.popcount(best[-1]), eps, x_lc, eps > C.TOL, rho, rel.value, rel.prices, rel.opened,
                    float(c[-1]) / rel.value, float(c[-1]) - rel.value, alloc, kz, float(c[-1]) - rel.value > C.GAP_TOL)


def analyse(settings: Settings) -> Analysis:
    return analyse_instance(make_instance(settings))


# ---- Messreihen ---------------------------------------------------------------------------------------------------------------------------


def instance_summary(inst: Instance) -> dict:
    """Die drei Größen der Raster-Experimente für eine Instanz: ε*, c(N), LP-Wert."""
    c, _ = G.coalition_costs(inst.d, inst.fix)
    eps = least_core(c, inst.n)[0]
    lp = L.lp_relaxation(inst.d, inst.fix).value
    return dict(eps=eps, cn=float(c[-1]), lp=lp, empty=eps > C.TOL, gap_empty=float(c[-1]) - lp > C.GAP_TOL)


def raster_cell(n: int, m: int, f: int, blocks: int = C.RASTER_BLOECKE, per_block: int = C.RASTER_PRO_BLOCK) -> dict:
    """Eine Zelle des Rasters (E1): Zufall gleichverteilt, einheitliche Fixkosten f, `blocks` Blöcke zu `per_block` Instanzen mit eigenen Zufalls-Seeds."""
    empty_by_block, agree, max_rel, gaps = [], 0, 0.0, []
    for b in range(blocks):
        k = 0
        for i in range(per_block):
            r = instance_summary(uniform_instance(n, m, f, raster_seed(n, m, f, b, i)))
            k += r["empty"]
            agree += r["empty"] == r["gap_empty"]
            gaps.append(r["cn"] / r["lp"])
            if r["empty"]:
                max_rel = max(max_rel, r["eps"] / r["cn"])
        empty_by_block.append(k)
    return dict(n=n, m=m, f=f, empty=sum(empty_by_block), total=blocks * per_block, by_block=empty_by_block, agree=agree, max_rel_eps=max_rel, max_gap=max(gaps))


def triangle_seed(sigma: int, f: int, i: int) -> int:
    return 2_000_000_000 + (sigma * 1000 + f) * 1000 + i


def triangle_threshold(s: float = 100.0) -> float:
    """Hand hergeleitet: der Kern des Dreiecks (Seite s, Fixkosten f, ohne Streuung) ist leer genau für f < (√3 - 1) s."""
    return (3 ** 0.5 - 1.0) * s


def triangle_cell(sigma: int, f: int, count: int = C.DREIECK_INSTANZEN, s: int = 100) -> dict:
    """Dreieck (Ring mit n = 3) mit Positionsstörung ±sigma je Koordinate (E2): Zahl der leeren Kerne unter `count` Instanzen."""
    empty = 0
    for i in range(count):
        inst = triangle_instance(s, f, sigma, triangle_seed(sigma, f, i))
        empty += least_core(G.coalition_costs(inst.d, inst.fix)[0], 3)[0] > C.TOL
    return dict(sigma=sigma, f=f, empty=int(empty), total=count)


def e3_seed(f: int, i: int) -> int:
    return 3_000_000 + 1000 * f + i


def shapley_by_open(f: int, count: int = C.E3_INSTANZEN, n: int = 6, m: int = 4) -> dict:
    """E3: Shapley im Kern, getrennt nach der Zahl k offener Standorte der großen Koalition; nur Instanzen mit nichtleerem Kern.
    Liefert nonempty (Zahl nichtleerer Kerne), in_core (Shapley im Kern) und je k das Paar (im Kern, Instanzen)."""
    by_k, nonempty, in_core = {}, 0, 0
    for i in range(count):
        inst = uniform_instance(n, m, f, e3_seed(f, i))
        c, best = G.coalition_costs(inst.d, inst.fix)
        if least_core(c, n)[0] > C.TOL:
            continue
        nonempty += 1
        ok = bool(excess(shapley(c, n), c, n).max() <= C.TOL)
        in_core += ok
        k = G.popcount(best[-1])
        a, b = by_k.get(k, (0, 0))
        by_k[k] = (a + ok, b + 1)
    return dict(f=f, total=count, nonempty=nonempty, in_core=int(in_core), by_k=dict(sorted(by_k.items())))


def large_cell(n: int, m: int, phi: int, count: int = C.E6_INSTANZEN) -> dict:
    """E6: Kern leer nach dem Kriterium c(N) > LP ohne die 2^n Bedingungen; Zufall gleichverteilt, einheitliche Fixkosten f = phi · n."""
    empty, max_gap = 0, 1.0
    for i in range(count):
        inst = uniform_instance(n, m, phi * n, 70_000_000 + 1000 * (n * 100 + phi) + i)
        cn, lp, g = L.gap(inst.d, inst.fix)
        empty += cn - lp > C.GAP_TOL
        max_gap = max(max_gap, g)
    return dict(n=n, m=m, phi=phi, empty=int(empty), total=count, max_gap=max_gap)


def max_excess_equal_share(d: np.ndarray, fix: np.ndarray, x: float, chunk: int = 1 << 15) -> float:
    """Größter Überschuss über alle nichtleeren Koalitionen (die große eingeschlossen, also >= 0) bei gleichem Anteil x je Kunde, ohne die 2^n Koalitionen:
    max über Standortmengen O von Σ_i max(0, x - DM[O, i]) - F(O). Gilt, weil eine Koalition bei fester Standortmenge genau die Kunden mit x_i > Weg mitnimmt."""
    n, m = d.shape
    best = -np.inf
    for start in range(1, 1 << m, chunk):
        masks = np.arange(start, min(1 << m, start + chunk))
        DM = np.full((len(masks), n), np.inf)
        F = np.zeros(len(masks))
        for j in range(m):
            sel = ((masks >> j) & 1).astype(bool)
            DM[sel] = np.minimum(DM[sel], d[:, j][None, :])
            F[sel] += fix[j]
        best = max(best, float((np.maximum(0.0, x - DM).sum(axis=1) - F).max()))
    return best


def ring_formulas(n: int, f: float, s: float = 100.0) -> tuple[float, float]:
    """Herleitung für ungerade n: Lücke 1 + f/(n (f + s)) und ε* = f (n - 1)/(2 n). Gerade n: Lücke 1 und ε* = 0. Gilt nur in dem gemessenen Bereich (E5)."""
    if n % 2 == 0:
        return 1.0, 0.0
    return 1.0 + f / (n * (f + s)), f * (n - 1) / (2.0 * n)


def ring_row(n: int, f: float, s: float = 100.0) -> dict:
    """E5: Ring ohne Störung. c(N) durch Aufzählung (n <= M_ENUM_MAX) oder gemischt-ganzzahlig, ε* aus der Drehsymmetrie (Gleichanteil c(N)/n ist optimal),
    daneben die Formeln. eps ist max(ε*, 0)."""
    inst = ring_instance(n, f, s)
    cn, lp, g = L.gap(inst.d, inst.fix)
    eps = max(max_excess_equal_share(inst.d, inst.fix, cn / n), 0.0)
    gap_formula, eps_formula = ring_formulas(n, f, s)
    return dict(n=n, f=f, cn=cn, lp=lp, gap=g, gap_formula=gap_formula, eps=eps, eps_formula=eps_formula, rel_eps=eps / cn,
                formula_ok=abs(g - gap_formula) < 1e-9 and abs(eps - eps_formula) < 1e-6 * max(1.0, eps_formula))


def allocation_row(inst: Instance) -> dict:
    """E4: eine Instanz mit leerem Kern, Kennzahlen aller fünf Aufteilungen."""
    a = analyse_instance(inst)
    row = dict(eps_rel=a.eps / a.cn, gap=a.gap)
    for name, k in a.kz.items():
        row[name] = dict(e_rel=k.e_max / a.cn, rho=k.rho, blocking=k.blocking)
    return row


def find_empty_instances(n: int, m: int, f: int, count: int, start: int = 30_000_000) -> list[int]:
    """Die ersten `count` Zufalls-Seeds ab `start`, deren Instanz (Zufall gleichverteilt, einheitliche Fixkosten f) einen leeren Kern hat."""
    seeds, seed = [], start
    while len(seeds) < count:
        seed += 1
        inst = uniform_instance(n, m, f, seed)
        if least_core(G.coalition_costs(inst.d, inst.fix)[0], n)[0] > C.TOL:
            seeds.append(seed)
    return seeds


def allocation_study(configs=C.E4_KONFIG, per_config: int = C.E4_PRO_KONFIG) -> dict:
    """E4 (vorgerechnet in data/aufteilungen_leerer_kern.json): je Konfiguration die ersten `per_config` Instanzen mit leerem Kern, alle fünf Aufteilungen."""
    rows = []
    for n, m, f in configs:
        for seed in find_empty_instances(n, m, f, per_config):
            r = allocation_row(uniform_instance(n, m, f, seed))
            r.update(n=n, m=m, f=f, seed=seed)
            rows.append(r)
    return dict(rows=rows, summary=allocation_summary(rows))


def allocation_summary(rows: list[dict]) -> dict:
    """Mittel und Maximum je Aufteilung über die Zeilen; best_e und best_rho zählen, wie oft eine Aufteilung (Toleranz 1e-9) die beste ist."""
    out = {}
    for name in AL.RULES:
        e = np.array([r[name]["e_rel"] for r in rows])
        rho = np.array([r[name]["rho"] for r in rows])
        bl = np.array([r[name]["blocking"] for r in rows])
        out[name] = dict(e_mean=float(e.mean()), e_max=float(e.max()), e_over_eps=float((e / np.array([r["eps_rel"] for r in rows])).mean()), rho_mean=float(rho.mean()),
                         rho_max=float(rho.max()), blocking_mean=float(bl.mean()), blocking_max=int(bl.max()))
    e_mat = np.array([[r[name]["e_rel"] for r in rows] for name in AL.RULES])
    rho_mat = np.array([[r[name]["rho"] for r in rows] for name in AL.RULES])
    for i, name in enumerate(AL.RULES):
        out[name]["best_e"] = int((e_mat[i] <= e_mat.min(axis=0) + 1e-9).sum())
        out[name]["best_rho"] = int((rho_mat[i] <= rho_mat.min(axis=0) + 1e-9).sum())
    out["_n"] = len(rows)
    out["_eps_mean"] = float(np.mean([r["eps_rel"] for r in rows]))
    out["_eps_max"] = float(np.max([r["eps_rel"] for r in rows]))
    out["_gap_mean"] = float(np.mean([r["gap"] for r in rows]))
    return out


# ---- Verdikte (reine Funktionen) ---------------------------------------------------------------------------------------------------------


def verdict_core(eps: float, cn: float, gap: float, subsidy: float, n: int) -> tuple[str, str]:
    """Kernfrage: gibt es eine Aufteilung, die keine Koalition zum Austritt reizt?"""
    if n < 2:
        return "info", "Mit einem einzigen Kunden gibt es keine Koalition, die austreten könnte: der Kern besteht aus dem einen Anteil c(N)."
    if eps > C.TOL:
        return "warning", (f"**Der Kern ist leer.** Bei jeder Aufteilung gibt es mindestens eine Koalition, die um mindestens ε* = {de(eps, 3)} ({pct(eps / cn)} von c(N) = {de(cn)}) "
                           f"mehr zahlt, als sie allein müsste, und deshalb austritt. Die Ganzzahligkeitslücke c(N)/LP ist {de(gap, 4)} und damit größer als 1; "
                           f"ein Kern entstünde erst mit einem Zuschuss von {de(subsidy, 3)} (Cost of Stability).")
    if eps >= -C.TOL:
        return "info", (f"**Der Kern ist nicht leer, hat aber keinen Spielraum** (ε* = {de(0.0, 3)}): jede Aufteilung im Kern lässt mindestens eine echte Koalition genau bei ihren Alleinkosten. "
                        f"Die Lücke c(N)/LP ist {de(gap, 4)}.")
    return "success", (f"**Der Kern ist nicht leer.** ε* = {de(eps, 3)} < 0: es gibt Aufteilungen, bei denen jede echte Koalition mindestens {de(-eps, 3)} gegenüber ihren Alleinkosten spart. "
                       f"Die Lücke c(N)/LP ist {de(gap, 4)}.")


def verdict_gap(core_empty: bool, gap_empty: bool, gap: float, cn: float, lp: float) -> tuple[str, str]:
    """Stimmen das Kern-LP (alle Koalitionen) und das Kriterium Lücke > 1 (ohne die Koalitionen) überein?"""
    state = "leer" if core_empty else "nicht leer"
    if core_empty == gap_empty:
        return "success", (f"Der Kern ist **{state}**, und die Lücke bestätigt das: c(N) = {de(cn, 3)}, der Wert der Relaxierung ist {de(lp, 3)}, der Quotient {de(gap, 4)} "
                           f"({'größer als 1' if gap_empty else 'gleich 1'}).")
    return "warning", (f"Das Kern-LP meldet den Kern als **{state}**, das Lückenkriterium (c(N) = {de(cn, 3)}, LP = {de(lp, 3)}, Quotient {de(gap, 4)}) widerspricht. "
                       "Das ist Rechenrauschen an der Toleranz, kein Gegenbeispiel.")


def verdict_choice(kz: dict, eps: float, cn: float, core_empty: bool) -> tuple[str, str]:
    """Was wählen: welche der Aufteilungen liegt im Kern (nichtleer) bzw. hält den größten Überschuss und das größte Verhältnis klein (leer)?"""
    names = list(kz)
    best_e = min(kz[nm].e_max for nm in names)
    best_rho = min(kz[nm].rho for nm in names)
    by_e = [nm for nm in names if kz[nm].e_max <= best_e + 1e-9]
    by_rho = [nm for nm in names if kz[nm].rho <= best_rho + 1e-9]
    if core_empty and len(by_e) == len(names):
        return "info", (f"Bei leerem Kern blockiert jede Aufteilung mindestens eine Koalition. Hier ist es für alle {len(names)} Aufteilungen gleich: der größte Überschuss ist {de(best_e, 3)} ({pct(best_e / cn)} von c(N)), "
                        f"das größte Verhältnis x(S)/c(S) ist {de(best_rho, 4)}. Die Wahl der Regel ändert an dieser Instanz nichts.")
    if core_empty:
        return "info", (f"Bei leerem Kern blockiert jede Aufteilung mindestens eine Koalition. Der kleinste größte Überschuss ist {de(best_e, 3)} ({pct(best_e / cn)} von c(N)) bei {', '.join(by_e)} "
                        f"(ε* = {de(eps, 3)}); das kleinste größte Verhältnis x(S)/c(S) ist {de(best_rho, 4)} bei {', '.join(by_rho)}.")
    in_core = [nm for nm in names if kz[nm].e_max <= C.TOL]
    out = [nm for nm in names if kz[nm].e_max > C.TOL]
    if not out:
        return "success", f"Alle gezeigten Aufteilungen liegen im Kern ({', '.join(in_core)})."
    worst = max(out, key=lambda nm: kz[nm].e_max)
    inside = f"Im Kern liegen: {', '.join(in_core)}." if in_core else "Keine der gezeigten Aufteilungen liegt im Kern."
    return "info", (f"{inside} Außerhalb liegen: {', '.join(out)}; am größten ist der Überschuss bei {worst} mit {de(kz[worst].e_max, 3)} ({pct(kz[worst].e_max / cn)} von c(N)), "
                    f"bei {kz[worst].blocking} blockierenden Koalitionen.")


def verdict_raster(empty: int, total: int, cells_with: int, cells: int, top_cells: list, k: int, t: int, max_rel: float) -> tuple[str, str]:
    """E1: wie oft ist der Kern in Zufallsinstanzen leer? `top_cells`: die Zellen (n, m, f) mit dem größten Anteil (k von t leeren Kernen, auch bei Gleichstand genannt)."""
    where = " und ".join(f"n = {n}, m = {m}, f = {f}" for n, m, f in top_cells)
    return "info", (f"Der Kern ist in {count_text(empty, total)} Instanzen leer ({pct(empty / total)}); in {cells_with} von {cells} Zellen (n, m, f) mindestens einmal, "
                    f"am häufigsten bei {where} mit je {k} von {t} ({pct(k / t)}). Der größte Least-Core-Wert ε* ist {pct(max_rel)} von c(N). "
                    "In diesen Zufallsinstanzen ist der leere Kern also selten und der Effekt klein.")


def verdict_triangle(rows: list[dict]) -> tuple[str, str]:
    """E2: Dreieck mit Streuung; nennt Bereich ohne Streuung und die Zählung mit Streuung."""
    base = [r for r in rows if r["sigma"] == 0]
    low = [r for r in base if r["empty"] == r["total"]]
    none = [r for r in base if r["empty"] == 0]
    noisy = [r for r in rows if r["sigma"] > 0]
    mixed = [r for r in noisy if 0 < r["empty"] < r["total"]]
    text = (f"Ohne Streuung ist der Kern des Dreiecks bei f = {', '.join(str(r['f']) for r in low)} in allen Instanzen leer und bei f = {', '.join(str(r['f']) for r in none)} in keiner "
            f"(Schwelle der Herleitung bei s = 100: f = {de(triangle_threshold(), 1)}). ")
    text += f"Mit Streuung gibt es in {len(mixed)} von {len(noisy)} Zellen (σ, f) gemischte Anteile zwischen 0 und {noisy[0]['total']} leeren Kernen."
    return "info", text


def verdict_shapley_k(rows: list[dict]) -> tuple[str, str]:
    """E3: Shapley im Kern nach der Zahl offener Standorte (Summe über die f-Werte)."""
    tot: dict[int, list] = {}
    for r in rows:
        for k, (a, b) in r["by_k"].items():
            t = tot.setdefault(k, [0, 0])
            t[0] += a
            t[1] += b
    parts = "; ".join(f"k = {k}: {a} von {b}" for k, (a, b) in sorted(tot.items()))
    return "info", f"Der Shapley-Wert liegt bei nichtleerem Kern nach der Zahl k offener Standorte so oft im Kern: {parts}."


def verdict_allocations(summary: dict) -> tuple[str, str]:
    """E4: fünf Aufteilungen bei leerem Kern (vorgerechnet)."""
    n = summary["_n"]
    e = {nm: summary[nm]["e_mean"] for nm in AL.RULES}
    best_e = min(AL.RULES, key=lambda nm: e[nm])
    best_rho = min(AL.RULES, key=lambda nm: summary[nm]["rho_mean"])
    definition = " Beim Nukleolus ist das per Definition so: sein größter Überschuss ist ε*." if best_e == AL.NUKLEOLUS else ""
    return "info", (f"In {n} Instanzen mit leerem Kern hat {best_e} den kleinsten größten Überschuss (im Mittel {pct(e[best_e])} von c(N), in {summary[best_e]['best_e']} von {n} Instanzen der beste).{definition} "
                    f"Das kleinste Verhältnis x(S)/c(S) hat {best_rho} (im Mittel {de(summary[best_rho]['rho_mean'], 4)}, in {summary[best_rho]['best_rho']} von {n} der beste). "
                    f"Der Shapley-Wert liegt bei {pct(e[AL.SHAPLEY])}.")


def verdict_ring(rows: list[dict]) -> tuple[str, str]:
    """E5: Ring; Zählung, in wie vielen Zeilen die Formeln stimmen, und der größte Anteil ε*/c(N)."""
    odd = [r for r in rows if r["n"] % 2]
    ok = [r for r in rows if r["formula_ok"]]
    empty_odd = [r for r in odd if r["gap"] > 1 + 1e-9]
    mx = max(rows, key=lambda r: r["rel_eps"])
    return "info", (f"Bei {len(empty_odd)} von {len(odd)} ungeraden Ringen ist der Kern leer (Lücke größer als 1); die Formeln für Lücke und ε* stimmen in {len(ok)} von {len(rows)} Zeilen. "
                    f"Der größte Anteil ε*/c(N) ist {pct(mx['rel_eps'])} (n = {mx['n']}, f = {de(mx['f'], 0)}).")


def verdict_large(rows: list[dict]) -> tuple[str, str]:
    """E6: Kriterium bei großer Kundenzahl."""
    never = [r for r in rows if r["empty"] == 0]
    some = [r for r in rows if r["empty"] > 0]
    mx = max(rows, key=lambda r: r["empty"] / r["total"])
    return "info", (f"In {len(some)} von {len(rows)} Zellen (n, f/n) ist der Kern mindestens einmal leer, in {len(never)} wurde in {rows[0]['total']} Instanzen keiner gezählt; der höchste Anteil ist {mx['empty']} von {mx['total']} "
                    f"bei n = {mx['n']} und f = {mx['phi']} · n ({pct(mx['empty'] / mx['total'], 1)}). "
                    "Gezählt wird über das Lückenkriterium (für n bis 8 gegen das Kern-LP bestätigt).")


# ---- Tabellen der App (Zeilen aus Text, damit der Test jede angezeigte Zahl prüfen kann) --------------------------------------------------


def names(mask: int, count: int, prefix: str = "K") -> str:
    """Koalition oder Standortmenge als Text: Maske 5 mit Präfix K gibt „K1, K3“."""
    return ", ".join(f"{prefix}{i + 1}" for i in G.members(mask, count))


def allocation_table(a: Analysis) -> list[dict]:
    """Eine Zeile je Aufteilung: größter Überschuss, Anteil an c(N), größtes Verhältnis, blockierende Koalitionen, im Kern."""
    rows = []
    for name, k in a.kz.items():
        rows.append({"Aufteilung": name, "größter Überschuss": de(k.e_max, 3), "in % von c(N)": de(100.0 * k.e_max / a.cn, 2), "größtes x(S)/c(S)": de(k.rho, 4),
                     "blockierende Koalitionen": k.blocking, "im Kern": "ja" if k.e_max <= C.TOL else "nein"})
    return rows


def coalition_rows(a: Analysis, limit: int | None = None) -> list[dict]:
    """Echte Koalitionen mit c(S), bester Standortmenge und Überschuss bei der Least-Core-Aufteilung, größter Überschuss zuerst (Gleichstand: kleinere Maske zuerst)."""
    n, m = a.inst.n, a.inst.m
    if n < 2:
        return []
    e = excess(a.x_lc, a.c, n)
    order = np.argsort(-e, kind="stable")
    rows = [{"Koalition": names(int(k) + 1, n), "c(S)": de(float(a.c[k + 1]), 2), "beste Standorte": names(int(a.best[k + 1]), m, "S"), "Überschuss bei x(Least Core)": de(float(e[k]), 3)} for k in order]
    return rows if limit is None else rows[:limit]


def group_rows(a: Analysis) -> list[dict]:
    """Zerfällt die große Koalition (zwei oder mehr offene Standorte) in Gruppen je Standort: c(S_q) je Gruppe und ihre Summe (ist c(N)). Sonst leer."""
    if a.k_open < 2:
        return []
    assigned = G.assignment(a.inst.d, a.open_mask)
    n = a.inst.n
    rows = []
    for q in sorted(set(assigned.tolist())):
        mask = sum(1 << i for i in range(n) if assigned[i] == q)
        rows.append({"Standort": f"S{q + 1}", "Gruppe": names(mask, n), "c(Gruppe)": de(float(a.c[mask]), 2)})
    rows.append({"Standort": "Summe", "Gruppe": "", "c(Gruppe)": de(sum(float(a.c[sum(1 << i for i in range(n) if assigned[i] == q)]) for q in set(assigned.tolist())), 2)})
    return rows
