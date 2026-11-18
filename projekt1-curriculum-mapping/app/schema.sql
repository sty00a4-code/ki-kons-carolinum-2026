-- Schema der Anwendung. Wird beim ersten Datenbankzugriff ausgeführt und
-- ist wiederholbar.

create table if not exists users (
    id integer primary key autoincrement,
    username text unique not null,
    password_hash text not null,
    role text not null check (role in ('doktorand', 'admin'))
);

-- Vorlesungsabgleich: die Folien einer Vorlesung mit Lernzielen oder
-- Prüfzielen abgleichen, Folie für Folie.
create table if not exists folienabgleiche (
    id integer primary key autoincrement,
    token text unique not null,
    titel text not null,
    ziel text not null check (ziel in ('lernziele', 'pruefziele')),
    modell text not null,
    -- Modell für die Bildbeschreibung, NULL: nur der Text der Folien
    bildmodell text,
    temperatur real,
    prompt text,
    vorlesung_name text not null,
    -- Lernziel- oder Prüfziel-Datei
    ziele_name text not null,
    ziele_text text not null,
    status text not null check (status in ('laeuft', 'fertig', 'fehler')),
    fehler text,
    erstellt_von text,
    erstellt_am text not null,
    aktualisiert_am text not null
);

-- PDF-Datei der Vorlesung, getrennt gespeichert, damit Listen sie nicht laden
create table if not exists vorlesungen (
    abgleich_id integer primary key,
    pdf blob not null,
    foreign key (abgleich_id) references folienabgleiche (id) on delete cascade
);

-- Eine Folie mit Text, Vorschaubild (JPEG) und Antwort des Modells. Solange
-- antwort NULL ist, ist die Folie noch nicht bearbeitet.
create table if not exists folien (
    abgleich_id integer not null,
    nr integer not null,
    folientext text not null default '',
    vorschau blob,
    bildbeschreibung text,
    antwort text,
    primary key (abgleich_id, nr),
    foreign key (abgleich_id) references folienabgleiche (id) on delete cascade
);
