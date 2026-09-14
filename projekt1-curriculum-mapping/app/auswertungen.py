"""Auswertungen anlegen, laden und ihr Ergebnis berechnen.

Wird von den Seiten und von scripts/import_excel.py genutzt.
"""

import os

from . import db, excel_import, pruefziele, zuordnung
from .security import new_token

PROMPT_DATEI = os.path.join(pruefziele.DATEN, "prompt_kategorie1.txt")
MAX_TITEL = 160

FELDER = (
    "titel",
    "kategorie",
    "modell",
    "temperatur",
    "prompt",
    "pruefziele_liste",
    "vorlesung_name",
    "vorlesung_text",
    "lernziele_name",
    "lernziele_text",
    "quelle",
    "quelle_hinweis",
    "status",
    "rohantwort",
    "erstellt_von",
)


def standard_prompt():
    with open(PROMPT_DATEI, encoding="utf-8") as fh:
        return fh.read().strip()


def anlegen(con, **werte):
    """Legt eine Auswertung an und liefert (id, token), ohne zu committen."""
    unbekannt = set(werte) - set(FELDER)
    if unbekannt:
        raise TypeError(f"Unbekannte Felder: {sorted(unbekannt)}")
    werte["titel"] = werte.get("titel", "")[:MAX_TITEL]
    werte.setdefault("kategorie", 1)
    werte.setdefault("rohantwort", "")
    token = new_token()
    zeit = db.jetzt()
    spalten = ["token", *werte, "erstellt_am", "aktualisiert_am"]
    cur = con.execute(
        # Spaltennamen stammen aus FELDER, die Werte sind Parameter.
        f"insert into auswertungen ({', '.join(spalten)}) "  # noqa: S608
        f"values ({', '.join('?' * len(spalten))})",
        (token, *werte.values(), zeit, zeit),
    )
    return cur.lastrowid, token


def holen(con, token):
    return con.execute("select * from auswertungen where token = ?", (token,)).fetchone()


def ergebnis(auswertung, liste=None):
    """Liefert die ausgewertete Antwort einer Auswertung."""
    liste = liste or pruefziele.liste(auswertung["pruefziele_liste"])
    return zuordnung.auswerten(auswertung["rohantwort"], liste, auswertung["lernziele_text"] or "")


def excel_uebernehmen(
    con,
    daten,
    excel_name,
    *,
    modell,
    pruefziele_liste=pruefziele.STANDARD,
    titel="",
    prompt="",
    lernziele=None,
    vorlesung=None,
    erstellt_von=None,
):
    """Legt für jedes Blatt einer Ergebnis-Excel eine Auswertung an.

    lernziele und vorlesung sind Tupel (Dateiname, Text) oder None. Rückgabe
    ist eine Liste von (Blattname, Token, Zeilenzahl).
    """
    grundname = titel.strip() or os.path.splitext(excel_name)[0]
    vorlesung_name, vorlesung_text = vorlesung or (None, None)
    lernziele_name, lernziele_text = lernziele or (None, None)
    angelegt = []
    for blatt, text, anzahl in excel_import.blaetter(daten):
        _, token = anlegen(
            con,
            titel=f"{grundname} · {blatt}",
            modell=modell,
            temperatur=excel_import.temperatur_aus_name(blatt),
            prompt=prompt.strip() or None,
            pruefziele_liste=pruefziele_liste,
            vorlesung_name=vorlesung_name,
            vorlesung_text=vorlesung_text,
            lernziele_name=lernziele_name,
            lernziele_text=lernziele_text,
            quelle="import",
            quelle_hinweis=f"{excel_name}, Blatt {blatt}",
            status="fertig",
            rohantwort=text,
            erstellt_von=erstellt_von,
        )
        angelegt.append((blatt, token, anzahl))
    return angelegt
