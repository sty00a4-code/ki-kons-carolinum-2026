"""Lernziel/Prüfziel Vorlesungsabgleich als Flask-Anwendung.

Flask-Fassung von UI.py: Option wählen, Vorlesung als PDF hochladen und den
Vergleich starten. Der Vergleich läuft im Hintergrund. Danach zeigt die Seite
für jedes Lernziel, ob es in der Vorlesung enthalten ist.

Start aus dem Hauptordner des Repositories:

    pip install flask
    python projekt1/app.py

Danach im Browser http://127.0.0.1:5001 öffnen.
"""

import json
import os
import runpy
import shutil
import threading

import matplotlib
from flask import (
    Flask,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

import lernziel_preprocessing
import pruefziel_preprocessing
import vorlesung_preprocessing

# Die Skripte lesen und schreiben relativ zu diesem Ordner.
PROJEKT_ORDNER = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJEKT_ORDNER)

# Die Skripte laufen im Hintergrund, eine Grafik darf dort kein Fenster öffnen.
matplotlib.use("Agg")

OPTIONEN = {
    "lernziele": "Lernziele mit Vorlesung vergleichen",
    "pruefziele": "Prüfziele mit Vorlesung vergleichen",
}
ORDNER_VORLESUNG = "assets/Vorlesung"
ORDNER_PRUEFZIELE = "assets/Prüfziele"
ORDNER_SEITEN = "einzelne_seiten_vorlesung"

# Dateien, die der Vergleich schreibt
FOLIEN = "vorlesung.json"
ERGEBNIS = "LernzielBeinhaltetZuordnung.json"
EXCEL = "LernzielBeinhaltetZuordnung.xlsx"

app = Flask(__name__)
# Obergrenze für einen Upload, wie in Streamlit 200 MB
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

# Stand des letzten Vergleichs
stand = {"laeuft": False, "fehler": None, "gespeichert": [], "hinweis": None}


def dateiname(datei):
    """Liefert den Namen einer hochgeladenen Datei ohne Ordneranteil."""
    return os.path.basename(datei.filename or "")


def ist_pdf(datei):
    """Prüft, ob eine PDF-Datei hochgeladen wurde."""
    if datei is None:
        return False
    return dateiname(datei).lower().endswith(".pdf")


def speichern(datei, ordner):
    """Speichert eine hochgeladene Datei im Zielordner und liefert ihren Namen."""
    name = dateiname(datei)
    os.makedirs(ordner, exist_ok=True)
    datei.save(os.path.join(ordner, name))
    return name


def folien_pruefen():
    """Bricht ab, wenn die Auswertung der Vorlesung keine Folie geliefert hat."""
    with open(FOLIEN, encoding="utf-8") as datei:
        folien = json.load(datei)
    if not folien:
        meldung = "Die Auswertung hat keine Folien gefunden."
        raise RuntimeError(meldung)


def vergleichen(vorlesung_pfad):
    """Vergleicht die Vorlesung mit den Lernzielen, läuft im Hintergrund."""
    try:
        # Seiten einer früheren Vorlesung entfernen, dann die neue aufteilen
        shutil.rmtree(ORDNER_SEITEN, ignore_errors=True)
        lernziel_preprocessing.pdf_in_einzelne_seiten_aufteilen(
            vorlesung_pfad, ORDNER_SEITEN
        )
        # Text und Bild jeder Folie auswerten, Ergebnis in vorlesung.json
        vorlesung_preprocessing.vorlesungs_preprocessing()
        folien_pruefen()
        # Alle Folien als ein Text in vorlesungFull.txt
        runpy.run_path("vorlesungPartsToText.py")
        # Jedes Lernziel mit der ganzen Vorlesung vergleichen (JSON und Excel)
        runpy.run_path("vorlesung_lernziel_processing.py")
    except Exception as fehler:
        stand["fehler"] = f"{type(fehler).__name__}: {fehler}"
        raise
    finally:
        stand["laeuft"] = False


def pruefziele_aufbereiten(pruefziele_pfad):
    """Schreibt die Prüfziele der PDF als JSON und liefert den Hinweis dazu."""
    anzahl = pruefziel_preprocessing.pruefziele_speichern(pruefziele_pfad)
    if not anzahl:
        return "In der Datei wurde keine Tabelle mit Prüfzielen gefunden."
    return (
        f"{anzahl} Prüfziele stehen jetzt in {pruefziel_preprocessing.JSON}. "
        "Der Vergleich mit der Vorlesung folgt für Prüfziele noch."
    )


def ergebnis_lesen():
    """Liest das Ergebnis je Lernziel, sobald der Vergleich es geschrieben hat."""
    if stand["laeuft"] or stand["fehler"] or not os.path.exists(ERGEBNIS):
        return []
    with open(ERGEBNIS, encoding="utf-8") as datei:
        ziele = json.load(datei)
    for ziel in ziele:
        # Antwort des Modells einheitlich als "JA" oder "NEIN"
        antwort = str(ziel["beinhaltet"] or "")
        ziel["beinhaltet"] = antwort.strip().rstrip(".").upper()
    return ziele


@app.route("/", methods=["GET", "POST"])
def index():
    """Zeigt die Seite, speichert die Uploads und startet den Vergleich."""
    auswahl = request.form.get("auswahl", "lernziele")
    eingabefehler = None

    if request.method == "POST":
        vorlesung = request.files.get("vorlesung")
        pruefziele = request.files.get("pruefziele")
        if stand["laeuft"]:
            eingabefehler = "Es läuft bereits ein Vergleich."
        elif not ist_pdf(vorlesung):
            eingabefehler = "Bitte laden Sie Ihre Vorlesung als PDF hoch."
        elif auswahl == "pruefziele" and not ist_pdf(pruefziele):
            eingabefehler = "Bitte laden Sie Ihre Prüfziele als PDF hoch."
        else:
            name = speichern(vorlesung, ORDNER_VORLESUNG)
            stand.update(
                fehler=None, hinweis=None, gespeichert=[(ORDNER_VORLESUNG, name)]
            )
            if auswahl == "pruefziele":
                name_pruefziele = speichern(pruefziele, ORDNER_PRUEFZIELE)
                stand["gespeichert"].append((ORDNER_PRUEFZIELE, name_pruefziele))
                stand["hinweis"] = pruefziele_aufbereiten(
                    os.path.join(ORDNER_PRUEFZIELE, name_pruefziele)
                )
            else:
                # Die Lernziele stehen als JSON-Datei bereit, ein Upload entfällt.
                stand["laeuft"] = True
                threading.Thread(
                    target=vergleichen,
                    args=(os.path.join(ORDNER_VORLESUNG, name),),
                    daemon=True,
                ).start()
            return redirect(url_for("index"))

    return render_template(
        "index.html",
        optionen=OPTIONEN,
        auswahl=auswahl,
        eingabefehler=eingabefehler,
        stand=stand,
        ziele=ergebnis_lesen(),
    )


@app.route("/stand")
def stand_melden():
    """Meldet dem Skript der Seite, ob der Vergleich noch läuft."""
    return {"laeuft": stand["laeuft"]}


@app.route("/excel")
def excel():
    """Liefert die Excel-Datei mit dem Ergebnis zum Herunterladen."""
    return send_from_directory(PROJEKT_ORDNER, EXCEL, as_attachment=True)


if __name__ == "__main__":
    app.run(port=5001)
