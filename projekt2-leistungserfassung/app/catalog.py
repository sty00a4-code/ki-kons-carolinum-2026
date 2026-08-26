"""Leistungskatalog Projekt 2 ("Blaue Liste").

Quelle: Punkteübersicht IKI_ILs.pdf. Grundregel: 1 Punkt ~ 45 min.
Studierende dürfen NUR Leistungen aus diesem Katalog erfassen (kontrolliertes
Vokabular). Die Punkte-Grenzen (points_min/points_max) sind zugleich die
Validierungsregel für die Prüfung durch Doktoranden.

Diese Datei ist die zentrale Stelle zum Anpassen des Katalogs.
"""

SEMESTERS = ["IK I", "IK II", "IK III", "IK IV"]

# Jede Kategorie -> Liste von Leistungen.
# points_min/points_max: erlaubter Punktbereich pro Durchführung.
# soll_anzahl: Richtwert (Soll) laut Katalog; unit: Zähl-Einheit.
CATALOG = [
    (
        "Parodontologie",
        [
            {
                "code": "pa_ait",
                "name": "Antiinfektiöse Parodontitistherapie (MHT, FMS, Reevaluation)",
                "points_min": 8,
                "points_max": 8,
                "soll_anzahl": 3,
                "unit": "Patient",
            },
            {
                "code": "pa_upt",
                "name": "Unterstützende Parodontitistherapie (UPT, Recall)",
                "points_min": 2,
                "points_max": 3,
                "soll_anzahl": 4,
                "unit": "Sitzung",
            },
        ],
    ),
    (
        "Zahnhartsubstanz/Prävention/Restauration",
        [
            {
                "code": "zhs_fuell_1_2",
                "name": "Plastische Füllungen Klasse I und II",
                "points_min": 1,
                "points_max": 4,
                "soll_anzahl": 6,
                "unit": "Füllung",
            },
            {
                "code": "zhs_fuell_3_4",
                "name": "Plastische definitive Füllungen Klasse III/IV",
                "points_min": 2,
                "points_max": 4,
                "soll_anzahl": 3,
                "unit": "Füllung",
            },
            {
                "code": "zhs_fuell_5",
                "name": "Plastische definitive Füllungen Klasse V",
                "points_min": 1,
                "points_max": 1,
                "soll_anzahl": 2,
                "unit": "Füllung",
            },
            {
                "code": "zhs_befund",
                "name": "Kariologischer Befund, Kariesrisiko, Therapieplanung",
                "points_min": 2,
                "points_max": 3,
                "soll_anzahl": 4,
                "unit": "Befund",
            },
            {
                "code": "zhs_prophylaxe",
                "name": "Prophylaxesitzung MuHy + PZR",
                "points_min": 1.5,
                "points_max": 1.5,
                "soll_anzahl": 4,
                "unit": "Sitzung",
            },
        ],
    ),
    (
        "Endodontologie",
        [
            {
                "code": "endo_aufbereitung",
                "name": "Wurzelkanalaufbereitung inkl. Arbeitslänge + Masterpoint (je Kanal)",
                "points_min": 3,
                "points_max": 3,
                "soll_anzahl": 3,
                "unit": "Kanal",
            },
            {
                "code": "endo_fuellung",
                "name": "Wurzelkanalfüllung inkl. Röntgenkontrolle + adhäsive Deckfüllung (je Kanal)",
                "points_min": 2,
                "points_max": 2,
                "soll_anzahl": 3,
                "unit": "Kanal",
            },
            {
                "code": "endo_revision",
                "name": "Entfernung Wurzelkanalfüllmaterial (Revision)",
                "points_min": 3,
                "points_max": 3,
                "soll_anzahl": 1,
                "unit": "Kanal",
            },
        ],
    ),
    (
        "Kinderzahnheilkunde",
        [
            {
                "code": "kzh_befund",
                "name": "Befund inkl. Planung (Milch-/Wechselgebiss)",
                "points_min": 1,
                "points_max": 3,
                "soll_anzahl": 2,
                "unit": "Befund",
            },
            {
                "code": "kzh_prophylaxe",
                "name": "Individuelle, ausführliche Prophylaxesitzung (Milch-/Wechselgebiss)",
                "points_min": 2,
                "points_max": 2,
                "soll_anzahl": 1,
                "unit": "Sitzung",
            },
            {
                "code": "kzh_behandlung",
                "name": "non-invasive / invasive Behandlung",
                "points_min": 2,
                "points_max": 2,
                "soll_anzahl": 1,
                "unit": "Behandlung",
            },
        ],
    ),
    (
        "Prothetik",
        [
            {
                "code": "proth_krone",
                "name": "Krone auf Zahn/Implantat (inkl. Stumpfaufbau)",
                "points_min": 12,
                "points_max": 15,
                "soll_anzahl": 1,
                "unit": "Krone",
            },
            {
                "code": "proth_bruecke",
                "name": "Brückenglied",
                "points_min": 10,
                "points_max": 10,
                "soll_anzahl": 1,
                "unit": "Glied",
            },
            {
                "code": "proth_totalprothese",
                "name": "Totalprothese je Kiefer",
                "points_min": 20,
                "points_max": 20,
                "soll_anzahl": 1,
                "unit": "Kiefer",
            },
            {
                "code": "proth_teilprothese",
                "name": "Teilprothese Doppelkrone",
                "points_min": 20,
                "points_max": 20,
                "soll_anzahl": 1,
                "unit": "Prothese",
            },
            {
                "code": "proth_teleskop",
                "name": "pro Teleskop",
                "points_min": 10,
                "points_max": 10,
                "soll_anzahl": 1,
                "unit": "Teleskop",
            },
            {
                "code": "proth_modellguss",
                "name": "Klammermodellgussprothese (Ersatz ≥1 Stützzone)",
                "points_min": 15,
                "points_max": 15,
                "soll_anzahl": 1,
                "unit": "Prothese",
            },
            {
                "code": "proth_interims",
                "name": "Interimsprothese (Ersatz ≥1 Stützzone)",
                "points_min": 10,
                "points_max": 10,
                "soll_anzahl": 1,
                "unit": "Prothese",
            },
            {
                "code": "proth_unterfuett",
                "name": "Unterfütterung",
                "points_min": 5,
                "points_max": 5,
                "soll_anzahl": 1,
                "unit": "Vorgang",
            },
            {
                "code": "proth_remontage",
                "name": "Remontage",
                "points_min": 5,
                "points_max": 5,
                "soll_anzahl": 1,
                "unit": "Vorgang",
            },
            {
                "code": "proth_recall",
                "name": "Recall",
                "points_min": 2,
                "points_max": 3,
                "soll_anzahl": 1,
                "unit": "Sitzung",
            },
            {
                "code": "proth_aufbiss",
                "name": "Aufbissbehelf (inkl. FAL und Zentrikregistrat)",
                "points_min": 7,
                "points_max": 7,
                "soll_anzahl": 1,
                "unit": "Behelf",
            },
        ],
    ),
    (
        "Schnittmenge Restauration/Prothetik",
        [
            {
                "code": "schnitt_inlay",
                "name": "Inlay oder Teilkrone (inkl. Stumpfaufbau)",
                "points_min": 12,
                "points_max": 15,
                "soll_anzahl": 1,
                "unit": "Stück",
            },
            {
                "code": "schnitt_reparatur",
                "name": "Kariesbedingte Reparatur Kronenrand",
                "points_min": 3,
                "points_max": 3,
                "soll_anzahl": 1,
                "unit": "Reparatur",
            },
            {
                "code": "schnitt_stumpfaufbau",
                "name": "adhäsiver Stumpfaufbau",
                "points_min": 3,
                "points_max": 3,
                "soll_anzahl": 1,
                "unit": "Aufbau",
            },
            {
                "code": "schnitt_stiftaufbau",
                "name": "Stiftaufbau",
                "points_min": 3,
                "points_max": 3,
                "soll_anzahl": 1,
                "unit": "Aufbau",
            },
        ],
    ),
    (
        "Chirurgie/Implantologie",
        [
            {
                "code": "chir_msh",
                "name": "Systematische Untersuchung der Mundschleimhaut (MSH)",
                "points_min": 1,
                "points_max": 1,
                "soll_anzahl": 4,
                "unit": "Untersuchung",
            },
            {
                "code": "chir_dvt",
                "name": "Planung oralchir. Eingriffe / Indikationsstellung DVT",
                "points_min": 1,
                "points_max": 1,
                "soll_anzahl": 4,
                "unit": "Planung",
            },
            {
                "code": "chir_impl_beratung",
                "name": "Implantat-prothetische Beratung",
                "points_min": 1,
                "points_max": 1,
                "soll_anzahl": 4,
                "unit": "Beratung",
            },
            {
                "code": "chir_impl_nachsorge",
                "name": "Implantatnachsorge",
                "points_min": 1,
                "points_max": 1,
                "soll_anzahl": 4,
                "unit": "Sitzung",
            },
        ],
    ),
    (
        "Kieferorthopädie (KFO)",
        [
            {
                "code": "kfo_erstgespraech",
                "name": "Erstaufnahmegespräch / KIG-Klassifizierung",
                "points_min": 1,
                "points_max": 1,
                "soll_anzahl": 1,
                "unit": "Gespräch",
            },
            {
                "code": "kfo_anamnese",
                "name": "KFO-Anamnese, Aufklärung, Epikrise",
                "points_min": 1,
                "points_max": 1,
                "soll_anzahl": 1,
                "unit": "Vorgang",
            },
            {
                "code": "kfo_abformung",
                "name": "Abformung OK/UK, Scan, Registrat, Zielbiss",
                "points_min": 1,
                "points_max": 1,
                "soll_anzahl": 1,
                "unit": "Vorgang",
            },
            {
                "code": "kfo_modell",
                "name": "Modellherstellung (analog und digital)",
                "points_min": 1,
                "points_max": 1,
                "soll_anzahl": 1,
                "unit": "Modell",
            },
            {
                "code": "kfo_3d",
                "name": "3D-Modellanalyse",
                "points_min": 1,
                "points_max": 1,
                "soll_anzahl": 1,
                "unit": "Analyse",
            },
            {
                "code": "kfo_foto",
                "name": "Foto/Gesichtsscan mit Auswertung",
                "points_min": 1,
                "points_max": 1,
                "soll_anzahl": 1,
                "unit": "Auswertung",
            },
            {
                "code": "kfo_roentgen",
                "name": "Rö, Befund OPG und FRS",
                "points_min": 1,
                "points_max": 1,
                "soll_anzahl": 1,
                "unit": "Befund",
            },
            {
                "code": "kfo_plan",
                "name": "KFO-Behandlungsplan",
                "points_min": 1,
                "points_max": 1,
                "soll_anzahl": 1,
                "unit": "Plan",
            },
            {
                "code": "kfo_konstruktion",
                "name": "Konstruktionszeichnung Gerät / ClinCheck",
                "points_min": 1,
                "points_max": 1,
                "soll_anzahl": 1,
                "unit": "Zeichnung",
            },
            {
                "code": "kfo_kontrolle",
                "name": "Kontrollsitzung",
                "points_min": 0.5,
                "points_max": 0.5,
                "soll_anzahl": 6,
                "unit": "Sitzung",
            },
        ],
    ),
]

# Flache Nachschlage-Struktur code -> item (inkl. category)
ALL_ITEMS = {}
for _category, _items in CATALOG:
    for _it in _items:
        _it = dict(_it, category=_category)
        ALL_ITEMS[_it["code"]] = _it


def find_item(code: str):
    return ALL_ITEMS.get(code)


def validate(item, count, points):
    """Serverseitige Validierung. Gibt Fehlermeldung (str) oder None zurück."""
    if item is None:
        return "Leistung ist nicht im Katalog."
    if count is None or count < 1:
        return "Anzahl muss mindestens 1 sein."
    pmin, pmax = item["points_min"], item["points_max"]
    if points is None or not (pmin <= points <= pmax):
        if pmin == pmax:
            return f"Punkte müssen genau {pmin} sein (Leistung: {item['name']})."
        return f"Punkte müssen zwischen {pmin} und {pmax} liegen (Leistung: {item['name']})."
    return None


# Mindestanforderung (Ziel-Punkte) je Kategorie – Quelle: Punkteübersicht.
CATEGORY_TARGET = {
    "Parodontologie": 32,
    "Zahnhartsubstanz/Prävention/Restauration": 55,
    "Endodontologie": 20,
    "Kinderzahnheilkunde": 8,
    "Prothetik": 116,  # festsitzend 51 + herausnehmbar 51 + Funktionstherapie 14
    "Schnittmenge Restauration/Prothetik": 33,
    "Chirurgie/Implantologie": 16,
    "Kieferorthopädie (KFO)": 48,
}

TOTAL_TARGET = sum(CATEGORY_TARGET.values())  # 328
