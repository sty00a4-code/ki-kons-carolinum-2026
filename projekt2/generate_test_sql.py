import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
XLSX_PATH = (
    ROOT.parent
    / "data"
    / "statistik"
    / "AuswertungKursleistungenIKIV SoSe26_korrigiert.xlsx"
)
TEST_SQL_PATH = ROOT / "test.sql"

NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

CATEGORY_ROWS = [
    (1, "Parodontologie"),
    (2, "ZHS/Präv./Rest."),
    (3, "Endodontologie"),
    (4, "Kinderzahnheilkunde"),
    (5, "Prothetik"),
    (6, "Schnittmenge ZHS/Restauration/Prothetik"),
]

CLASS_ROWS = [
    (1, "AIT", 50, 1),
    (2, "UPT", 50, 1),
    (3, "Klasse I und II", 50, 2),
    (4, "Klasse III und IV", 50, 2),
    (5, "Klasse V", 50, 2),
    (6, "Befund", 50, 2),
    (7, "PZR", 50, 2),
    (8, "WK", 50, 3),
    (9, "WF", 50, 3),
    (10, "Befund Kind", 50, 4),
    (11, "Prophylaxe Kind", 50, 4),
    (12, "Non-invasiv/invasiv Kind", 50, 4),
    (13, "Krone", 50, 5),
    (14, "Brückenglied", 50, 5),
    (15, "Totalprothese", 50, 5),
    (16, "Teilprothese Doppelkrone", 50, 5),
    (17, "Teleskop", 50, 5),
    (18, "MEG", 50, 5),
    (19, "Interimsprothese", 50, 5),
    (20, "Unterfütterung", 50, 5),
    (21, "Remontage", 50, 5),
    (22, "Proth. Recall", 50, 5),
    (23, "Inlay/Teilkrone", 50, 6),
    (24, "Kronenrandfensterung", 50, 6),
    (25, "Stumpfaufbau(KVB)", 50, 6),
    (26, "Stiftaufbau", 50, 6),
    (27, "Hosp. in Kindersprechstunde", 50, 4),
]

STUDENT_IDS = [1, 2, 3, 4, 5]

SHEET_SEMESTER = {
    "IK I": "WiSe2024/2025",
    "IK II": "SoSe2025",
    "IK III": "WiSe2025/26",
    "IK IV": "SoSe26",
}

CLASS_NAME_TO_ID = {name: cid for cid, name, _, _ in CLASS_ROWS}

COLS = [chr(c) for c in range(ord("A"), ord("Z") + 1)] + [
    "AA",
    "AB",
    "AC",
    "AD",
    "AE",
    "AF",
    "AG",
    "AH",
    "AI",
    "AJ",
    "AK",
    "AL",
    "AM",
    "AN",
    "AO",
    "AP",
    "AQ",
    "AR",
    "AS",
    "AT",
    "AU",
    "AV",
    "AW",
    "AX",
    "AY",
    "AZ",
    "BA",
]


def col_name(ref: str) -> str:
    return "".join(ch for ch in ref if ch.isalpha())


def parse_shared_strings(z):
    text = z.read("xl/sharedStrings.xml")
    root = ET.fromstring(text)
    values = []
    for si in root.findall(".//main:si", NS):
        values.append("".join(si.itertext()))
    return values


def parse_workbook_sheets(z):
    text = z.read("xl/workbook.xml")
    root = ET.fromstring(text)
    sheets = []
    for sheet in root.find("main:sheets", NS).findall("main:sheet", NS):
        rid = sheet.attrib.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        )
        sheets.append((sheet.attrib["name"], rid))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target_by_id = {
        r.attrib["Id"]: r.attrib["Target"]
        for r in rels.findall(".//")
        if r.tag.endswith("Relationship")
    }
    return [(name, "xl/" + target_by_id[rid]) for name, rid in sheets]


def get_cell(rows, row, col):
    row_el = rows.get(row)
    if row_el is None:
        return None
    for c in row_el.findall("main:c", NS):
        if col_name(c.attrib["r"]) == col:
            v = c.find("main:v", NS)
            if v is None:
                return None
            if c.attrib.get("t") == "s":
                return SHARED_STRINGS[int(v.text)]
            return v.text
    return None


def normalize_number(value):
    if value is None or value == "":
        return None
    try:
        if "." in value:
            n = float(value)
            return int(n) if n.is_integer() else n
        return int(value)
    except ValueError:
        return None


def parse_sheet(z, sheet_name, sheet_path):
    xml = ET.fromstring(z.read(sheet_path))
    rows = {int(r.attrib["r"]): r for r in xml.findall("main:sheetData/main:row", NS)}
    semester = SHEET_SEMESTER.get(sheet_name)
    if semester is None:
        return []
    class_columns = []
    for idx, col in enumerate(COLS):
        header = get_cell(rows, 4, col)
        if header not in CLASS_NAME_TO_ID:
            continue
        next_col = COLS[idx + 1] if idx + 1 < len(COLS) else None
        next2_col = COLS[idx + 2] if idx + 2 < len(COLS) else None
        if (
            next_col
            and get_cell(rows, 5, next_col) == "Anzahl"
            and next2_col
            and get_cell(rows, 5, next2_col) == "Punkte"
        ):
            class_columns.append(
                (CLASS_NAME_TO_ID[header], header, next_col, next2_col)
            )
        elif next_col and get_cell(rows, 5, next_col) == "Punkte":
            class_columns.append((CLASS_NAME_TO_ID[header], header, None, next_col))
    student_rows = []
    for row_num in range(6, 11):
        name = get_cell(rows, row_num, "A")
        if not name or not name.startswith("Stud."):
            continue
        sid = int(name.split(".")[1])
        for class_id, _, count_col, points_col in class_columns:
            count = (
                normalize_number(get_cell(rows, row_num, count_col)) if count_col else 0
            )
            points = normalize_number(get_cell(rows, row_num, points_col))
            if points is None:
                continue
            if count is None:
                count = 0
            if count == 0 and points == 0:
                continue
            student_rows.append((sid, class_id, semester, count, points))
    return student_rows


def render_sql(rows):
    lines = [
        "begin transaction;",
        "",
        "insert into",
        "    categories (id, name)",
        "values",
        ",\n".join(f"    ({cid}, '{name}')" for cid, name in CATEGORY_ROWS) + ";",
        "",
        "insert into",
        "    classes (id, name, min, category_id)",
        "values",
        ",\n".join(
            f"    ({cid}, '{name}', {min_points}, {category_id})"
            for cid, name, min_points, category_id in CLASS_ROWS
        )
        + ";",
        "",
        "insert into",
        "    students (id)",
        "values",
        ",\n".join(f"    ({sid})" for sid in STUDENT_IDS) + ";",
        "",
        "insert into",
        "    students_classes (student_id, class_id, semester, count, points)",
        "values",
        ",\n".join(
            f"    ({sid}, {cid}, '{semester}', {count}, {points})"
            for sid, cid, semester, count, points in rows
        )
        + ";",
        "",
        "commit;",
    ]
    return "\n".join(lines) + "\n"


def main():
    if not XLSX_PATH.exists():
        raise FileNotFoundError(f"Missing workbook: {XLSX_PATH}")
    with zipfile.ZipFile(XLSX_PATH) as z:
        global SHARED_STRINGS
        SHARED_STRINGS = parse_shared_strings(z)
        sheet_files = parse_workbook_sheets(z)
        rows = []
        for name, path in sheet_files:
            if name == "GESAMT":
                continue
            rows.extend(parse_sheet(z, name, path))
    # sort by student, semester, class
    rows.sort(key=lambda x: (x[0], x[2], x[1]))
    sql = render_sql(rows)
    TEST_SQL_PATH.write_text(sql, encoding="utf-8")
    print(f"Wrote {TEST_SQL_PATH} ({len(rows)} student rows)")


if __name__ == "__main__":
    main()
