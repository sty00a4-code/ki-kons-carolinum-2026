import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).with_name("leistungen.db")
SQL_FILE = Path(__file__).with_name("test.sql")

if not DB_FILE.exists():
    raise FileNotFoundError(f"Database file not found: {DB_FILE}")
if not SQL_FILE.exists():
    raise FileNotFoundError(f"SQL file not found: {SQL_FILE}")

sql_text = SQL_FILE.read_text(encoding="utf-8")

with sqlite3.connect(DB_FILE) as conn:
    conn.executescript(sql_text)

print(f"Inserted dummy data from {SQL_FILE} into {DB_FILE}")
