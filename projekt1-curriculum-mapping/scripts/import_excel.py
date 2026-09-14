"""Importiert eine Ergebnis-Excel über die Kommandozeile.

    python -m scripts.import_excel EXCEL [--lernziele PDF] [--vorlesung PDF]
                                         [--modell ID] [--titel TEXT] [--benutzer NAME]

Beispiel:

    python -m scripts.import_excel "ModellAuswertung Mistral.xlsx" \\
        --lernziele NKLZLernziele242248.pdf \\
        --vorlesung Vorlesung_1_OraleMedizinUndSystemischeAspekte.pdf
"""

import argparse
import os
import sys

from app import auswertungen, create_app, dokumente, excel_import, ki_dienst
from app.db import get_db


class _Datei:
    """Datei von der Festplatte mit der Schnittstelle eines Uploads."""

    def __init__(self, pfad):
        self.filename = os.path.basename(pfad)
        self._pfad = pfad

    def read(self):
        with open(self._pfad, "rb") as fh:
            return fh.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("excel")
    parser.add_argument("--lernziele")
    parser.add_argument("--vorlesung")
    parser.add_argument("--modell", default=ki_dienst.modelle()[0][0])
    parser.add_argument("--titel", default="")
    parser.add_argument("--benutzer", default="import")
    args = parser.parse_args()

    try:
        lernziele = (
            dokumente.text_aus_upload(_Datei(args.lernziele), "Lernziele")
            if args.lernziele
            else None
        )
        vorlesung = (
            dokumente.text_aus_upload(_Datei(args.vorlesung), "Vorlesung")
            if args.vorlesung
            else None
        )
        with open(args.excel, "rb") as fh:
            daten = fh.read()
        app = create_app()
        with app.app_context():
            con = get_db()
            angelegt = auswertungen.excel_uebernehmen(
                con,
                daten,
                os.path.basename(args.excel),
                modell=args.modell,
                titel=args.titel,
                prompt=auswertungen.standard_prompt(),
                lernziele=lernziele,
                vorlesung=vorlesung,
                erstellt_von=args.benutzer,
            )
            con.commit()
    except (OSError, dokumente.DokumentFehler, excel_import.ExcelFehler) as exc:
        sys.exit(f"Fehler: {exc}")
    for blatt, token, anzahl in angelegt:
        print(f"{blatt}: {anzahl} Zeilen, /ergebnisse/{token}")


if __name__ == "__main__":
    main()
