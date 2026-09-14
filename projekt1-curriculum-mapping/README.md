# Curriculum-Mapping (Projekt 1, Kategorie 1)

Web-Anwendung, die die Prüfziele des IMPP-Gegenstandskatalogs (Orale Medizin
und systemische Aspekte) den Lernzielen zuordnet, mit Begründung und
tabellarischer Auswertung.

Ablauf: Prompt eingeben, Vorlesung und Lernziele als PDF hochladen, Modell und
Temperatur wählen. Die Anwendung sendet dem Modell die Prüfziel-Liste, die
Lernziele, die Vorlesung und den Prompt und liest die Antwort im Format
`Prüfziel;Abdeckung;Begründung;Lernziel-ID`.

## Seiten

| Seite | Inhalt |
| --- | --- |
| Neue Zuordnung | Prompt (vorausgefüllt mit dem Standard-Prompt), Upload von Vorlesung und Lernzielen, Modell, Temperatur |
| Aus Excel übernehmen | Ergebnis-Excel wie `ModellAuswertung Mistral.xlsx`, jedes Blatt wird ein Ergebnis |
| Ergebnisse | alle Durchläufe mit Status und Abdeckung, Auswahl für den Vergleich |
| Ergebnis | Kennzahlen, Tabelle mit Prüfziel, Abdeckung, Begründung und Lernziel-ID mit Filter und Suche; Ansichten nach Lernzielen, Antwort des Modells und Eingaben; Excel-Export; erneut ausführen |
| Vergleich | zwei bis vier Ergebnisse je Prüfziel nebeneinander, Übereinstimmung und Kappa nach Cohen |
| Prüfziele | die Prüfziel-Liste in der Form, die das Modell erhält |

Formulareingaben bleiben beim Neuladen als Entwurf im Browser erhalten
(`app/static/entwurf.js`), bis das Formular abgeschickt oder verworfen wird.
Dateien müssen nach dem Neuladen erneut ausgewählt werden.

## Einrichten und starten

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python -m scripts.init_db
venv/bin/flask --app app run --port 5002
```

`scripts.init_db` ohne Argument legt für den lokalen Testbetrieb den Login
`doktorand1` mit dem Passwort `doktorand1` an.
`venv/bin/python -m scripts.init_db NAME` legt einen Login mit abgefragtem
Passwort an.

## KI-Dienst

Die Anwendung nutzt einen OpenAI-kompatiblen Dienst, standardmäßig den
LiteLLM-Server der Goethe-Universität Frankfurt. Konfiguration über
Umgebungsvariablen:

| Variable | Bedeutung |
| --- | --- |
| `P1_LLM_API_KEY` | API-Schlüssel, ohne ihn startet keine Zuordnung (der Excel-Import funktioniert trotzdem) |
| `P1_LLM_URL` | Basis-URL, Standard `https://litellm.s.studiumdigitale.uni-frankfurt.de/v1` |
| `P1_LLM_MODELLE` | Modellauswahl, z. B. `mistral-large-3-675b-instruct-2512=Mistral Large 3,qwen3-235b-a22b=Qwen3 235B` |
| `P1_LLM_MAX_TOKENS` | optionale Obergrenze für die Länge der Antwort |
| `P1_MAX_ZEICHEN` | Obergrenze für alle Texte einer Anfrage, Standard 400000 |
| `P1_MAX_UPLOAD_MB` | Obergrenze in MB für alle Dateien eines Formulars, Standard 80 |
| `COOKIE_SECURE` | `1` beim Betrieb hinter HTTPS |

Ein Durchlauf läuft mit Streaming im Hintergrund. Die Ergebnisseite zeigt den
Fortschritt und lädt neu, sobald die Antwort vollständig ist. Höchstens zwei
Durchläufe laufen gleichzeitig. Ein Durchlauf, der zehn Minuten keine Daten
erhält, gilt als abgebrochen.

## Ergebnis-Excel übernehmen

Über die Seite oder die Kommandozeile:

```bash
venv/bin/python -m scripts.import_excel "ModellAuswertung Mistral.xlsx" \
    --lernziele NKLZLernziele242248.pdf \
    --vorlesung Vorlesung_1_OraleMedizinUndSystemischeAspekte.pdf
```

Mit der Lernziel-PDF zeigt die Tabelle den Wortlaut der Lernziele und markiert
IDs, die im Dokument nicht vorkommen. Dateien aus dem Excel-Export lassen sich
wieder importieren, auch nach manuellen Korrekturen.

## Prüfziel-Liste

`app/daten/pruefziele_orale_medizin.json` wird aus der Prüfziel-Tabelle und
dem IMPP-Katalog erzeugt (benötigt `pdftotext` aus Poppler):

```bash
venv/bin/python -m scripts.pruefziele_bauen "Tabelle Prüfziele.xlsx" \
    IMPPPrüfziele_OraleMedizinUndSystemischeAspekte.pdf
```

Schreibweise und Nummern stammen aus dem IMPP-Katalog. Zwei Nummern der
Tabelle weichen davon ab (Depression 4.12.2 statt 4.13.2,
Spurenelementstoffwechsel 10.6.2 statt 10.6.4), in Antworten werden beide
Varianten erkannt.

## Aufbau

| Datei | Aufgabe |
| --- | --- |
| `app/zuordnung.py` | Antwort lesen, Prüfzielen zuordnen, zählen, Tabelle, Vergleich und Kappa |
| `app/pruefziele.py` | Prüfziel-Liste laden, Zeilen einem Prüfziel zuordnen |
| `app/ki_dienst.py` | Anfrage an den KI-Dienst, Streaming im Hintergrund-Thread |
| `app/dokumente.py` | Text aus PDF- und Textdateien |
| `app/excel_import.py`, `app/export.py` | Excel lesen und schreiben |
| `app/auswertungen.py` | Auswertungen anlegen und laden |
| `app/formate.py` | Datum und Zahlen in deutscher Schreibweise |
| `app/auth.py`, `app/security.py` | Anmeldung, CSRF-Schutz, Tokens |
| `app/db.py`, `app/schema.sql` | SQLite-Datenbank |
| `app/routes.py`, `app/templates/`, `app/static/` | Seiten, Entwurf im Browser, Tabellenfilter |
| `scripts/` | Login anlegen, Ergebnis-Excel übernehmen, Prüfziel-Liste erzeugen |

## Test

```bash
venv/bin/python -m tests.selftest
```

Der Selbsttest läuft ohne Netzwerkzugriff gegen einen lokalen Test-Server für
den KI-Dienst und prüft Upload, Streaming, Tabelle, Export, Reimport, Vergleich
und die Fehlerfälle. Mit den Umgebungsvariablen `P1_TEST_EXCEL` (Ergebnis-Excel
mit drei Blättern) und `P1_TEST_LERNZIELE` (Lernziel-PDF, optional) prüft er
zusätzlich echte Dateien.

Die Codeprüfung (ruff, djLint, sqlfluff, stylelint) läuft über pre-commit, Aufruf
im App-Ordner:

```bash
uvx pre-commit run --all-files
```
