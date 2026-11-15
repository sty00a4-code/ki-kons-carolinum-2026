# Curriculum-Mapping (Projekt 1, Kategorie 1)

Web-Anwendung, die die Prüfziele des IMPP-Gegenstandskatalogs (Orale Medizin
und systemische Aspekte) den Lernzielen zuordnet, mit Begründung und
tabellarischer Auswertung.

Ablauf: Prompt eingeben, Vorlesung und Lernziele als PDF hochladen, Modell und
Temperatur wählen. Die Anwendung sendet dem Modell die Prüfziel-Liste, die
Lernziele, die Vorlesung und den Prompt und liest die Antwort im Format
`Prüfziel;Abdeckung;Begründung;Lernziel-ID`.

Der Vorlesungsabgleich geht eine Vorlesung Folie für Folie durch und zeigt,
welche Lernziele oder Prüfziele auf welcher Folie gelehrt werden und welche
auf keiner Folie vorkommen (siehe [Vorlesungsabgleich](#vorlesungsabgleich)).

## Seiten

| Seite | Inhalt |
| --- | --- |
| Neue Zuordnung | Prompt (vorausgefüllt mit dem Standard-Prompt), Upload von Vorlesung und Lernzielen, Modell, Temperatur |
| Aus Excel übernehmen | Ergebnis-Excel wie `ModellAuswertung Mistral.xlsx`, jedes Blatt wird ein Ergebnis |
| Ergebnisse | alle Durchläufe mit Status und Abdeckung, Auswahl für den Vergleich |
| Ergebnis | Kennzahlen, Tabelle mit Prüfziel, Abdeckung, Begründung und Lernziel-ID mit Filter und Suche; Ansichten nach Lernzielen, Antwort des Modells und Eingaben; Excel-Export; erneut ausführen |
| Vergleich | zwei bis vier Ergebnisse je Prüfziel nebeneinander, Übereinstimmung und Kappa nach Cohen |
| Prüfziele | die Prüfziel-Liste in der Form, die das Modell erhält |
| Vorlesungsabgleich | alle Abgleiche mit Status und Abdeckung; neuer Abgleich mit Vorlesung, Lernzielen oder Prüfzielen (eingebaute Liste oder eigene Datei), Modell, Bildmodell, Temperatur und Prompt; Übernahme fertiger Ergebnisse |
| Abgleich | Kennzahlen, Folien mit Vorschaubild, Bildbeschreibung und zugeordneten Zielen; Anzahl der Folien je Ziel als Balken; Antworten des Modells; Eingaben; Excel-Export; fortsetzen und erneut ausführen |

Formulareingaben bleiben beim Neuladen als Entwurf im Browser erhalten
(`app/static/entwurf.js`), bis das Formular abgeschickt oder verworfen wird.
Dateien müssen nach dem Neuladen erneut ausgewählt werden.

## Einrichten und starten

Voraussetzung ist Python 3.11 oder neuer.

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
| `P1_LLM_BILDMODELLE` | Modelle für die Bildbeschreibung im Vorlesungsabgleich, gleiches Format, Standard `qwen3-omni-30b-a3b-instruct` |
| `P1_LLM_MAX_TOKENS` | optionale Obergrenze für die Länge der Antwort |
| `P1_MAX_ZEICHEN` | Obergrenze für alle Texte einer Anfrage, Standard 400000 |
| `P1_MAX_UPLOAD_MB` | Obergrenze in MB für alle Dateien eines Formulars, Standard 80 |
| `P1_MAX_FOLIEN` | Obergrenze für die Seitenzahl einer Vorlesung im Vorlesungsabgleich, Standard 200 |
| `COOKIE_SECURE` | `1` beim Betrieb hinter HTTPS |

Ein Durchlauf läuft mit Streaming im Hintergrund. Die Ergebnisseite zeigt den
Fortschritt und lädt neu, sobald die Antwort vollständig ist. Höchstens zwei
Durchläufe laufen gleichzeitig, Vorlesungsabgleiche zählen mit. Ein Durchlauf,
der zehn Minuten keine Daten erhält, gilt als abgebrochen.

## Vorlesungsabgleich

Beim Anlegen speichert die Anwendung die PDF-Datei der Vorlesung und je Folie
den Text (pypdf) und ein Vorschaubild (pypdfium2). Ein Hintergrund-Thread
bearbeitet danach jede Folie einzeln:

1. Das Bildmodell beschreibt die gerenderte Folie in einem Satz
   („Interpretiere das Bild in einem Satz!“). Ohne Bildmodell entfällt dieser
   Schritt.
2. Das Modell erhält die Liste der Ziele, die Nummer der Folie, den Folientext,
   die Bildbeschreibung und den Prompt und nennt die passenden Lernziel-IDs
   oder Prüfziele (Teil und Nummer, z. B. `VI 1.2.4`).

Schlägt eine Anfrage fehl, wiederholt der Abgleich sie einmal. Meldet der
Dienst zu viele Anfragen (Status 429), wartet er vorher die verlangte Zeit,
höchstens zwei Minuten, ohne Angabe eine Minute. Jede Antwort wird sofort
gespeichert. Bricht ein
Abgleich ab, setzt „Fortsetzen“ bei der ersten offenen Folie wieder ein.
„Erneut ausführen“ legt einen neuen Abgleich mit derselben Vorlesung an und
übernimmt die Bildbeschreibungen, wenn das Bildmodell gleich bleibt.

Abgeglichen wird entweder mit den Lernzielen eines NKLZ-Kapitels (IDs wie
25.1.1.1; IDs mit Unterpunkten wie 25.1 sind Überschriften) oder mit
Prüfzielen. Die Prüfziele stammen aus einer eingebauten Liste oder aus einer
eigenen Datei (PDF, TXT oder MD), etwa einem Kapitel des IMPP-Katalogs. Aus der
Datei werden Zeilen mit Nummer und Name gelesen, etwa `VI.1.1.1 Karies` oder
`1.1.1 Karies`; Seitenzahlen und Fließtext bleiben außen vor. Die Datei mit den
Zielen darf höchstens `P1_MAX_ZEICHEN` Zeichen haben. Angaben, die nicht
in der Liste stehen, sind rot markiert und werden gesondert gezählt.

Fertige Ergebnisse lassen sich übernehmen: der Excel-Export eines Abgleichs
(Blatt „Folien“ mit den Spalten Folie und Lernziele oder Prüfziele) oder eine
JSON-Liste mit einem Objekt je Folie (Schlüssel `folien-nr` und `Zuordnung`,
optional eine Bildbeschreibung). Beginnt die Nummerierung bei 0, werden alle
Nummern um 1 erhöht. Die Nummer muss der Seite in der PDF-Datei entsprechen.

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
dem IMPP-Katalog erzeugt:

```bash
venv/bin/python -m scripts.pruefziele_bauen "Tabelle Prüfziele.xlsx" \
    IMPPPrüfziele_OraleMedizinUndSystemischeAspekte.pdf
```

Schreibweise und Nummern stammen aus dem IMPP-Katalog. Zwei Nummern der
Tabelle weichen davon ab (Depression 4.12.2 statt 4.13.2,
Spurenelementstoffwechsel 10.6.2 statt 10.6.4), in Antworten werden beide
Varianten erkannt.

## Aufbau

Die Anwendung ist eine Flask-App mit drei Blueprints: `auth`, `zuordnung`
(Prüfziele den Lernzielen zuordnen) und `folien` (Vorlesungsabgleich).
Gemeinsame Bausteine liegen direkt in `app/`.

| Datei | Aufgabe |
| --- | --- |
| `app/__init__.py` | App-Factory: Konfiguration, Blueprints, Fehlerseiten, Template-Filter |
| `app/config.py` | Einstellungen aus Umgebungsvariablen (KI-Dienst, Grenzen) |
| `app/db.py`, `app/schema.sql` | SQLite-Datenbank, Anlage und Migration |
| `app/auth.py`, `app/security.py` | Anmeldung, CSRF-Schutz, Tokens, Sicherheits-Header |
| `app/ki.py` | Anfragen an den KI-Dienst mit Streaming |
| `app/hintergrund.py` | Durchläufe im Hintergrund-Thread, Höchstzahl, Abbruch nach Zeitgrenze |
| `app/pruefziele.py` | Prüfziel-Listen laden oder aus einer Datei lesen, Zeilen einem Prüfziel zuordnen |
| `app/lernziele.py` | Lernziele eines NKLZ-Kapitels und Lernziel-IDs in Texten |
| `app/dokumente.py`, `app/eingaben.py` | Text aus PDF- und Textdateien, Prüfung der Formulareingaben |
| `app/excel.py`, `app/formate.py` | Bausteine für Excel, deutsche Schreibweise von Datum und Zahlen |
| `app/seiten.py`, `app/fehler.py` | gemeinsame Bausteine der Seiten, Fehler mit Meldung für die Oberfläche |
| `app/zuordnung/` | Antwort lesen, auswerten, Vergleich und Kappa, Excel-Import und -Export, Seiten |
| `app/folien/` | Folien aus der PDF-Datei, Liste der Ziele, Ablauf je Folie, Auswertung, Übernahme, Export, Seiten |
| `app/templates/`, `app/static/` | Seiten, Stylesheet, Skripte als ES-Module (Entwurf, Tabellenfilter, Fortschritt) |
| `scripts/` | Login anlegen, Ergebnis-Excel übernehmen, Prüfziel-Liste erzeugen |
| `tests/` | pytest-Tests mit lokalem Test-Server für den KI-Dienst |

Die Seiten enthalten kein eigenes Skript; `app/static/seiten.js` richtet alle
Bausteine über `data`-Attribute ein. Die Content Security Policy lässt deshalb
nur Skripte aus `app/static/` zu.

## Tests und Codeprüfung

```bash
venv/bin/pip install -r requirements-dev.txt
venv/bin/python -m pytest --cov
```

Die Tests laufen ohne Netzwerkzugriff gegen einen lokalen Test-Server für den
KI-Dienst und prüfen Upload, Streaming, Tabelle, Export, Reimport, Vergleich,
den Vorlesungsabgleich, die Sicherheit und die Fehlerfälle. Die Abdeckung muss
mindestens 95 % betragen. Mit den Umgebungsvariablen `P1_TEST_EXCEL`
(Ergebnis-Excel mit drei Blättern) und `P1_TEST_LERNZIELE` (Lernziel-PDF,
optional) prüft `tests/test_echte_dateien.py` zusätzlich echte Dateien.

Die Codeprüfung (ruff, djLint, sqlfluff, stylelint) läuft über pre-commit, Aufruf
im App-Ordner:

```bash
uvx pre-commit run --all-files
```

pre-commit prüft außerdem die Skripte mit ESLint und die Markdown-Dateien mit
markdownlint. Typen, Stil, Sicherheit und Abhängigkeiten:

```bash
venv/bin/python -m mypy
venv/bin/python -m pylint app scripts tests
venv/bin/python -m bandit -c pyproject.toml -r app scripts
venv/bin/python -m vulture
venv/bin/python -m pip_audit -r requirements.txt
```
