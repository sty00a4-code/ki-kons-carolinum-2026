"""Seiten der Zuordnung: neu, Excel-Import, Ergebnisse, Vergleich und Prüfziel-Liste."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import PurePath

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask.typing import ResponseReturnValue

from .. import eingaben, formate, hintergrund, pruefziele
from ..config import grenzen, ki_einstellungen
from ..db import get_db
from ..dokumente import Textdatei
from ..fehler import EingabeFehler
from ..security import login_required
from ..seiten import datensatz_oder_404, excel_antwort
from . import excel_import, export, lauf, speicher
from .antwort import lesen
from .auswertung import Ergebnis
from .vergleich import vergleichen

bp = Blueprint("zuordnung", __name__)

ANSICHTEN = {
    "tabelle": "Zuordnung",
    "lernziele": "Nach Lernzielen",
    "antwort": "Antwort des Modells",
    "eingaben": "Eingaben",
}
MAX_VERGLEICH = 4


@dataclass(frozen=True)
class Einstellungen:
    """Geprüfte Einstellungen für einen Durchlauf."""

    prompt: str
    modell: str
    temperatur: float
    liste: str


@dataclass(frozen=True)
class Eintrag:
    """Eine Zuordnung in der Liste der Ergebnisse, ausgewertet, sobald Text vorliegt."""

    a: sqlite3.Row
    e: Ergebnis | None


# Neue Zuordnung mit dem KI-Dienst


@bp.route("/neu", methods=["GET", "POST"])
@login_required
def neu() -> ResponseReturnValue:
    """Formular für eine neue Zuordnung; startet den Durchlauf."""
    ki = ki_einstellungen()
    werte = eingaben.formularwerte(
        {
            "titel": "",
            "prompt": lauf.standard_prompt(),
            "modell": ki.modelle[0][0],
            "temperatur": "0",
            "liste": pruefziele.STANDARD,
        }
    )
    if request.method == "POST":
        try:
            einstellungen = _einstellungen(werte)
            vorlesung = eingaben.pflichttext("vorlesung", "Vorlesung")
            lernziele = eingaben.pflichttext("lernziele", "Lernziele")
            token = _starten(einstellungen, lernziele, vorlesung, werte["titel"])
        except EingabeFehler as exc:
            flash(str(exc))
        else:
            return redirect(url_for(".ergebnis", token=token))
    return render_template(
        "neu.html",
        werte=werte,
        modelle=ki.modelle,
        listen=pruefziele.auswahl(),
        liste=pruefziele.liste(),
    )


def _einstellungen(werte: dict[str, str]) -> Einstellungen:
    ki = ki_einstellungen()
    if not ki.bereit:
        raise EingabeFehler(
            "Für den KI-Dienst ist kein Schlüssel hinterlegt (P1_LLM_API_KEY). "
            "Ohne ihn lassen sich nur Ergebnisse aus einer Excel-Datei übernehmen."
        )
    return Einstellungen(
        prompt=eingaben.prompt_pruefen(werte["prompt"]),
        modell=eingaben.modell_pruefen(werte["modell"], ki.modelle),
        temperatur=eingaben.temperatur_lesen(werte["temperatur"]),
        liste=_liste_pruefen(werte["liste"]),
    )


def _liste_pruefen(schluessel: str) -> str:
    if schluessel not in pruefziele.DATEIEN:
        raise EingabeFehler("Bitte eine Prüfziel-Liste aus der Auswahl wählen.")
    return schluessel


def _starten(
    einstellungen: Einstellungen,
    lernziele: Textdatei,
    vorlesung: Textdatei | None,
    titel: str,
) -> str:
    """Legt eine Zuordnung an, startet den Durchlauf und liefert das Token."""
    liste = pruefziele.liste(einstellungen.liste)
    zeichen = sum(
        len(text)
        for text in (
            einstellungen.prompt,
            liste.text_fuer_modell(),
            lernziele.text,
            vorlesung.text if vorlesung else "",
        )
    )
    erlaubt = grenzen().zeichen
    if zeichen > erlaubt:
        raise EingabeFehler(
            f"Die Texte sind zusammen {formate.zahl(zeichen)} Zeichen lang, erlaubt sind "
            f"{formate.zahl(erlaubt)}. Bitte eine kürzere Vorlesung oder nur "
            "das passende Lernziel-Kapitel hochladen."
        )
    con = get_db()
    hintergrund.platz_pruefen(con)
    kennung, token = speicher.anlegen(
        con,
        speicher.NeueZuordnung(
            titel=titel or PurePath((vorlesung or lernziele).name).stem,
            modell=einstellungen.modell,
            quelle="ki",
            pruefziele_liste=einstellungen.liste,
            temperatur=einstellungen.temperatur,
            prompt=einstellungen.prompt,
            vorlesung_name=vorlesung.name if vorlesung else None,
            vorlesung_text=vorlesung.text if vorlesung else None,
            lernziele_name=lernziele.name,
            lernziele_text=lernziele.text,
            erstellt_von=session.get("username"),
        ),
    )
    con.commit()
    lauf.starten(kennung)
    return token


# Ergebnisse aus einer Excel-Datei übernehmen


@bp.route("/import", methods=["GET", "POST"])
@login_required
def excel_uebernehmen() -> ResponseReturnValue:
    """Formular zum Übernehmen einer Ergebnis-Excel."""
    ki = ki_einstellungen()
    werte = eingaben.formularwerte(
        {
            "titel": "",
            "prompt": lauf.standard_prompt(),
            "modell": ki.modelle[0][0],
            "liste": pruefziele.STANDARD,
        }
    )
    if request.method == "POST":
        try:
            angelegt = _excel_anlegen(werte)
        except EingabeFehler as exc:
            flash(str(exc))
        else:
            if len(angelegt) == 1:
                flash("Das Blatt wurde übernommen.")
                return redirect(url_for(".ergebnis", token=angelegt[0].token))
            flash(
                f"{len(angelegt)} Blätter übernommen: "
                + ", ".join(f"{u.blatt} ({u.zeilen} Zeilen)" for u in angelegt)
                + "."
            )
            return redirect(url_for(".ergebnisse"))
    return render_template(
        "import.html", werte=werte, modelle=ki.modelle, listen=pruefziele.auswahl()
    )


def _excel_anlegen(werte: dict[str, str]) -> list[excel_import.Uebernommen]:
    name, daten = eingaben.dateiinhalt("excel", "Bitte die Ergebnis-Excel auswählen.")
    _liste_pruefen(werte["liste"])
    if not werte["modell"]:
        raise EingabeFehler("Bitte angeben, welches Modell die Excel-Datei erzeugt hat.")
    angaben = excel_import.Uebernahme(
        modell=werte["modell"],
        pruefziele_liste=werte["liste"],
        titel=werte["titel"],
        prompt=werte["prompt"],
        lernziele=eingaben.dateitext("lernziele", "Lernziele"),
        vorlesung=eingaben.dateitext("vorlesung", "Vorlesung"),
        erstellt_von=session.get("username"),
    )
    con = get_db()
    angelegt = excel_import.uebernehmen(con, daten, name, angaben)
    con.commit()
    return angelegt


# Ergebnisse


@bp.route("/ergebnisse")
@login_required
def ergebnisse() -> ResponseReturnValue:
    """Liste aller Zuordnungen."""
    con = get_db()
    hintergrund.verwaiste_beenden(con)
    eintraege = [
        Eintrag(a, speicher.ergebnis(a) if a["rohantwort"] else None) for a in speicher.alle(con)
    ]
    return render_template("ergebnisse.html", eintraege=eintraege, max_vergleich=MAX_VERGLEICH)


@bp.route("/ergebnisse/<token>")
@login_required
def ergebnis(token: str) -> ResponseReturnValue:
    """Ergebnisseite einer Zuordnung mit ihren Ansichten."""
    return _ergebnis_seite(_zuordnung(token), request.args.get("ansicht", "tabelle"))


def _ergebnis_seite(
    a: sqlite3.Row, ansicht: str, formular: dict[str, str] | None = None
) -> ResponseReturnValue:
    """Rendert die Ergebnisseite.

    formular enthält nach einem Fehler die abgeschickten Werte für "Erneut
    ausführen", sonst sind die Werte der Zuordnung vorbelegt.
    """
    if ansicht not in ANSICHTEN:
        ansicht = "tabelle"
    liste = pruefziele.liste(a["pruefziele_liste"])
    reiter = [
        (name, url_for(".ergebnis", token=a["token"], ansicht=schluessel))
        for schluessel, name in ANSICHTEN.items()
    ]
    werte = formular or {
        "modell": a["modell"],
        "temperatur": formate.temperatur(a["temperatur"]) or "0",
        "prompt": a["prompt"] or lauf.standard_prompt(),
    }
    return render_template(
        "ergebnis.html",
        a=a,
        e=speicher.ergebnis(a, liste),
        liste=liste,
        ansicht=ansicht,
        aktive_ansicht=ANSICHTEN[ansicht],
        reiter=reiter,
        modelle=ki_einstellungen().modelle,
        werte=werte,
    )


@bp.route("/ergebnisse/<token>/stand")
@login_required
def stand(token: str) -> ResponseReturnValue:
    """Stand eines Durchlaufs als JSON für die Ergebnisseite."""
    a = _zuordnung(token)
    zeilen, _ = lesen(a["rohantwort"])
    return jsonify(
        status=a["status"],
        fertig=len(zeilen),
        gesamt=len(pruefziele.liste(a["pruefziele_liste"]).zaehlend),
        zeichen=len(a["rohantwort"]),
        fehler=a["fehler"],
    )


@bp.route("/ergebnisse/<token>/excel", endpoint="excel")
@login_required
def excel_datei(token: str) -> ResponseReturnValue:
    """Die Zuordnung als Excel-Datei."""
    a = _zuordnung(token)
    liste = pruefziele.liste(a["pruefziele_liste"])
    daten = export.xlsx(a, speicher.ergebnis(a, liste), liste, ki_einstellungen())
    return excel_antwort(daten, export.dateiname(a))


@bp.route("/ergebnisse/<token>/wiederholen", methods=["POST"])
@login_required
def wiederholen(token: str) -> ResponseReturnValue:
    """Startet einen neuen Durchlauf mit den gespeicherten Texten der Dateien."""
    a = _zuordnung(token)
    werte = {
        "prompt": request.form.get("prompt", "").strip(),
        "modell": request.form.get("modell", "").strip(),
        "temperatur": request.form.get("temperatur", "").strip(),
        "liste": a["pruefziele_liste"],
    }
    try:
        lernziele, vorlesung = _gespeicherte_dateien(a)
        neuer = _starten(_einstellungen(werte), lernziele, vorlesung, a["titel"])
    except EingabeFehler as exc:
        flash(str(exc))
        # Rendern statt umleiten, damit die Eingaben erhalten bleiben.
        return _ergebnis_seite(a, "eingaben", werte)
    return redirect(url_for(".ergebnis", token=neuer))


def _gespeicherte_dateien(a: sqlite3.Row) -> tuple[Textdatei, Textdatei | None]:
    """Liefert die gespeicherten Texte von Lernzielen und Vorlesung einer Zuordnung."""
    if not a["lernziele_text"]:
        raise EingabeFehler(
            "Zu diesem Ergebnis ist keine Lernziel-Datei gespeichert; "
            "bitte eine neue Zuordnung anlegen."
        )
    lernziele = Textdatei(a["lernziele_name"], a["lernziele_text"])
    if not a["vorlesung_text"]:
        return lernziele, None
    return lernziele, Textdatei(a["vorlesung_name"], a["vorlesung_text"])


@bp.route("/ergebnisse/<token>/loeschen", methods=["POST"])
@login_required
def loeschen(token: str) -> ResponseReturnValue:
    """Löscht eine Zuordnung."""
    a = _zuordnung(token)
    con = get_db()
    speicher.loeschen(con, a["id"])
    con.commit()
    flash(f"„{a['titel']}“ wurde gelöscht.")
    return redirect(url_for(".ergebnisse"))


def _zuordnung(token: str) -> sqlite3.Row:
    return datensatz_oder_404(speicher.holen, token)


# Vergleich mehrerer Ergebnisse


@bp.route("/vergleich")
@login_required
def vergleich() -> ResponseReturnValue:
    """Auswahl und Vergleich von zwei bis MAX_VERGLEICH Ergebnissen."""
    auswahl = speicher.fertige(get_db())
    tokens = list(dict.fromkeys(request.args.getlist("t")))
    nach_token = {a["token"]: a for a in auswahl}
    gewaehlt = [nach_token[t] for t in tokens if t in nach_token]
    daten = laeufe = liste = None
    # Mit "aendern" zeigt die Seite nur die Auswahl mit den bisher gewählten Ergebnissen.
    if not request.args.get("aendern"):
        meldung = _vergleich_pruefen(tokens, gewaehlt)
        if meldung:
            flash(meldung)
        elif gewaehlt:
            liste = pruefziele.liste(gewaehlt[0]["pruefziele_liste"])
            laeufe = [(a, speicher.ergebnis(a, liste)) for a in gewaehlt]
            daten = vergleichen(laeufe, liste)
    return render_template(
        "vergleich.html",
        auswahl=auswahl,
        gewaehlt={a["token"] for a in gewaehlt},
        daten=daten,
        laeufe=laeufe,
        liste=liste,
        max_vergleich=MAX_VERGLEICH,
    )


def _vergleich_pruefen(tokens: list[str], gewaehlt: list[sqlite3.Row]) -> str | None:
    """Liefert eine Meldung, wenn die Auswahl keinen Vergleich erlaubt."""
    if len(tokens) > MAX_VERGLEICH:
        return f"Bitte höchstens {MAX_VERGLEICH} Ergebnisse auswählen."
    if len(gewaehlt) < len(tokens):
        abort(404)
    if len(gewaehlt) == 1:
        return "Für einen Vergleich bitte mindestens 2 Ergebnisse auswählen."
    if len({a["pruefziele_liste"] for a in gewaehlt}) > 1:
        return "Die gewählten Ergebnisse beruhen auf verschiedenen Prüfziel-Listen."
    return None


# Prüfziel-Liste


@bp.route("/pruefziele")
@login_required
def pruefziel_liste() -> ResponseReturnValue:
    """Die Prüfziel-Liste mit allen Teilen, Bereichen und Gruppen."""
    schluessel = request.args.get("liste", pruefziele.STANDARD)
    if schluessel not in pruefziele.DATEIEN:
        abort(404)
    return render_template("pruefziele.html", liste=pruefziele.liste(schluessel))
