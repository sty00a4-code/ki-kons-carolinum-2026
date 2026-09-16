# Leistungsübersicht API

FastAPI-Backend für die klinische Kompetenz- und Lernverlaufsanalyse. Liest/schreibt auf `leistungen.db` was aus dem Schema in
`leistungen.sql` über SQLAlchemy Core (rohes SQL via `text()`) erstellt wird.

Diese API ist die einzige Komponente, die direkt mit der DB spricht. Jede zukünftige UI sprechen nur über HTTP/JSON mit
dieser API.

```
UI  <- HTTP/JSON ->  API  <- SQLAlchemy ->  DB
```

## Inhalt

- [Schnellstart](#schnellstart)
- [Projektstruktur](#projektstruktur)
- [Architektur-Entscheidungen](#architektur-entscheidungen)
- [Endpunkte](#endpunkte)
  - [/students](#students)
  - [/classes](#classes)
  - [/semesters](#semesters)
  - [/patients](#patients)
  - [/assignments](#assignments)
  - [/treatment-cases](#treatment-cases)
  - [/osce](#osce)
  - [/analysis](#analysis)
- [Der Matching-Algorithmus](#der-matching-algorithmus-assignment_servicepy)
- [Bekannte Lücken / offene Punkte](#bekannte-lücken--offene-punkte)
- [Typische Stolpersteine](#typische-stolpersteine)

## Schnellstart

Voraussetzung: `leistungen.db` existiert bereits im `projekt2`-Hauptordner, per `build-db.py` + `dummy.py` erzeugt, basierend auf `leistungen.sql` + `test.sql`.

```bash
cd projekt2/api

# 1. Virtuelle Umgebung anlegen und aktivieren
python3 -m venv .venv
source .venv/bin/activate # Windows: .venv\Scripts\activate

# 2. Abhängigkeiten installieren
pip install -r requirements.txt

# 3. DB-Datei im api/-Ordner erreichbar machen (einmalig, nicht kopieren!)
ln -s ../leistungen.db leistungen.db # Windows: DB stattdessen manuell reinkopieren

# 4. Server starten
uvicorn app.main:app --reload --port 8000
```

Danach im Browser öffnen:
- **http://localhost:8000/docs:** interaktive Swagger-UI, jeder Endpunkt
  direkt mit "Try it out" testbar
- **http://localhost:8000/health:** sollte `{"status": "ok"}` zurückgeben

## Projektstruktur

```
api/
├── requirements.txt
├── leistungen.db                  (Symlink auf ../leistungen.db)
└── app/
    ├── main.py                    FastAPI-Einstiegspunkt: App-Objekt, CORS, bindet alle Router ein, ruft ensure_schema() beim Start
    ├── database.py                SQLAlchemy-Engine + get_db()-Dependency (eine Session pro Request)
    ├── schema_updates.py          ensure_schema(): ergänzt fehlende Spalten und Tabellen in einer bestehenden DB
    ├── schemas.py                 Pydantic-Modelle für Requests/Responses
    ├── security.py                require_write_key(): X-API-Key-Prüfung für Schreib-Endpunkte
    ├── routers/
    │   ├── students.py            /students - Studentenliste, Fortschritt pro Kategorie/Klasse
    │   ├── classes.py             /classes, Klassenkatalog lesen und Planungswerte ändern
    │   ├── semesters.py           /semesters, alle Semester mit Daten
    │   ├── patients.py            /patients - Patientenfälle
    │   ├── assignments.py         /assignments, Zuordnung Patient zu Studierendem
    │   ├── treatment_cases.py     /treatment-cases - lesen + anlegen
    │   ├── osce.py                /osce - OSCE-Ergebnisse
    │   └── analysis.py            /analysis - KI-Trigger/Job-Status, Patienten-Matching
    └── services/
        └── assignment_service.py  Matching-Logik (Studenten-Defizite ↔ Patienten-Beiträge), von analysis.py aufgerufen
```

Router enthalten nur HTTP-Handling (Pfad, Query-Parameter, Response-Model).
Alles, was mehr als eine einzelne SQL-Abfrage braucht, insbesondere die
Matching-Logik. Steht in `services/`, damit es unabhängig von FastAPI
testbar bleibt.

## Architektur-Entscheidungen

- **SQLAlchemy Core**: Jede Query ist rohes SQL in `text(...)`, Ergebnisse werden per
  `.mappings()` in Dicts umgewandelt und dann mit `SchemaKlasse.model_validate(row)`
  in ein Pydantic-Modell gegossen.
- **SQLite mit `check_same_thread=False`**: uvicorn bedient Requests aus
  mehreren Threads, SQLite-Connections sind standardmäßig an einen Thread
  gebunden. Für den Pilotbetrieb mit wenigen gleichzeitigen Nutzern reicht das.
  Sobald mehrere Personen gleichzeitig **schreiben**, sollte auf PostgreSQL migriert werden.
  SQLite serialisiert Schreibzugriffe und kann bei echter Nebenläufigkeit zu
  `database is locked`-Fehlern führen.
- **Response-Modelle mit `from_attributes=True`**: erlaubt `model_validate()`
  direkt auf SQLAlchemy-`RowMapping`-Objekten (die sich wie ein Mapping/Objekt
  mit Attributen verhalten), ohne die Zeilen erst manuell in Dicts umzubauen.
- **Schema-Ergänzung beim Start**: `main.py` ruft in der Lifespan-Funktion
  `ensure_schema(engine)` aus `schema_updates.py` auf. Die Funktion liest
  `pragma table_info` und legt nur an, was fehlt: die Spalten
  `classes.stretchable`, `classes.max_semesters`, `patients.pseudonym`,
  `patients.age`, `patients.category`, `patient_cases.difficulty`,
  `patient_cases.expected_dur_min`, die Tabelle `patient_assignments` und
  den eindeutigen Index auf `patients.pseudonym`. Vorhandene Daten bleiben
  unverändert, ein zweiter Start ändert nichts mehr. Frische Datenbanken
  bekommen dieselben Definitionen über `leistungen.sql` (`build-db.py`);
  beide Stellen müssen zusammenpassen.
- **CORS offen (`allow_origins=["*"]`)**: für lokale Entwicklung, damit z.B.
  eine separate UI auf einem anderen Port ohne CORS-Fehler zugreifen kann.
  **Vor Produktivbetrieb auf die tatsächliche UI-Domain einschränken.**
- **Keine Auth bisher**: `POST /treatment-cases` ist aktuell ungeschützt.
  Die im Haupt-README skizzierten Rollen (Studierende/Lehrende/Admin) sind
  noch nicht implementiert (siehe [Bekannte Lücken](#bekannte-lücken--offene-punkte)).

## Endpunkte

Alle Beispiele gehen von `http://localhost:8000` aus. Vollständige,
interaktive Dokumentation immer unter `/docs`.

Alle schreibenden Endpunkte (`POST`, `PATCH`, `PUT`, `DELETE`) verlangen den
Header `X-API-Key`, sobald die Umgebungsvariable `PROJEKT2_API_KEY` gesetzt
ist (`security.py`); ohne die Variable bleibt alles offen. Fehlt der
Schlüssel oder stimmt er nicht, antwortet die API mit 401.

### `/students`

| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | `/students` | Alle Studierenden (id, anon_code, enrollment_semester) |
| GET | `/students/{student_id}/category-progress` | Fortschritt pro **Kategorie** für einen Studenten |
| GET | `/students/{student_id}/class-progress` | Fortschritt pro einzelner **Klasse** (feingranularer) |

Beide Progress-Endpunkte akzeptieren optional `?semester=2025SoSe`, um auf
ein einzelnes Semester einzuschränken (Format `YYYYSoSe`/`YYYYWiSe`, wie in
der DB). Ohne den Parameter wird über alle Semester aggregiert.

`category-progress` summiert `students_classes.points` pro Kategorie und
vergleicht mit `categories.min_points`. `done` ist `true`, sobald die Summe
das Minimum erreicht; `progress_pct` ist der Prozentsatz davon (kann über
100 gehen).

`class-progress` macht dasselbe eine Ebene tiefer, pro `classes`-Zeile, und
berücksichtigt zusätzlich `min_count` (Mindestanzahl an Fällen, nicht nur
Punkte). `done` ist nur `true`, wenn **beide** Bedingungen erfüllt sind
(falls für die Klasse definiert; `null` bedeutet "keine Vorgabe", zählt
also nicht negativ).

Beispiel:
```bash
curl "http://localhost:8000/students/0/class-progress?semester=2025SoSe"
```

### `/classes`

| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | `/classes` | Katalog aller Behandlungsklassen mit Kategoriename und Planungswerten |
| PATCH | `/classes/{class_id}` | Planungswerte einer Klasse ändern (`ClassUpdate`), 404 falls unbekannt |

`ClassOut` enthält neben den Katalogfeldern die Planungswerte `difficulty`
(1 leicht, 2 mittel, 3 schwer), `expected_dur_min` (Minuten; die Oberfläche
rechnet in Blöcken zu 90 Minuten), `stretchable` (`true`: die Leistung darf
sich über mehrere Semester ziehen) und `max_semesters` (1 bis 4, `null` =
keine Vorgabe).

`PATCH`-Body (`ClassUpdate`), alle Felder optional. Nur gesendete Felder
werden geschrieben, ein gesendetes `null` löscht den Wert:
```json
{"difficulty": 2, "expected_dur_min": 90, "stretchable": false, "max_semesters": 1}
```

### `/semesters`

| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | `/semesters` | Alle Semester, in denen Daten existieren, chronologisch sortiert |

### `/patients`

| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | `/patients` | Alle Patienten, auch ohne Fälle, mit `case_count` |
| GET | `/patients/{patient_id}` | Ein Patient mit seinen geplanten Fällen (`PatientDetail`), 404 falls unbekannt |
| GET | `/patients/{patient_id}/cases` | Alle geplanten Leistungen (`patient_cases`) für einen Patienten |
| POST | `/patients` | Patient anlegen (`PatientIn`), Antwort 201 mit `PatientDetail` |
| PATCH | `/patients/{patient_id}` | Patient ändern (`PatientUpdate`), nur gesendete Felder |
| DELETE | `/patients/{patient_id}` | Patient samt Zuordnung und geplanten Fällen löschen, 204; 409 wenn Behandlungsfälle auf ihn verweisen |
| POST | `/patients/{patient_id}/cases` | Geplanten Fall anlegen (`PatientCaseIn`), Antwort 201 mit `PatientCaseOut` |
| PATCH | `/patients/{patient_id}/cases/{case_id}` | Fall ändern (`PatientCaseUpdate`), 404 wenn der Fall nicht zum Patienten gehört |
| DELETE | `/patients/{patient_id}/cases/{case_id}` | Fall löschen, 204 |

Felder am Patienten: `pseudonym` (Kennung statt Klarname, 1 bis 50
Zeichen, eindeutig; eine doppelte Kennung ergibt 409), `age` (0 bis 120) und
`category` (Patientenkategorie 1 bis 4: über wie viele Semester sich die
Behandlung erstreckt). `name` bleibt für Bestandsdaten erhalten. Beim Anlegen
muss mindestens `pseudonym` oder `name` gesetzt sein, sonst 422; ein `PATCH`
darf nicht beide auf `null` setzen.

Felder am geplanten Fall: `difficulty` (1 bis 3) und `expected_dur_min`
(Minuten), beide optional; `null` heißt, der Wert der Klasse gilt. Eine
unbekannte `class_id` ergibt 422 mit dem Feldnamen im Detail.
`GET /patients/{patient_id}/cases` liefert zusätzlich `id` (Fall-id),
`class_id`, `difficulty` und `expected_dur_min`; die bisherigen Felder
bleiben. Die feste Zuordnung eines Patienten zu einem Studierenden steht
unter [/assignments](#assignments).

`POST`-Body (`PatientIn`):
```json
{"pseudonym": "P-0417", "name": null, "age": 54, "category": 2}
```

`POST`-Body für einen Fall (`PatientCaseIn`):
```json
{"class_id": 5, "region": "36", "min_points": 2, "max_points": 4, "difficulty": 2, "expected_dur_min": 90}
```

Liefert Region/Zahn, Kategorie, Klasse und die im Schema hinterlegte
Punkte-Spanne (`min_points`/`max_points`) je Fall. **Patienten haben im
Schema keinen direkten `student_id`-Bezug**; ein Patient ist nicht fest
einem Studenten zugeordnet; welcher Student welchen Patienten behandelt,
steht (sobald vorhanden) in `treatment_cases`, nicht in `patient_cases`.
Eine geplante Zuordnung für die Kursplanung (noch vor der Behandlung) steht
in `patient_assignments`, siehe [/assignments](#assignments).

### `/assignments`

Zuordnung Patient zu Studierendem (Tabelle `patient_assignments`). Ein Patient
ist höchstens einem Studierenden zugeordnet, deshalb ist die `patient_id` der
Schlüssel in der Adresse.

| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | `/assignments` | Alle Zuordnungen (`AssignmentOut`) |
| PUT | `/assignments/{patient_id}` | Zuordnung anlegen oder ersetzen (`AssignmentIn`), 422 bei unbekannter `patient_id` oder `student_id` |
| DELETE | `/assignments/{patient_id}` | Zuordnung aufheben, 204; 404 wenn keine besteht |

`PUT`-Body (`AssignmentIn`):
```json
{"student_id": 3, "semester": "2026WiSe", "note": "Recall im Januar"}
```

`semester` ist optional und folgt dem Muster `JJJJSoSe`/`JJJJWiSe`.
`AssignmentOut` enthält `patient_id`, `patient` (Pseudonym, sonst Name),
`student_id`, `semester`, `note` und `created_at`. Ein `PUT` auf eine
bestehende Zuordnung ersetzt sie vollständig, `created_at` wird neu gesetzt.

### `/treatment-cases`

| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | `/treatment-cases` | Liste, optional gefiltert nach `?student_id=` und/oder `?semester=` |
| GET | `/treatment-cases/{case_id}` | Einzelner Behandlungsfall, 404 falls nicht gefunden |
| POST | `/treatment-cases` | Neuen Behandlungsfall anlegen |

`POST`-Body (`TreatmentCaseIn`):
```json
{
  "student_id": 0,
  "class_id": 5,
  "patient_id": 2,
  "case_category_id": null,
  "semester": "2025SoSe",
  "difficulty": 2,
  "expected_duration_min": 60,
  "actual_duration_min": null,
  "setting": null,
  "treatment_date": "2025-05-14",
  "notes": "Erstuntersuchung"
}
```
Nur `student_id`, `class_id` und `semester` sind Pflichtfelder, alles
andere optional. Antwort ist `201 Created` mit dem vollständigen,
angereicherten Datensatz (inkl. aufgelöster Kategorie-/Klassen-/Patientennamen).

**Wichtig:** Dieser Endpunkt ist aktuell **ungeschützt**. Jeder, der die API
erreicht, kann Behandlungsfälle anlegen. Das ist als Platzhalter gedacht
(siehe Haupt-README: "Lehrende: ... Behandlungsfälle anlegen/bewerten") und
muss vor echtem Einsatz mit Auth abgesichert werden.

Die Tabelle `treatment_cases` ist in der aktuellen Testdatenbank leer. Die
Query funktioniert, liefert aber `[]`, bis Daten reinkommen.

### `/osce`

| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | `/osce/results` | OSCE-Ergebnisse, optional gefiltert nach `?student_id=` und/oder `?semester=` |

Joint über `student_osce_results` → `osce_stations` → `osce_exams`, plus
optional die geprüfte Kompetenz (`competencies`, falls einer Station
zugeordnet). Auch diese Tabelle ist aktuell leer.

### `/analysis`

Kernstück des QuiS_kiwi-Projekts: KI-gestützte Lernverlaufsanalyse und
Patienten-Zuweisung.

| Methode | Pfad | Beschreibung |
|---|---|---|
| POST | `/analysis/students/{student_id}/trigger` | Startet die Lernverlaufsanalyse für einen Studenten |
| GET | `/analysis/jobs/{job_id}` | Status/Ergebnis eines Analyse-Jobs |
| GET | `/analysis/students/{student_id}/patient-recommendations` | Patienten-Rangliste für einen Studenten |
| GET | `/analysis/patient-matching` | Gesamtzuordnung aller Patienten zu Studenten |

#### Trigger/Job-Status (LLM-Analyse)

```bash
curl -X POST http://localhost:8000/analysis/students/0/trigger
# → {"job_id": "...", "status": "done"}

curl http://localhost:8000/analysis/jobs/<job_id>
# → {"status": "done", "student_id": 0, "result": {...}}
```

`build_learning_trajectory()` sammelt die Rohdaten (Kategorie-Fortschritt
über alle Semester) als Kontext. `call_llm_for_insights()` ist **noch kein
echter LLM-Call**, sie gibt aktuell nur einen Platzhalter-Text zurück.

Der Job-Status wird aktuell in einem einfachen **In-Memory-Dict** (`_JOBS`)
gehalten. geht beim Neustart des Servers verloren und funktioniert nicht,
wenn die API später mit mehreren Worker-Prozessen läuft (jeder Worker hätte
sein eigenes `_JOBS`-Dict). Für den Uni-Server durch eine echte Tabelle
(`analysis_jobs`) oder eine Task-Queue (Celery/RQ mit Redis) ersetzen, sobald
`call_llm_for_insights` durch einen echten (potenziell langsamen) API-Call
ersetzt wird und der synchrone Ablauf nicht mehr reicht.

#### Patienten-Matching

Siehe eigener Abschnitt unten, hier nur die Endpunkte:

```bash
# Rangliste für Student 0, Top 5 (Standard), optional ?limit=10
curl "http://localhost:8000/analysis/students/0/patient-recommendations"

# Gesamtzuordnung aller Patienten
curl "http://localhost:8000/analysis/patient-matching"
```

## Der Matching-Algorithmus (`assignment_service.py`)

Ziel: **Welche Patienten würden welchem Studenten am meisten helfen, ihre
offenen Anforderungen aus dem Leistungskatalog zu erfüllen**.

### 1. Defizite pro Student ermitteln (`find_missing_classes`)

Für jede Klasse mit definiertem `min_points` und/oder `min_count` wird
verglichen, was der Student **kumuliert über alle Semester** in
`students_classes` bereits erreicht hat:

```
deficit_points = max(0, min_points - erreichte_punkte)
deficit_count  = max(0, min_count  - erreichte_anzahl)
```

Klassen ganz ohne Vorgabe (`min_points` und `min_count` beide `null`)
zählen nie als Defizit, denn dafür gibt es schlicht keine Anforderung.

> **Hinweis zur Kompetenz- vs. Klassen-Ebene:** Im ursprünglichen
> API-Outline (Haupt-README) war `find_missing_competencies` vorgesehen,
> also ein Matching über die Tabellen `competencies`/`class_competencies`.
> Diese sind in der aktuellen DB aber leer, daher matcht diese Version auf
> **Klassen-Ebene**. Sobald Kompetenzdaten gepflegt werden, kann
> `find_missing_classes` durch eine kompetenzbasierte Variante ersetzt
> werden, ohne dass `rank_patients_for_student` oder `suggest_global_matching`
> sich ändern müssen. Die Funktionssignatur (Liste von "Dingen, die fehlen")
> bleibt gleich.

### 2. Beitrag jedes Patienten ermitteln (`get_patient_contributions`)

Für jeden Patienten wird über `patient_cases` gruppiert nach Klasse
berechnet, was er an Punkten beisteuern könnte:
`avg_points = AVG((min_points + max_points) / 2)` je Klasse, plus die
Anzahl der Fälle (`case_count`). Ein Patient kann mehrere Fälle derselben
Klasse haben (z.B. mehrere Füllungen).

### 3. Score berechnen (`score_patient_for_deficits`)

Für einen konkreten Studenten × Patient wird pro gemeinsamer Klasse der
**gedeckelte** Beitrag berechnet:

```
covered_points = min(avg_points * case_count, deficit_points)
covered_count  = min(case_count, deficit_count)
score += covered_points + covered_count
```

Die Deckelung (immer `min(..., deficit)`) ist bewusst so gewählt, dass ein
Patient mit einem einzigen, weit überschüssigen Fall (z.B. 20 Punkte, obwohl
der Student nur noch 2 braucht) nicht automatisch höher bewertet wird als
ein Patient, der mehrere kleinere Lücken gleichzeitig schließt. Patienten,
die **mehrere offene Klassen gleichzeitig abdecken**, werden bevorzugt.

### 4a. Rangliste pro Student (`rank_patients_for_student`)

Nicht-exklusiv: berechnet den Score jedes Patienten gegen die Defizite
**eines** Studenten, sortiert absteigend, gibt die Top-`limit` zurück.
Mehrere Studenten können hier denselben Patienten empfohlen bekomme. Das
ist beabsichtigt, es ist eine reine Empfehlung, keine Zuteilung.

### 4b. Gesamtzuordnung (`suggest_global_matching`)

Das ist die "matcht Studenten und Patienten so gut wie möglich
zusammen"-Funktion: ein **greedy Algorithmus**, kein global optimaler
(das wäre der Hungarian-Algorithmus / `scipy.optimize.linear_sum_assignment`,
bewusst nicht verwendet, um keine zusätzliche Abhängigkeit einzuführen. Bei
~5 Studenten/~10 Patienten ist der Unterschied praktisch vernachlässigbar).

Ablauf:
1. Für jeden Studenten die aktuellen Defizite berechnen.
2. In jeder Runde: über alle (Student, noch nicht zugewiesener Patient)
   -Paare den höchsten Score finden.
3. Dieses Paar zuweisen; den Patienten aus dem Pool entfernen; die Defizite
   des Studenten um das reduzieren, was der Patient abdeckt (`matched_classes`).
4. Wiederholen, bis entweder kein Patient mehr übrig ist oder kein
   verbleibendes Paar noch einen positiven Score hat.

Patienten, die für **keinen** Studenten mehr einen Nutzen bringen (weil
ihre Fälle nur Klassen betreffen, die bei allen Studenten schon erfüllt
sind), landen in `unmatched_patients`.

Antwortformat:
```json
{
  "assignments": [
    {
      "student_id": 4,
      "patient_id": 2,
      "patient_name": "Tim Keller",
      "score": 26.0,
      "matched_classes": [
        {"class_id": 7, "class_name": "WK", "category": "Endodontologie",
         "covered_points": 9.0, "covered_count": 1, "available_cases": 1}
      ]
    }
  ],
  "unmatched_patients": [
    {"patient_id": 3, "patient_name": "Elena Rodriguez"}
  ]
}
```

## Bekannte Lücken / offene Punkte

- **Keine Authentifizierung/Autorisierung.** Alle Endpunkte sind offen,
  inklusive des schreibenden `POST /treatment-cases`. Die im Haupt-README
  skizzierten Rollen (Studierende/Lehrende/Admin) sowie `routers/auth.py`
  (`login`, `get_current_user`) sind noch nicht implementiert.
- **`call_llm_for_insights` ist ein Platzhalter.** Kein echter LLM-API-Call.
- **Job-Status nur in-memory.** Siehe oben. Für Mehrprozess-/Neustart-feste
  Jobs auf eine DB-Tabelle oder Task-Queue umstellen.
- **Matching ist klassen- statt kompetenzbasiert**, weil `competencies` /
  `class_competencies` leer sind (siehe oben).
- **Matching ist greedy, nicht global optimal.** Für die aktuelle
  Kohortengröße unkritisch, bei deutlich mehr Studierenden/Patienten ggf.
  auf `scipy.optimize.linear_sum_assignment` umstellen.
- **`update_treatment_case`** (aus dem ursprünglichen Outline) fehlt noch.
  Bisher nur Anlegen (`POST`), kein Bearbeiten (`PUT`/`PATCH`) oder Löschen.
- **`treatment_cases` und `student_osce_results` sind in der Testdatenbank
  leer.** Die zugehörigen Endpunkte sind fertig und funktionieren, liefern
  aber `[]`, bis über die DB oder `POST /treatment-cases` Daten angelegt werden.
- **`generate_test_sql.py`** (im `projekt2`-Hauptordner, nicht Teil der API)
  erzeugt SQL, das nicht zum aktuellen Schema passt (schreibt in eine
  Spalte `classes.min`, die es nicht gibt). Betrifft die API nicht direkt,
  aber die Testdaten-Erzeugung aus der echten Kursleistungs-Excel.

## Typische Stolpersteine

- **`GET /students` gibt 500 / "no such table: students"** → `leistungen.db`
  im `api/`-Ordner ist leer oder fehlt (SQLite legt beim ersten Zugriff
  automatisch eine neue, leere Datei an, statt einen Fehler zu werfen).
  Prüfen mit:
  ```bash
  ls -la leistungen.db
  sqlite3 leistungen.db ".tables"   # sollte students, classes, categories, ... auflisten
  ```
  Falls leer/fehlend: Symlink neu setzen und Server neu starten:
  ```bash
  rm leistungen.db && ln -s ../leistungen.db leistungen.db
  ```
- **`ModuleNotFoundError`** → venv nicht aktiviert oder
  `pip install -r requirements.txt` nicht ausgeführt.
- **Port 8000 schon belegt** → anderen Port nehmen:
  `uvicorn app.main:app --reload --port 8010`.
- **Leere Listen (`[]`) bei `/treatment-cases` oder `/osce/results`** → kein
  Fehler, die Tabellen sind in der aktuellen Testdatenbank einfach leer.