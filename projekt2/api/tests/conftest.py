"""Testumgebung: jeder Test bekommt eine frische Datenbank aus leistungen.sql
und test.sql aus dem Projektordner, die Original-leistungen.db bleibt
unberührt. PROJEKT2_DB muss gesetzt sein, bevor app.database importiert wird."""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[2]
API = PROJECT / "api"
sys.path.insert(0, str(API))

_TMP = Path(tempfile.mkdtemp(prefix="projekt2-tests-"))
_TEMPLATE = _TMP / "template.db"
_LIVE = _TMP / "live.db"

os.environ["PROJEKT2_DB"] = str(_LIVE)
os.environ.pop("PROJEKT2_API_KEY", None)

_conn = sqlite3.connect(_TEMPLATE)
_conn.executescript((PROJECT / "leistungen.sql").read_text(encoding="utf-8"))
_conn.executescript((PROJECT / "test.sql").read_text(encoding="utf-8"))
_conn.commit()
_conn.close()


def _reset_live_db() -> None:
    source = sqlite3.connect(_TEMPLATE)
    target = sqlite3.connect(_LIVE)
    source.backup(target)
    source.close()
    target.close()


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    _reset_live_db()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session():
    from app.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
