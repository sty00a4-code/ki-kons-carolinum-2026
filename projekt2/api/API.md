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
- [Neu in 0.2: Sicherheit, Verträge, Betrieb](#neu-in-02-sicherheit-verträge-betrieb)
  - [Versionierung](#versionierung)
  - [Anmeldung und Rollen](#anmeldung-und-rollen)
  - [Fehlerformat](#fehlerformat)
  - [Pagination, Sortierung, Suche](#pagination-sortierung-suche)
  - [Soft Delete und Audit-Log](#soft-delete-und-audit-log)
  - [Migrationen](#migrationen)
  - [Asynchrone Analyse-Jobs](#asynchrone-analyse-jobs)
  - [Konfiguration](#konfiguration)
- [Endpunkte](#endpunkte)
  - [/students](#students)
  - [/categories](#categories)
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

# 4. Datenbank auf den aktuellen Stand bringen (in der Entwicklung macht das
#    die API beim Start auch selbst) und einen ersten Admin anlegen
python -m app.cli migrate
python -m app.cli create-user admin admin

# 5. Server starten; ohne PROJEKT2_JWT_SECRET läuft der offene Entwicklungsmodus
export PROJEKT2_JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
uvicorn app.main:app --reload --port 8000
```

Danach im Browser öffnen:
- **http://localhost:8000/docs:** interaktive Swagger-UI (nur in der Entwicklung); mit "Authorize"
  das Token aus `POST /api/v1/auth/login` eintragen
- **http://localhost:8000/api/v1/health:** sollte `{"status": "ok"}` zurückgeben

## Projektstruktur

```
api/
├── requirements.txt
├── requirements-dev.txt           zusätzlich pytest + httpx für die Tests
├── leistungen.db                  (Symlink auf ../leistungen.db)
├── tests/                         pytest-Suite (frische Wegwerf-DB pro Test)
└── app/
    ├── main.py                    FastAPI-Einstiegspunkt: App, CORS, Fehler-Handler, Request-ID, /api/v1, Startprüfungen
    ├── config.py                  Umgebungsvariablen, Startprüfung (fail closed in Produktion)
    ├── database.py                SQLAlchemy-Engine + get_db()-Dependency (eine Session pro Request)
    ├── migrations.py              nummerierte Schema-Migrationen (ersetzt schema_updates.py/ensure_schema)
    ├── cli.py                     python -m app.cli migrate | status | create-user | list-users
    ├── schemas.py                 Pydantic-Modelle für Requests/Responses
    ├── security.py                JWT, get_current_user, require_roles, Zugriff auf eigene Daten
    ├── passwords.py               scrypt-Hashing; throttle.py: Login-Bremse
    ├── errors.py                  einheitliches Fehlerformat
    ├── pagination.py              limit/offset, X-Total-Count, sort-Whitelist
    ├── audit.py                   Änderungsprotokoll (audit_log), schreibt in die laufende Transaktion
    ├── semester.py                Semester: Format, Parsen, Sortierschlüssel
    ├── repositories/              DB-Zugriff für neue Teile (users.py, jobs.py)
    ├── routers/
    │   ├── students.py            /students - Studentenliste, Übersicht, Fortschritt pro Kategorie/Klasse
    │   ├── categories.py          /categories - Katalog, direkt vergebene Kategorie-Punkte
    │   ├── classes.py             /classes, Klassenkatalog lesen und Planungswerte ändern
    │   ├── semesters.py           /semesters, alle Semester mit Daten
    │   ├── patients.py            /patients - Patientenfälle, Behandlungsstand
    │   ├── assignments.py         /assignments, Zuordnung Patient zu Studierendem
    │   ├── treatment_cases.py     /treatment-cases - lesen, anlegen, korrigieren, löschen
    │   ├── osce.py                /osce - OSCE-Ergebnisse
    │   ├── analysis.py            /analysis - asynchrone Jobs, Patienten-Matching
    │   ├── auth.py                /auth/login, /me
    │   ├── users.py               /users (Admin)
    │   └── audit_log.py           /audit-log (Admin)
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
- **Schema-Migrationen** statt implizitem `ensure_schema()`: siehe [Migrationen](#migrationen).
  Migration 1 enthält den früheren Stand (Spalten `classes.stretchable`, `patients.pseudonym` ...,
  Tabellen `patient_assignments`, `students_categories`); vorhandene Daten bleiben unverändert.
- **CORS** kommt aus `PROJEKT2_CORS_ORIGINS`: in der Entwicklung ohne Angabe offen, in
  Produktion ohne Angabe aus und mit `*` verboten (die API startet dann nicht).
- **Auth und Rollen** sind umgesetzt (JWT, Rollen student/teacher/admin), siehe
  [Anmeldung und Rollen](#anmeldung-und-rollen).

## Neu in 0.2: Sicherheit, Verträge, Betrieb

Die Beispiele in diesem Abschnitt nutzen die versionierten Pfade `/api/v1/...`.

### Versionierung

Alle Endpunkte stehen unter **`/api/v1`**. Die bisherigen unversionierten Pfade
(`/students`, `/patients` ...) laufen als **veraltete Aliase** weiter, sind aber
nicht mehr in `/docs` zu sehen und entfallen mit v2. Nur dort gibt es noch die
alten Kategorie-Punkte-Routen (`PUT/DELETE /categories/{id}/points`); in v1 ersetzt
sie `PUT/DELETE /api/v1/students/{student_id}/categories/{category_id}/points/{semester}`
mit dem Body `{"points": 5}`. Student, Kategorie und Semester bilden die Identität
der Ressource und stehen deshalb alle in der URL (unbekannter Student: 404 statt 422).

`GET /students/{id}/overview` ist als **Read Model** gekennzeichnet (Tag
`read-models`): eine für die UI zugeschnittene Aggregation, nicht die kanonische
Ressource.

### Anmeldung und Rollen

```bash
curl -X POST localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username": "lehrer", "password": "..."}'
# -> {"access_token": "...", "token_type": "bearer", "expires_in": 3600, "user": {...}}

curl localhost:8000/api/v1/me -H "Authorization: Bearer <token>"
```

Das Token (JWT, HS256) enthält nur die Benutzer-ID. Rolle und Aktiv-Status werden
bei jeder Anfrage aus der Datenbank gelesen: Sperren und Rollenwechsel wirken sofort.
Nach 5 Fehlversuchen in 15 Minuten (je Benutzername und Adresse) antwortet der Login
mit 429 und `Retry-After`. Die Bremse liegt im Prozess; bei mehreren Workern zählt
jeder für sich.

| Rolle | darf |
|---|---|
| `student` | nur eigene Daten: eigener Fortschritt/Overview, eigene Behandlungen, OSCE-Ergebnisse, eigene Analyse-Jobs, Kataloge |
| `teacher` | alles lesen, Behandlungen erfassen/korrigieren/löschen, Kategorie-Punkte setzen, Analysen starten |
| `admin` | zusätzlich Katalog (`PATCH /classes`), Planung (Patienten, geplante Fälle, Zuordnungen), Benutzer, Audit-Log |

Fehlt die Anmeldung, antwortet die API mit 401, fehlt die Rolle mit 403.

Betriebsarten:

- **`PROJEKT2_JWT_SECRET` gesetzt:** Anmeldung für alle Endpunkte außer `/health` und Login.
- **nicht gesetzt, `PROJEKT2_ENV=development` (Standard):** Entwicklungsmodus, jede Anfrage
  gilt als Admin (Warnung im Log). Ist `PROJEKT2_API_KEY` gesetzt, verlangen schreibende
  Methoden den Header `X-API-Key` (bisheriges Verhalten).
- **nicht gesetzt, `PROJEKT2_ENV=production`:** die API **startet nicht** (fail closed);
  zusätzlich antwortet jede Anfrage mit 401, falls die Startprüfung umgangen wird.

Der `X-API-Key` (falls konfiguriert) gilt in jeder Betriebsart als Dienst-Admin, etwa
für Skripte. Passwörter werden mit scrypt gehasht (Standardbibliothek).

Den ersten Admin legt man per CLI an (siehe [Migrationen](#migrationen)):

```bash
python -m app.cli create-user admin admin
python -m app.cli create-user studi0 student --student-id 0
```

Benutzerverwaltung (Admin): `GET/POST /users`, `PATCH /users/{id}` (Rolle, sperren,
Passwort zurücksetzen). Den eigenen Zugang kann man nicht sperren oder herabstufen (409).

### Fehlerformat

Jede Fehlerantwort hat dieselbe Form (angelehnt an RFC 7807, Content-Type
`application/problem+json`):

```json
{
  "type": "validation_error",
  "title": "Unprocessable Entity",
  "status": 422,
  "detail": "semester: Ungültiges Semester ...",
  "request_id": "9f1c...",
  "errors": [{"location": "body", "field": "semester", "message": "..."}]
}
```

`detail` ist immer ein String; `errors` gibt es nur bei Validierungsfehlern der
Eingabe. `type` ist einer von `bad_request`, `unauthorized`, `forbidden`, `not_found`,
`method_not_allowed`, `conflict`, `validation_error`, `too_many_requests`,
`unavailable`, `internal_error`. Jede Antwort trägt den Header `X-Request-ID` (ein
passender Wert des Clients wird übernommen), derselbe Wert steht im Log.

### Pagination, Sortierung, Suche

Listen (`/students`, `/patients`, `/patients/open-cases`, `/treatment-cases`,
`/assignments`, `/users`, `/audit-log`) nehmen `?limit=` (1 bis 500, Standard 100) und
`?offset=`. Der Body bleibt eine einfache Liste, die Gesamtzahl steht im Header
**`X-Total-Count`**. **Achtung:** wer bisher alles ohne Parameter abgeholt hat, bekommt
jetzt höchstens 100 Zeilen und muss Seiten abfragen.

- `/patients`: `?search=` (Teilstring in Pseudonym/Name), `?sort=id|pseudonym|age|case_count`, `?order=asc|desc`
- `/treatment-cases`: `?date_from=`, `?date_to=` (Behandlungsdatum, einschließlich),
  `?sort=treatment_date|semester|student_id|id`, `?order=`
- Ein unbekannter `sort`-Wert ergibt 422. `?semester=` wird geprüft (Format `JJJJSoSe`/`JJJJWiSe`).

Semester ist ein eigenes Konzept (`app/semester.py`): Format, Jahresbereich (2000 bis 2100),
Parsen, Weiterzählen und Sortierschlüssel stehen an einer Stelle.

### Soft Delete und Audit-Log

**Behandlungen werden nicht mehr physisch gelöscht.** `DELETE /treatment-cases/{id}?reason=...`
setzt `deleted_at`, `deleted_by`, `deletion_reason`; der Datensatz bleibt, taucht aber in
keiner Abfrage mehr auf, und der geplante Fall gilt wieder als offen. Bewertungen/Kompetenzen
an der Behandlung verhindern das Löschen weiterhin (409). Ein Patient mit Behandlungen,
auch soft-gelöschten, lässt sich nicht löschen (409), damit keine Historie verwaist.

**`GET /audit-log`** (Admin; Filter `entity`, `entity_id`, `action`, `username`) zeigt
wer wann was geändert hat, mit Zustand `before`/`after`. Protokolliert werden Behandlungen,
Patienten, geplante Fälle, Zuordnungen, Kategorie-Punkte, Klassen-Planwerte, Benutzer
(ohne Passwörter) und Analyse-Jobs. Der Eintrag entsteht in derselben Transaktion wie die
Änderung. Korrekturen (`PATCH`) überschreiben so keine Historie: der alte Stand steht im Log.
Beispiel: `?entity=treatment_case&entity_id=7`.

**Zuordnungen:** `PUT /assignments/{patient_id}` behält beim Ersetzen `created_at`, setzt
`updated_at` und legt die vorherige Fassung in der Historie ab: `GET /assignments/{patient_id}/history`
(`change` ist `replaced` oder `removed`).

### Migrationen

Das frühere `ensure_schema()` ist durch nummerierte Migrationen (`app/migrations.py`,
Tabelle `schema_migrations`) ersetzt. Der Stand von `ensure_schema` ist Migration 1.

```bash
python -m app.cli status     # Stand anzeigen
python -m app.cli migrate    # ausstehende Schritte anwenden
```

- **Entwicklung:** die API wendet beim Start ausstehende Schritte selbst an.
- **Produktion** (`PROJEKT2_AUTO_MIGRATE` aus): erst `migrate`, dann API starten.
  Startet sie mit offenen Migrationen, bricht sie ab, statt das Schema zu verändern.

Jeder Schritt ist idempotent; neue Schritte kommen unten an `MIGRATIONS`, bestehende werden
nie geändert. `leistungen.sql` bleibt das Basisschema; alles Neue (users, audit_log,
analysis_jobs, Soft-Delete-Spalten) kommt über Migrationen. Es ist bewusst **kein Alembic**:
die Schritte nutzen SQLite-Syntax. Beim Umstieg auf PostgreSQL ist Alembic die richtige Wahl.

### Asynchrone Analyse-Jobs

```bash
curl -X POST localhost:8000/api/v1/analysis/jobs -H 'Content-Type: application/json' \
  -H "Authorization: Bearer <token>" -d '{"student_id": 0}'
# 202 -> {"job_id": "abc...", "status": "queued"}
curl localhost:8000/api/v1/analysis/jobs/abc... -H "Authorization: Bearer <token>"
# -> {"status": "running", "progress": 0.4, ...}  dann  {"status": "completed", "progress": 1, "result": {...}}
```

Status: `queued`, `running`, `completed`, `failed` (mit `error`). Jobs liegen in der Tabelle
`analysis_jobs` und überleben einen Neustart als Datensatz. **Grenze:** die Ausführung läuft
über FastAPI-`BackgroundTasks` im selben Prozess. Beim Start werden unfertige Jobs als
`failed` markiert. Für mehrere Worker oder Ausfallsicherheit kommt später eine Task-Queue,
der HTTP-Vertrag bleibt gleich. `POST /analysis/students/{id}/trigger` ist veraltet: läuft
weiter synchron, liefert aber `completed`/`failed` statt `done`.

### Konfiguration

| Variable | Bedeutung |
|---|---|
| `PROJEKT2_ENV` | `development` (Standard) oder `production` |
| `PROJEKT2_JWT_SECRET` | Signierschlüssel, in Produktion Pflicht, mind. 32 Zeichen |
| `PROJEKT2_TOKEN_MINUTES` | Token-Gültigkeit, Standard 60 (kein Refresh-Token) |
| `PROJEKT2_API_KEY` | optionaler Dienst-Schlüssel (`X-API-Key`), gilt als Admin |
| `PROJEKT2_CORS_ORIGINS` | kommagetrennte UI-Origins. Ohne Angabe: Entwicklung offen, Produktion aus. In Produktion ist `*` verboten |
| `PROJEKT2_AUTO_MIGRATE` | `1`/`0`, Standard: an in Entwicklung, aus in Produktion |
| `PROJEKT2_DOCS` | `1`/`0`: Swagger-UI, Standard: an in Entwicklung, aus in Produktion |
| `PROJEKT2_DB` | Pfad der SQLite-Datei |

## Endpunkte

Alle Beispiele gehen von `http://localhost:8000` aus. Vollständige,
interaktive Dokumentation immer unter `/docs`.

Berechtigungen siehe [Anmeldung und Rollen](#anmeldung-und-rollen). In den Tabellen
unten stehen die Pfade ohne Präfix; die aktuelle Form ist `/api/v1/...`.

### `/students`

| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | `/students` | Alle Studierenden (id, anon_code, enrollment_semester) |
| GET | `/students/{student_id}/category-progress` | Fortschritt pro **Kategorie** für einen Studenten |
| GET | `/students/{student_id}/class-progress` | Fortschritt pro einzelner **Klasse** (feingranularer) |
| GET | `/students/{student_id}/overview` | Alles Wesentliche in einem Aufruf: Kategorie-Fortschritt, erfüllte/offene Kategorien und Klassen, Zahl der Behandlungen, zugeordnete Patienten. 404 bei unbekannter ID |
| GET | `/students/{student_id}/category-points` | Nur die direkt an Kategorien vergebenen Punkte (`students_categories`), ohne die über Klassen erreichten |

Beide Progress-Endpunkte akzeptieren optional `?semester=2025SoSe`, um auf
ein einzelnes Semester einzuschränken (Format `YYYYSoSe`/`YYYYWiSe`, wie in
der DB). Ohne den Parameter wird über alle Semester aggregiert.

`category-progress` summiert **zwei unabhängige Quellen**: `students_classes.points`
(über die Klassen/Unterkategorien) UND `students_categories.points` (direkt an
der Kategorie vergeben, siehe [/categories](#categories)) und vergleicht die
Summe mit `categories.min_points`. Eine Kategorie mit ausschließlich direkt
vergebenen Punkten - ganz ohne Klassen-Einträge - taucht hier genauso auf wie
eine, die nur über Klassen befüllt ist. Die Herkunft der Summe steht getrennt in `class_points` und
`direct_points` (`total_points` ist ihre Summe). `done` ist `true`, sobald die Summe
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

### `/categories`

| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | `/categories` | Katalog aller Oberkategorien (`id`, `name`, `descr`, `min_points`) |
| GET | `/categories/{category_id}/points` | Alle direkt an dieser Kategorie vergebenen Punkte, über alle Studierenden |
| PUT | `/categories/{category_id}/points` | VERALTET, nur unversioniert; v1: `PUT /students/{id}/categories/{id}/points/{semester}` mit `{"points": 5}` |
| DELETE | `/categories/{category_id}/points?student_id=&semester=` | VERALTET, nur unversioniert; v1: `DELETE /students/{id}/categories/{id}/points/{semester}` |

Damit lässt sich eine Oberkategorie **pauschal bepunkten, ohne eine einzelne
Klasse (Unterkategorie) darunter anzufassen** - z.B. für Bonuspunkte oder eine
Gesamtbeurteilung, die sich nicht sauber einer einzelnen Klasse zuordnen lässt.
Diese Punkte landen in einer eigenen Tabelle (`students_categories`) und
werden von `/students/{id}/category-progress` **zusätzlich** zu den über
Klassen erreichten Punkten gezählt (siehe [/students](#students)). Die
Matching-Logik unter [/analysis](#analysis) bleibt davon unberührt, da sie
ausschließlich auf `classes.min_points`/`min_count` arbeitet.

`PUT`-Body (`CategoryPointsIn`):
```json
{"student_id": 0, "semester": "2026SoSe", "points": 5}
```

Ein zweiter `PUT` für denselben Studenten und dasselbe Semester **ersetzt**
den Wert (Upsert), addiert ihn also nicht. `student_id` unbekannt ergibt 422,
`category_id` unbekannt 404.

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
| GET | `/patients/{patient_id}/cases` | Alle geplanten Leistungen (`patient_cases`) für einen Patienten, inkl. Behandlungsstatus |
| GET | `/patients/{patient_id}/treatments` | Komplette Behandlungshistorie dieses Patienten, chronologisch |
| GET | `/patients/{patient_id}/treatment-progress` | Behandlungsstand: geplante/behandelte/offene Fälle, Fortschritt in %, Punkte-Spannen, letzter Behandlungstermin |
| GET | `/patients/open-cases` | Arbeitsliste: alle noch nicht behandelten geplanten Fälle über alle Patienten, filterbar mit `?class_id=` und `?category_id=` |
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

**Behandlungen tracken:** `GET /patients/{patient_id}/cases` liefert zu jedem
geplanten Fall zusätzlich `treated` (`true`, sobald ein `treatment_cases`-
Eintrag über `patient_case_id` darauf verweist), `treatment_case_id`,
`treated_by_student_id` und `treatment_date`. Gibt es mehrere Behandlungen
zum selben geplanten Fall, zeigt das Feld die zeitlich letzte. Für die volle
Historie eines Patienten (alle Behandlungen, nicht nur die zu geplanten
Fällen) `GET /patients/{patient_id}/treatments` verwenden - kurz für
`GET /treatment-cases?patient_id=...` (siehe [/treatment-cases](#treatment-cases)).
`GET /patients/{patient_id}/cases?treated=false` liefert nur die noch offenen
Fälle, `?treated=true` nur die behandelten.

Ein bereits behandelter geplanter Fall lässt sich nicht löschen
(`DELETE /patients/{id}/cases/{case_id}` antwortet mit **409**): erst die
Behandlung löschen oder ihre Verknüpfung lösen (`PATCH /treatment-cases/{id}`
mit `patient_case_id: null`).

### `/assignments`

Zuordnung Patient zu Studierendem (Tabelle `patient_assignments`). Ein Patient
ist höchstens einem Studierenden zugeordnet, deshalb ist die `patient_id` der
Schlüssel in der Adresse.

| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | `/assignments` | Alle Zuordnungen (`AssignmentOut`, mit `updated_at`) |
| GET | `/assignments/{patient_id}/history` | Frühere Fassungen der Zuordnung |
| PUT | `/assignments/{patient_id}` | Zuordnung anlegen oder ersetzen (`AssignmentIn`), 422 bei unbekannter `patient_id` oder `student_id` |
| DELETE | `/assignments/{patient_id}` | Zuordnung aufheben, 204; 404 wenn keine besteht |

`PUT`-Body (`AssignmentIn`):
```json
{"student_id": 3, "semester": "2026WiSe", "note": "Recall im Januar"}
```

`semester` ist optional und folgt dem Muster `JJJJSoSe`/`JJJJWiSe`.
`AssignmentOut` enthält `patient_id`, `patient` (Pseudonym, sonst Name),
`student_id`, `semester`, `note` und `created_at`. Ein `PUT` auf eine
bestehende Zuordnung ersetzt sie, `created_at` bleibt, `updated_at` wird gesetzt, die alte Fassung steht in der Historie.

### `/treatment-cases`

| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | `/treatment-cases` | Liste, optional gefiltert nach `?student_id=`, `?patient_id=` und/oder `?semester=` |
| GET | `/treatment-cases/{case_id}` | Einzelner Behandlungsfall, 404 falls nicht gefunden |
| POST | `/treatment-cases` | Neuen Behandlungsfall anlegen |
| PATCH | `/treatment-cases/{case_id}` | Behandlungsfall korrigieren (`TreatmentCaseUpdate`), nur gesendete Felder ändern sich |
| DELETE | `/treatment-cases/{case_id}?reason=` | Behandlungsfall per Soft Delete entfernen, 204 |

**Geplanten Fall als behandelt tracken:** `TreatmentCaseIn` akzeptiert optional
`patient_case_id` (verweist auf `patient_cases.id`). Wird es gesetzt, gilt der
referenzierte geplante Fall ab sofort als behandelt (`treated: true` unter
[/patients](#patients)). Fehlt `patient_id` im Request, aber `patient_case_id`
ist gesetzt, übernimmt die API die `patient_id` automatisch vom geplanten Fall.
Sind beide gesetzt und passen nicht zusammen (`patient_id` gehört nicht zu
diesem `patient_case_id`), antwortet die API mit 422; eine unbekannte
`patient_case_id` ebenso.

`POST`-Body (`TreatmentCaseIn`):
```json
{
  "student_id": 0,
  "class_id": 5,
  "patient_id": 2,
  "patient_case_id": null,
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

Anlegen, korrigieren und löschen dürfen Lehrende und Admins; Studierende sehen
nur ihre eigenen Behandlungen.

**Korrigieren und löschen:** `PATCH` ändert nur die gesendeten Felder. Mit
`patient_case_id: null` löst man die Verknüpfung, der geplante Fall gilt dann
wieder als offen; `student_id`, `class_id` und `semester` dürfen nicht `null`
werden (422). Wird nur `patient_case_id` geändert, übernimmt die API den
Patienten vom neuen Fall, passen `patient_id` und `patient_case_id` danach
nicht zusammen, gibt es 422. `DELETE` öffnet den verknüpften geplanten Fall
wieder; hängen Bewertungen (`case_assessments`) oder erworbene Kompetenzen
(`student_competencies`) an der Behandlung, antwortet die API mit 409.

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
| POST | `/analysis/students/{student_id}/trigger` | VERALTET (synchron), stattdessen `POST /analysis/jobs` |
| POST | `/analysis/jobs` | Analyse-Job anlegen, 202 mit `job_id` (siehe [Asynchrone Analyse-Jobs](#asynchrone-analyse-jobs)) |
| GET | `/analysis/jobs/{job_id}` | Status, Fortschritt, Ergebnis eines Analyse-Jobs |
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

`GET /analysis/patient-matching?strategy=hungarian|greedy&max_per_student=N`

**Standard: Hungarian-Algorithmus (`class-match-v2`)**, eigene Implementierung in
`services/hungarian.py` (reines Python, kein scipy). Der Score je (Student, Patient) ist
derselbe wie oben. Ablauf, rundenweise:

1. Matrix aufbauen: Studierende mit offenen Defiziten x noch freie Patienten, Wert = Score.
2. Per Hungarian-Algorithmus die Zuordnung mit der **größten Gesamtsumme** bestimmen. Jeder Student
   bekommt in einer Runde höchstens einen Patienten, jeder Patient höchstens einen Studenten.
   Paare mit Score 0 werden nicht zugeordnet.
3. Defizite um das Zugewiesene verringern (der Score weiterer Patienten sinkt dadurch, Überschuss
   zählt nicht), zugewiesene Patienten entfernen.
4. Wiederholen, bis kein Paar mehr einen positiven Score hat oder `max_per_student` erreicht ist.

Gegenüber dem greedy-Verfahren verbaut sich die Zuordnung nicht mit dem besten Einzelpaar:
bei den Scores `[[10, 9], [9, 0]]` nähme greedy 10 und ließe den zweiten Studenten leer,
Hungarian wählt 9 + 9 = 18. Außerdem verteilt es die Patienten gleichmäßiger, weil ein Student pro Runde
nur einen bekommt. Jede Zuordnung nennt ihre `round`, die Antwort `total_score`.

**Grenze:** Jede Runde ist optimal, die Folge der Runden insgesamt nicht zwingend. Eine frühe Runde kann
Patienten verbrauchen, die später mehr gebracht hätten. Das wäre nur mit einem Modell lösbar, in dem
ein Student mehrere Patienten gleichzeitig bekommt und die Überschneidung der Defizite mitrechnet
(ganzzahlige Optimierung). Bei ~5 Studierenden/~10 Patienten ist der Unterschied klein.

`strategy=greedy` (`class-match-v1`) liefert das frühere Verfahren zum Vergleich: in jedem Schritt das
aktuell beste (Student, Patient)-Paar, ein Student kann mehrere Patienten hintereinander bekommen.
`max_per_student` begrenzt in beiden Verfahren die Patientenzahl je Student.

Antwortformat (`unmatched_patients` und `matched_classes` wie vorher):
```json
{
  "algorithm_version": "class-match-v2",
  "strategy": "hungarian",
  "total_score": 26.0,
  "assignments": [
    {"student_id": 4, "patient_id": 2, "patient_name": "Tim Keller", "score": 26.0,
     "algorithm_version": "class-match-v2", "round": 1,
     "matched_classes": [{"class_id": 7, "class_name": "WK", "category": "Endodontologie",
        "covered_points": 9.0, "covered_count": 1, "available_cases": 1,
        "deficit_points_before": 12.0, "deficit_count_before": 1}]}
  ],
  "unmatched_patients": [{"patient_id": 3, "patient_name": "Elena Rodriguez"}]
}
```

Patienten, die für **keinen** Studenten mehr einen Nutzen bringen (weil
ihre Fälle nur Klassen betreffen, die bei allen Studenten schon erfüllt
sind), landen in `unmatched_patients`.

Antwortformat. `algorithm_version` (aktuell `class-match-v1`) benennt die Bewertungslogik;
sie steht in der Gesamtantwort und je Empfehlung/Zuordnung und ändert sich bei jeder
fachlichen Änderung am Score (z.B. Wechsel auf Kompetenzen). `matched_classes` erklärt
das Ergebnis; `deficit_points_before`/`deficit_count_before` zeigen die Lücke vor diesem Patienten.
```json
{
  "algorithm_version": "class-match-v1",
  "assignments": [
    {
      "student_id": 4,
      "patient_id": 2,
      "patient_name": "Tim Keller",
      "score": 26.0,
      "algorithm_version": "class-match-v1",
      "matched_classes": [
        {"class_id": 7, "class_name": "WK", "category": "Endodontologie",
         "covered_points": 9.0, "covered_count": 1, "available_cases": 1,
         "deficit_points_before": 12.0, "deficit_count_before": 1}
      ]
    }
  ],
  "unmatched_patients": [
    {"patient_id": 3, "patient_name": "Elena Rodriguez"}
  ]
}
```

## Bekannte Lücken / offene Punkte

- **Kein Refresh-Token, keine Token-Sperrliste.** Ein Token gilt bis zum Ablauf (Standard 60 Minuten);
  gesperrte Benutzer fliegen aber sofort raus, weil der Status bei jeder Anfrage geprüft wird.
  Login-Bremse nur pro Prozess. Uni-SSO (Shibboleth/LDAP) ist nicht angebunden.
- **Router greifen teils direkt per SQL auf die DB zu.** Die Repository-Schicht gibt es bisher nur
  für Benutzer und Jobs (`repositories/`); die älteren Router sind nicht umgezogen.
- **Kein Optimistic Locking/ETags.** Zwei gleichzeitige `PATCH` auf denselben Datensatz: der letzte gewinnt
  (beide stehen im Audit-Log).
- **Löschen von Patienten, geplanten Fällen und Zuordnungen ist weiterhin physisch** (mit Audit-Eintrag
  und, bei Zuordnungen, Historie). Nur Behandlungen sind Soft Delete.
- **`call_llm_for_insights` nutzt LLM_CLI, sonst Platzhalter.** Job-Ausführung im selben Prozess, siehe
  [Asynchrone Analyse-Jobs](#asynchrone-analyse-jobs).
- **Matching ist klassen- statt kompetenzbasiert**, weil `competencies` /
  `class_competencies` leer sind (siehe oben).
- **Matching ist rundenweise optimal, nicht insgesamt.** Der Hungarian-Algorithmus löst jede Runde
  optimal; die Folge der Runden ist es nicht zwingend (siehe [4b](#4b-gesamtzuordnung-suggest_global_matching)).
  Die Empfehlungsliste je Student (`patient-recommendations`) ist nicht-exklusiv und nutzt keine Zuordnung.
- **Punkte werden nicht automatisch aus Behandlungen berechnet.** Eine
  erfasste Behandlung (`treatment_cases`) füllt `students_classes` nicht von
  selbst; die aggregierten Punkte kommen weiterhin aus dem Import. Heute gilt:
  `students_classes` = importierte Angaben, `treatment_cases` = Ereignisse,
  `category-progress` = abgeleitet (mit `class_points`/`direct_points` getrennt
  ausgewiesen). Eine einzige maßgebliche Quelle (Behandlung → Bewertung → Punkte →
  Fortschritt) ist fachlich noch zu entscheiden. Ob und wie
  Bewertungen (`case_assessments`) in Klassenpunkte einfließen sollen, ist
  fachlich noch zu klären.
- **`treatment_cases` und `student_osce_results` sind in der Testdatenbank
  leer.** Die zugehörigen Endpunkte sind fertig und funktionieren, liefern
  aber `[]`, bis über die DB oder `POST /treatment-cases` Daten angelegt werden.
- **`generate_test_sql.py`** (im `projekt2`-Hauptordner, nicht Teil der API)
  erzeugt SQL, das nicht zum aktuellen Schema passt (schreibt in eine
  Spalte `classes.min`, die es nicht gibt). Betrifft die API nicht direkt,
  aber die Testdaten-Erzeugung aus der echten Kursleistungs-Excel.

## Tests

```bash
cd projekt2/api
pip install -r requirements-dev.txt
python -m pytest tests -q
```

Jeder Test läuft gegen eine frische Kopie einer Datenbank, die aus
`leistungen.sql` und `test.sql` im Projektordner aufgebaut wird; die echte
`leistungen.db` wird nicht angefasst. Dafür überschreibt die Umgebungsvariable
`PROJEKT2_DB` den Datenbankpfad (ohne sie gilt weiter `api/leistungen.db`).
`tests/test_api.py` deckt die Kernfunktionen ab (Kategorie-Punkte, Behandlungen tracken
und korrigieren, 409/422, `X-API-Key`); `tests/test_v1.py` Anmeldung und Rollen, Fehlerformat,
Pagination, Soft Delete, Audit-Log, Zuordnungs-Historie, Jobs und Matching-Version.

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