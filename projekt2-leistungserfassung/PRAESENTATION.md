# Präsentations-Leitfaden – Demo in 10 Minuten

> Drehbuch für die Live-Demo der Leistungserfassung (Projekt 2).
> App starten, falls nötig: `portpilot start projekt2-leistung` → **http://localhost:5001**
> Frische Demo-Daten: `python -m scripts.init_db` (gibt die Logins aus).

## Die Kernbotschaft (1 Satz)

Der Doktorand trägt für jede/n Studierende/n die erbrachten klinischen Leistungen
digital ein – daraus entstehen **sofort** Auswertungen, die die Kompetenz­entwicklung
jedes Studierenden über die vier IK-Semester sichtbar machen. Studierende sehen
nur ihren eigenen Stand und können einen Demo-Assistenten dazu befragen.

## Rollen & Sichtbarkeit (wichtig bei Rückfragen)

| Rolle | darf | darf NICHT |
|---|---|---|
| **Studierende/r** | sich anmelden und **nur den eigenen Stand ansehen** (read-only); Demo-Bot fragen | etwas eintragen/ändern, andere Studierende oder deren Namen sehen |
| **Doktorand/in** | **für jede/n Studierende/n Leistungen eintragen**; alle sehen (Klarnamen), Auswertung | – |

Die pseudonyme Kennung (z. B. `S-RiZ82Q`) ist nur der **Login-Name** der
Studierenden, damit niemand fremde Konten erraten kann. Der Doktorand arbeitet
mit Klarnamen. **Nur der Doktorand schreibt** – Studierende sind rein lesend.

## Demo-Ablauf (4 Schritte)

**Logins (Passwort = Benutzername):** Doktorand `doktorand1 / doktorand1` ·
Studierende: Kennung aus `init_db`-Ausgabe, Passwort = dieselbe Kennung.

### 1. Doktorand trägt eine Leistung ein (3 Min)
Als `doktorand1` anmelden → **„Studierende"** → eine Person **„Öffnen / eintragen"**.
- Oben Formular **„Leistung eintragen"**: Semester (IK I–IV) · Leistung aus dem
  festen Katalog (kein Freitext) · Anzahl · Punkte (nur erlaubter Bereich, wird
  vorbelegt) · anonymer Fallbezug (Fall-Nr., keine Patientendaten) · Datum.
- **„Leistung eintragen"** → zählt **sofort**, signiert mit dem Prüfernamen.
- Darunter sieht man live: **Verlauf über die Jahre**, **Radar**, **Fortschritt**
  und alle Einzel-Einträge (mit „Löschen").

> 💬 „Nur der Doktorand trägt ein – kein Student kann Daten verändern."

### 2. Auswertung – alle im Vergleich (2 Min)
Menü **„Auswertung"**:
- **Balken-Vergleich** aller Studierenden (Ampel: grün ≥ 75 %, gelb 50–75 %, rot < 50 %).
- **Kompetenzmatrix** Studierende × Kategorien – wer ist wo stark, wo sind Lücken.
- **🔄 Aktualisieren** zeigt: die Grafiken werden **live aus der Datenbank** berechnet.

### 3. Studenten-Sicht – read-only (2 Min)
Abmelden → als Studierende/r (Kennung) anmelden:
- **„Mein Stand"**: Metriken (Gesamt-%, Kategorien erfüllt), Fortschrittsbalken je
  Kategorie, eigene Einträge mit „eingetragen von Dr. …". **Keine Buttons zum
  Ändern** – rein lesend.
- Der eben eingetragene Eintrag ist sofort da.

### 4. Demo-Bot (1 Min)
Unten rechts **„🤖 Studien-Assistent (Demo)"** anklicken:
- Fragen wie „Wie ist mein Stand?", „Wo habe ich Lücken?", „Gib mir einen Tipp".
- Wichtig: **nur Demo** (noch kein echter Bot) und er kennt **ausschließlich die
  eigenen Daten** – man kann darüber nichts über andere Studierende erfahren.

## Häufige Fragen – Antworten

- **„Wann werden die Grafiken neu generiert? Wer macht das?"** Niemand –
  **automatisch bei jedem Seitenaufruf** (Live-Routen). Nach einem Eintrag genügt
  „🔄 Aktualisieren". Die Skripte (`student_report.py`, `make_diagrams.py`) sind
  nur zum **Export als Dateien**.
- **„Kann ein Student Daten ändern?"** Nein. Studierende haben **keine**
  Schreib-Route; jeder Schreibversuch wird serverseitig mit `403` abgelehnt.
  Belegt durch `python -m tests.selftest_security` (8 Prüfungen).
- **„Kann der Bot Daten anderer sehen?"** Nein. Der Bot bekommt nur die Daten
  der/des eingeloggten Studierenden; es gibt keinen Endpoint für fremde Daten.
- **„Wo liegen die Daten?"** Lokal in SQLite (`data/leistung.db`). Backups:
  `python -m scripts.backup`.
- **„Woher kommt der Leistungskatalog?"** Aus der Punkteübersicht IK I–IV
  („Blaue Liste", 1 Punkt ≈ 45 min) in `app/catalog.py` (Ziel gesamt 328 Punkte).

## Not-Hilfe während der Demo

| Problem | Lösung |
|---|---|
| Seite lädt nicht | `portpilot restart projekt2-leistung`, dann http://localhost:5001 |
| Demo-Daten neu | `python -m scripts.init_db` (neue Logins werden ausgegeben) |
| Logins vergessen | Doktorand immer `doktorand1 / demo-doktorand`; Studierende in der `init_db`-Ausgabe |
