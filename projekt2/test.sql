begin transaction;

insert into
    categories (id, name, min_points)
values
    (0, 'Parodontologie', 32),
    (1, 'ZHS/Präv./Rest.', 55),
    (2, 'Endodontologie', 20),
    (3, 'Kinderzahnheilkunde', 8),
    (4, 'Prothetik', 51),
    (5, 'Schnittmenge', 33);

insert into
    classes (id, name, min_count, min_points, category_id)
values
    (0, 'AIT', 3, 24, 0),
    (1, 'UPT', 4, 8, 0),
    (2, 'Klasse I und II', 6, 12, 1),
    (3, 'Klasse III und IV', 3, 6, 1),
    (4, 'Klasse V', 2, 2, 1),
    (5, 'Befund', 4, 8, 1),
    (6, 'PZR', 4, 6, 1),
    (7, 'WK', 1, 9, 2),
    (8, 'WF', 1, 6, 2),
    (9, 'Befund Kind', 2, null, 3),
    (10, 'Prophylaxe Kind', null, null, 3),
    (11, 'Non-invasiv/invasiv Kind', null, null, 3),
    (12, 'Krone', null, null, 4),
    (13, 'Brückenglied', null, null, 4),
    (14, 'Totalprothese', null, null, 4),
    (15, 'Teilprothese Doppelkrone', null, null, 4),
    (16, 'Teleskop', null, null, 4),
    (17, 'MEG', null, null, 4),
    (18, 'Interimsprothese', null, null, 4),
    (19, 'Unterfütterung', null, null, 4),
    (20, 'Remontage', null, null, 4),
    (21, 'Proth. Recall', null, null, 4),
    (22, 'Inlay/Teilkrone', null, null, 5),
    (23, 'Kronenrandfensterung', null, null, 5),
    (24, 'Stumpfaufbau(KVB)', null, null, 5),
    (25, 'Stiftaufbau', null, null, 5),
    (26, 'Hosp. in Kindersprechstunde', null, null, 3),
    (27, 'WF-Revision', null, null, 2),
    (28, 'Aufbissbehelf', null, null, 4);

insert into
    students (id)
values
    (0),
    (1),
    (2),
    (3),
    (4);

insert into
    students_classes (student_id, class_id, semester, count, points)
values
    (0, 0, '2024WiSe', 1, 8),
    (0, 1, '2024WiSe', 1, 2),
    (0, 2, '2024WiSe', 2, 4),
    (0, 4, '2024WiSe', 1, 1),
    (0, 5, '2024WiSe', 4, 11),
    (0, 6, '2024WiSe', 3, 4.5),
    (0, 7, '2024WiSe', 2, 6),
    (0, 8, '2024WiSe', 2, 4),
    (0, 14, '2024WiSe', 1, 20),
    (0, 21, '2024WiSe', 1, 5),
    (0, 24, '2024WiSe', 1, 6),
    (0, 26, '2024WiSe', 3, 0),
    (1, 0, '2024WiSe', 1, 8),
    (1, 1, '2024WiSe', 1, 2),
    (1, 2, '2024WiSe', 2, 3),
    (1, 3, '2024WiSe', 2, 4),
    (1, 5, '2024WiSe', 2, 5),
    (1, 6, '2024WiSe', 2, 3),
    (1, 12, '2024WiSe', 1, 30),
    (1, 21, '2024WiSe', 1, 5),
    (1, 24, '2024WiSe', 1, 6),
    (1, 26, '2024WiSe', 4, 0),
    (2, 1, '2024WiSe', 3, 6),
    (2, 2, '2024WiSe', 4, 4),
    (2, 4, '2024WiSe', 1, 1),
    (2, 5, '2024WiSe', 4, 10),
    (2, 6, '2024WiSe', 5, 7.5),
    (2, 12, '2024WiSe', 1, 45),
    (2, 18, '2024WiSe', 1, 10),
    (2, 21, '2024WiSe', 1, 5),
    (2, 26, '2024WiSe', 2, 0),
    (3, 0, '2024WiSe', 1, 8),
    (3, 1, '2024WiSe', 3, 6),
    (3, 2, '2024WiSe', 5, 8),
    (3, 3, '2024WiSe', 1, 2),
    (3, 5, '2024WiSe', 4, 9),
    (3, 6, '2024WiSe', 4, 6),
    (3, 17, '2024WiSe', 1, 15),
    (3, 21, '2024WiSe', 1, 5),
    (3, 26, '2024WiSe', 2, 0),
    (4, 0, '2024WiSe', 1, 8),
    (4, 1, '2024WiSe', 2, 4),
    (4, 2, '2024WiSe', 3, 6),
    (4, 5, '2024WiSe', 5, 13),
    (4, 6, '2024WiSe', 4, 6),
    (4, 14, '2024WiSe', 1, 20),
    (4, 21, '2024WiSe', 1, 5),
    (4, 26, '2024WiSe', 2, 0),
    (0, 0, '2025SoSe', 1, 8),
    (0, 1, '2025SoSe', 1, 2.5),
    (0, 2, '2025SoSe', 2, 4),
    (0, 9, '2025SoSe', 1, 2),
    (0, 10, '2025SoSe', 1, 2),
    (0, 12, '2025SoSe', 1, 61),
    (0, 15, '2025SoSe', 1, 20),
    (0, 24, '2025SoSe', 1, 18),
    (0, 26, '2025SoSe', 2, 0),
    (1, 1, '2025SoSe', 1, 2.5),
    (1, 2, '2025SoSe', 2, 4),
    (1, 7, '2025SoSe', 1, 3),
    (1, 8, '2025SoSe', 1, 2),
    (1, 9, '2025SoSe', 1, 2),
    (1, 10, '2025SoSe', 1, 2),
    (1, 12, '2025SoSe', 1, 72),
    (1, 24, '2025SoSe', 1, 18),
    (1, 25, '2025SoSe', 1, 3),
    (1, 26, '2025SoSe', 2, 0),
    (2, 0, '2025SoSe', 1, 8),
    (2, 1, '2025SoSe', 2, 5),
    (2, 2, '2025SoSe', 2, 2),
    (2, 3, '2025SoSe', 1, 4),
    (2, 4, '2025SoSe', 1, 1),
    (2, 5, '2025SoSe', 4, 9),
    (2, 6, '2025SoSe', 4, 6),
    (2, 7, '2025SoSe', 1, 3),
    (2, 8, '2025SoSe', 1, 2),
    (2, 9, '2025SoSe', 1, 3),
    (2, 10, '2025SoSe', 1, 2),
    (2, 12, '2025SoSe', 1, 45),
    (2, 21, '2025SoSe', 1, 2.5),
    (2, 24, '2025SoSe', 1, 3),
    (2, 26, '2025SoSe', 2, 0),
    (3, 0, '2025SoSe', 1, 8),
    (3, 1, '2025SoSe', 3, 7.5),
    (3, 3, '2025SoSe', 1, 3),
    (3, 5, '2025SoSe', 1, 3),
    (3, 6, '2025SoSe', 1, 1.5),
    (3, 7, '2025SoSe', 1, 3),
    (3, 8, '2025SoSe', 1, 2),
    (3, 9, '2025SoSe', 2, 4.5),
    (3, 10, '2025SoSe', 1, 3.5),
    (3, 12, '2025SoSe', 1, 21),
    (3, 21, '2025SoSe', 1, 5),
    (3, 26, '2025SoSe', 2, 0),
    (4, 0, '2025SoSe', 1, 8),
    (4, 1, '2025SoSe', 2, 5),
    (4, 2, '2025SoSe', 3, 5),
    (4, 5, '2025SoSe', 3, 7),
    (4, 6, '2025SoSe', 2, 3),
    (4, 9, '2025SoSe', 1, 3),
    (4, 10, '2025SoSe', 1, 2),
    (4, 14, '2025SoSe', 1, 40),
    (4, 26, '2025SoSe', 2, 0),
    (0, 1, '2025WiSe', 2, 5),
    (0, 2, '2025WiSe', 6, 15),
    (0, 3, '2025WiSe', 1, 3),
    (0, 4, '2025WiSe', 1, 1),
    (0, 5, '2025WiSe', 1, 2.5),
    (0, 6, '2025WiSe', 1, 1.5),
    (0, 7, '2025WiSe', 5, 15),
    (0, 8, '2025WiSe', 5, 10),
    (0, 27, '2025WiSe', 1, 3),
    (0, 9, '2025WiSe', 1, 2),
    (0, 10, '2025WiSe', 1, 2),
    (0, 11, '2025WiSe', 1, 4),
    (0, 21, '2025WiSe', 1, 2.5),
    (0, 28, '2025WiSe', 1, 7),
    (0, 24, '2025WiSe', 1, 3),
    (0, 25, '2025WiSe', 1, 3),
    (0, 26, '2025WiSe', 2, 0),
    (1, 0, '2025WiSe', 2, 16),
    (1, 2, '2025WiSe', 2, 5),
    (1, 5, '2025WiSe', 1, 2.5),
    (1, 7, '2025WiSe', 4, 12),
    (1, 8, '2025WiSe', 4, 8),
    (1, 9, '2025WiSe', 1, 2),
    (1, 10, '2025WiSe', 1, 2),
    (1, 11, '2025WiSe', 1, 4),
    (1, 14, '2025WiSe', 1, 20),
    (1, 18, '2025WiSe', 1, 10),
    (1, 28, '2025WiSe', 1, 7),
    (1, 24, '2025WiSe', 1, 7),
    (1, 26, '2025WiSe', 2, 0),
    (2, 0, '2025WiSe', 1, 8),
    (2, 1, '2025WiSe', 1, 2.5),
    (2, 2, '2025WiSe', 4, 4),
    (2, 3, '2025WiSe', 1, 2),
    (2, 4, '2025WiSe', 6, 6),
    (2, 5, '2025WiSe', 5, 12.5),
    (2, 6, '2025WiSe', 5, 7.5),
    (2, 7, '2025WiSe', 4, 12),
    (2, 8, '2025WiSe', 4, 8),
    (2, 9, '2025WiSe', 2, 5),
    (2, 10, '2025WiSe', 1, 4),
    (2, 11, '2025WiSe', 1, 2),
    (2, 14, '2025WiSe', 1, 40),
    (2, 21, '2025WiSe', 1, 5),
    (2, 26, '2025WiSe', 2, 0),
    (3, 0, '2025WiSe', 1, 8),
    (3, 1, '2025WiSe', 2, 5),
    (3, 2, '2025WiSe', 1, 1),
    (3, 3, '2025WiSe', 1, 3),
    (3, 4, '2025WiSe', 2, 2),
    (3, 5, '2025WiSe', 2, 5),
    (3, 6, '2025WiSe', 2, 3),
    (3, 7, '2025WiSe', 4, 12),
    (3, 8, '2025WiSe', 4, 8),
    (3, 9, '2025WiSe', 2, 4),
    (3, 10, '2025WiSe', 1, 4),
    (3, 11, '2025WiSe', 1, 1),
    (3, 17, '2025WiSe', 1, 15),
    (3, 24, '2025WiSe', 1, 3),
    (3, 26, '2025WiSe', 2, 0),
    (4, 0, '2025WiSe', 1, 8),
    (4, 1, '2025WiSe', 2, 5),
    (4, 5, '2025WiSe', 1, 2.5),
    (4, 6, '2025WiSe', 1, 1.5),
    (4, 9, '2025WiSe', 1, 2),
    (4, 10, '2025WiSe', 1, 2),
    (4, 11, '2025WiSe', 1, 2),
    (4, 15, '2025WiSe', 1, 20),
    (4, 21, '2025WiSe', 1, 2.5),
    (4, 28, '2025WiSe', 1, 7),
    (4, 26, '2025WiSe', 2, 0),
    (0, 1, '2026SoSe', 3, 7.5),
    (0, 2, '2026SoSe', 3, 8),
    (0, 3, '2026SoSe', 3, 7),
    (0, 9, '2026SoSe', 1, 2),
    (0, 10, '2026SoSe', 1, 2),
    (0, 21, '2026SoSe', 1, 7.5),
    (0, 28, '2026SoSe', 1, 7),
    (0, 24, '2026SoSe', 1, 3),
    (0, 26, '2026SoSe', 2, 0),
    (1, 1, '2026SoSe', 3, 7.5),
    (1, 2, '2026SoSe', 2, 3),
    (1, 3, '2026SoSe', 1, 3),
    (1, 4, '2026SoSe', 3, 4),
    (1, 5, '2026SoSe', 2, 5),
    (1, 6, '2026SoSe', 2, 3),
    (1, 9, '2026SoSe', 1, 2),
    (1, 10, '2026SoSe', 1, 2),
    (1, 14, '2026SoSe', 1, 40),
    (1, 28, '2026SoSe', 1, 7),
    (1, 26, '2026SoSe', 2, 0),
    (2, 1, '2026SoSe', 1, 2.5),
    (2, 2, '2026SoSe', 1, 2),
    (2, 3, '2026SoSe', 2, 5),
    (2, 4, '2026SoSe', 1, 1),
    (2, 5, '2026SoSe', 1, 2.5),
    (2, 6, '2026SoSe', 1, 1.5),
    (2, 7, '2026SoSe', 1, 3),
    (2, 8, '2026SoSe', 1, 2),
    (2, 27, '2026SoSe', 1, 3),
    (2, 9, '2026SoSe', 1, 2),
    (2, 10, '2026SoSe', 1, 2),
    (2, 11, '2026SoSe', 1, 2),
    (2, 28, '2026SoSe', 1, 14),
    (2, 26, '2026SoSe', 2, 0),
    (3, 1, '2026SoSe', 1, 2.5),
    (3, 2, '2026SoSe', 1, 3),
    (3, 5, '2026SoSe', 2, 5),
    (3, 6, '2026SoSe', 2, 3),
    (3, 11, '2026SoSe', 1, 1),
    (3, 12, '2026SoSe', 1, 30),
    (3, 21, '2026SoSe', 1, 12.5),
    (3, 28, '2026SoSe', 1, 14),
    (3, 26, '2026SoSe', 2, 0),
    (4, 1, '2026SoSe', 1, 2.5),
    (4, 2, '2026SoSe', 1, 1),
    (4, 3, '2026SoSe', 3, 8),
    (4, 4, '2026SoSe', 2, 2),
    (4, 5, '2026SoSe', 2, 5),
    (4, 6, '2026SoSe', 2, 3),
    (4, 7, '2026SoSe', 4, 12),
    (4, 8, '2026SoSe', 4, 8),
    (4, 9, '2026SoSe', 1, 2),
    (4, 10, '2026SoSe', 1, 2),
    (4, 11, '2026SoSe', 1, 1),
    (4, 21, '2026SoSe', 1, 5),
    (4, 28, '2026SoSe', 1, 7),
    (4, 26, '2026SoSe', 2, 0);

insert into
    patients (id, name)
values (0, 'Marcus Weber'),
    (1, 'Sophie Berger'),
    (2, 'Tim Keller'),
    (3, 'Elena Rodriguez'),
    (4, 'Wilhelm Schmitz'),
    (5, 'Jasmin Ahmad'),
    (6, 'Klaus Hoffmann'),
    (7, 'Anna Petrov'),
    (8, 'David Zimmermann'),
    (9, 'Mira Patel');

insert into
    patient_cases (
        patient_id,
        class_id,
        region,
        min_points,
        max_points
    )
values (0, 5, 'gesamtes Gebiss', 2, 3),
    (
        0,
        0,
        'generalisiert OK/UK',
        8,
        8
    ),
    (
        0,
        2,
        'Zahn 16, okklusal (Kl. I)',
        1,
        4
    ),
    (
        0,
        2,
        'Zahn 26, okklusal (Kl. I)',
        1,
        4
    ),
    (
        0,
        2,
        'Zahn 36, mesio-okklusal (Kl. II)',
        1,
        4
    ),
    (
        0,
        2,
        'Zahn 46, disto-okklusal (Kl. II)',
        1,
        4
    ),
    (
        0,
        6,
        'gesamtes Gebiss',
        1.5,
        1.5
    ),
    (
        0,
        1,
        'generalisiert OK/UK, 1. Recall',
        2,
        3
    ),
    (1, 5, 'gesamtes Gebiss', 2, 3),
    (
        1,
        2,
        'Zahn 14, mesial (Kl. II)',
        1,
        4
    ),
    (
        1,
        6,
        'gesamtes Gebiss',
        1.5,
        1.5
    ),
    (2, 5, 'gesamtes Gebiss', 2, 3),
    (
        2,
        0,
        'lokalisiert UK-Molaren (36-46)',
        8,
        8
    ),
    (2, 7, 'Zahn 46', 9, 9),
    (2, 8, 'Zahn 46', 6, 6),
    (2, 24, 'Zahn 46', 3, 3),
    (
        2,
        2,
        'Zahn 15, okklusal (Kl. I)',
        1,
        4
    ),
    (
        2,
        2,
        'Zahn 25, mesio-okklusal (Kl. II)',
        1,
        4
    ),
    (
        2,
        3,
        'Zahn 11, mesial (Kl. III)',
        2,
        4
    ),
    (
        2,
        6,
        'gesamtes Gebiss',
        1.5,
        1.5
    ),
    (
        3,
        9,
        'Wechselgebiss, gesamt',
        1,
        3
    ),
    (
        3,
        10,
        'Wechselgebiss, gesamt',
        2,
        2
    ),
    (
        3,
        11,
        'Zahn 75 (Milchmolar), okklusal',
        2,
        2
    ),
    (
        3,
        11,
        'Zahn 85 (Milchmolar), okklusal',
        2,
        2
    ),
    -- ÜBERSPRUNGEN Wilhelm Schmitz (Prothesenlager UK, gesamte MSH):
    -- Chirurgie/Implantologie: "Systematische Untersuchung der Mundschleimhaut (MSH)"
    -- -- keine Kategorie/Klasse im Schema vorhanden
    (
        4,
        5,
        'Restgebiss 33-43',
        2,
        3
    ),
    (
        4,
        0,
        'Restzähne 33, 32, 31, 41, 42, 43',
        8,
        8
    ),
    (4, 19, 'UK-Altprothese', 5, 5),
    -- ÜBERSPRUNGEN Wilhelm Schmitz (UK, Klammern an 34 und 44, Freiend beidseits):
    -- Prothetik herausnehmbar: "Klammermodellgussprothese (mind. eine Stützzone)"
    -- -- keine passende Klasse im Schema vorhanden
    (
        4,
        20,
        'UK-Klammermodellgussprothese',
        5,
        5
    ),
    (
        4,
        21,
        'UK-Klammermodellgussprothese',
        2,
        3
    ),
    (5, 5, 'gesamtes Gebiss', 2, 3),
    (
        5,
        3,
        'Zahn 12, mesial (Kl. III)',
        2,
        4
    ),
    (
        5,
        3,
        'Zahn 22, distal (Kl. III)',
        2,
        4
    ),
    (
        5,
        4,
        'Zahn 13, vestibulär zervikal',
        1,
        1
    ),
    (
        5,
        4,
        'Zahn 23, vestibulär zervikal',
        1,
        1
    ),
    (
        5,
        2,
        'Zahn 24, okklusal (Kl. I)',
        1,
        4
    ),
    (
        5,
        6,
        'gesamtes Gebiss',
        1.5,
        1.5
    ),
    (6, 5, 'gesamtes Gebiss', 2, 3),
    -- ÜBERSPRUNGEN Klaus Hoffmann (OK, Michigan-Schiene):
    -- Funktionstherapie: "Aufbissbehelf (inkl. FAL und Zentrikregistrat)"
    -- -- keine Kategorie/Klasse im Schema vorhanden
    (
        6,
        22,
        'Zahn 16, Teilkrone',
        12,
        15
    ), -- Punkteangabe im Excel '12 (15)' als Spanne 12-15 interpretiert, bitte prüfen
    (
        6,
        23,
        'Zahn 26, bestehende Krone',
        3,
        3
    ),
    (
        6,
        1,
        'generalisiert OK/UK',
        2,
        3
    ),
    (
        6,
        6,
        'gesamtes Gebiss',
        1.5,
        1.5
    ),
    -- ÜBERSPRUNGEN Anna Petrov (gesamte MSH, periimplantär 46):
    -- Chirurgie/Implantologie: "Systematische Untersuchung der Mundschleimhaut (MSH)"
    -- ÜBERSPRUNGEN Anna Petrov (Implantat regio 46):
    -- Chirurgie/Implantologie: "Implantatnachsorge"
    -- ÜBERSPRUNGEN Anna Petrov (regio 36, Implantatplanung):
    -- Chirurgie/Implantologie: "Planung oralchir. Eingriffe / Indikationsstellung DVT"
    -- ÜBERSPRUNGEN Anna Petrov (regio 36):
    -- Chirurgie/Implantologie: "Implantat-prothetische Beratung"
    -- -- keine Kategorie/Klasse im Schema vorhanden
    (
        7,
        12,
        'Implantat regio 36, Implantatkrone',
        12,
        15
    ), -- Punkteangabe im Excel '12 (15)' als Spanne 12-15 interpretiert, bitte prüfen
    (
        7,
        0,
        'lokalisiert OK (17-27)',
        8,
        8
    ),
    (7, 27, 'Zahn 27', 9, 9),
    (7, 7, 'Zahn 27', 9, 9),
    (7, 8, 'Zahn 27', 6, 6),
    (
        7,
        6,
        'gesamtes Gebiss',
        1.5,
        1.5
    ),
    (8, 5, 'gesamtes Gebiss', 2, 3),
    (
        8,
        0,
        'generalisiert OK/UK',
        8,
        8
    ),
    -- ÜBERSPRUNGEN David Zimmermann (UK, Freiend 36 und 46, Klammern an 35 und 45):
    -- Prothetik herausnehmbar: "Klammermodellgussprothese (mind. eine Stützzone)"
    -- -- keine passende Klasse im Schema vorhanden
    (
        8,
        21,
        'UK-Klammermodellgussprothese',
        2,
        3
    ),
    (
        8,
        1,
        'generalisiert OK/UK',
        2,
        3
    ),
    -- ÜBERSPRUNGEN Mira Patel: 13 Kieferorthopädie-Leistungen (Erstaufnahmegespräch,
    -- KFO-Anamnese, Abformung/Scan, Modellherstellung, 3D-Modellanalyse, Foto/Gesichtsscan,
    -- Rö-Befund OPG+FRS, KFO-Behandlungsplan, Konstruktionszeichnung/ClinCheck,
    -- 6x Kontrollsitzung) -- Kategorie "Kieferorthopädie" existiert nicht im Schema
    (
        9,
        6,
        'gesamtes Gebiss, Multibandapparatur',
        1.5,
        1.5
    );

commit;
