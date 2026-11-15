"""Übernimmt eine Ergebnis-Excel über die Kommandozeile.

    python -m scripts.import_excel EXCEL [--lernziele DATEI] [--vorlesung DATEI]
                                         [--modell ID] [--titel TEXT] [--benutzer NAME]
                                         [--datenbank PFAD]

Jedes Blatt mit einer Zuordnung wird ein eigenes Ergebnis. Beispiel:

    python -m scripts.import_excel "ModellAuswertung Mistral.xlsx" \\
        --lernziele NKLZLernziele242248.pdf \\
        --vorlesung Vorlesung_1_OraleMedizinUndSystemischeAspekte.pdf
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from contextlib import closing
from pathlib import Path

from app import db, dokumente
from app.config import STANDARD_MODELLE
from app.dokumente import Textdatei
from app.fehler import EingabeFehler
from app.zuordnung.excel_import import Uebernahme, uebernehmen
from app.zuordnung.lauf import standard_prompt


def textdatei(pfad: Path | None, bezeichnung: str) -> Textdatei | None:
    """Liest den Text einer PDF- oder Textdatei, ohne Pfad None."""
    if pfad is None:
        return None
    return Textdatei(pfad.name, dokumente.text_lesen(pfad.name, pfad.read_bytes(), bezeichnung))


def main(argv: Sequence[str] | None = None) -> int:
    """Übernimmt die Excel-Datei und nennt je Blatt die Adresse des Ergebnisses."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("excel", type=Path, help="Ergebnis-Excel (.xlsx)")
    parser.add_argument("--lernziele", type=Path, help="Lernziel-Datei als PDF oder Text")
    parser.add_argument("--vorlesung", type=Path, help="Vorlesung als PDF oder Text")
    parser.add_argument(
        "--modell", default=STANDARD_MODELLE[0][0], help="Modell, das die Datei erzeugt hat"
    )
    parser.add_argument("--titel", default="", help="Titel, sonst der Dateiname")
    parser.add_argument("--benutzer", default="import", help="Eintrag unter „erstellt von“")
    parser.add_argument("--datenbank", type=Path, help="SQLite-Datei, sonst die der App")
    args = parser.parse_args(argv)

    try:
        angaben = Uebernahme(
            modell=args.modell,
            titel=args.titel,
            prompt=standard_prompt(),
            lernziele=textdatei(args.lernziele, "Lernziele"),
            vorlesung=textdatei(args.vorlesung, "Vorlesung"),
            erstellt_von=args.benutzer,
        )
        daten = args.excel.read_bytes()
        with closing(db.oeffnen(args.datenbank or db.STANDARD_PFAD)) as con:
            angelegt = uebernehmen(con, daten, args.excel.name, angaben)
            con.commit()
    except (OSError, EingabeFehler) as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1
    for blatt in angelegt:
        print(f"{blatt.blatt}: {blatt.zeilen} Zeilen, /ergebnisse/{blatt.token}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
