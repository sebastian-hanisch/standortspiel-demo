"""Feste Texte der App, die die README wörtlich wiederholt (ein Test vergleicht beide Fassungen)."""

import stg_constants as C

ASSUMPTIONS_MARKDOWN = f"""
**Annahmen**
- **Ein Kunde ist ein Spieler.** Ein Standort kostet Fixkosten f, ein Kunde den Weg zum nächsten offenen Standort. Wege sind euklidisch in der Ebene, Standorte unkapazitiert (ein offener Standort bedient beliebig viele Kunden). Fixkosten und Lagen sind **Modellannahmen**, keine Daten.
- **Jede Koalition wählt ihre eigene billigste Standortmenge** und handelt ohne Kosten mit niemandem sonst. Das ist die Definition des Koalitionswerts c(S), keine Aussage über reale Gruppen.
- Die Zufallslagen sind gleichverteilt im Quadrat {C.AREA:.0f} × {C.AREA:.0f} oder zwei Ballungen; der Ring hat Kunden im Abstand s auf einem Kreis und die Standorte in den Kantenmitten (n = 3 ist das gleichseitige Dreieck); die Störung der Ring-Positionen ist gleichverteilt in ±σ je Koordinate.

**Grenzen**
- Der Kern wird über alle 2^n − 2 echten Koalitionen per LP bestimmt, deshalb höchstens n = {C.N_MAX} Kunden und {C.M_MAX} Standorte (beim Ring m = n). Das Kriterium „Kern leer genau dann, wenn Lücke größer als 1“ braucht die Koalitionen nicht und reicht im Experiment 6 bis n = {C.N_GROSS_MAX} mit {C.M_GROSS_MAX} Standorten.
- Die Gleichwertigkeit „Kern leer genau dann, wenn Lücke größer als 1“ ist für den unkapazitierten Fall hier hergeleitet (Beweisskizze im 📐-Expander) und an Instanzen gemessen. Sie ist nicht aus dem Volltext der Quelle übernommen.
- Die Ring-Formeln für Lücke und ε* sind hergeleitet und nur im gemessenen Bereich bestätigt (Experiment 5); außerhalb stimmen sie nicht.
- Der Zuschuss „Preis der Stabilität“ ist ein Rechenwert des Modells, kein Vorschlag, wer ihn zahlen soll.

**Bekannte Probleme und Unsicherheiten**
- Zählungen wie „Kern leer in k von N Instanzen“ sind Messungen an gezogenen Zufallsinstanzen, **kein Beweis**. Wie oft der Kern leer ist, hängt von der Verteilung ab (gemessen: gleichverteilt, n bis 8, einheitliche Fixkosten).
- Zufallsinstanzen haben selten einen leeren Kern, und der Effekt ist dort klein; die Presets mit Dreieck und Ring sind **konstruiert**, damit man den leeren Kern überhaupt sieht.
- Die Duallösung der Relaxierung ist bei Gleichstand nicht eindeutig. Die Aufteilung „Dual × Lücke“ nimmt die Lösung, die HiGHS liefert; die Zahlen dazu gelten für diese Wahl.
- Der Befund zum Shapley-Wert (Experiment 3) gilt für n = 6 Kunden und m = 4 Standorte mit den gemessenen Fixkosten.
- Literatur: von Goemans und Skutella wurden nur Titel, Jahr und Zusammenfassung gelesen (nicht der Volltext); Kolen und der Begriff „cost of stability“ sind nicht geprüft.
"""
