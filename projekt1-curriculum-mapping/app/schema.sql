-- Schema der Anwendung. Wird beim ersten Datenbankzugriff ausgeführt und
-- ist wiederholbar.

create table if not exists users (
    id integer primary key autoincrement,
    username text unique not null,
    password_hash text not null,
    role text not null check (role in ('doktorand', 'admin'))
);

-- Ein Durchlauf des Modells oder ein importiertes Excel-Blatt. Die
-- Zuordnungstabelle wird bei jeder Anzeige aus rohantwort berechnet.
create table if not exists auswertungen (
    id integer primary key autoincrement,
    -- zufälliger Schlüssel für URLs
    token text unique not null,
    titel text not null,
    kategorie integer not null default 1,
    modell text not null,
    temperatur real,
    prompt text,
    pruefziele_liste text not null,
    vorlesung_name text,
    vorlesung_text text,
    lernziele_name text,
    lernziele_text text,
    -- ki: Durchlauf in der App, import: aus einer Excel-Datei
    quelle text not null check (quelle in ('ki', 'import')),
    quelle_hinweis text,
    status text not null check (status in ('laeuft', 'fertig', 'fehler')),
    fehler text,
    rohantwort text not null default '',
    -- finish_reason des Modells, z. B. length bei abgeschnittener Antwort
    abbruch text,
    erstellt_von text,
    erstellt_am text not null,
    aktualisiert_am text not null
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
    pruefziele_liste text,
    vorlesung_name text not null,
    -- Lernziel-Datei oder eigene Prüfziel-Datei, NULL bei eingebauter Liste
    ziele_name text,
    ziele_text text,
    quelle text not null check (quelle in ('ki', 'import')),
    quelle_hinweis text,
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
