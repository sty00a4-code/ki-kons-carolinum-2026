import os
import subprocess

import streamlit as st
import pandas as pd

import lernziel_preprocessing
import vorlesung_preprocessing

st.title("Lernziel/Prüfziel Vorlesungsabgleich")

auswahl = st.selectbox(
    "Wähle Sie eine Option aus:",
    ["Lernziele mit Vorlesung vergleichen", "Prüfziele mit Vorlesung vergleichen"]
)

# 1. Definiere den Zielordner (z.B. "meine_pdfs")
ziel_ordner_vorlesung = "projekt1/assets/Vorlesung"
ziel_ordner_lernziel = " "
ziel_ordner_prüfziel = " "



if auswahl == "Lernziele mit Vorlesung vergleichen":
    ziel_ordner_lernziel = "projekt1/assets/Lernziele"
    os.makedirs( ziel_ordner_lernziel, exist_ok=True)
else:
    ziel_ordner_prüfziel = "projekt1/assets/Prüfziele"
    os.makedirs(ziel_ordner_prüfziel, exist_ok=True)


# Datei-Uploader erstellen (optional mit Dateitypen-Einschränkung)
uploaded_vorlesung_file = st.file_uploader("Laden Sie Ihre Vorlesung als PDF hoch. Laden Sie dabei bitte nur ein Kapitel hoch:", type=["pdf"])
uploaded_lernziel_file = None
uploaded_prüfziel_file = None

volesungsFileName = ""

if uploaded_vorlesung_file is not None: vorlesungsFileName = uploaded_vorlesung_file.name

if auswahl == "Lernziele mit Vorlesung vergleichen": #Uploader für Vorlesung erstellen
    ziel_ordner_lernziel = "projekt1/assets/Lernziele"
    os.makedirs(ziel_ordner_lernziel, exist_ok=True)
    uploaded_lernziel_file = st.file_uploader("Laden Sie Ihre Lernziele als PDF hoch. Laden Sie dabei bitte nur ein Kapitel hoch:", type=["pdf"])
else:
    ziel_ordner_prüfziel = "projekt1/assets/Prüfziele"
    os.makedirs(ziel_ordner_prüfziel, exist_ok=True)
    uploaded_prüfziel_file = st.file_uploader("Laden Sie Ihre Prüfziele als PDF hoch. Laden Sie dabei bitte nur ein Kapitel hoch:", type=["pdf"])

if uploaded_vorlesung_file is not None: #Über den Uploader die Vorlesung hochladen in Ziel Ordner
    # Den Dateipfad im Zielordner zusammenbauen
    dateipfad = os.path.join(ziel_ordner_vorlesung, uploaded_vorlesung_file.name)

    # Datei speichern
    with open(dateipfad, "wb") as f:
        f.write(uploaded_vorlesung_file.getbuffer())

    st.success(f"Erfolgreich gespeichert im Ordner '{ziel_ordner_vorlesung}': **{uploaded_vorlesung_file.name}**")


if uploaded_lernziel_file is not None: #Über den Uploader die Lernziele hochladen in Ziel Ordner
    # Den Dateipfad im Zielordner zusammenbauen
    dateipfad = os.path.join(ziel_ordner_lernziel, uploaded_lernziel_file.name)

    # Datei speichern
    with open(dateipfad, "wb") as f:
        f.write(uploaded_lernziel_file.getbuffer())

    st.success(f"Erfolgreich gespeichert im Ordner '{ziel_ordner_lernziel}': **{uploaded_lernziel_file.name}**")

if uploaded_prüfziel_file is not None: #Über den Uploader die Prüfziele hochladen in Ziel Ordner
    # Den Dateipfad im Zielordner zusammenbauen
    dateipfad = os.path.join(ziel_ordner_prüfziel, uploaded_prüfziel_file.name)

    # Datei speichern
    with open(dateipfad, "wb") as f:
        f.write(uploaded_prüfziel_file.getbuffer())

    st.success(f"Erfolgreich gespeichert im Ordner '{ziel_ordner_prüfziel}': **{uploaded_prüfziel_file.name}**")


st.divider()

import os
os.environ["STREAMLIT_SERVER_ENABLE_FILE_WATCHER"] = "false"


if st.button("Vergleich starten..."):

    # Validierung: Prüfen, ob eine Eingabe da ist
    if auswahl == "Lernziele mit Vorlesung vergleichen":

        print("Test!")
        lernziel_preprocessing.pdf_in_einzelne_seiten_aufteilen("projekt1/assets/Vorlesung"+"/"+vorlesungsFileName, "projekt1/einzelne_seiten_vorlesung")

        vorlesung_preprocessing.vorlesungs_preprocessing()
    else:
        st.warning("Bitte gib zuerst einen Projektnamen ein!")



