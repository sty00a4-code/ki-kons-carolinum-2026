"""Anbindung des KI-Dienstes und Ablauf einer Zuordnung im Hintergrund.

Der Dienst muss die OpenAI-kompatible Schnittstelle /chat/completions
anbieten. Konfiguration über Umgebungsvariablen:

P1_LLM_URL         Basis-URL, Standard ist STANDARD_URL
P1_LLM_API_KEY     API-Schlüssel, ohne ihn startet keine Zuordnung
P1_LLM_MODELLE     Modellauswahl als "modell-id=Anzeigename,..."
P1_LLM_MAX_TOKENS  Obergrenze für die Länge der Antwort

Die Anfrage läuft gestreamt in einem eigenen Thread. Der bisher empfangene
Text wird regelmäßig gespeichert, die Ergebnisseite fragt den Stand ab.
"""

import json
import os
import threading
import time
from http import HTTPStatus

import requests

from . import db, pruefziele

STANDARD_URL = "https://litellm.s.studiumdigitale.uni-frankfurt.de/v1"
SYSTEM = "Du bist ein Dozent der Zahnmedizin"

# Auswahl, solange P1_LLM_MODELLE nicht gesetzt ist.
STANDARD_MODELLE = [
    ("mistral-large-3-675b-instruct-2512", "Mistral Large 3"),
    ("qwen3-235b-a22b", "Qwen3 235B"),
    ("openai-gpt-oss-120b", "GPT-OSS 120B"),
]

MAX_TEMPERATUR = 2
MAX_GLEICHZEITIG = 2
ZWISCHENSTAND_SEKUNDEN = 3
VERBINDUNGS_TIMEOUT = 15
LESE_TIMEOUT = 300
# Durchläufe ohne Aktualisierung gelten danach als abgebrochen.
ABGEBROCHEN_NACH_MINUTEN = 10


class KiFehler(RuntimeError):
    """Fehler bei der Anfrage an den KI-Dienst."""


def basis_url():
    return os.environ.get("P1_LLM_URL", STANDARD_URL).rstrip("/")


def schluessel():
    return os.environ.get("P1_LLM_API_KEY", "").strip()


def bereit():
    return bool(schluessel())


def modelle():
    eigene = os.environ.get("P1_LLM_MODELLE", "").strip()
    if not eigene:
        return STANDARD_MODELLE
    paare = []
    for teil in eigene.split(","):
        mid, _, name = teil.partition("=")
        if mid.strip():
            paare.append((mid.strip(), name.strip() or mid.strip()))
    return paare or STANDARD_MODELLE


def modell_name(modell_id):
    return dict(modelle()).get(modell_id, modell_id)


def nachricht(auswertung):
    """Baut die Nutzernachricht aus Prüfziel-Liste, Lernzielen, Vorlesung und Prompt.

    Die Nummern der Dokumente entsprechen den Verweisen im Prompt.
    """
    liste = pruefziele.liste(auswertung["pruefziele_liste"])
    teile = [
        f"Dokument 1: Prüfziele {liste.titel}\n\n{liste.text_fuer_modell()}",
        f"Dokument 2: Lernziele ({auswertung['lernziele_name']})\n\n{auswertung['lernziele_text']}",
    ]
    if auswertung["vorlesung_text"]:
        teile.append(
            f"Dokument 3: Vorlesung ({auswertung['vorlesung_name']})\n\n"
            f"{auswertung['vorlesung_text']}"
        )
    teile.append(auswertung["prompt"])
    return "\n\n".join(teile)


def anfrage(auswertung):
    body = {
        "model": auswertung["modell"],
        "temperature": auswertung["temperatur"],
        "stream": True,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": nachricht(auswertung)},
        ],
    }
    grenze = os.environ.get("P1_LLM_MAX_TOKENS", "").strip()
    if grenze.isdigit():
        body["max_tokens"] = int(grenze)
    return body


def laufende(con):
    return con.execute(
        "select count(*) from auswertungen where status = 'laeuft' and aktualisiert_am >= ?",
        (db.vor_minuten(ABGEBROCHEN_NACH_MINUTEN),),
    ).fetchone()[0]


def verwaiste_beenden(con):
    """Markiert Durchläufe ohne Aktualisierung als abgebrochen, etwa nach einem Neustart.

    Liefert die Anzahl der beendeten Durchläufe.
    """
    cur = con.execute(
        "update auswertungen set status = 'fehler', fehler = ? "
        "where status = 'laeuft' and aktualisiert_am < ?",
        (
            f"Abgebrochen: {ABGEBROCHEN_NACH_MINUTEN} Minuten ohne Antwort vom KI-Dienst.",
            db.vor_minuten(ABGEBROCHEN_NACH_MINUTEN),
        ),
    )
    con.commit()
    return cur.rowcount


def starten(app, auswertung_id):
    thread = threading.Thread(
        target=_lauf, args=(app, auswertung_id), name=f"zuordnung-{auswertung_id}", daemon=True
    )
    thread.start()
    return thread


def _lauf(app, auswertung_id):
    con = db.verbindung(app.config["DATABASE"])
    try:
        auswertung = con.execute(
            "select * from auswertungen where id = ?", (auswertung_id,)
        ).fetchone()
        text, grund = abrufen(anfrage(auswertung), lambda t: _zwischenstand(con, auswertung_id, t))
        con.execute(
            "update auswertungen set status = 'fertig', rohantwort = ?, abbruch = ?, "
            "aktualisiert_am = ? where id = ?",
            (text, grund, db.jetzt(), auswertung_id),
        )
        con.commit()
    except KiFehler as exc:
        _fehler(con, auswertung_id, str(exc))
    except Exception as exc:
        app.logger.exception("Zuordnung %s fehlgeschlagen", auswertung_id)
        _fehler(con, auswertung_id, f"Unerwarteter Fehler ({type(exc).__name__}).")
    finally:
        con.close()


def abrufen(body, zwischenstand=None):
    """Sendet die Anfrage und liefert (Antworttext, finish_reason)."""
    kopf = {"Authorization": f"Bearer {schluessel()}", "Content-Type": "application/json"}
    try:
        antwort = requests.post(
            f"{basis_url()}/chat/completions",
            json=body,
            headers=kopf,
            stream=True,
            timeout=(VERBINDUNGS_TIMEOUT, LESE_TIMEOUT),
        )
    except requests.RequestException as exc:
        raise KiFehler(f"Der KI-Dienst ist nicht erreichbar ({type(exc).__name__}).") from exc

    with antwort:
        if antwort.status_code != HTTPStatus.OK:
            raise KiFehler(_fehlertext(antwort))
        art = antwort.headers.get("content-type", "")
        try:
            if "text/event-stream" not in art:
                wahl = antwort.json()["choices"][0]
                return (wahl.get("message") or {}).get("content") or "", wahl.get("finish_reason")
            return _strom_lesen(antwort, zwischenstand)
        except requests.RequestException as exc:
            raise KiFehler(
                f"Die Verbindung zum KI-Dienst ist abgerissen ({type(exc).__name__})."
            ) from exc
        except (ValueError, KeyError, IndexError) as exc:
            raise KiFehler("Der KI-Dienst hat eine unerwartete Antwort geschickt.") from exc


def _strom_lesen(antwort, zwischenstand):
    antwort.encoding = "utf-8"
    teile, grund = [], None
    zuletzt = time.monotonic()
    for zeile in antwort.iter_lines(decode_unicode=True):
        if not zeile or not zeile.startswith("data:"):
            continue
        daten = zeile.removeprefix("data:").strip()
        if daten == "[DONE]":
            break
        stueck = json.loads(daten)
        if stueck.get("error"):
            raise KiFehler(f"Der KI-Dienst meldet: {_kurz(stueck['error'])}")
        for wahl in stueck.get("choices") or []:
            teile.append((wahl.get("delta") or {}).get("content") or "")
            grund = wahl.get("finish_reason") or grund
        if zwischenstand and time.monotonic() - zuletzt >= ZWISCHENSTAND_SEKUNDEN:
            zwischenstand("".join(teile))
            zuletzt = time.monotonic()
    return "".join(teile), grund


def _fehlertext(antwort):
    try:
        meldung = _kurz(antwort.json().get("error") or antwort.text)
    except ValueError:
        meldung = _kurz(antwort.text)
    if antwort.status_code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
        return f"Der KI-Dienst hat den Schlüssel abgelehnt ({antwort.status_code})."
    return f"Der KI-Dienst antwortet mit Status {antwort.status_code}: {meldung}"


def _kurz(fehler):
    if isinstance(fehler, dict):
        fehler = fehler.get("message") or json.dumps(fehler, ensure_ascii=False)
    return str(fehler).strip()[:300]


def _zwischenstand(con, auswertung_id, text):
    con.execute(
        "update auswertungen set rohantwort = ?, aktualisiert_am = ? where id = ?",
        (text, db.jetzt(), auswertung_id),
    )
    con.commit()


def _fehler(con, auswertung_id, meldung):
    con.execute(
        "update auswertungen set status = 'fehler', fehler = ?, aktualisiert_am = ? where id = ?",
        (meldung, db.jetzt(), auswertung_id),
    )
    con.commit()
