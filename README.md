# Standortspiel – wann ist eine Aufteilung der Fixkosten stabil? – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-standortspiel-demo.streamlit.app/)**

Diese Demo gehört zur Linie [Koalitionen und Teilen](https://sebastianhanisch.net/konzepte-koalitionen-teilen.html). Sie steht neben `kern-demo` (Kern, Least Core und Nukleolus bei der Tour von Spediteuren),
`shapley-demo` (der Shapley-Wert), `standortplanung-demo` (Standortproblem ohne Kapazität als Optimierung, mit der LP-Lücke) und `moulin-demo` (Kostenteilung bei privaten Werten). Hier teilen **Kunden** die Fixkosten von Standorten,
und es geht um die **Erklärung des leeren Kerns** und um die Wahl der Aufteilung, wenn er leer ist. Fixkosten und Lagen sind Modellannahmen, keine Daten und keine Beratung. Die Erklärseite „verständlich erklärt“: [Wann lässt sich ein Standort nicht fair teilen?](https://sebastianhanisch.net/standortspiel-erklaert.html)

## Kernfrage

Kunden teilen die Fixkosten eines oder mehrerer Standorte und zahlen den Weg zum nächsten offenen Standort. **Gibt es eine Aufteilung, bei der keine Gruppe austreten will, und wenn nein: wie viel fehlt, und welche Aufteilung wählt man trotzdem?**
Die Antwort der Demo auf das „Warum“: Der Kern ist **genau dann leer, wenn die Ganzzahligkeitslücke größer als 1 ist**, wenn also eine Lösung mit halb geöffneten Standorten billiger ist als jede ganzzahlige. Das ist hier für den Fall ohne Kapazitätsgrenze
hergeleitet (Beweisskizze im 📐-Expander der App) und an 33.600 Zufallsinstanzen, an Ringen und an einem Handbeispiel gemessen.

## Modell

Gegeben sind n Kunden, m mögliche Standorte, Wege d_ij und Fixkosten f_j. Der Koalitionswert c(S) ist die billigste nichtleere Standortmenge für die Kunden von S: Fixkosten plus Weg jedes Kunden zum nächsten gewählten Standort
(alle 2^m − 1 Standortmengen werden aufgezählt). Lagen: gleichverteilt im Quadrat 100 × 100, zwei Ballungen oder ein **Ring** (n Kunden im Abstand s auf einem Kreis, die Standorte in den Kantenmitten; n = 3 ist das gleichseitige Dreieck).
Formeln, Symboltabelle und die Beweisskizze stehen im 📐-Expander der App.

**Begriffe.** *Ganzzahligkeitslücke* ist c(N)/LP, der Wert der großen Koalition geteilt durch den Wert der Relaxierung (mindestens 1). ρ\* (der multiplikative Least-Core-Wert) ist das kleinste ρ, für das es eine Aufteilung mit x(N) = c(N) und x(S) ≤ ρ · c(S) für alle echten Koalitionen gibt; der Kern ist nicht leer genau dann, wenn ρ\* ≤ 1, bei leerem Kern ist ρ\* = c(N)/LP, und die App zeigt max(ρ\*, 1). *Preis der Stabilität* (der *Zuschuss*) ist das kleinste Δ ≥ 0, für das es eine Aufteilung mit x(N) = c(N) − Δ und x(S) ≤ c(S) für alle echten Koalitionen gibt, also der Betrag, den ein Dritter übernehmen müsste, damit ein Kern entsteht; er ist c(N) − LP, bei nichtleerem Kern 0.

## Methodik

- **Kern und Least Core:** ein LP über alle 2^n − 2 echten Koalitionen (HiGHS); ε* ist das kleinste ε mit x(S) ≤ c(S) + ε, der Kern ist leer genau dann, wenn ε* > 10⁻⁷.
- **Lücke ohne die Koalitionen:** c(N) durch Aufzählung der Standortmengen (m ≤ 12) oder gemischt-ganzzahlig, dazu die Relaxierung als LP mit n·m + m Variablen und ihre Duallösung (Preise der Kunden).
- **Fünf Aufteilungen:** Nukleolus (Folge von LP, Technik der Kern-Demo, bis n = 10), Shapley, Dual × Lücke (Preise der Duallösung mal Lücke c(N)/LP), proportional zu den Alleinkosten, gleich. Kennzahlen: größter Überschuss x(S) − c(S), größtes Verhältnis x(S)/c(S), Zahl blockierender Koalitionen.
- **Sechs Experimente:** Raster der Seltenheit (vorgerechnet), Dreieck mit Streuung, Shapley im Kern nach Zahl offener Standorte, Aufteilungen bei leerem Kern (vorgerechnet), Ring bis n = 21, Kriterium bis n = 30.
- **Zufall:** SplitMix64 (wörtliche Kopie von `ab-test-demo/abt_rng.py`, mit Kopier-Test); die Störung der Ring-Positionen ist gleichverteilt in ±σ je Koordinate (keine Normalverteilung, damit kein `math.log` und kein `math.cos` im Spiel ist).
- **Gleichstände:** Bei gleich teuren Standortmengen gewinnt die mit der kleineren Maske; die Kosten c(S) hängen davon nicht ab (`tests/test_game.py`, `tests/test_edge_cases.py`). Die Duallösung der Relaxierung ist bei Gleichstand nicht eindeutig; bei vier gleichen Kunden mit zwei gleich weiten Standorten liefert HiGHS (14, 4, 4, 4)
  statt dreimal gleich (`tests/test_edge_cases.py`), deshalb ist „Dual × Lücke“ nur bei eindeutiger Duallösung symmetrisch.

## Befunde (gemessen, keine Behauptungen)

Jede Zahl steht in `tests/test_claims.py` (Zählungen exakt, LP-Werte als Band); „Messung dieser README“ heißt: nicht im Test. Die Zufallsinstanzen sind Zufall gleichverteilt im Quadrat 100 × 100 mit einheitlichen Fixkosten, soweit nichts anderes steht.

| Frage | Befund (Voraussetzung, Läufe) | Test |
|---|---|---|
| Kern leer genau dann, wenn Lücke größer als 1? | In allen 33.600 Instanzen des Rasters (n ∈ {5, 6, 8}, m ∈ {3, 4, 6, 8}, f ∈ {10, …, 150}, 84 Zellen zu je 400) stimmen beide Kriterien überein; dazu das Orakel im Repo an 30 Instanzen (11 gezielt gesuchte leere Kerne, 14 nichtleere, vier Ringe, ein Dreieck). | `test_raster_empty_core_equals_positive_gap_in_every_instance`, `test_core_is_empty_exactly_when_the_gap_is_positive` |
| Wie oft ist der Kern in Zufallsinstanzen leer? | In 122 von 33.600 Instanzen (0,36 %); in 41 von 84 Zellen mindestens einmal, in 43 Zellen in keiner der 400. Am häufigsten 7 von 400 (1,75 %), in den Zellen n = 6, m = 6, f = 100 und n = 8, m = 8, f = 100. Nach f: 1, 5, 7, 26, 43, 32, 8 bei f = 10, 20, 30, 45, 60, 100, 150 (je 4.800 Instanzen). | `test_raster_totals`, `test_raster_most_affected_cells_and_largest_values`, `test_raster_counts_by_fixed_cost` |
| Ist „in 43 Zellen kein leerer Kern“ ein Beweis? | Nein: bei einem Anteil von 122/33.600 liegt die Wahrscheinlichkeit, in 400 Instanzen keinen zu sehen, bei 0,23. | `test_raster_probability_of_seeing_no_empty_core_in_a_cell` |
| Wie groß ist der Effekt dort? | Der größte Least-Core-Wert ist 1,43 % von c(N), die größte Lücke 1,0219 (in den 122 Instanzen mit leerem Kern des Rasters). | `test_raster_most_affected_cells_and_largest_values` |
| Ändern andere Lagen die Seltenheit? | n = 6, m = 4, f = 30/60/100, je 400 Instanzen: gleichverteilt 0/3/1, ungleiche Fixkosten 0/3/3, zwei Ballungen 2/0/0 leere Kerne; höchstens 3 von 400. Andere Lagen zeigen in dieser Stichprobe keine größere Häufigkeit; ein kleiner Unterschied lässt sich mit solchen Zählungen nicht ausschließen. | `test_variants_do_not_change_the_rarity` |
| Dreieck: ab wann ist der Kern leer? | Ohne Streuung leer bei f = 30, 60, 73 (400 von 400) und bei f = 80, 100 in keinem der 400 Dreiecke (0 von 400); hergeleitete Schwelle f < (√3 − 1)·s = 73,2 bei s = 100, per Halbierung bestätigt. Die Formeln für c(N) und ε* gelten erst ab f = (√3 − 1)/2·s = 36,6 (darunter sind zwei Standorte billiger als einer); für kleineres f ist „Kern leer“ gemessen, nicht hergeleitet: leer bei f = 5, 10, 20, 30 und 36. | `test_triangle_counts_by_noise_and_fixed_cost`, `test_triangle_threshold_by_bisection` |
| Dreieck mit gestörten Positionen? | Störung gleichverteilt in ±σ, je 400 Instanzen, f = 30/60/73/80/100: σ = 5: 400/380/37/1/0, σ = 10: 350/205/37/3/0, σ = 20: 93/70/29/4/0 leere Kerne. | `test_triangle_counts_by_noise_and_fixed_cost` |
| Dreieck von Hand? | c = 2 für Einzelne und Paare, c(N) = 4, LP 3, ε* = 2/3, ρ* = 4/3, Preis der Stabilität 1, Shapley und Nukleolus 4/3 je Kunde. | `test_hand_example_numbers`, `test_hand_triangle_least_core_by_grid_search` |
| Ringe? | Dreieck (f = 50): c(N) 236,60, LP 225,00, ε* 7,735 (3,27 %). Fünferring (f = 50): 400, 375, 20 (5,00 %). Sechserring: 450, 450, ε* = 0 (Kern ohne Spielraum). In der Tabelle von Experiment 5 (36 Zeilen, n bis 21) ist die Lücke bei allen 24 ungeraden Ringen größer als 1, bei allen 12 geraden gleich 1; bei n = 21 ist ε*/c(N) 0,41 / 0,90 / 1,49 % für f = 10 / 25 / 50. | `test_ring_preset_numbers`, `test_ring_table_formula_rows_and_relative_eps` |
| Gelten die Ring-Formeln (Lücke 1 + f/(n(f + s)), ε* = f(n − 1)/(2n), ungerades n)? | Nur im gemessenen Bereich: im Raster n = 3, …, 11, f = 5, …, 200 (s = 100) stimmen sie für n = 5 bis f = 50, für n = 7, 9, 11 bis f = 75, nicht beim Dreieck ab f = 50; bei geraden Ringen (Lücke 1, ε* = 0) außer n = 6 und n = 10 bei f = 200. In der Tabelle von Experiment 5 stimmen sie in 35 von 36 Zeilen. | `test_ring_formula_range_on_the_full_grid`, `test_ring_table_formula_rows_and_relative_eps` |
| Shapley im Kern? | n = 6, m = 4, f = 10/30/60/100, je 150 Instanzen, 597 mit nichtleerem Kern; Shapley im Kern bei k = 1 offenem Standort in 160 von 224, bei k = 2 in 42 von 268, bei k = 3 in 21 von 96, bei k = 4 in 3 von 9 (insgesamt 226 von 597). Bei f = 60 und k = 2 in 0 von 77. | `test_shapley_in_core_by_number_of_open_stations`, `test_shapley_with_two_open_stations_at_f_60_is_never_in_the_core_in_these_77_instances` |
| Warum liegt der Shapley-Wert bei k ≥ 2 seltener im Kern (16 bis 33 %; bei k = 4 nur 9 Instanzen) als bei k = 1 (71 %)? | Bei k ≥ 2 zerfällt die große Koalition in Gruppen je Standort, c(N) = Σ c(S_q) (hergeleitet, an mehr als 15 Instanzen im Repo und an allen 373 Instanzen mit k ≥ 2 und nichtleerem Kern geprüft: ε* = 0). Im Kern muss jede Gruppe genau ihre Alleinkosten zahlen; der Shapley-Wert verteilt Fixkosten über Gruppen hinweg. Bei k = 1 hat der Kern in allen 224 Instanzen Spielraum (ε* < 0). | `test_a_single_open_station_leaves_no_slack_in_the_core_when_two_are_open`, `test_core_without_slack_when_two_or_more_stations_are_open` |
| Was wählen bei leerem Kern? | 40 Instanzen mit leerem Kern (5 Konfigurationen n = 6 bis 8, je 8): größter Überschuss im Mittel in % von c(N): Nukleolus 0,49, Dual × Lücke 0,61, Shapley 2,78, proportional 7,01, gleich 8,62; ε* im Mittel 0,49 % (größter 1,38 %). Vielfache von ε* (Mittel der Einzelverhältnisse): Dual × Lücke 1,27, Shapley 53,1; der Shapley-Mittelwert wird von Instanzen mit sehr kleinem ε* getrieben (Median 7,3, Spanne 1,8 bis 935; Median und Spanne bei der Aussagenprüfung nachgerechnet, nicht im Test). Der Nukleolus erreicht per Definition den kleinsten größten Überschuss ε* (in 40 von 40 Instanzen). | `test_allocation_study_means_in_percent_of_the_total_cost`, `test_allocation_study_multiples_of_eps_ratios_and_blocking`, `test_allocation_study_best_counts_and_dual_ratio_equals_the_gap` |
| Und nach dem Verhältnis x(S)/c(S)? | Dual × Lücke erreicht die Lücke exakt (im Mittel 1,0073, gleich dem Mittel der Lücke) und ist in 40 von 40 die beste; Nukleolus 1,0103, Shapley 1,0485, proportional 1,1329, gleich 1,1785. Blockierende Koalitionen im Mittel: 6,1 (Nukleolus), 6,3 (Shapley), 10,2 (Dual × Lücke), 18,4 (proportional), 25,0 (gleich). | `test_allocation_study_multiples_of_eps_ratios_and_blocking`, `test_allocation_study_best_counts_and_dual_ratio_equals_the_gap` |
| Kern ohne 2^n Bedingungen? | m = 12, f = φ·n, n = 20 und 30, φ = 3/6/10/15/25, je 100 Instanzen, über das Lückenkriterium gezählt (für n bis 8 gegen das Kern-LP bestätigt): 22 von 1.000 leer (n = 20: 1/1/1/3/0, n = 30: 4/2/9/1/0); bei φ = 25 in keiner der 200 Instanzen. | `test_large_counts_of_empty_cores` |
| Preis der Stabilität und ρ*? | An 320 Instanzen (160 mit leerem Kern, n = 5 bis 8, 8 Konfigurationen): Preis der Stabilität gleich c(N) − LP bis 1,4·10⁻¹³, max(ρ*, 1) gleich c(N)/LP bis 6,7·10⁻¹⁶ (Messung dieser README, nicht im Test); im Repo an 14 Instanzen und zwei Ringen. | `test_price_of_stability_equals_cn_minus_lp`, `test_multiplicative_least_core_equals_the_gap_when_it_exceeds_one` |
| Presets? | Standard (Zufalls-Seed 1, n = 8, m = 6, f = 60): Kern nicht leer, ε* = −5,538. „Zufall mit leerem Kern“ (Seed 1362, n = 6, m = 4, f = 60): ε* = 1,38 % von c(N). „Shapley außerhalb“ (Seed 182): zwei offene Standorte, Shapley-Überschuss 18,14. | `test_preset_numbers`, `tests/test_presets.py` |

**Orakel (Scratch-Lauf des Baus, nicht im Repo):** 320 Instanzen (8 Konfigurationen mit n = 5 bis 8, je 20 mit leerem und 20 mit nichtleerem Kern): Koalitionswerte gegen Schleifen (n ≤ 6) Abweichung 0, Kern-leer-Kriterium gegen Lücke 0 Abweichungen, Duallösung dual zulässig und im Kern in allen 320,
Nukleolus gegen `kern-demo` (n ≤ 7), Shapley gegen alle Reihenfolgen (n = 6), Abweichungen höchstens 1,2·10⁻¹². Laufzeiten (Messung dieser README, nicht im Test, ein Rechner): eine Instanz des Rasters rund 5 ms; n = 10 mit m = 8 samt Nukleolus und Relaxierung bis 5,1 s im schlechtesten von 20 geprüften Fällen (der Ring mit n = 10, f = 5, σ = 30);
100 Instanzen des Kriteriums bei n = 20 bis 30 und m = 12 rund 1,3 s.

## Ehrliche Grenzen

- **In den gemessenen Verteilungen haben Zufallsinstanzen selten einen leeren Kern, und der Effekt ist klein.** Die Demo lebt für den leeren Kern von konstruierten Fällen (Dreieck, ungerade Ringe) und von gesuchten Zufallsinstanzen (Presets).
- **Ring-Formeln gelten nur in einem Bereich** (siehe Tabelle) und sind hergeleitet, nicht aus der Literatur übernommen.
- **Der Befund zum Shapley-Wert** gilt für n = 6, m = 4 und die gemessenen Fixkosten; die Herleitung (Zerfall bei k ≥ 2) gilt allgemein für das hier gebaute Spiel.
- **Die Duallösung ist bei Gleichstand nicht eindeutig**; die Zahlen zu „Dual × Lücke“ gelten für die Lösung, die HiGHS liefert.
- **Die Kern-Prüfung über alle Koalitionen** reicht bis n = 10 und m = 8 (Ring: m = n); darüber nur das Lückenkriterium (Experiment 6), das den Kern nicht konstruiert.
- **Literatur:** von Goemans und Skutella (CORE Discussion Paper 2000/14) wurden nur Titel, Jahr und Zusammenfassung gelesen, nicht der Volltext; Kolen und der Begriff „cost of stability“ sind nicht geprüft. Nukleolus: D. Schmeidler 1969 („The nucleolus of a characteristic function game“); Maschler, Peleg, Shapley 1979 („Geometric properties of the kernel, nucleolus, and related solution concepts“); Titel und Jahre aus der README von `kern-demo` übernommen, hier nicht erneut geprüft.

**Annahmen**
- **Ein Kunde ist ein Spieler.** Ein Standort kostet Fixkosten f, ein Kunde den Weg zum nächsten offenen Standort. Wege sind euklidisch in der Ebene, Standorte unkapazitiert (ein offener Standort bedient beliebig viele Kunden). Fixkosten und Lagen sind **Modellannahmen**, keine Daten.
- **Jede Koalition wählt ihre eigene billigste Standortmenge** und handelt ohne Kosten mit niemandem sonst. Das ist die Definition des Koalitionswerts c(S), keine Aussage über reale Gruppen.
- Die Zufallslagen sind gleichverteilt im Quadrat 100 × 100 oder zwei Ballungen; der Ring hat Kunden im Abstand s auf einem Kreis und die Standorte in den Kantenmitten (n = 3 ist das gleichseitige Dreieck); die Störung der Ring-Positionen ist gleichverteilt in ±σ je Koordinate.

**Grenzen**
- Der Kern wird über alle 2^n − 2 echten Koalitionen per LP bestimmt, deshalb höchstens n = 10 Kunden und 8 Standorte (beim Ring m = n). Das Kriterium „Kern leer genau dann, wenn Lücke größer als 1“ braucht die Koalitionen nicht und reicht im Experiment 6 bis n = 30 mit 12 Standorten.
- Die Gleichwertigkeit „Kern leer genau dann, wenn Lücke größer als 1“ ist für den unkapazitierten Fall hier hergeleitet (Beweisskizze im 📐-Expander) und an Instanzen gemessen. Sie ist nicht aus dem Volltext der Quelle übernommen.
- Die Ring-Formeln für Lücke und ε* sind hergeleitet und nur im gemessenen Bereich bestätigt (Experiment 5); außerhalb stimmen sie nicht.
- Der Zuschuss „Preis der Stabilität“ ist ein Rechenwert des Modells, kein Vorschlag, wer ihn zahlen soll.

**Bekannte Probleme und Unsicherheiten**
- Zählungen wie „Kern leer in k von N Instanzen“ sind Messungen an gezogenen Zufallsinstanzen, **kein Beweis**. Wie oft der Kern leer ist, hängt von der Verteilung ab (gemessen: gleichverteilt, n bis 8, einheitliche Fixkosten).
- Zufallsinstanzen haben selten einen leeren Kern, und der Effekt ist dort klein; die Presets mit Dreieck und Ring sind **konstruiert**, damit man den leeren Kern überhaupt sieht.
- Die Duallösung der Relaxierung ist bei Gleichstand nicht eindeutig. Die Aufteilung „Dual × Lücke“ nimmt die Lösung, die HiGHS liefert; die Zahlen dazu gelten für diese Wahl.
- Der Befund zum Shapley-Wert (Experiment 3) gilt für n = 6 Kunden und m = 4 Standorte mit den gemessenen Fixkosten.
- Literatur: von Goemans und Skutella wurden nur Titel, Jahr und Zusammenfassung gelesen (nicht der Volltext); Kolen und der Begriff „cost of stability“ sind nicht geprüft.

## Befunde und Korrekturen gegenüber dem Plan

Der Einzelplan stützte sich auf eine Vormessung mit einem anderen Zufallsgenerator (`numpy.random`); die Demo misst mit SplitMix64 neu, und Zahlen weichen ab. Gilt die Messung, steht hier die Abweichung:

- **Seltenheit:** 122 von 33.600 Instanzen (0,36 %) statt 139 (0,41 %), 41 statt 44 Zellen mit leerem Kern, höchster Anteil 7 von 400 (1,75 %) in zwei Zellen statt 10 von 400 (2,50 %) in n = 8, m = 8, f = 100, größter ε*/c(N) 1,43 % statt 1,66 %. Der Gipfel bei f = 60 bleibt (43 leere Kerne bei f = 60).
- **Dreieck mit Streuung nicht vergleichbar:** Der Plan störte normalverteilt mit σ = 5 (93/64/8,5/0,2 %), die Demo gleichverteilt in ±σ (Standardabweichung σ/√3). σ = 5 gibt hier 400/380/37/1/0 von 400, weil die Störung kleiner ist; die Zahlen des Plans gelten nicht für diese Demo.
- **ρ\* = c(N)/LP gilt nur bei leerem Kern.** Bei nichtleerem Kern liegt der multiplikative Least-Core-Wert (nur echte Koalitionen) bei höchstens 1 und kann darunter liegen; die Demo zeigt max(ρ\*, 1). Der erste Test des Baus (ρ\* = Lücke für alle Instanzen) schlug an einer Instanz mit nichtleerem Kern fehl (ρ\* ≈ 0,97).
- **Neu gegenüber dem Plan: die Shapley-Deutung ist hergeleitet.** Der Plan nannte „Shapley verteilt die Fixkosten des zweiten Standorts auch auf Kunden des ersten“ eine Deutung. Bei k ≥ 2 offenen Standorten gilt c(N) = Σ c(S_q); im Kern zahlt dann jede Gruppe genau ihre Alleinkosten, ε* ist 0 (373 von 373 Instanzen mit nichtleerem Kern), und der Shapley-Wert liegt nur dort im Kern, wo er jeder Gruppe genau das zuweist. Die Zahlen nach k (160/224, 42/268, 21/96, 3/9) ersetzen die der Vormessung (163/234, 28/247, 27/106, 0/7).
- **„Dreieck von Hand“ ist kein Preset,** sondern ein fester Expander in der App: die Wegetabelle (Wege 0 und 2) ist keine ebene Geometrie, und die Regler der App bauen nur ebene Lagen. Als Preset gibt es das geometrische Dreieck (Ring mit n = 3). Das Dreieck ist der Ring mit n = 3 (kein eigener Lage-Eintrag), Ring und Zufall teilen die Regler; die Regler, die in einer Lage nichts bewirken (m beim Ring, s und σ sonst), sind deaktiviert statt ausgeblendet.
- **Nukleolus bis n = 10** statt bis n = 8: die Laufzeit blieb in 20 geprüften Fällen unter 5,2 s (Messung dieser README).
- **Experiment 6 ohne n = 10:** Raster n = 20 und 30 (je Zelle 100 Instanzen, 10 Zellen); die Gegenprobe des Plans bei n = 10 (24 von 24, mit gezielt gesuchten leeren Kernen) wurde nicht wiederholt. Das Kriterium gegen das Least-Core-LP prüft die Demo an 33.600 Instanzen mit n ≤ 8 und an drei Instanzen mit n = 10 (`tests/test_edge_cases.py`).
- **Ring-Formeln mit Bereich:** Im Plan standen sie ohne Bereich (geprüft bei f = 10, 25, 50). Das Raster bis f = 200 zeigt, wo sie enden (siehe Tabelle); beim Dreieck mit f = 50 stimmen sie nicht (die Höhe √3/2 · s ist dort kürzer als ein zweiter Standort).
- **Zeit des gemischt-ganzzahligen Programms:** Ring n = 21 mit `scipy.optimize.milp` rund 0,014 s statt der 2,6 s des Plans (dünne Matrizen); die Messung stammt von einem Rechner und steht nicht im Test.
- **Zweites Vehikel Energiegemeinschaft:** nicht gebaut (Empfehlung des Plans: nein; dasselbe Modell mit anderer Kulisse).

## Tests

**217 Tests** (`pytest tests/ -n 8`, rund eine Minute auf einem Rechner mit 16 Kernen). Zusammensetzung: Einheiten an Handbeispielen (`test_game.py`, `test_lp.py`, `test_core.py`, `test_allocations.py`), **Orakel** (`test_oracle_standortspiel.py`: Koalitionswerte gegen Schleifen,
Least Core des Dreiecks gegen Gittersuche, Kern leer gegen Lücke an gezielt gesuchten leeren Kernen, Preis der Stabilität als eigenes LP, Duallösung gegen jede Koalition, Shapley gegen alle Reihenfolgen, Nukleolus gegen `kern-demo` und gegen seine Definition, Ring-Formeln gegen volles LP und MILP, Dreieck-Schwelle gegen Halbierung),
Zahlen der README (`test_claims.py`), Messreihen aus den Dateien (`test_data.py`, mit Erzeuger-Hash und Neuberechnung von Stichproben), Verdikte als reine Funktionen (`test_verdicts.py`), Randfälle (`test_edge_cases.py`: n = 1, n = 2, m = 1, Gleichstände, Reglerränder, Toleranz), Presets mit erwarteter Verdikt-Zeile je Preset (`test_presets.py`),
Szenario und Kopie des Zufallsgenerators (`test_scenario.py`, `test_copies.py`), AppTest (`test_app.py`: jeder Knopf, jeder Regler an Minimum und Maximum, alle Minima und alle Maxima je Lage, Permalink, jedes Experiment), Layout, Footer, Laufzeit-Importe und die Übereinstimmung von README und App (`test_readme.py`).
Beim ersten Lauf auf Linux (CI) können LP-Werte in der letzten Stelle abweichen; Tests vergleichen sie als Band.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Ergebnis, Kernfrage, Lücke, fünf Aufteilungen, sechs Experimente, Grenzen, Formeln |
| `stg_constants.py` | Regler-Grenzen, Toleranzen, Raster, Presets |
| `stg_rng.py` | SplitMix64, wörtliche Kopie von `ab-test-demo/abt_rng.py` |
| `stg_scenario.py` | Instanzen: Zufall, Ballung, Ring, Handbeispiel; feste Seeds |
| `stg_game.py` | Koalitionswerte c(S) (Standortmengen, Matrixprodukt), Schleifenfassung einer Koalition |
| `stg_lp.py` | Relaxierung und Duallösung, ganzzahliges Optimum (Aufzählung, MILP), Lücke |
| `stg_core.py` | Least Core (additiv, multiplikativ), Shapley, Nukleolus |
| `stg_allocations.py` | fünf Aufteilungen und ihre Kennzahlen |
| `stg_evaluation.py` | Analyse einer Instanz, Messreihen der Experimente, Verdikte, Tabellen |
| `stg_data.py` | Laden der vorgerechneten Reihen, Erzeuger-Hash |
| `stg_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `stg_presets.py`, `stg_layout.py` | Permalink, Presets, Schnellstart in der Seitenleiste, fester Kopf |
| `stg_texts.py` | Annahmen-Text (App und README wörtlich gleich) |
| `data/` | `raster_leere_kerne.json` (Experiment 1), `aufteilungen_leerer_kern.json` (Experiment 4) |
| `tools/make_data.py` | erzeugt die beiden Dateien in `data/` (rund 2,5 Minuten) |
| `tests/` | siehe Tests |

## Bewusst nicht umgesetzt

- **Kapazität der Standorte** (siehe `kapazitierte-standortplanung-demo`; die Herleitung „Kern leer genau dann, wenn Lücke größer als 1“ ist hier nur für den Fall ohne Kapazität gebaut) und **private Werte** (siehe `moulin-demo`).
- **Ein zweites Vehikel Energiegemeinschaft:** dasselbe Modell mit anderer Kulisse.
- **Nukleolus oberhalb n = 10** und eine Konstruktion des Kerns ohne die 2^n Koalitionen (Zeilenerzeugung): Experiment 6 entscheidet nur, ob der Kern leer ist.
- **PDF-Export.** Die Erklärseite „verständlich erklärt“ gibt es: [standortspiel-erklaert.html](https://sebastianhanisch.net/standortspiel-erklaert.html).

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Die in der Streamlit Cloud eingestellte Python-Version ist beim ersten Deploy zu nennen; lokal lief die Entwicklung mit Python 3.14, die CI nutzt 3.12. <!-- lint-ok: dezimalpunkt -->

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy (HiGHS).

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Koalitionen und Teilen: Macht und Aufteilung](https://sebastianhanisch.net/konzepte-koalitionen-teilen.html).
