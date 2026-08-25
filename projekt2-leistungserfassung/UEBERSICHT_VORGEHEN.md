# Übersicht & Vorgehen – für die Demonstration

Diese Datei erklärt Schritt für Schritt, **welche Daten eingegeben werden**,
**was genehmigt wird** und **wer was macht**. Ideal zum Vorführen im Team.

## Rollen auf einen Blick

![Workflow](docs/diagrams/workflow.png)

| Rolle | Darf | Darf nicht |
|---|---|---|
| **Studierende/r** | eigene Leistungen erfassen, bearbeiten (Entwurf/abgelehnt), einreichen; nur eigene Daten sehen | fremde Daten sehen, genehmigen |
| **Doktorand/in** | eingereichte Leistungen prüfen, genehmigen/ablehnen (mit Kommentar); nur Pseudonyme sehen | – |

**Vier-Augen-Prinzip:** Wer erfasst, genehmigt nicht selbst.

## 1) Was Studierende eingeben (pro Leistung)

- **Semester/IK** (IK I–IV)
- **Leistung** aus dem festen Leistungskatalog (kein Freitext)
- **Anzahl** (wie oft durchgeführt)
- **Punkte** (1 Punkt ≈ 45 min; nur im erlaubten Bereich der Leistung)
- **anonymer Fallbezug** (Fall-Nr., keine Patienten-Klardaten) + **Datum**
- optional: **Schwierigkeitsgrad**, **Zeitbedarf**, Anmerkung

Der Leistungskatalog (Kategorien wie Parodontologie, Endodontologie, Prothetik,
KFO …) steckt in `app/catalog.py` und lässt sich dort anpassen.

## 2) Der Status-Lebenszyklus

```
Entwurf → Eingereicht → (Doktorand prüft) → Genehmigt → Auswertung
                                     ↘ Abgelehnt (mit Grund) → Korrektur → erneut
```

Nur **Genehmigt** zählt in der Auswertung.

## 3) Was Doktoranden prüfen (Validität)

Beim Öffnen eines Eintrags zeigt die App automatische Checks:

1. Leistung ist im Katalog
2. Punkte im erlaubten Bereich (z. B. Klasse V = genau 1; UPT = 2–3)
3. Anzahl plausibel (Soll-Richtwert)
4. Semester zugeordnet
5. anonymer Fallbezug vorhanden

Die Doktorandin/der Doktorand entscheidet dann **fachlich final**: **Genehmigen**
(optional Kommentar) oder **Ablehnen** (Grund ist Pflicht → geht zur Korrektur zurück).

## 4) Auswertung

Unter „Auswertung" erscheint ein aus Code erzeugtes Diagramm (matplotlib):
genehmigte Punkte je Kategorie, rein aggregiert/anonym. Anpassbar in
`app/routes_analysis.py`.

## 5) Demo-Skript (zum Vorführen)

1. **student1** anmelden → *Neu erfassen* → z. B. „UPT", Anzahl 1, Punkte 2 → *Speichern & Einreichen*.
2. Logout → **doktorand1** anmelden → *Prüfen* → Eintrag öffnen → Checks zeigen ✓ → *Genehmigen*.
3. *Auswertung* öffnen → Balken erscheint bei „Parodontologie".
4. Zweiten Eintrag mit ungültigen Punkten testen → Doktorand *Ablehnt* mit Grund.
5. Wieder **student1** → abgelehnten Eintrag *Bearbeiten* → korrigieren → erneut einreichen.

## Architektur

![Architektur](docs/diagrams/architektur.png)

Browser → Flask (Login, Rollen, CSRF, Eigentümer-Prüfung) → SQLite
(Pseudonyme + zufällige Tokens). Alles lokal.
