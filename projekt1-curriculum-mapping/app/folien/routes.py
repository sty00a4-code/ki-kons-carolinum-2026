"""Seiten des Vorlesungsabgleichs: Liste, anlegen, Ergebnis übernehmen und Ergebnis."""

from __future__ import annotations

import dataclasses
import io
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
    send_file,
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
from . import anfragen, export, lauf, speicher
from .auswertung import Ergebnis, ergebnis
from .katalog import ZIELARTEN, katalog, lernziel_katalog
from .pdf import Seite, seiten_lesen
from .uebernahme import antworten_aus_datei

bp = Blueprint("folien", __name__, url_prefix="/folien")

ANSICHTEN = ("folien", "ziele", "antworten", "eingaben")
STANDARD_MODELL = "qwen3-30b-a3b-instruct-2507"
# Vorschaubilder ändern sich nicht, der Browser darf sie einen Tag behalten.
VORSCHAU_CACHE_SEKUNDEN = 24 * 3600


@dataclass(frozen=True)
class Eintrag:
    """Ein Abgleich in der Liste mit seinem ausgewerteten Ergebnis."""

    a: sqlite3.Row
    e: Ergebnis


@dataclass(frozen=True)
class Vorlesung:
    """Die hochgeladene Vorlesung: Dateiname, PDF-Datei und gelesene Seiten."""

    name: str
    pdf: bytes
    seiten: list[Seite]


@bp.route("/")
@login_required
def liste() -> ResponseReturnValue:
    """Liste aller Vorlesungsabgleiche."""
    con = get_db()
    hintergrund.verwaiste_beenden(con)
    eintraege = [Eintrag(a, ergebnis(con, a)) for a in speicher.alle(con)]
    return render_template("folien_liste.html", eintraege=eintraege, ziele=_zielnamen())


# Neuer Abgleich mit dem KI-Dienst


@bp.route("/neu", methods=["GET", "POST"])
@login_required
def neu() -> ResponseReturnValue:
    """Formular für einen neuen Abgleich; startet den Durchlauf."""
    werte = eingaben.formularwerte(_vorgaben())
    if request.method == "POST":
        try:
            token = _neu_starten(werte)
        except EingabeFehler as exc:
            flash(str(exc))
        else:
            return redirect(url_for(".ergebnis", token=token))
    return render_template("folien_neu.html", werte=werte, **_auswahl())


def _vorgaben() -> dict[str, str]:
    ki = ki_einstellungen()
    modelle = [mid for mid, _ in ki.modelle]
    return {
        "ziel": "lernziele",
        "titel": "",
        "prompt": anfragen.standard_prompt("lernziele"),
        "modell": STANDARD_MODELL if STANDARD_MODELL in modelle else modelle[0],
        "bildmodell": ki.bildmodelle[0][0] if ki.bildmodelle else "",
        "temperatur": "0",
        "liste": pruefziele.STANDARD,
    }


def _auswahl() -> dict[str, object]:
    ki = ki_einstellungen()
    return {
        "ziele": _zielnamen(),
        "modelle": ki.modelle,
        "bildmodelle": ki.bildmodelle,
        "listen": pruefziele.auswahl(),
        "prompts": {ziel: anfragen.standard_prompt(ziel) for ziel in ZIELARTEN},
    }


def _zielnamen() -> dict[str, str]:
    return {schluessel: art.name for schluessel, art in ZIELARTEN.items()}


def _einstellungen(werte: dict[str, str]) -> speicher.Einstellungen:
    ki = ki_einstellungen()
    if not ki.bereit:
        raise EingabeFehler(
            "Für den KI-Dienst ist kein Schlüssel hinterlegt (P1_LLM_API_KEY). "
            "Ohne ihn lassen sich nur fertige Ergebnisse übernehmen."
        )
    _ziel_pruefen(werte)
    prompt = eingaben.prompt_pruefen(werte["prompt"])
    modell = eingaben.modell_pruefen(werte["modell"], ki.modelle)
    bildmodell = werte["bildmodell"]
    if bildmodell:
        eingaben.modell_pruefen(bildmodell, ki.bildmodelle, "Bildmodell")
    return speicher.Einstellungen(
        ziel=werte["ziel"],
        modell=modell,
        bildmodell=bildmodell or None,
        temperatur=eingaben.temperatur_lesen(werte["temperatur"]),
        prompt=prompt,
        pruefziele_liste=werte["liste"] if werte["ziel"] == "pruefziele" else None,
    )


def _ziel_pruefen(werte: dict[str, str]) -> None:
    if werte["ziel"] not in ZIELARTEN:
        raise EingabeFehler("Bitte wählen, ob mit Lernzielen oder mit Prüfzielen abgeglichen wird.")
    if werte["ziel"] == "pruefziele" and werte["liste"] not in pruefziele.DATEIEN:
        raise EingabeFehler("Bitte eine Prüfziel-Liste aus der Auswahl wählen.")


def _vorlesung() -> Vorlesung:
    name, daten = eingaben.dateiinhalt("vorlesung", "Vorlesung: Bitte die PDF-Datei auswählen.")
    return Vorlesung(name, daten, seiten_lesen(daten, grenzen().folien))


def _ziele_datei(ziel: str) -> Textdatei | None:
    """Liest die Lernziel-Datei oder die optionale Prüfziel-Datei und prüft ihren Inhalt."""
    if ziel == "lernziele":
        datei = eingaben.pflichttext("lernziele", "Lernziele", grenzen().zeichen)
        if not lernziel_katalog(datei.text).zaehlend:
            raise EingabeFehler(
                "Lernziele: In der Datei stehen keine Lernziel-IDs. Erwartet wird ein Kapitel "
                "des NKLZ mit IDs wie 25.1.1.1 am Zeilenanfang."
            )
        return datei
    eigene = eingaben.dateitext("pruefziele", "Prüfziele", grenzen().zeichen)
    if eigene and not pruefziele.aus_text(eigene.text, eigene.name).zaehlend:
        raise EingabeFehler(
            "Prüfziele: In der Datei stehen keine Prüfziele. Erwartet werden Zeilen mit "
            "Nummer und Name wie „VI.1.1.1 Karies“ oder „1.1.1 Karies“."
        )
    return eigene


def _ohne_liste_bei_datei(
    einstellungen: speicher.Einstellungen, ziele: Textdatei | None
) -> speicher.Einstellungen:
    """Mit eigener Prüfziel-Datei gilt keine der eingebauten Listen."""
    if einstellungen.ziel == "pruefziele" and ziele is not None:
        return dataclasses.replace(einstellungen, pruefziele_liste=None)
    return einstellungen


def _neu_starten(werte: dict[str, str]) -> str:
    einstellungen = _einstellungen(werte)
    vorlesung = _vorlesung()
    ziele = _ziele_datei(einstellungen.ziel)
    # Erst nach dem Lesen der Dateien, die Sperre von platz_pruefen soll kurz sein.
    con = get_db()
    hintergrund.platz_pruefen(con)
    kennung, token = speicher.anlegen(
        con,
        speicher.NeuerAbgleich(
            titel=werte["titel"] or PurePath(vorlesung.name).stem,
            einstellungen=_ohne_liste_bei_datei(einstellungen, ziele),
            vorlesung_name=vorlesung.name,
            quelle="ki",
            ziele=ziele,
            erstellt_von=session.get("username"),
        ),
        vorlesung.pdf,
        vorlesung.seiten,
    )
    con.commit()
    lauf.starten(kennung)
    return token


# Fertiges Ergebnis übernehmen


@bp.route("/import", methods=["GET", "POST"])
@login_required
def uebernehmen() -> ResponseReturnValue:
    """Formular zum Übernehmen eines fertigen Ergebnisses."""
    werte = eingaben.formularwerte(
        {
            "ziel": "lernziele",
            "titel": "",
            "modell": STANDARD_MODELL,
            "liste": pruefziele.STANDARD,
        }
    )
    if request.method == "POST":
        try:
            token, meldung = _uebernehmen(werte)
        except EingabeFehler as exc:
            flash(str(exc))
        else:
            flash(meldung)
            return redirect(url_for(".ergebnis", token=token))
    return render_template("folien_import.html", werte=werte, **_auswahl())


def _uebernehmen(werte: dict[str, str]) -> tuple[str, str]:
    _ziel_pruefen(werte)
    if not werte["modell"]:
        raise EingabeFehler("Bitte angeben, welches Modell die Ergebnisdatei erzeugt hat.")
    ergebnis_name, daten = eingaben.dateiinhalt(
        "ergebnis", "Ergebnis: Bitte die Excel- oder JSON-Datei auswählen."
    )
    antworten = antworten_aus_datei(daten, ergebnis_name)
    vorlesung = _vorlesung()
    hoechste = max(antworten.je_folie)
    if hoechste > len(vorlesung.seiten):
        raise EingabeFehler(
            f"Die Ergebnisdatei nennt Folie {hoechste}, die Vorlesung hat aber nur "
            f"{len(vorlesung.seiten)} Folien. Bitte prüfen, ob beide Dateien zusammengehören."
        )
    ziele = _ziele_datei(werte["ziel"])
    hinweis = ergebnis_name
    if antworten.verschoben:
        hinweis += ", Folien ab 0 gezählt und deshalb um 1 verschoben"
    einstellungen = speicher.Einstellungen(
        ziel=werte["ziel"],
        modell=werte["modell"],
        pruefziele_liste=werte["liste"] if werte["ziel"] == "pruefziele" else None,
    )
    con = get_db()
    kennung, token = speicher.anlegen(
        con,
        speicher.NeuerAbgleich(
            titel=werte["titel"] or PurePath(vorlesung.name).stem,
            einstellungen=_ohne_liste_bei_datei(einstellungen, ziele),
            vorlesung_name=vorlesung.name,
            quelle="import",
            ziele=ziele,
            quelle_hinweis=hinweis,
            erstellt_von=session.get("username"),
        ),
        vorlesung.pdf,
        vorlesung.seiten,
    )
    speicher.antworten_setzen(con, kennung, antworten.je_folie)
    con.commit()
    anzahl = formate.anzahl(len(antworten.je_folie), "Folie", "Folien")
    meldung = f"{anzahl} aus {ergebnis_name} übernommen."
    if antworten.verschoben:
        meldung += " Die Datei zählt die Folien ab 0, die Nummern wurden um 1 erhöht."
    return token, meldung


# Ergebnis


@bp.route("/<token>", endpoint="ergebnis")
@login_required
def ergebnis_seite(token: str) -> ResponseReturnValue:
    """Ergebnisseite eines Abgleichs mit ihren Ansichten."""
    return _ergebnis_seite(_abgleich(token), request.args.get("ansicht", "folien"))


def _ergebnis_seite(
    a: sqlite3.Row, ansicht: str, formular: dict[str, str] | None = None
) -> ResponseReturnValue:
    """Rendert die Ergebnisseite.

    formular enthält nach einem Fehler die abgeschickten Werte für "Erneut
    ausführen", sonst sind die Werte des Abgleichs vorbelegt.
    """
    if ansicht not in ANSICHTEN:
        ansicht = "folien"
    ziele = katalog(a)
    zielart = ZIELARTEN[a["ziel"]]
    namen = {
        "folien": "Folien",
        "ziele": f"Nach {zielart.dativ}",
        "antworten": "Antworten",
        "eingaben": "Eingaben",
    }
    reiter = [(namen[s], url_for(".ergebnis", token=a["token"], ansicht=s)) for s in ANSICHTEN]
    werte = formular or {
        "modell": a["modell"],
        "bildmodell": a["bildmodell"] or "",
        "temperatur": formate.temperatur(a["temperatur"]) or "0",
        "prompt": a["prompt"] or anfragen.standard_prompt(a["ziel"]),
    }
    e = ergebnis(get_db(), a, ziele)
    ki = ki_einstellungen()
    return render_template(
        "folien_ergebnis.html",
        a=a,
        e=e,
        ziele=ziele,
        zielart=zielart,
        ansicht=ansicht,
        aktive_ansicht=namen[ansicht],
        reiter=reiter,
        werte=werte,
        modelle=ki.modelle,
        bildmodelle=ki.bildmodelle,
        fortsetzbar=a["status"] == "fehler" and a["quelle"] == "ki" and e.bearbeitet < e.gesamt,
    )


@bp.route("/<token>/stand")
@login_required
def stand(token: str) -> ResponseReturnValue:
    """Stand eines Abgleichs als JSON für die Ergebnisseite."""
    a = _abgleich(token)
    bearbeitet, gesamt = speicher.fortschritt(get_db(), a["id"])
    return jsonify(status=a["status"], fertig=bearbeitet, gesamt=gesamt, fehler=a["fehler"])


@bp.route("/<token>/folie/<int:nr>.jpg")
@login_required
def vorschau(token: str, nr: int) -> ResponseReturnValue:
    """Vorschaubild einer Folie."""
    con = get_db()
    a = speicher.holen(con, token)
    bild = speicher.vorschau(con, a["id"], nr) if a else None
    if not bild:
        abort(404)
    antwort = send_file(io.BytesIO(bild), mimetype="image/jpeg", max_age=VORSCHAU_CACHE_SEKUNDEN)
    antwort.cache_control.public = False
    antwort.cache_control.private = True
    return antwort


@bp.route("/<token>/vorlesung.pdf", endpoint="vorlesung")
@login_required
def vorlesung_pdf(token: str) -> ResponseReturnValue:
    """Die PDF-Datei der Vorlesung."""
    con = get_db()
    a = speicher.holen(con, token)
    pdf = speicher.pdf_datei(con, a["id"]) if a else None
    if a is None or not pdf:
        abort(404)
    name = str(a["vorlesung_name"])
    return send_file(
        io.BytesIO(pdf),
        mimetype="application/pdf",
        download_name=name if name.lower().endswith(".pdf") else f"{name}.pdf",
    )


@bp.route("/<token>/excel", endpoint="excel")
@login_required
def excel_datei(token: str) -> ResponseReturnValue:
    """Der Abgleich als Excel-Datei."""
    a = _abgleich(token)
    ziele = katalog(a)
    daten = export.xlsx(a, ergebnis(get_db(), a, ziele), ziele, ki_einstellungen())
    return excel_antwort(daten, export.dateiname(a))


@bp.route("/<token>/fortsetzen", methods=["POST"])
@login_required
def fortsetzen(token: str) -> ResponseReturnValue:
    """Setzt einen abgebrochenen Abgleich bei der ersten offenen Folie fort."""
    a = _abgleich(token)
    try:
        _fortsetzen(a)
    except EingabeFehler as exc:
        flash(str(exc))
    return redirect(url_for(".ergebnis", token=token))


def _fortsetzen(a: sqlite3.Row) -> None:
    _fortsetzbar_pruefen(a)
    con = get_db()
    hintergrund.platz_pruefen(con)
    fortgesetzt = speicher.fortsetzen(con, a["id"])
    con.commit()
    if not fortgesetzt:
        raise EingabeFehler("Der Abgleich wurde inzwischen schon fortgesetzt.")
    lauf.starten(a["id"])


def _fortsetzbar_pruefen(a: sqlite3.Row) -> None:
    if a["status"] != "fehler" or a["quelle"] != "ki":
        raise EingabeFehler("Nur abgebrochene Abgleiche lassen sich fortsetzen.")
    if lauf.laeuft(a["id"]):
        raise EingabeFehler(
            "Der Abgleich beendet gerade noch eine Anfrage, bitte gleich noch einmal versuchen."
        )
    if not ki_einstellungen().bereit:
        raise EingabeFehler("Für den KI-Dienst ist kein Schlüssel hinterlegt (P1_LLM_API_KEY).")


@bp.route("/<token>/wiederholen", methods=["POST"])
@login_required
def wiederholen(token: str) -> ResponseReturnValue:
    """Startet einen neuen Abgleich mit derselben Vorlesung und denselben Zielen."""
    a = _abgleich(token)
    werte = {
        "ziel": a["ziel"],
        "liste": a["pruefziele_liste"] or pruefziele.STANDARD,
        "prompt": request.form.get("prompt", "").strip(),
        "modell": request.form.get("modell", "").strip(),
        "bildmodell": request.form.get("bildmodell", "").strip(),
        "temperatur": request.form.get("temperatur", "").strip(),
    }
    ziele = Textdatei(a["ziele_name"], a["ziele_text"]) if a["ziele_text"] else None
    try:
        einstellungen = _ohne_liste_bei_datei(_einstellungen(werte), ziele)
        con = get_db()
        hintergrund.platz_pruefen(con)
        kennung, neuer = speicher.kopieren(
            con,
            a["id"],
            speicher.NeuerAbgleich(
                titel=a["titel"],
                einstellungen=einstellungen,
                vorlesung_name=a["vorlesung_name"],
                quelle="ki",
                ziele=ziele,
                erstellt_von=session.get("username"),
            ),
            bilder=bool(einstellungen.bildmodell) and einstellungen.bildmodell == a["bildmodell"],
        )
        con.commit()
    except EingabeFehler as exc:
        flash(str(exc))
        # Rendern statt umleiten, damit die Eingaben erhalten bleiben.
        return _ergebnis_seite(a, "eingaben", werte)
    lauf.starten(kennung)
    return redirect(url_for(".ergebnis", token=neuer))


@bp.route("/<token>/loeschen", methods=["POST"])
@login_required
def loeschen(token: str) -> ResponseReturnValue:
    """Löscht einen Abgleich mit Vorlesung und Folien."""
    a = _abgleich(token)
    con = get_db()
    speicher.loeschen(con, a["id"])
    con.commit()
    flash(f"„{a['titel']}“ wurde gelöscht.")
    return redirect(url_for(".liste"))


def _abgleich(token: str) -> sqlite3.Row:
    return datensatz_oder_404(speicher.holen, token)
