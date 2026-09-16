"""Erzeugt test.sql aus der Auswertungs-Excel der fünf Studierenden.

Gelesen werden die Blätter IK I bis IK IV. In Zeile 4 steht der Name der
Leistung, in Zeile 5 darunter entweder "Anzahl" und "Punkte" (zwei Spalten)
oder nur "Punkte" (eine Spalte); Hospitationen haben nur eine Anzahl. Der Name steht immer in der ersten Spalte
der Leistung. Gesamt-Spalten werden nicht übernommen, sie dienen nur zur
Kontrolle: Am Ende wird jede Semestersumme gegen die Excel geprüft.

Der Abschnitt mit Patienten und Fällen am Ende der vorhandenen test.sql wird
unverändert übernommen.

Aufruf im Ordner projekt2:  python generate_test_sql.py
Danach:                     python build-db.py && python dummy.py
"""

import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
XLSX_PATH = (
    ROOT.parent
    / "data"
    / "statistik"
    / "Auswertung KursleistungenIK I bis IKIV fünf Stud.xlsx"
)
TEST_SQL_PATH = ROOT / "test.sql"

NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NAME_ROW = 4
KIND_ROW = 5
STUDENT_ROWS = range(6, 11)

CATEGORY_ROWS = [
    (0, "Parodontologie", 32),
    (1, "ZHS/Präv./Rest.", 55),
    (2, "Endodontologie", 20),
    (3, "Kinderzahnheilkunde", 8),
    (4, "Prothetik", 51),
    (5, "Schnittmenge", 33),
]

# (id, name, min_count, min_points, category_id)
CLASS_ROWS = [
    (0, "AIT", 3, 24, 0),
    (1, "UPT", 4, 8, 0),
    (2, "Klasse I und II", 6, 12, 1),
    (3, "Klasse III und IV", 3, 6, 1),
    (4, "Klasse V", 2, 2, 1),
    (5, "Befund", 4, 8, 1),
    (6, "PZR", 4, 6, 1),
    (7, "WK", 1, 9, 2),
    (8, "WF", 1, 6, 2),
    (9, "Befund Kind", 2, None, 3),
    (10, "Prophylaxe Kind", None, None, 3),
    (11, "Non-invasiv/invasiv Kind", None, None, 3),
    (12, "Krone", None, None, 4),
    (13, "Brückenglied", None, None, 4),
    (14, "Totalprothese", None, None, 4),
    (15, "Teilprothese Doppelkrone", None, None, 4),
    (16, "Teleskop", None, None, 4),
    (17, "MEG", None, None, 4),
    (18, "Interimsprothese", None, None, 4),
    (19, "Unterfütterung", None, None, 4),
    (20, "Remontage", None, None, 4),
    (21, "Proth. Recall", None, None, 4),
    (22, "Inlay/Teilkrone", None, None, 5),
    (23, "Kronenrandfensterung", None, None, 5),
    (24, "Stumpfaufbau(KVB)", None, None, 5),
    (25, "Stiftaufbau", None, None, 5),
    (26, "Hosp. in Kindersprechstunde", None, None, 3),
    (27, "WF-Revision", None, None, 2),
    (28, "Aufbissbehelf", None, None, 4),
]
CLASS_ID = {name: cid for cid, name, _, _, _ in CLASS_ROWS}

# Die Excel führt die Spalte im Schnittmenge-Block, zählt sie dort aber nicht mit.
OUTSIDE_BLOCKS = {"Aufbissbehelf"}

SHEET_SEMESTER = {
    "IK I": "2024WiSe",
    "IK II": "2025SoSe",
    "IK III": "2025WiSe",
    "IK IV": "2026SoSe",
}


def col_index(ref):
    n = 0
    for ch in ref:
        if ch.isalpha():
            n = n * 26 + ord(ch.upper()) - 64
    return n


def col_letter(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def shared_strings(z):
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    return ["".join(si.itertext()) for si in root.findall(".//main:si", NS)]


def workbook_sheets(z):
    root = ET.fromstring(z.read("xl/workbook.xml"))
    rid_attr = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = {
        r.attrib["Id"]: r.attrib["Target"]
        for r in rels.iter()
        if r.tag.endswith("Relationship")
    }
    return [
        (sheet.attrib["name"], "xl/" + target[sheet.attrib[rid_attr]])
        for sheet in root.find("main:sheets", NS).findall("main:sheet", NS)
    ]


def sheet_cells(z, path, strings):
    """Gibt {(zeile, spaltenindex): wert} zurück."""
    cells = {}
    root = ET.fromstring(z.read(path))
    for row in root.findall("main:sheetData/main:row", NS):
        r = int(row.attrib["r"])
        for c in row.findall("main:c", NS):
            v = c.find("main:v", NS)
            if v is None:
                continue
            value = strings[int(v.text)] if c.attrib.get("t") == "s" else v.text
            cells[(r, col_index(c.attrib["r"]))] = value
    return cells


def number(value):
    if value in (None, ""):
        return None
    try:
        n = float(value)
    except ValueError:
        return None
    return int(n) if n.is_integer() else n


def parse_sheet(name, cells):
    """Liest ein Semesterblatt und liefert (zeilen, warnungen)."""
    semester = SHEET_SEMESTER[name]
    max_col = max(c for _, c in cells)
    columns = []  # (klassen_id, name, anzahl_spalte, punkte_spalte)
    blocks = []  # (blockname, gesamt_spalte, [punkte_spalten])
    current = []
    for col in range(2, max_col + 1):
        header = cells.get((NAME_ROW, col))
        kind = cells.get((KIND_ROW, col))
        if kind == "Gesamt":
            if header == name:
                total_col = col
            else:
                blocks.append((header, col, current))
            current = []
            continue
        if not header:
            continue
        if header not in CLASS_ID:
            if kind in ("Anzahl", "Punkte"):
                print(
                    f"{name}: Spalte {col_letter(col)} '{header}' ist keine Klasse, übersprungen"
                )
            continue
        if kind == "Anzahl" and cells.get((KIND_ROW, col + 1)) == "Punkte":
            columns.append((CLASS_ID[header], header, col, col + 1))
            points_col = col + 1
        elif kind == "Punkte":
            columns.append((CLASS_ID[header], header, None, col))
            points_col = col
        elif kind in ("Anzahl", None):
            # nur eine Anzahl, keine Punkte (Hospitationen)
            columns.append((CLASS_ID[header], header, col, None))
            continue
        else:
            continue
        if header not in OUTSIDE_BLOCKS:
            current.append(points_col)

    rows = []
    warnings = []
    for r in STUDENT_ROWS:
        label = cells.get((r, 1), "")
        if not label.startswith("Stud."):
            continue
        sid = int(label.split(".")[1]) - 1
        total = 0
        for cid, header, count_col, points_col in columns:
            points = number(cells.get((r, points_col))) if points_col else None
            count = number(cells.get((r, count_col))) if count_col else None
            if not points and not count:
                continue
            rows.append((sid, cid, semester, count or 1, points or 0))
            total += points or 0
        unassigned = 0
        for block, total_col_b, points_cols in blocks:
            excel = number(cells.get((r, total_col_b))) or 0
            parsed = sum(number(cells.get((r, c))) or 0 for c in points_cols)
            if excel != parsed:
                unassigned += excel - parsed
                warnings.append(
                    f"{name} {label}: Block '{block}' hat {excel} P in "
                    f"{col_letter(total_col_b)}{r}, die Einzelspalten ergeben {parsed} P. "
                    f"Differenz {excel - parsed} P ohne Leistung, nicht übernommen."
                )
        expected = number(cells.get((r, total_col))) or 0
        if round(total + unassigned - expected, 2) != 0:
            warnings.append(
                f"{name} {label}: Semestersumme {expected} P in "
                f"{col_letter(total_col)}{r}, gelesen {total} P."
            )
    return rows, warnings


def sql_value(value):
    if value is None:
        return "null"
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    return str(value)


def values_block(tuples):
    return ",\n".join(
        "    (" + ", ".join(sql_value(v) for v in t) + ")" for t in tuples
    )


def render_sql(rows, patients_part):
    parts = [
        "begin transaction;",
        "",
        "insert into",
        "    categories (id, name, min_points)",
        "values",
        values_block(CATEGORY_ROWS) + ";",
        "",
        "insert into",
        "    classes (id, name, min_count, min_points, category_id)",
        "values",
        values_block(CLASS_ROWS) + ";",
        "",
        "insert into",
        "    students (id)",
        "values",
        values_block((sid,) for sid in range(5)) + ";",
        "",
        "insert into",
        "    students_classes (student_id, class_id, semester, count, points)",
        "values",
        values_block(rows) + ";",
        "",
    ]
    if patients_part:
        parts.append(patients_part.rstrip())
        parts.append("")
    parts.append("commit;")
    return "\n".join(parts) + "\n"


def existing_patients_part():
    if not TEST_SQL_PATH.exists():
        return ""
    text = TEST_SQL_PATH.read_text(encoding="utf-8")
    start = text.find("insert into\n    patients")
    if start < 0:
        return ""
    end = text.rfind("commit;")
    return text[start:end] if end > start else text[start:]


def main():
    if not XLSX_PATH.exists():
        sys.exit(f"Excel nicht gefunden: {XLSX_PATH}")
    rows = []
    warnings = []
    with zipfile.ZipFile(XLSX_PATH) as z:
        strings = shared_strings(z)
        for name, path in workbook_sheets(z):
            if name not in SHEET_SEMESTER:
                continue
            sheet_rows, sheet_warnings = parse_sheet(
                name, sheet_cells(z, path, strings)
            )
            rows.extend(sheet_rows)
            warnings.extend(sheet_warnings)
    patients_part = existing_patients_part()
    TEST_SQL_PATH.write_text(render_sql(rows, patients_part), encoding="utf-8")
    print(f"{len(rows)} Leistungszeilen nach {TEST_SQL_PATH.name} geschrieben")
    for line in warnings:
        print("Hinweis:", line)


if __name__ == "__main__":
    main()
