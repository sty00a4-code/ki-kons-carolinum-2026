from openai import OpenAI
import requests
import base64
import glob


import fitz

from transformers import pipeline
from PIL import Image
import requests
import torch

import io

client = OpenAI(
    api_key=" ",
    base_url="https://litellm.s.studiumdigitale.uni-frankfurt.de/v1/"
)
"""
response = requests.get(
    "https://litellm.s.studiumdigitale.uni-frankfurt.de/v1/model/info",
    headers={"x-litellm-api-key": " "}
)


for modell in response.json()["data"]:
    name = modell["model_name"]
    vision = modell.get("model_info", {}).get("supports_vision", False)
    print(f"{name}: Vision={vision}")
"""
"""
bildpfad = "C:/DeineOrdner/rontgenbild.jpg"  # oder /home/user/bild.jpg

with open(bildpfad, "rb") as f:
    base64_str = base64.b64encode(f.read()).decode("utf-8")
"""

def pdf_zu_text(pfad):
    doc = fitz.open(pfad)
    return "\n".join([seite.get_text() for seite in doc])


prüfzieleTabelle = pdf_zu_text("assets/Prüfziele/PrüfzieleTabelle.pdf")

NKLZLernziele242248 = pdf_zu_text("assets/Lernziele/NKLZLernziele242248.pdf")

pdfFolien  = pdf_zu_text("assets/Vorlesung_1_OraleMedizinUndSystemischeAspekte.pdf")

tabelleAusfüllen  = pdf_zu_text("assets/tabelleAusfüllen.pdf")

"""
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": [{"type": "text", "text": "Du bist ein Dozent der Zahnmedizin"}]
        },
        {
            "role": "user",
            "content": [
                        {"type": "text", "text": prüfzieleTabelle},
                        {"type": "text", "text": NKLZLernziele242248},
                        {"type": "text", "text": "Liste mir alle Prüfziele aus dem Dokument auf, so wie sie auch aufgelistet sind. Überprüfe für jedes Prüfziel, ob dieses von Kompetenz, Lernzielen des zweiten Dokuments Orale Medizin und systemische Aspekte"
                                +" konkret abgdeckt wird. Falls ja, dann markiere das Prüfziel mit X und begründe dahinter. Sage mir in welcher Tabellenzeile aus dem zweiten Dokument die Prüfungsziele voraussichtlich abgedeckt werden."},
                        {"type": "text", "text": "Folgende Struktur sollen die Zeilen der Ergebnisliste haben: Prüfziele;Abdeckung;Begründung;Lernziel-ID_Kapitel . Die Infos in jeder Zeile sind mit Semikolone getrennt. Bitte Zeile für Zeile die Prüfziele durchgehen."}],


        }],
    model="qwen3-235b-a22b",  # Beispiel-Modell
    temperature=0.0
)
"""

# Alle Bilddateien aus einem Ordner holen (z.B. alle PNGs)
bild_pfade = sorted(glob.glob("assets/*.png"))  # sortiert, damit Reihenfolge stimmt

image_blocks = []
for pfad in bild_pfade:
    with open(pfad, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    image_blocks.append({
        "type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{b64}"}
    })


bild_pfade2 = sorted(glob.glob("assets/Vorlesung_2/*.png"))  # sortiert, damit Reihenfolge stimmt

image_blocks2 = []
for pfad in bild_pfade2:
    with open(pfad, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    image_blocks.append({
        "type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{b64}"}
    })


chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": [{"type": "text", "text": "Du bist ein Dozent der Zahnmedizin"}]
            },
            {
                "role": "user",
                "content": [

                    {"type": "text", "text": tabelleAusfüllen},

                    {"type": "text", "text": pdfFolien},

                    {"type": "text", "text": prüfzieleTabelle},

                    {"type": "text",
                     "text": "Ordne jedem Lernziel und Prüfziel aus der Tabelle mit den Lernziele, die passenden Seiten aus dem Foliensatz zu. Stelle die Abdeckung in einer Tabelle dar und trenne die Einträge mit einem Semikolon. Pro Lernziel sollst du eine Zeile in der Tabelle verwenden. "
                             "Füge nach jedem Lernziel und das Prüdziel getrennt mit einem Semikolon, eine kurze Begründung, warum das Lernziel und das Prüfziel von dem Foliensatz abgedeckt wird."}],

            }],
        model="openai-gpt-oss-120b",  # Beispiel-Modell
        temperature=0.0
)

print(chat_completion.choices[0].message.content)


"""
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": [{"type": "text", "text": "Du bist ein Dozent der Zahnmedizin"}]
        },
        {
            "role": "user",
            "content": [

                        {"type": "text", "text": prüfzieleTabelle},

                        *image_blocks2,

                        {"type": "text", "text": "Ordne jedem Prüfziel aus der Prüfzieltabelle, Folien zu, die das Prüfziel abdecken. Stelle die Abdeckung in einer Tabelle dar und trenne die Einträge mit einem Semikolon. Pro Prüfziel sollst du eine Zeile in der Tabelle verwenden. "
                                                 "Die passenden Foliennummern kommen rechts vom Prüfziel in dieselbe Zeile und getrennt per Semikolon. Analysiere hierzu auch die Bilder und Texte auf den Folien. Beachte dabei die Ergebnisliste deiner vorherigen Antwort."}],


        }],
    model="qwen3-omni-30b-a3b-instruct",  # Beispiel-Modell
    temperature=0.0
)
print(chat_completion.choices[0].message.content)
"""

"""
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": [{"type": "text", "text": "Du bist ein Dozent der Zahnmedizin"}]
        },
        {
            "role": "user",
            "content": [

                        {"type": "text", "text": prüfzieleTabelle},

                       *image_blocks,

                        {"type": "text", "text": "Analysiere die Bilder und orde Ihnen Prüfziele aus der Prüfzieltabelle zu. "
                                                 "Füge nach jedem Prüfziel getrennt mit einem Semikolon, eine kurze Begründung, warum das Prüfziel von dem Bild abgedeckt wird. Am Ende soll eine tabellenartige Struktur entstehen."}],


        }],
    model="mistral-large-3-675b-instruct-2512",  # Beispiel-Modell
    temperature=0.0
)
print(chat_completion.choices[0].message.content)
"""

def promptEval(prompt, folienDatei, lernzieleDatei, prüfzieleDatei):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": [{"type": "text", "text": "Du bist ein Dozent der Zahnmedizin"}]
            },
            {
                "role": "user",
                "content": [

                    {"type": "text", "text": pdf_zu_text(lernzieleDatei)},

                    {"type": "text", "text": pdf_zu_text(folienDatei)},

                    {"type": "text", "text": pdf_zu_text(prüfzieleDatei)},

                    {"type": "text",
                     "text": prompt}],

            }],
        model="openai-gpt-oss-120b",  # Beispiel-Modell
        temperature=0.0
    )

    return chat_completion.choices[0].message.content
