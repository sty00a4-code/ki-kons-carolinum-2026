# KI-Analyse – Prompt- und Modell-Dokumentation (Reproduzierbarkeit)

**Modell:** `claude-fable-5` (Anthropic) · **Datum des Laufs:** 2026-08-10 ·
**Reasoning-Effort:** high · **Je Proband ein unabhängiger Lauf** (5 parallel) ·
**Output:** JSON-Schema-erzwungen (Befunde / optimierter Verlauf / Auswirkungen / Fazit)

## Input

`probanden_export.json` (erzeugt von `scripts/export_ki.py`): Leistungskatalog
mit Soll-Werten, Regeln (1 P ≈ 45 min; Ampel ≥75/50–75/<50), je Proband die
Leistungen je Semester (IK I–III), Kontrollsummen, dokumentierte Lücken.

## Prompt-Vorlage (N = Probanden-Nummer 1–5)

```text
Du bist die KI-Analyse in "Projekt 2 – KI-gestützte Analyse klinischer
Lernverläufe" (Zahnmedizin, Uni Frankfurt). Lies die Datei
"docs/ki-analyse/probanden_export.json" (READ-ONLY). Analysiere
AUSSCHLIESSLICH den Probanden "Stud. N" – erfinde keine Daten, rechne nur
mit dem, was in der Datei steht.

Methodik-Vorgaben (aus dem Kick-Off, Folie 4 Schritt 3):
1. PRÜFUNG vs. Originalstand: Bewerte je Dimension – didaktische Reihenfolge
   (einfach → schwer über die Semester; nutze die Demo-Schwierigkeitsgrade
   1–3), inhaltliche Ausgewogenheit über die Kategorien, Erfüllung der
   Mindestpunkte je Kategorie (Ampel: >=75 % gut, 50–75 % mittel, <50 %
   gering), Klumpenbildung/Lücken (Kategorien ganz ohne Leistungen!).
   Beachte: Punkte sind je Semester aggregiert – Aussagen zur Reihenfolge
   INNERHALB eines Semesters sind nicht möglich, nur zwischen Semestern
   (das als Limitation benennen, nicht spekulieren).
2. OPTIMIERTER VERLAUF: IK I–III retrospektiv (was hätte anders verteilt
   werden sollen – konkret mit Katalog-Codes), IK IV prospektiv als
   konkreter 14-Wochen-Plan (Wochenblöcke), der die größten Lücken schließt.
   Randbedingungen: Katalog-Mindestpunkte je Kategorie, realistische
   Punktzahl je IK (~31–72 P wie bisher), Priorisierung nach Lückengröße ×
   Machbarkeit, Schwierigkeit 3 nicht alles in die ersten Wochen.
3. AUSWIRKUNGEN: je Kategorie die Ziel-Erreichung Ende IK III (exakt aus
   kategorien_summen / mindestpunkte, ganze %, Deckel 100) vs. projiziert
   Ende IK IV unter deinem Plan (nachvollziehbar aus den punkte_ziel-Werten).

WICHTIG: Schwierigkeit/Zeit sind DEMO-Platzhalter – kennzeichne Aussagen,
die darauf beruhen. Antworte auf Deutsch, für Lehrende nachvollziehbar.
```

## Vorbehalt

Schwierigkeitsgrad/Zeitbedarf waren zum Zeitpunkt des Laufs
**Demo-Platzhalter** (kein Lehrenden-Konsens, → UNIFR-16/17). Nach Vorliegen
der konsentierten Kartierung und der IK-IV-Daten: `scripts/export_ki.py` neu
ausführen und die Analyse mit identischem Prompt wiederholen.
