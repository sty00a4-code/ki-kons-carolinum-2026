"""Skripte für Datenbank, Excel-Übernahme und den Bau der Prüfziel-Liste."""

import datetime
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, NamedTuple

import openpyxl
import pytest
from werkzeug.security import check_password_hash

from app import pruefziele
from scripts import import_excel, init_db, pruefziele_bauen
from tests.hilfen import LERNZIELE_PDF, mini_pdf

# Prüfziel-Tabelle ab Zeile 7: Nummer in Spalte B, Name in Spalte D. Excel hat
# "1.1." und "2.1.12" in Datumswerte umgewandelt, "4.12.2" ist veraltet.
TABELLE = [
    (datetime.date(2026, 1, 1), "Zahnhartsubstanzen"),
    ("1.1.1", "Karies"),
    ("1.1.2", "Erosion, Abrasion, Attrition"),
    ("1.1.2.1", "Erosion durch Saeuren"),
    (datetime.date(2012, 1, 2), "Vaskulitiden"),
    ("4.12.2", "Depression"),
    ("4.13.5", "Angststoerung"),
    (None, None),
    ("VIII", "Uebergeordnete Kompetenzen"),
    ("3.2.1", "Kommunikation mit Patienten"),
]
KATALOG = mini_pdf(
    [
        "VI Erkrankungen",
        "VI.1.1 Zahnhartsubstanzen",
        "VI.1.1.1 Karies (2.1.1)",
        "VI.1.1.2 Erosion, Abrasion und Attrition",
        "VI.1.1.2.1 Erosion durch Saeuren",
        "VI.2.1.12 Vaskulitiden der Haut",
        "VI.4.13.2 Depression",
        "VI.4.13.5 Schizophrenie",
        "VIII Uebergeordnete Kompetenzen",
        "VIII.3.2.1 Kommunikation mit Patientinnen und Patienten",
    ]
)


def _db(tmp_path: Path) -> Path:
    return tmp_path / "skript.db"


def _zeilen(pfad: Path, sql: str) -> list[sqlite3.Row]:
    with closing(sqlite3.connect(pfad)) as con:
        con.row_factory = sqlite3.Row
        return con.execute(sql).fetchall()


# Login anlegen


def test_init_db_legt_den_testlogin_an(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Ohne Angaben entsteht der Testlogin mit dem Namen als Passwort."""
    assert init_db.main(["--datenbank", str(_db(tmp_path))]) == 0
    login = _zeilen(_db(tmp_path), "select * from users")[0]
    assert login["username"] == init_db.TESTLOGIN
    assert check_password_hash(login["password_hash"], init_db.TESTLOGIN)
    assert "nur für den Testbetrieb" in capsys.readouterr().out


def test_init_db_aendert_einen_vorhandenen_login(tmp_path: Path) -> None:
    """Ein vorhandener Login erhält neues Passwort und neue Rolle."""
    datenbank = ["--datenbank", str(_db(tmp_path))]
    assert init_db.main(["lehrende", *datenbank], eingabe=lambda _: "erstes-passwort") == 0
    assert (
        init_db.main(["lehrende", "admin", *datenbank], eingabe=lambda _: "zweites-passwort") == 0
    )
    logins = _zeilen(_db(tmp_path), "select * from users")
    assert [(z["username"], z["role"]) for z in logins] == [("lehrende", "admin")]
    assert check_password_hash(logins[0]["password_hash"], "zweites-passwort")


@pytest.mark.parametrize("eingaben", [["kurz"], ["langes-passwort", "anderes-passwort"]])
def test_init_db_lehnt_ungueltige_passwoerter_ab(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], eingaben: list[str]
) -> None:
    """Zu kurze oder abweichende Passwörter brechen ohne Login ab."""
    folge = iter(eingaben)
    assert (
        init_db.main(["name", "--datenbank", str(_db(tmp_path))], eingabe=lambda _: next(folge))
        == 1
    )
    assert "Passw" in capsys.readouterr().err
    assert not _db(tmp_path).exists()


# Ergebnis-Excel übernehmen


def _ergebnis_excel(pfad: Path) -> None:
    mappe = openpyxl.Workbook()
    blatt = mappe.active
    assert blatt is not None
    blatt.title = "mistral 0.5"
    blatt.append(["Prüfziele", "Abdeckung", "Begründung", "Lernziel-ID_Kapitel"])
    blatt.append(["1.1.1 Karies", "X", "Wird behandelt.", "25.1.1.1"])
    blatt.append(["1.1.2 Erosion, Abrasion, Attrition", "", "Fehlt.", ""])
    mappe.save(pfad)


def test_import_excel_legt_je_blatt_ein_ergebnis_an(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Jedes Blatt wird ein Ergebnis mit Temperatur aus dem Blattnamen."""
    excel, lernziele = tmp_path / "Auswertung.xlsx", tmp_path / "Lernziele.pdf"
    _ergebnis_excel(excel)
    lernziele.write_bytes(LERNZIELE_PDF)
    argumente = [str(excel), "--lernziele", str(lernziele), "--datenbank", str(_db(tmp_path))]
    assert import_excel.main(argumente) == 0
    ergebnis = _zeilen(_db(tmp_path), "select * from auswertungen")[0]
    assert ergebnis["titel"] == "Auswertung · mistral 0.5"
    assert ergebnis["temperatur"] == 0.5
    assert ergebnis["lernziele_name"] == "Lernziele.pdf"
    assert ergebnis["erstellt_von"] == "import"
    assert f"/ergebnisse/{ergebnis['token']}" in capsys.readouterr().out


def test_import_excel_meldet_unlesbare_dateien(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Eine Datei, die keine Excel-Datei ist, ergibt eine Meldung statt eines Abbruchs."""
    falsch = tmp_path / "Auswertung.xlsx"
    falsch.write_bytes(b"keine Excel-Datei")
    assert import_excel.main([str(falsch), "--datenbank", str(_db(tmp_path))]) == 1
    assert "keine lesbare Excel-Datei" in capsys.readouterr().err


# Prüfziel-Liste bauen


@pytest.fixture(name="quellen")
def fixture_quellen(tmp_path: Path) -> tuple[Path, Path]:
    """Prüfziel-Tabelle und Katalog als Dateien."""
    mappe = openpyxl.Workbook()
    blatt = mappe.active
    assert blatt is not None
    for _ in range(pruefziele_bauen.ERSTE_ZEILE - 1):
        blatt.append(["Kopf"])
    for nr, name in TABELLE:
        blatt.append([None, nr, None, name])
    tabelle, katalog = tmp_path / "Tabelle.xlsx", tmp_path / "Katalog.pdf"
    mappe.save(tabelle)
    katalog.write_bytes(KATALOG)
    return tabelle, katalog


class Gebaut(NamedTuple):
    """Einträge der gebauten Liste und die Ausgaben des Skripts."""

    eintraege: list[dict[str, Any]]
    aus: str
    err: str

    def eintrag(self, teil: str, nr: str) -> dict[str, Any]:
        """Der Eintrag mit Teil und Nummer."""
        return next(e for e in self.eintraege if (e["teil"], e["nr"]) == (teil, nr))


@pytest.fixture(name="gebaut")
def fixture_gebaut(
    tmp_path: Path, quellen: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> Gebaut:
    """Die aus TABELLE und KATALOG gebaute Liste."""
    ziel = tmp_path / "liste.json"
    assert pruefziele_bauen.main([*map(str, quellen), "--ziel", str(ziel)]) == 0
    ausgabe = capsys.readouterr()
    daten = json.loads(ziel.read_text(encoding="utf-8"))
    return Gebaut(daten["eintraege"], ausgabe.out, ausgabe.err)


def test_liste_beginnt_mit_teil_und_gruppe(gebaut: Gebaut) -> None:
    """Vor dem ersten Prüfziel stehen der Teil und die Gruppe."""
    assert [e["ebene"] for e in gebaut.eintraege][:2] == ["teil", "gruppe"]


@pytest.mark.parametrize(
    ("teil", "nr", "name"),
    [
        pytest.param("VI", "1.1.2", "Erosion, Abrasion und Attrition", id="katalog"),
        pytest.param("VI", "2.1.12", "Vaskulitiden der Haut", id="datumswert"),
        pytest.param("VI", "4.13.5", "Angststoerung", id="zu-verschieden"),
        pytest.param("VIII", "VIII", pruefziele.TEILE["VIII"], id="teil"),
        pytest.param("VIII", "3.2.1", "Kommunikation mit Patientinnen und Patienten", id="viii"),
    ],
)
def test_schreibweise_nach_katalog(gebaut: Gebaut, teil: str, nr: str, name: str) -> None:
    """Namen folgen dem Katalog, bei zu großer Abweichung bleibt der Name der Tabelle."""
    assert gebaut.eintrag(teil, nr)["name"] == name


def test_unterpunkte_markiert(gebaut: Gebaut) -> None:
    """Ein Prüfziel mit Unterpunkten ist markiert."""
    assert gebaut.eintrag("VI", "1.1.2")["unterpunkte"] is True
    assert gebaut.eintrag("VI", "1.1.1")["unterpunkte"] is False


def test_veraltete_nummer_ersetzt(gebaut: Gebaut) -> None:
    """Eine Nummer, unter der im Katalog ein anderer Name steht, wird ersetzt und gemeldet."""
    assert gebaut.eintrag("VI", "4.13.2")["nr_tabelle"] == "4.12.2"
    assert "Nummer VI 4.12.2 ersetzt durch 4.13.2" in gebaut.aus


def test_abweichender_name_gemeldet(gebaut: Gebaut) -> None:
    """Weicht der Name zu stark vom Katalog ab, warnt das Skript."""
    assert "WARNUNG VI 4.13.5" in gebaut.err


def test_anzahl_gemeldet(gebaut: Gebaut) -> None:
    """Das Skript nennt die Zahl der Prüfziele."""
    assert "7 Prüfziele (6 ohne Unterpunkte)" in gebaut.aus


def test_liste_bauen_ohne_katalog(
    tmp_path: Path, quellen: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """Eine fehlende Datei ergibt eine Meldung und keine Liste."""
    ziel = tmp_path / "liste.json"
    argumente = [str(quellen[0]), str(tmp_path / "fehlt.pdf"), "--ziel", str(ziel)]
    assert pruefziele_bauen.main(argumente) == 1
    assert "Fehler" in capsys.readouterr().err
    assert not ziel.exists()


def test_nummer_aus_datumswerten() -> None:
    """Datumswerte aus Excel werden in Nummern zurückverwandelt."""
    utc = datetime.UTC
    assert pruefziele_bauen.nummer(datetime.datetime(2026, 3, 1, tzinfo=utc)) == "1.3"
    assert pruefziele_bauen.nummer(datetime.datetime(2012, 6, 4, tzinfo=utc)) == "4.6.12"
    assert pruefziele_bauen.nummer(" 1.2.3. ") == "1.2.3"
    assert pruefziele_bauen.nummer(None) == ""


def test_sauber_fasst_leerraum_zusammen() -> None:
    """Zeilenumbrüche und doppelte Leerzeichen im Namen verschwinden."""
    assert pruefziele_bauen.sauber("  Karies\n und  Erosion ") == "Karies und Erosion"
    assert pruefziele_bauen.sauber(None) == ""


def test_tabelle_lesen(quellen: tuple[Path, Path]) -> None:
    """Die Tabelle wird ab der ersten Datenzeile gelesen, leere Zeilen fehlen."""
    zeilen = pruefziele_bauen.tabelle_lesen(quellen[0])
    assert zeilen[0] == pruefziele_bauen.Tabellenzeile("VI", "1.1", "Zahnhartsubstanzen")
    assert [z.teil for z in zeilen].count("VIII") == 1
    assert len(zeilen) == len(TABELLE) - 2
