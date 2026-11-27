"""Semester als eigenes, zentral validiertes Konzept.

Kanonische Darstellung: JJJJSoSe oder JJJJWiSe (z.B. 2026SoSe). Dieses Format
sortiert lexikographisch gleich chronologisch (SoSe vor WiSe im selben Jahr),
weshalb die Datenbank die Strings direkt vergleichen darf. Alles andere
(Parsen, Weiterzählen, Sortierschlüssel) läuft über dieses Modul.
"""

import re
from typing import Literal

SEMESTER_PATTERN = r"^[0-9]{4}(SoSe|WiSe)$"
_RE = re.compile(SEMESTER_PATTERN)
Term = Literal["SoSe", "WiSe"]
MIN_YEAR, MAX_YEAR = 2000, 2100


def parse_semester(value: str) -> tuple[int, Term]:
    """'2026SoSe' -> (2026, 'SoSe'). ValueError bei jedem anderen Format."""
    if not isinstance(value, str) or not _RE.match(value):
        raise ValueError(f"Ungültiges Semester: {value!r} (erwartet JJJJSoSe oder JJJJWiSe)")
    year, term = int(value[:4]), value[4:]
    if not MIN_YEAR <= year <= MAX_YEAR:
        raise ValueError(f"Jahr außerhalb {MIN_YEAR} bis {MAX_YEAR}: {year}")
    return year, term  # type: ignore[return-value]


def format_semester(year: int, term: Term) -> str:
    value = f"{year:04d}{term}"
    parse_semester(value)
    return value


def semester_index(value: str) -> int:
    """Fortlaufende Nummer: je Jahr zwei Semester, SoSe vor WiSe."""
    year, term = parse_semester(value)
    return year * 2 + (0 if term == "SoSe" else 1)


def next_semester(value: str) -> str:
    year, term = parse_semester(value)
    return f"{year:04d}WiSe" if term == "SoSe" else f"{year + 1:04d}SoSe"


def validate_semester(value: str) -> str:
    """Für Pydantic (AfterValidator in schemas.py): gibt den Wert unverändert
    zurück oder wirft ValueError."""
    parse_semester(value)
    return value
