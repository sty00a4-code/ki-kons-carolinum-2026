import pdfplumber
from openai import OpenAI
import requests
import base64
import glob
import json
import fitz

from transformers import pipeline
from PIL import Image
import requests
import torch

import io

from pathlib import Path

from PIL import Image

import base64

client = OpenAI(
    api_key=" ",
    base_url="https://litellm.s.studiumdigitale.uni-frankfurt.de/v1/"
)

def pdf_to_png(pdf_path, output_png_path, dpi=300):
    doc = fitz.open(pdf_path)
    page = doc[0]  # Erste Seite
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img.save(output_png_path, "PNG", dpi=(dpi, dpi))
    doc.close()

def encode_image_to_base64(image_path):
    """Kodiert ein Bild als Base64 für die OpenAI API."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")



# Pfad zum Ordner
folder_path = Path("/Users/abdul-haqhaqani/PycharmProjects/ki-kons-carolinum-2026/projekt1/einzelne_seiten_vorlesung")

# Durch alle PDFs iterieren
slideNr = 0

jsonVorlesung = []

for pdf_path in folder_path.glob("*.pdf"):
    folienText = ""
    with pdfplumber.open(
            pdf_path) as pdf:
        for page in pdf.pages:
            folienText = folienText + page.extract_text() + "/n"

            print(folienText)

    pdf_to_png(pdf_path, f"vorlesung_pngs/slide_{slideNr}.png", dpi=300)

    # Bild kodieren
    image_path = f"vorlesung_pngs/slide_{slideNr}.png"  # Pfad zu deinem Bild
    base64_image = encode_image_to_base64(image_path)

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": [{"type": "text", "text": "Du bist ein Dozent der Zahnmedizin"}]
            },
            {
                "role": "user",
                "content": [

                    {"type": "text", "text": "Interpretiere das Bild in einem Satz!"},
                    {
                        "type": "image_url",
                        "image_url": f"data:image/png;base64,{base64_image}"
                    }
                ]

            }],
        model="qwen3-omni-30b-a3b-instruct",  # Beispiel-Modell
        temperature=0.0
    )

    promptAusgabe = chat_completion.choices[0].message.content

    tempFolieJson = {"folien-nr": slideNr,"textinhalt": folienText, "bildinterpretation": promptAusgabe}

    jsonVorlesung.append(tempFolieJson)

    slideNr += 1

# JSON in eine Datei speichern
with open("vorlesung.json", "w", encoding="utf-8") as file:
    json.dump(jsonVorlesung, file, indent=2, ensure_ascii=False)
