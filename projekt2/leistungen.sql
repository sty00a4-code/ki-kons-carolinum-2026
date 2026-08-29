-- Übergeordnete Kompetenzbereiche (z.B. Konservierung, Parodontologie)
create table if not exists categories (
    id integer primary key autoincrement,
    name varchar(100) unique not null,
    descr text,
    min_points decimal
);

-- Einzelne Kompetenzen, direkt referenzierbar über einen Kürzel-Code
create table if not exists competencies (
    id integer primary key autoincrement,
    code varchar(50) unique not null,
    name varchar(200) not null,
    descr text,
    category_id int references categories (id)
);

-- Behandlungsklassen / Leistungsarten
create table if not exists classes (
    id integer primary key autoincrement,
    name varchar(100) unique not null,
    descr text,
    min_count int,
    min_points decimal,
    difficulty int check (difficulty in (1, 2, 3)), -- 1=leicht, 2=mittel, 3=schwer
    expected_dur_min int,
    setting varchar(50),
    category_id int references categories (id)
);

-- Welche Kompetenzen fördert eine Behandlungsklasse?
create table if not exists class_competencies (
    class_id int references classes (id),
    competency_id int references competencies (id),
    primary key (class_id, competency_id)
);

-- Bewertungskriterien pro Behandlungsklasse
create table if not exists assessment_criteria (
    id integer primary key autoincrement,
    class_id int references classes (id),
    criterion varchar(200) not null,
    max_points decimal,
    weight decimal default 1.0
);

-- Anonymisierte Patienten
create table if not exists patients (
    id integer primary key autoincrement,
    name varchar(100)
);

-- Patienten Fälle
create table if not exists patient_cases (
    id integer primary key autoincrement,
    patient_id int references patients (id),
    class_id int references classes (id),
    region text,
    min_points decimal,
    max_points decimal
);

-- Klinische Fallkategorien (Fallkomplexität / Falltyp)
create table if not exists case_categories (
    id integer primary key autoincrement,
    name varchar(100) unique not null,
    descr text
);

-- Studierende (muss vor treatment_cases stehen, da dort referenziert)
create table if not exists students (
    id integer primary key autoincrement,
    anon_code varchar(50) unique,
    enrollment_semester varchar(8)
);

-- Einzelne Behandlungsfälle (Patient + Behandlung + Termin)
create table if not exists treatment_cases (
    id integer primary key autoincrement,
    student_id int references students (id),
    class_id int references classes (id),
    case_category_id int references case_categories (id),
    patient_id int references patients (id),
    semester varchar(8) not null, -- YYYYSoSe / YYYYWiSe
    difficulty decimal(1, 2) check (
        difficulty >= 1
        and difficulty <= 3
    ),
    expected_duration_min int,
    actual_duration_min int,
    setting varchar(50),
    treatment_date date,
    notes text
);

-- Detailbewertungen pro Behandlungsfall und Kriterium
create table if not exists case_assessments (
    id integer primary key autoincrement,
    treatment_case_id int references treatment_cases (id),
    criterion_id int references assessment_criteria (id),
    points_achieved decimal,
    graded_by varchar(100),
    graded_at date,
    notes text
);

-- Aggregierte Leistungen pro Student x Klasse x Semester
create table if not exists students_classes (
    student_id int references students (id),
    class_id int references classes (id),
    semester varchar(8), -- YYYYSoSe / YYYYWiSe
    count int default 1,
    points decimal default 0,
    primary key (
        student_id,
        class_id,
        semester
    )
);

-- OSCE-Prüfungen (Zeitpunkt, Semester)
create table if not exists osce_exams (
    id integer primary key autoincrement,
    name varchar(200) not null,
    semester varchar(8), -- YYYYSoSe / YYYYWiSe
    exam_date date,
    description text
);

-- Einzelne Stationen einer OSCE-Prüfung, mit Bezug zur gemessenen Kompetenz
create table if not exists osce_stations (
    id integer primary key autoincrement,
    exam_id int references osce_exams (id),
    name varchar(200) not null,
    competency_id int references competencies (id),
    max_points decimal,
    duration_min int
);

-- Ergebnisse der Studierenden pro OSCE-Station
-- Hinweis: 'id' als Surrogatschlüssel ergänzt, da student_competencies
-- weiter unten per FK auf eine einzelne Zeile dieser Tabelle verweist
-- (der bisherige zusammengesetzte Primärschlüssel student_id+station_id
-- kann von einer FK-Spalte nicht referenziert werden).
create table if not exists student_osce_results (
    id integer primary key autoincrement,
    student_id int references students (id),
    station_id int references osce_stations (id),
    points_achieved decimal,
    passed int default 0, -- 0 = nicht bestanden, 1 = bestanden
    unique (student_id, station_id)
);

-- Explizit erworbene Kompetenzen pro Studierendem (mit Nachweis-Typ und -ID)
create table if not exists student_competencies (
    student_id int references students (id),
    competency_id int references competencies (id),
    semester_achieved varchar(8),
    evidence_type varchar(50), -- 'treatment_case' | 'osce' | 'manual'
    treatment_cases_id int references treatment_cases (id),
    student_osce_results_id int references student_osce_results (id),
    primary key (student_id, competency_id)
);