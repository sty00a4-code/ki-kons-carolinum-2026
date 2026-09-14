"""Seiten: neue Zuordnung, Excel-Import, Ergebnisse, Vergleich und Prüfziel-Liste."""

import io
import os

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from . import (
    auswertungen,
    dokumente,
    excel_import,
    export,
    formate,
    ki_dienst,
    pruefziele,
    zuordnung,
)
from .db import get_db
from .security import login_required

bp = Blueprint("zuordnung", __name__)

ANSICHTEN = {
    "tabelle": "Zuordnung",
    "lernziele": "Nach Lernzielen",
    "antwort": "Antwort des Modells",
    "eingaben": "Eingaben",
}
MAX_VERGLEICH = 4
MIN_PROMPT = 10
MAX_PROMPT = 20000


class EingabeFehler(ValueError):
    """Fehlende oder ungültige Formulareingabe."""


# Neue Zuordnung mit dem KI-Dienst


@bp.route("/neu", methods=["GET", "POST"])
@login_required
def neu():
    werte = {
        "titel": "",
        "prompt": auswertungen.standard_prompt(),
        "modell": ki_dienst.modelle()[0][0],
        "temperatur": "0",
        "liste": pruefziele.STANDARD,
    }
    if request.method == "POST":
        werte.update({k: request.form.get(k, "").strip() for k in werte})
        try:
            einstellungen = _einstellungen(werte)
            vorlesung = _datei("vorlesung", "Vorlesung")
            lernziele = _datei("lernziele", "Lernziele")
            token = _starten(einstellungen, vorlesung, lernziele, werte["titel"])
        except (EingabeFehler, dokumente.DokumentFehler) as exc:
            flash(str(exc))
        else:
            return redirect(url_for(".ergebnis", token=token))
    return render_template(
        "neu.html",
        werte=werte,
        modelle=ki_dienst.modelle(),
        listen=pruefziele.auswahl(),
        liste=pruefziele.liste(),
    )


def _einstellungen(werte):
    if not ki_dienst.bereit():
        raise EingabeFehler(
            "Für den KI-Dienst ist kein Schlüssel hinterlegt (P1_LLM_API_KEY). "
            "Ohne ihn lassen sich nur Ergebnisse aus einer Excel-Datei übernehmen."
        )
    prompt = werte["prompt"]
    if len(prompt) < MIN_PROMPT:
        raise EingabeFehler(f"Der Prompt muss mindestens {MIN_PROMPT} Zeichen lang sein.")
    if len(prompt) > MAX_PROMPT:
        raise EingabeFehler(f"Der Prompt ist länger als {MAX_PROMPT} Zeichen.")
    if werte["modell"] not in dict(ki_dienst.modelle()):
        raise EingabeFehler("Bitte ein Modell aus der Liste wählen.")
    _liste_pruefen(werte["liste"])
    return {
        "prompt": prompt,
        "modell": werte["modell"],
        "temperatur": _temperatur(werte["temperatur"]),
        "liste": werte["liste"],
    }


def _temperatur(text):
    try:
        wert = float((text or "0").replace(",", "."))
    except ValueError as exc:
        raise EingabeFehler("Die Temperatur ist keine Zahl.") from exc
    if not 0 <= wert <= ki_dienst.MAX_TEMPERATUR:
        raise EingabeFehler(
            f"Die Temperatur muss zwischen 0 und {ki_dienst.MAX_TEMPERATUR} liegen."
        )
    return wert


def _liste_pruefen(schluessel):
    if schluessel not in pruefziele.DATEIEN:
        raise EingabeFehler("Bitte eine Prüfziel-Liste aus der Auswahl wählen.")


def _datei(feld, bezeichnung, *, pflicht=True):
    datei = request.files.get(feld)
    if not datei or not datei.filename:
        if pflicht:
            raise EingabeFehler(f"{bezeichnung}: Bitte eine Datei auswählen.")
        return None
    return dokumente.text_aus_upload(datei, bezeichnung)


def _starten(einstellungen, vorlesung, lernziele, titel):
    """Legt eine Auswertung an und startet den Durchlauf.

    vorlesung und lernziele sind Tupel (Dateiname, Text), vorlesung kann None sein.
    """
    vorlesung_name, vorlesung_text = vorlesung or (None, None)
    lernziele_name, lernziele_text = lernziele
    liste = pruefziele.liste(einstellungen["liste"])
    zeichen = (
        len(einstellungen["prompt"])
        + len(liste.text_fuer_modell())
        + len(lernziele_text)
        + len(vorlesung_text or "")
    )
    if zeichen > dokumente.MAX_ZEICHEN:
        raise EingabeFehler(
            f"Die Texte sind zusammen {formate.zahl(zeichen)} Zeichen lang, erlaubt sind "
            f"{formate.zahl(dokumente.MAX_ZEICHEN)}. Bitte eine kürzere Vorlesung oder nur "
            "das passende Lernziel-Kapitel hochladen."
        )
    con = get_db()
    ki_dienst.verwaiste_beenden(con)
    if ki_dienst.laufende(con) >= ki_dienst.MAX_GLEICHZEITIG:
        raise EingabeFehler(
            f"Es laufen schon {ki_dienst.MAX_GLEICHZEITIG} Zuordnungen. Bitte warten, "
            "bis eine davon fertig ist."
        )
    auswertung_id, token = auswertungen.anlegen(
        con,
        titel=titel or os.path.splitext(vorlesung_name or lernziele_name)[0],
        modell=einstellungen["modell"],
        temperatur=einstellungen["temperatur"],
        prompt=einstellungen["prompt"],
        pruefziele_liste=einstellungen["liste"],
        vorlesung_name=vorlesung_name,
        vorlesung_text=vorlesung_text,
        lernziele_name=lernziele_name,
        lernziele_text=lernziele_text,
        quelle="ki",
        status="laeuft",
        erstellt_von=session.get("username"),
    )
    con.commit()
    ki_dienst.starten(current_app._get_current_object(), auswertung_id)  # noqa: SLF001
    return token


# Ergebnisse aus einer Excel-Datei übernehmen


@bp.route("/import", methods=["GET", "POST"])
@login_required
def excel_uebernehmen():
    werte = {
        "titel": "",
        "prompt": auswertungen.standard_prompt(),
        "modell": ki_dienst.modelle()[0][0],
        "liste": pruefziele.STANDARD,
    }
    if request.method == "POST":
        werte.update({k: request.form.get(k, "").strip() for k in werte})
        try:
            angelegt = _excel_anlegen(werte)
        except (EingabeFehler, dokumente.DokumentFehler, excel_import.ExcelFehler) as exc:
            flash(str(exc))
        else:
            if len(angelegt) == 1:
                flash("Das Blatt wurde übernommen.")
                return redirect(url_for(".ergebnis", token=angelegt[0][1]))
            flash(
                f"{len(angelegt)} Blätter übernommen: "
                + ", ".join(f"{blatt} ({anzahl} Zeilen)" for blatt, _, anzahl in angelegt)
                + "."
            )
            return redirect(url_for(".ergebnisse"))
    return render_template(
        "import.html", werte=werte, modelle=ki_dienst.modelle(), listen=pruefziele.auswahl()
    )


def _excel_anlegen(werte):
    datei = request.files.get("excel")
    if not datei or not datei.filename:
        raise EingabeFehler("Bitte die Ergebnis-Excel auswählen.")
    _liste_pruefen(werte["liste"])
    if not werte["modell"]:
        raise EingabeFehler("Bitte angeben, welches Modell die Excel-Datei erzeugt hat.")
    lernziele = _datei("lernziele", "Lernziele", pflicht=False)
    vorlesung = _datei("vorlesung", "Vorlesung", pflicht=False)
    con = get_db()
    angelegt = auswertungen.excel_uebernehmen(
        con,
        datei.read(),
        dokumente.dateiname(datei),
        modell=werte["modell"],
        pruefziele_liste=werte["liste"],
        titel=werte["titel"],
        prompt=werte["prompt"],
        lernziele=lernziele,
        vorlesung=vorlesung,
        erstellt_von=session.get("username"),
    )
    con.commit()
    return angelegt


# Ergebnisse


@bp.route("/ergebnisse")
@login_required
def ergebnisse():
    con = get_db()
    ki_dienst.verwaiste_beenden(con)
    eintraege = [
        {"a": a, "e": auswertungen.ergebnis(a) if a["rohantwort"] else None}
        for a in con.execute("select * from auswertungen order by erstellt_am desc, id desc")
    ]
    return render_template("ergebnisse.html", eintraege=eintraege, max_vergleich=MAX_VERGLEICH)


@bp.route("/ergebnisse/<token>")
@login_required
def ergebnis(token):
    return _ergebnis_seite(_auswertung(token), request.args.get("ansicht", "tabelle"))


def _ergebnis_seite(a, ansicht, formular=None):
    """Rendert die Ergebnisseite.

    formular enthält nach einem Fehler die abgeschickten Werte für "Erneut ausführen",
    sonst sind die Werte des Ergebnisses vorbelegt.
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
        "prompt": a["prompt"] or auswertungen.standard_prompt(),
    }
    return render_template(
        "ergebnis.html",
        a=a,
        e=auswertungen.ergebnis(a, liste),
        liste=liste,
        ansicht=ansicht,
        aktive_ansicht=ANSICHTEN[ansicht],
        reiter=reiter,
        modelle=ki_dienst.modelle(),
        werte=werte,
    )


@bp.route("/ergebnisse/<token>/stand")
@login_required
def stand(token):
    a = _auswertung(token)
    zeilen, _ = zuordnung.lesen(a["rohantwort"])
    return jsonify(
        status=a["status"],
        zeilen=len(zeilen),
        zeichen=len(a["rohantwort"]),
        zaehlend=len(pruefziele.liste(a["pruefziele_liste"]).zaehlend),
        fehler=a["fehler"],
    )


@bp.route("/ergebnisse/<token>/excel")
@login_required
def excel(token):
    a = _auswertung(token)
    liste = pruefziele.liste(a["pruefziele_liste"])
    daten = export.xlsx(a, auswertungen.ergebnis(a, liste), liste)
    return send_file(
        io.BytesIO(daten),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=export.dateiname(a),
    )


@bp.route("/ergebnisse/<token>/wiederholen", methods=["POST"])
@login_required
def wiederholen(token):
    """Startet einen neuen Durchlauf mit den gespeicherten Dateitexten."""
    a = _auswertung(token)
    werte = {
        "prompt": request.form.get("prompt", "").strip(),
        "modell": request.form.get("modell", "").strip(),
        "temperatur": request.form.get("temperatur", "").strip(),
        "liste": a["pruefziele_liste"],
    }
    try:
        vorlesung, lernziele = _gespeicherte_dateien(a)
        neuer = _starten(_einstellungen(werte), vorlesung, lernziele, a["titel"])
    except EingabeFehler as exc:
        flash(str(exc))
        # Rendern statt umleiten, damit die Eingaben erhalten bleiben.
        return _ergebnis_seite(a, "eingaben", werte)
    return redirect(url_for(".ergebnis", token=neuer))


def _gespeicherte_dateien(a):
    if not a["lernziele_text"]:
        raise EingabeFehler(
            "Zu diesem Ergebnis ist keine Lernziel-Datei gespeichert; "
            "bitte eine neue Zuordnung anlegen."
        )
    vorlesung = (a["vorlesung_name"], a["vorlesung_text"]) if a["vorlesung_text"] else None
    return vorlesung, (a["lernziele_name"], a["lernziele_text"])


@bp.route("/ergebnisse/<token>/loeschen", methods=["POST"])
@login_required
def loeschen(token):
    a = _auswertung(token)
    con = get_db()
    con.execute("delete from auswertungen where id = ?", (a["id"],))
    con.commit()
    flash(f"„{a['titel']}“ wurde gelöscht.")
    return redirect(url_for(".ergebnisse"))


def _auswertung(token):
    con = get_db()
    a = auswertungen.holen(con, token)
    if a is None:
        abort(404)
    if a["status"] == "laeuft" and ki_dienst.verwaiste_beenden(con):
        a = auswertungen.holen(con, token)
    return a


# Vergleich mehrerer Ergebnisse


@bp.route("/vergleich")
@login_required
def vergleich():
    con = get_db()
    auswahl = con.execute(
        "select * from auswertungen where status = 'fertig' and rohantwort != '' "
        "order by erstellt_am desc, id desc"
    ).fetchall()
    tokens = list(dict.fromkeys(request.args.getlist("t")))
    nach_token = {a["token"]: a for a in auswahl}
    gewaehlt = [nach_token[t] for t in tokens if t in nach_token]
    daten = laeufe = liste = None
    # Mit "aendern" zeigt die Seite nur die Auswahl mit den bisher gewählten Ergebnissen.
    if not request.args.get("aendern"):
        if len(tokens) > MAX_VERGLEICH:
            flash(f"Bitte höchstens {MAX_VERGLEICH} Ergebnisse auswählen.")
        elif len(gewaehlt) < len(tokens):
            abort(404)
        elif len(gewaehlt) == 1:
            flash("Für einen Vergleich bitte mindestens 2 Ergebnisse auswählen.")
        elif len({a["pruefziele_liste"] for a in gewaehlt}) > 1:
            flash("Die gewählten Ergebnisse beruhen auf verschiedenen Prüfziel-Listen.")
        elif gewaehlt:
            liste = pruefziele.liste(gewaehlt[0]["pruefziele_liste"])
            laeufe = [(a, auswertungen.ergebnis(a, liste)) for a in gewaehlt]
            daten = zuordnung.vergleichen(laeufe, liste)
    return render_template(
        "vergleich.html",
        auswahl=auswahl,
        gewaehlt={a["token"] for a in gewaehlt},
        daten=daten,
        laeufe=laeufe,
        liste=liste,
        max_vergleich=MAX_VERGLEICH,
    )


# Prüfziel-Liste


@bp.route("/pruefziele")
@login_required
def pruefziel_liste():
    schluessel = request.args.get("liste", pruefziele.STANDARD)
    if schluessel not in pruefziele.DATEIEN:
        abort(404)
    return render_template("pruefziele.html", liste=pruefziele.liste(schluessel))
