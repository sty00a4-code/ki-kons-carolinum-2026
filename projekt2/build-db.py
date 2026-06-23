import sqlite3
from pathlib import Path

SQL_FILE = Path(__file__).with_name("leistungen.sql")
DB_FILE = Path(__file__).with_name("leistungen.db")

if not SQL_FILE.exists():
    raise FileNotFoundError(f"Missing {SQL_FILE}")

sql_text = SQL_FILE.read_text(encoding="utf-8")

DB_FILE.unlink(missing_ok=True)
conn = sqlite3.connect(DB_FILE)
try:
    conn.executescript(sql_text)
    print(f"Created {DB_FILE} from {SQL_FILE}")
finally:
    conn.close()
