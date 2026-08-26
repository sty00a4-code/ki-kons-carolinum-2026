# Leistungserfassung IK – Projekt 2

Sichere Web-App zur **Erfassung klinischer Leistungen** in der Zahnmedizin
(IK I–IV). Alles läuft **lokal**, Daten bleiben auf dem Rechner.

- **Nur Doktoranden tragen ein**: Sie erfassen für jede/n Studierende/n die
  erbrachten Leistungen aus dem Katalog – das zählt sofort.
- **Studierende sind read-only**: Sie sehen nur ihren eigenen Stand und können
  einen **Demo-Assistenten** (nur eigene Daten) befragen.
- Daraus entstehen live die **Auswertungen** (Vergleich, Matrix, Verlauf).
- **Patientenfälle & Matching**: Doktoranden erfassen anonyme Fälle
  (Fall-Nr. + Behandlungsbedarf, Menü „Fälle"); das Matching empfiehlt je Fall
  die/den passende/n Studierende/n und zeigt Studierenden ihre Top-Fälle
  („Empfohlene Patientenfälle", wie Kick-Off-Dashboard D).

## Schnellstart

```bash
cd ki-kons-projekt2-app
python3.13 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python -m scripts.init_db         # DB + Demo-Zugänge anlegen
python -m scripts.make_diagrams   # Übersichts-Diagramme erzeugen
flask --app app run --debug       # startet http://127.0.0.1:5000
```

Demo-Zugänge (nach `init_db`, Passwörter nur für die Demo!):

**Passwort = Benutzername** (einfach für die Demo):

| Rolle | Benutzer | Passwort |
|---|---|---|
| Doktorand (Prüfer) | `doktorand1` | `doktorand1` |
| Studierende (Echtdaten-Import) | `stud1` … `stud5` | wie der Benutzername |

Die einfachen `stud1`-Logins gelten **nur für den Testbetrieb** – vor einem
Echtbetrieb müssen individuelle Passwörter gesetzt werden. Das anonyme
Pseudonym (z. B. `S-0R8P1w`) bleibt davon unberührt; den **Klarnamen** sieht
weiterhin nur der Doktorand.

**Für die Live-Demo:** Schritt-für-Schritt-Drehbuch in **[PRAESENTATION.md](PRAESENTATION.md)**.

## Demo in 4 Schritten

1. Als **doktorand1** anmelden → „Studierende" → eine Person „Öffnen / eintragen".
2. Formular **„Leistung eintragen"** ausfüllen → zählt sofort; darunter Verlauf, Radar, Fortschritt.
3. „Auswertung" → **alle Studierenden im Vergleich** (Balken + Kompetenzmatrix).
4. Abmelden, als Studierende/r (Kennung aus `init_db`) anmelden → **„Mein Stand"** (read-only) + **Demo-Bot** unten rechts.

Ausführliche Anleitung: **[UEBERSICHT_VORGEHEN.md](UEBERSICHT_VORGEHEN.md)**.

## Sicherheit / Datenschutz (Kurzfassung)

- Studierende werden nur über ein **zufälliges Pseudonym** geführt (kein Klarname in der DB).
- Datensätze haben **zufällige Tokens statt hochzählbarer IDs** → kein Zugriff durch
  „Zahl am Ende ändern" (IDOR-sicher). Zugriff auf eigene Daten nur über die Login-Session.
- **Rollen** serverseitig erzwungen: nur Doktoranden dürfen genehmigen.
- Passwörter gehasht, CSRF-Schutz, Session-Cookies httponly.
- **Echte Daten kommen nie ins Git-Repo** (`data/`, `backups/`, `instance/` sind ignoriert).

Details: **[DATENSCHUTZ.md](DATENSCHUTZ.md)**. Sicherheits-Selbsttest:
`python -m tests.selftest_security`.

## Projektstruktur

```
app/            Flask-App (Backend + Templates + CSS)
  catalog.py    Leistungskatalog ("Blaue Liste") – hier anpassen
  matching.py   Fall-Empfehlung (transparente Lücken-Logik, Dashboard D)
  schema.sql    Datenbank-Schema
  security.py   Tokens, CSRF, Rollen-/Eigentümer-Schutz
scripts/        init_db (Demo) · import_probanden (Echtdaten aus Excel) ·
                kartierung_demo · export_ki · migrate_faelle · seed_faelle ·
                backup · make_diagrams
tests/          Sicherheits-Selbsttest
docs/diagrams/  aus Code erzeugte Diagramme (Workflow, Architektur)
docs/kartierung/  Erfassungsvorlage Schwierigkeit/Zeit für die 3 Lehrenden
docs/ki-analyse/  KI-Export + Analyse-Ergebnisse (Phase 3)
data/           echte Datenbank (git-ignoriert)
```

## Datensicherung

`python -m scripts.backup` legt eine Zeitstempel-Kopie der Datenbank plus einen
CSV-Export (nur Pseudonyme) unter `backups/` ab.
