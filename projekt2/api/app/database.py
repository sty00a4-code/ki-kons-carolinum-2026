"""Zentrale DB-Engine. Ein Engine-Objekt pro Prozess, Sessions pro Request."""

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "leistungen.db"

# check_same_thread=False: SQLite + mehrere Worker-Threads unter uvicorn.
# Für den Uni-Server auf Postgres migrieren, sobald mehrere Nutzer gleichzeitig
# schreiben sollen - SQLite verträgt keine parallelen Schreibzugriffe gut.
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# sqlite wertet references-Klauseln nur aus, wenn pro Verbindung
# pragma foreign_keys=on gesetzt ist.
@event.listens_for(engine, "connect")
def _enable_foreign_keys(connection, _):
    connection.execute("pragma foreign_keys=on")


def get_db():
    """FastAPI-Dependency: liefert eine Session, schließt sie nach dem Request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
