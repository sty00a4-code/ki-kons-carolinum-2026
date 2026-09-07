# Komponentenübersicht
1. **UI**: html + javascript Website
       - HTTP + JSON für **API** Kommunikation
2. **API**: Analyse, KI-Modul, Aufrufe
       - SQLAlchemy für **DB** Kommunikation
3. **DB**: SQLite/Postgres Datenbank
```
       UI  <- HTTP/JSON ->  API  <- SQLAlchemy ->  DB 
```

Die UI spricht nie direkt mit der DB, sondern immer nur mit der API.

## Schnellstart: API ausführen

Voraussetzung: `leistungen.db` existiert bereits im `projekt2`-Hauptordner (per `build-db.py` + `dummy.py` erzeugt).

```bash
cd projekt2/api

# 1. Virtuelle Umgebung anlegen und aktivieren
python3 -m venv .venv
source .venv/bin/activate                 # Windows: .venv\Scripts\activate

# 2. Abhängigkeiten installieren
pip install -r requirements.txt

# 3. DB-Datei im api/-Ordner erreichbar machen (einmalig, nicht kopieren!)
ln -s ../leistungen.db leistungen.db      # Windows: DB stattdessen manuell reinkopieren

# 4. Server starten
uvicorn app.main:app --reload --port 8000
```

Danach im Browser öffnen:
- **http://localhost:8000/docs** — interaktive Swagger-UI, alle Endpunkte direkt testbar
- **http://localhost:8000/health** — sollte `{"status": "ok"}` zurückgeben

## Typische Stolpersteine

- **`GET /students` gibt 500 / "no such table: students"** → `leistungen.db` im `api/`-Ordner ist leer oder fehlt. Prüfen mit:
  ```bash
  ls -la leistungen.db
  sqlite3 leistungen.db ".tables"   # sollte students, classes, categories, ... auflisten
  ```
  Falls leer/fehlend: Symlink aus Schritt 3 neu setzen (`rm leistungen.db && ln -s ../leistungen.db leistungen.db`), dann Server neu starten.
- **`ModuleNotFoundError`** → venv nicht aktiviert oder `pip install -r requirements.txt` nicht ausgeführt.
- **Port 8000 schon belegt** → anderen Port nehmen: `uvicorn app.main:app --reload --port 8010`.

# Projektstruktur

```
api/
├── requirements.txt
├── leistungen.db          (Symlink auf ../leistungen.db)
└── app/
    ├── main.py             FastAPI-Einstiegspunkt, bindet alle Router ein
    ├── database.py         SQLAlchemy-Engine + Session-Dependency
    ├── schemas.py           Pydantic-Modelle (Request/Response)
    └── routers/
        ├── students.py      /students, Fortschritt pro Kategorie/Klasse
        ├── patients.py      /patients, Patientenfälle
        ├── treatment_cases.py  /treatment-cases (lesen + anlegen)
        ├── osce.py          /osce/results
        └── analysis.py      /analysis, KI-Kernstück (Trigger/Job-Status)
```

## Datenfluss
Lesen: UI → `GET /students/{id}/overview` → Service-Funktion → ORM-Query → JSON
Schreiben: UI → `POST /treatment-cases` → Validierung (Pydantic) → Service schreibt via ORM → DB
KI-Analyse: Trigger → Service liest Rohdaten → ruft LLM-API auf → schreibt Ergebnis in eigene Tabelle (learning_insights) → UI holt Insights über separaten Endpoint ab → Job-Status-Pattern

## Technologievorschlag
API: FastAPI passt zum bestehenden SQLAlchemy-Setup, generiert automatisch OpenAPI-Doku.
DB: SQLite für Pilot, migrationsfähig zu PostgreSQL.
UI: ...Thomas
Auth: JWT oder Uni-SSO, falls Shibboleth/LDAP verfügbar
Deployment: Docker Compose (api, ui, db-volume, nginx als Reverse Proxy mit TLS)

## API-Struktur (nur Signaturen)
```python
# schemas.py
class StudentOverview(BaseModel): ...
class ClassProgress(BaseModel): ...
class TreatmentCaseIn(BaseModel): ...
class TreatmentCaseOut(BaseModel): ...
class LearningInsight(BaseModel): ...
class PatientRecommendation(BaseModel): ...
```
```python
# routers/students.py
def list_students() -> list[StudentOut]: ...
def get_student_overview(student_id: int) -> StudentOverview: ...
def get_student_progress(student_id: int, semester: str | None = None) -> list[ClassProgress]: ...
```
```python
# routers/treatment_cases.py
def list_treatment_cases(student_id: int | None, semester: str | None) -> list[TreatmentCaseOut]: ...
def create_treatment_case(payload: TreatmentCaseIn, user: CurrentUser) -> TreatmentCaseOut: ...
def update_treatment_case(case_id: int, payload: TreatmentCaseIn, user: CurrentUser) -> TreatmentCaseOut: ...
```
```python
# routers/patients.py
def list_patients() -> list[PatientOut]: ...
def get_patient_cases(patient_id: int) -> list[PatientCaseOut]: ...
```
```python
# routers/analysis.py  (Kernstück des KI-Projekts)
def trigger_learning_analysis(student_id: int) -> JobStatus: ...
def get_analysis_status(job_id: str) -> JobStatus: ...
def get_learning_insights(student_id: int) -> list[LearningInsight]: ...
def suggest_patient_assignment(student_id: int) -> list[PatientRecommendation]: ...
```
```python
# routers/auth.py
def login(credentials: LoginIn) -> TokenOut: ...
def get_current_user(token: str = Depends(...)) -> UserOut: ...
```
## Service-Schicht (Business-Logik, getrennt von Routing)
```python
# services/analysis_service.py
def build_learning_trajectory(student_id: int, db: Session) -> LearningTrajectory: ...
def call_llm_for_insights(trajectory: LearningTrajectory) -> LearningInsight: ...
def persist_insight(insight: LearningInsight, db: Session) -> None: ...
```
```python
# services/assignment_service.py
def find_missing_competencies(student_id: int, db: Session) -> list[Competency]: ...
def rank_matching_patients(missing: list[Competency], db: Session) -> list[PatientRecommendation]: ...
```
## Rollen (grob)
Studierende: nur eigene Daten lesen
Lehrende: Daten ihrer Kursteilnehmer lesen, Behandlungsfälle anlegen/bewerten, Analyse triggern
Admin: Nutzerverwaltung, volle Rechte