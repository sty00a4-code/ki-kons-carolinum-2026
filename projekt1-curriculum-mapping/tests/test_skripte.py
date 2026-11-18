"""Skript zum Anlegen der Datenbank und der Logins."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from werkzeug.security import check_password_hash

from scripts import init_db


def _db(tmp_path: Path) -> Path:
    return tmp_path / "skript.db"


def _zeilen(pfad: Path, sql: str) -> list[sqlite3.Row]:
    with closing(sqlite3.connect(pfad)) as con:
        con.row_factory = sqlite3.Row
        return con.execute(sql).fetchall()


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
