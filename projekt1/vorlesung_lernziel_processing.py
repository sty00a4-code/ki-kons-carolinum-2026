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

import json

client = OpenAI(
    api_key=" ",
    base_url="https://litellm.s.studiumdigitale.uni-frankfurt.de/v1/"
)

lernziele = []
vorlesung = []

# JSON-Datei laden
with open('lernziele.json', 'r', encoding='utf-8') as file:
    lernziele = json.load(file)

with open('vorlesung.json', 'r', encoding='utf-8') as file:
    vorlesung = json.load(file)


jsonPromptAnswer = []

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
                                "text": textinhalt
                            },{
                                "type": "text",
                                "text": bildinterpretation
                            },

                            {"type": "text", "text": f"Ordne der Folie, die passenden Lernziele zu. Nenne dabei zuerst die FolienNr: {folien_nr} und danach aufeinanderfolgend die passenden Lernziele. Bitte nur die Folien_nr und dann anschließend die Lernziele in einer Zeile."},
                        ]

                    }],
                model="qwen3-omni-30b-a3b-instruct",  # Beispiel-Modell
                temperature=0.0
            )

        promptAusgabe = chat_completion.choices[0].message.content

        strOutput = promptAusgabe.split('\n')
        print(strOutput)
        tempFolieJson = {"folien-nr": strOutput[0], "FolienUndLernzieleZuordnung": strOutput[1]}
        jsonPromptAnswer.append(tempFolieJson)
        print(promptAusgabe)

with open("FolienUndLernzieleZuordnung.json", "w", encoding="utf-8") as file:
    json.dump(jsonPromptAnswer, file, indent=2, ensure_ascii=False)

