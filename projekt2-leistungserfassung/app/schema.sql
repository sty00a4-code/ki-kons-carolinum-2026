-- Datenmodell der Leistungserfassung (Projekt 2)
-- Datenschutz: Studierende werden über ein zufälliges Pseudonym geführt.
-- KEIN Klarname in der Datenbank. Datensätze tragen zufällige Tokens
-- (public_token) statt hochzählbarer IDs -> kein Zugriff durch "Zahl ändern".

drop table if exists patient_case_items;
drop table if exists patient_cases;
drop table if exists performances;
drop table if exists users;
drop table if exists students;

create table students (
    id integer primary key autoincrement,  -- intern, nie nach außen
    -- z.B. "S-a9Kx" (zufällig) = Login-Name
    pseudonym text unique not null,
    -- NUR für Doktoranden sichtbar
    real_name text,
    cohort text                                 -- z.B. "IK-Kohorte SoSe26"
);

create table users (
    id integer primary key autoincrement,
    username text unique not null,
    password_hash text not null,                     -- werkzeug scrypt/pbkdf2
    role text not null check (role in ('student', 'doktorand', 'admin')),
    -- Anzeigename des Prüfers (z.B. "Dr. …")
    real_name text,
    student_id integer references students (id)    -- nur bei role='student'
);

create table performances (
    id integer primary key autoincrement,
    public_token text unique not null,              -- zufällig, für URLs
    student_id integer not null references students (id),
    semester text not null,                     -- IK I | IK II | IK III | IK IV
    category text not null,                     -- Kategorie aus dem Katalog
    -- Leistungs-Code aus dem Katalog
    item_code text not null,
    item_name text not null,
    count integer not null,                  -- Anzahl
    points real not null,                     -- Punkte (1 Punkt ~ 45 min)
    -- anonymer Fallbezug (keine Klardaten)
    patient_ref text,
    performed_on text,                              -- Datum der Leistung
    -- optional: Schwierigkeitsgrad
    difficulty integer,
    time_minutes integer,                           -- optional: Zeitbedarf
    note text,
    status text not null default 'draft'
    check (status in ('draft', 'submitted', 'approved', 'rejected')),
    created_at text,
    submitted_at text,
    reviewed_by integer references users (id),
    reviewed_at text,
    review_comment text
);

create index idx_perf_student on performances (student_id);
create index idx_perf_status on performances (status);

-- Patientenfälle (anonymisiert!): Doktoranden/Profs tragen Fälle ein, das
-- Matching empfiehlt sie Studierenden mit passenden Lücken (Dashboard D).
-- DATENSCHUTZ: KEINE Patientendaten – nur anonyme Fall-Nr. + Behandlungsbedarf.
create table if not exists patient_cases (
    id integer primary key autoincrement,
    public_token text unique not null,              -- zufällig, für URLs
    -- anonyme Fall-Nr. (z. B. "Fall-051")
    case_ref text unique not null,
    -- Setting/Kurzbeschreibung, KEINE Klardaten
    description text,
    -- 1 leicht / 2 mittel / 3 schwer
    difficulty integer,
    est_minutes integer,                           -- geschätzte Dauer (min)
    status text not null default 'offen'
    check (status in ('offen', 'zugewiesen', 'abgeschlossen')),
    assigned_student_id integer references students (id),
    created_by integer references users (id),
    created_at text
);

-- Behandlungsbedarf eines Falls: welche Katalog-Leistungen bietet der Fall.
create table if not exists patient_case_items (
    id integer primary key autoincrement,
    case_id integer not null references patient_cases (id),
    item_code text not null,                        -- Code aus der Blauen Liste
    item_name text not null,
    category text not null,
    count integer not null default 1,
    points real not null                         -- Katalogpunkte * Anzahl
);

create index if not exists idx_case_items_case on patient_case_items (case_id);
