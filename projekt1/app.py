"""Lernziel/Prüfziel Vorlesungsabgleich als Flask-Anwendung.

Flask-Fassung von UI.py: Option wählen, Vorlesung als PDF hochladen und den
Vergleich starten. Der Vergleich läuft im Hintergrund. Danach zeigt die Seite
die Grafik mit der Anzahl pro Lernziel und die Zuordnung der Lernziele zu den
Folien.

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
import vorlesung_preprocessing

# Die Skripte lesen und schreiben relativ zu diesem Ordner.
PROJEKT_ORDNER = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJEKT_ORDNER)

# Die Grafik entsteht als Datei, es öffnet sich kein Fenster.
matplotlib.use("Agg")

OPTIONEN = {
    "lernziele": "Lernziele mit Vorlesung vergleichen",
    "pruefziele": "Prüfziele mit Vorlesung vergleichen",
}
ORDNER_VORLESUNG = "assets/Vorlesung"
ORDNER_PRUEFZIELE = "assets/Prüfziele"
ORDNER_SEITEN = "einzelne_seiten_vorlesung"

# Dateien, die der Vergleich schreibt
ZUORDNUNG = "FolienUndLernzieleZuordnung.json"
EXCEL = "folienUndLernziele.xlsx"
GRAFIK = "anzahlLernziele.jpg"

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
        # Lernziele aus lernziele.json zuordnen, Excel-Datei und Grafik schreiben
        runpy.run_path("vorlesung_lernziel_processing.py")
    except Exception as fehler:
        stand["fehler"] = f"{type(fehler).__name__}: {fehler}"
        raise
    finally:
        stand["laeuft"] = False


def zuordnung_lesen():
    """Liest die Zuordnung der Lernziele zu den Folien, sobald sie vorliegt."""
    if stand["laeuft"] or stand["fehler"] or not os.path.exists(ZUORDNUNG):
        return []
    with open(ZUORDNUNG, encoding="utf-8") as datei:
        return json.load(datei)


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
                stand["hinweis"] = "Für Prüfziele gibt es noch keine Auswertung."
            else:
                # Die Lernziele stehen in lernziele.json, ein Upload entfällt.
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
        folien=zuordnung_lesen(),
        grafik=os.path.exists(GRAFIK),
    )


@app.route("/stand")
def stand_melden():
    """Meldet dem Skript der Seite, ob der Vergleich noch läuft."""
    return {"laeuft": stand["laeuft"]}


@app.route("/grafik")
def grafik():
    """Liefert die Grafik mit der Anzahl pro Lernziel."""
    return send_from_directory(PROJEKT_ORDNER, GRAFIK)


@app.route("/excel")
def excel():
    """Liefert die Excel-Datei mit der Zuordnung zum Herunterladen."""
    return send_from_directory(PROJEKT_ORDNER, EXCEL, as_attachment=True)


if __name__ == "__main__":
    app.run(port=5001)
