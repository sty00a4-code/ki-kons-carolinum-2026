import pdfplumber
from openai import OpenAI
import requests
import base64
import glob
import json
import fitz
from pandas import json_normalize
import matplotlib.pyplot as plt

from transformers import pipeline
from PIL import Image
import requests
import torch

import io

from pathlib import Path

from PIL import Image

import base64

import pandas as pd

import json

client = OpenAI(
    api_key="sk-hmb6GIEX2f_-TD6PVdiTPQ",
    base_url="https://litellm.s.studiumdigitale.uni-frankfurt.de/v1/"
)

lernziele = []
vorlesung = []

# JSON-Datei laden
"""
with open('lernziele.json', 'r', encoding='utf-8') as file:
    lernziele = json.load(file)
"""
with open('lernziele_umstrukturiert.json', 'r', encoding='utf-8') as file:
    lernziele = json.load(file)

with open('vorlesung.json', 'r', encoding='utf-8') as file:
    vorlesung = json.load(file)

vorlesungsInhaltTXT = Path("vorlesungFull.txt").read_text(encoding="utf-8")


jsonPromptAnswer = []
lernzieleInsgesamt = []
lernzieleAlle = []
lernzieleAnzahl = []

#selfPrompt = input("Geben Sie hier Ihre gewünschte Anfrage an die KI ein, die auf Basis der Zuordnung zwischen den Lernzielen und Ihren Folien vorgenommen werden soll!")


def find_key(obj, key): #Felder in der JSON abrufen
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                yield v
            yield from find_key(v, key)
    elif isinstance(obj, list):
        for item in obj:
            yield from find_key(item, key)

ids = find_key(lernziele, "id")
beschreibungen = find_key(lernziele, "beschreibung")

#print(len(list(ids)))
#print(len(list(beschreibungen)))

beschreibungenListe = list(beschreibungen)
lernzielIDs = list(ids)

AI_Bewertung = []

i = 0
for lernzielID in lernzielIDs:

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": [{"type": "text", "text": "Du bist ein Dozent der Zahnmedizin und prüfst, welche Lernziele durch eine Vorlesungsfolie tatsächlich abgedeckt werden. Du arbeitest streng und konservativ: Eine falsche Zuordnung ist schlimmer als eine fehlende."}]
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Beschreibung: " + beschreibungenListe[i]},

                    {"type": "text", "text": "Vorlesungsinhalt: " + vorlesungsInhaltTXT},

                    {"type": "text",
                     "text": f"Entscheide ob die vorliegende Beschreibung im Vorlesungsinhalt enthalten ist."
                             f"Gebe nur ein JA oder NEIN zurück."},
                ]

            }],
        model="qwen3-30b-a3b-instruct-2507",  # Beispiel-Modell
        temperature=0.0
    )
    AI_Bewertung.append(chat_completion.choices[0].message.content)

    if chat_completion.choices[0].message.content is not None:
        promptAusgabe = f"Lernziel: {lernzielID}\n"+chat_completion.choices[0].message.content+f"\nBeschreibung: {beschreibungenListe[i]}"
        print(promptAusgabe)
    else:
        continue
    i+=1



datensaetzeLernzielAI_Bewertung_Beschreibung = [
    {"id": i, "beinhaltet": b, "beschreibung": e}
    for i, b, e in zip(lernzielIDs, AI_Bewertung, beschreibungenListe)
]

with open("LernzielBeinhaltetZuordnung.json", "w", encoding="utf-8") as f:
    json.dump(datensaetzeLernzielAI_Bewertung_Beschreibung, f, ensure_ascii=False, indent=2)

with open("LernzielBeinhaltetZuordnung.json") as file:
    data = json.load(file)
    df = json_normalize(data)
    df.to_excel("LernzielBeinhaltetZuordnung.xlsx", index=False)


"""
for folie in vorlesung:
        folien_nr = folie["folien-nr"]
        textinhalt = folie["textinhalt"]
        bildinterpretation = folie["bildinterpretation"]

        chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": [{"type": "text", "text": "Du bist ein Dozent der Zahnmedizin"}]
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": json.dumps(lernziele)},
                            {
                                "type": "text",
                                "text": "Textinhalt: "+textinhalt
                            },{
                                "type": "text",
                                "text": "Bild:" + bildinterpretation
                            },

                            {"type": "text", "text": f"Ordne den Folien die passenden Lernziele zu. Ordne dem Textinhalt und dem Bild, die passenden Lernziele zu.  Achte darauf, dass das Lernziel auch wirklich in Bild oder Textinhalt gelehrt wird. Falls dies nicht der Fall ist, dann keine Zuordnung vornehmen."
                                                     f" Liste dabei nur aufeinanderfolgend, die Lernziel-IDs auf. Verzichte auf Erklärungen, Sätze oder Bezeichnungen."},
                        ]

                    }],
                model="qwen3-30b-a3b-instruct-2507",  # Beispiel-Modell
                temperature=0.0
            )

        if chat_completion.choices[0].message.content is not None:
            promptAusgabe = f"Folien Nr: {folien_nr}\n"+chat_completion.choices[0].message.content
        else:
            continue

        strOutput = promptAusgabe.split('\n')
        print(strOutput)
        for lernzielID in strOutput[1:]:
            lernzieleAlle.append(lernzielID)
            if lernzielID not in lernzieleInsgesamt:
                lernzieleInsgesamt.append(lernzielID)
        tempFolieJson = {"folien-nr": strOutput[0], "Zuordnung": strOutput[1:]}
        jsonPromptAnswer.append(tempFolieJson)
        print(promptAusgabe)


for lernzielID in lernzieleInsgesamt:
    lernzieleAnzahl.append(lernzieleAlle.count(lernzielID))

print("Lernziele Insgesamt: ")
print(lernzieleInsgesamt)
print(lernzieleAlle)
print(lernzieleAnzahl)

with open("FolienUndLernzieleZuordnung.json", "w", encoding="utf-8") as file:
    json.dump(jsonPromptAnswer, file, indent=2, ensure_ascii=False)


with open("FolienUndLernzieleZuordnung.json") as file:
    data = json.load(file)
    df = json_normalize(data)
    df.to_excel("folienUndLernziele.xlsx", index=False)


# Zeichnen
px = 1/plt.rcParams['figure.dpi']  # pixel in inches
plt.figure(figsize=(1920*px,1080*px))
colors = ['red', 'green', 'blue', 'orange']  # ein Farbwert pro Säule
#counts.plot(kind='bar', color='skyblue')
plt.bar(lernzieleInsgesamt, lernzieleAnzahl, color=colors)
plt.xlabel('Lernziel')
plt.tick_params(axis='x', labelsize=6)  # Schriftgröße anpassen
plt.yticks(range(0, 90, 5))  # y-Achse in Schritten von 5 einstufen
plt.ylabel('Anzahl')
plt.title('Anzahl pro Lernziel')
plt.tight_layout()
plt.savefig("anzahlLernziele.jpg")
plt.show()
"""