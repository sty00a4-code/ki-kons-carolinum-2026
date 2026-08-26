--   1. Leistungskatalog (Kompetenzen, Anforderungen, Bewertungskriterien)
--   2. Behandlungsdaten (Behandlungsart, Fallkategorie, Schwierigkeit, Dauer, Setting)
--   3. Studierende      (Anonyme ID, Semester, Behandlungszuweisungen)
--   4. Ergebnisse       (Erreichte Kompetenzen, Leistungsnachweis, OSCE-Prüfungen)
--
-- Übergeordnete Kompetenzbereiche (z.B. Konservierung, Parodontologie)
create table categories (
    'id' int primary key autoincrement,
    'name' varchar(100) unique not null,
    'descr' text,
    'min_points' decimal
);

-- Einzelne Kompetenzen, direkt referenzierbar über einen Kürzel-Code
create table competencies (
    'id' int primary key autoincrement,
    'code' varchar(50) unique not null,
    'name' varchar(200) not null,
    'descr' text,
    'category_id' int references categories ('id')
);

-- Behandlungsklassen / Leistungsarten
create table classes (
    'id' int primary key autoincrement,
    'name' varchar(100) unique not null,
    'descr' text,
    'min_count' int,
    'min_points' decimal,
    'difficulty' int check (difficulty in (1, 2, 3)), -- 1=leicht, 2=mittel, 3=schwer
    'expected_dur_min' int,
    'setting' varchar(50),
    'category_id' int references categories ('id')
);

-- Welche Kompetenzen fördert eine Behandlungsklasse?
create table class_competencies (
    'class_id' int references classes ('id'),
    'competency_id' int references competencies ('id'),
    primary key ('class_id', 'competency_id')
);

-- Bewertungskriterien pro Behandlungsklasse
create table assessment_criteria (
    'id' int primary key autoincrement,
    'class_id' int references classes ('id'),
    'criterion' varchar(200) not null,
    'max_points' decimal,
    'weight' decimal default 1.0
);

-- Anonymisierte Patienten
create table patients (
    'id' int primary key autoincrement,
    'anon_code' varchar(50) unique not null
);

-- Klinische Fallkategorien (Fallkomplexität / Falltyp)
create table case_categories (
    'id' int primary key autoincrement,
    'name' varchar(100) unique not null,
    'descr' text
);

-- Einzelne Behandlungsfälle (Patient + Behandlung + Termin)
create table treatment_cases (
    'id' int primary key autoincrement,
    'student_id' int references students ('id'),
    'class_id' int references classes ('id'),
    'case_category_id' int references case_categories ('id'),
    'patient_id' int references patients ('id'),
    'semester' varchar(8) not null, -- YYYYSoSe / YYYYWiSe
    'difficulty' decimal(1, 2) check (
        difficulty >= 1
        and difficulty <= 3
    ),
    'expected_duration_min' int,
    'actual_duration_min' int,
    'setting' varchar(50),
    'treatment_date' date,
    'notes' text
);

-- Detailbewertungen pro Behandlungsfall und Kriterium
create table case_assessments (
    'id' int primary key autoincrement,
    'treatment_case_id' int references treatment_cases ('id'),
    'criterion_id' int references assessment_criteria ('id'),
    'points_achieved' decimal,
    'graded_by' varchar(100),
    'graded_at' date,
    'notes' text
);

create table students (
    'id' int primary key autoincrement,
    'anon_code' varchar(50) unique,
    'enrollment_semester' varchar(8)
);

-- Aggregierte Leistungen pro Student x Klasse x Semester
create table students_classes (
    'student_id' int references students ('id'),
    'class_id' int references classes ('id'),
    'semester' varchar(8), -- YYYYSoSe / YYYYWiSe
    'count' int default 1,
    'points' decimal default 0,
    primary key (
        student_id,
        class_id,
        semester
    )
);

-- Explizit erworbene Kompetenzen pro Studierendem (mit Nachweis-Typ und -ID)
create table student_competencies (
    'student_id' int references students ('id'),
    'competency_id' int references competencies ('id'),
    'semester_achieved' varchar(8),
    'evidence_type' varchar(50), -- 'treatment_case' | 'osce' | 'manual'
    'treatment_cases_id' int references treatment_cases ('id'),
    'student_osce_results_id' int references student_osce_results ('id'),
    primary key ('student_id', 'competency_id')
);

-- OSCE-Prüfungen (Zeitpunkt, Semester)
create table osce_exams (
    'id' int primary key autoincrement,
    'name' varchar(200) not null,
    'semester' varchar(8), -- YYYYSoSe / YYYYWiSe
    'exam_date' date,
    'description' text
);

-- Einzelne Stationen einer OSCE-Prüfung, mit Bezug zur gemessenen Kompetenz
create table osce_stations (
    'id' int primary key autoincrement,
    'exam_id' int references osce_exams ('id'),
    'name' varchar(200) not null,
    'competency_id' int references competencies ('id'),
    'max_points' decimal,
    'duration_min' int
);

-- Ergebnisse der Studierenden pro OSCE-Station
create table student_osce_results (
    'student_id' int references students ('id'),
    'station_id' int references osce_stations ('id'),
    'points_achieved' decimal,
    'passed' int default 0, -- 0 = nicht bestanden, 1 = bestanden
    primary key (student_id, station_id)
);