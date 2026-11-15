"""Gemeinsame Hilfen der Tests: Testdateien, Testserver für den KI-Dienst, Abfragen."""

import http.server
import io
import json
import re
import sqlite3
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any, cast

from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from app import pruefziele
from app.config import STANDARD_BILDMODELLE, STANDARD_MODELLE
from app.db import get_db
from app.pruefziele import Liste

MB = 1024 * 1024
BENUTZER = "doktorand1"
PASSWORT = "richtig-und-lang"
API_SCHLUESSEL = "test-schluessel"
MODELL = STANDARD_MODELLE[0][0]
ZWEITES_MODELL = STANDARD_MODELLE[1][0]
BILDMODELL = STANDARD_BILDMODELLE[0][0]
HINTERGRUND_PRAEFIXE = ("zuordnung-", "folien-")
BILD = "Eine Folie mit Text auf weissem Grund."
# Konto in der Meldung des Testservers bei Status 429
UEBERLASTET_KONTO = "nutzer@example.org"
# Antworten je Folie beim Abgleich mit Lernzielen und mit Prüfzielen
LERNZIEL_ANTWORTEN = {
    1: "25.1.1.1\n25.2.1.5",
    2: "<think>Die Folie behandelt Schwangerschaft.</think>25.1.1.2, 25.9.9.9",
    3: "25.3.1.1",
    4: "keine",
}
PRUEFZIEL_ANTWORTEN = {1: "VI 1.2.4 Parodontitis", 2: "VI 1.2.5", 3: "VIII 99.9", 4: "keine"}

# Testdateien


def _maskieren(text: str) -> str:
    """Maskiert Sonderzeichen für einen PDF-Textstring."""
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def pdf_mit_seiten(seiten: Sequence[Sequence[str]]) -> bytes:
    """Erzeugt eine PDF-Datei mit Textebene und einer Seite je Zeilenliste (nur ASCII)."""
    objekte = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    kinder = []
    for zeilen in seiten:
        inhalt = (
            "BT /F1 10 Tf 40 800 Td 13 TL "
            + " ".join(f"({_maskieren(z)}) '" for z in zeilen)
            + " ET"
        )
        nr = len(objekte) + 1
        kinder.append(f"{nr} 0 R")
        objekte.append(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {nr + 1} 0 R >>"
        )
        objekte.append(f"<< /Length {len(inhalt)} >>\nstream\n{inhalt}\nendstream")
    objekte[1] = f"<< /Type /Pages /Kids [{' '.join(kinder)}] /Count {len(kinder)} >>"
    daten = b"%PDF-1.4\n"
    versaetze = []
    for nr, objekt in enumerate(objekte, 1):
        versaetze.append(len(daten))
        daten += f"{nr} 0 obj\n{objekt}\nendobj\n".encode("latin-1")
    xref = len(daten)
    daten += f"xref\n0 {len(objekte) + 1}\n0000000000 65535 f \n".encode()
    for versatz in versaetze:
        daten += f"{versatz:010d} 00000 n \n".encode()
    daten += (
        f"trailer\n<< /Size {len(objekte) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return daten


def mini_pdf(zeilen: Sequence[str]) -> bytes:
    """Erzeugt eine minimale PDF-Datei mit einer Seite."""
    return pdf_mit_seiten([zeilen])


LERNZIELE_PDF = mini_pdf(
    [
        "25 Orale Medizin und systemische Aspekte",
        "25.1 Die Absolventin kann Auswirkungen von Allgemeinerkrankungen darstellen.",
        (
            "25.1.1.1 wichtige relevante Erkrankungen erkennen und in der Therapieplanung "
            "beruecksichtigen. 2"
        ),
        "25.1.1.2 psychische Auffaelligkeiten erkennen und somatische Ursachen abklaeren. 3a",
        (
            "25.2.1.5 Wechselwirkungen von Arzneimitteln mit der zahnaerztlichen Behandlung "
            "beschreiben. 2"
        ),
        "25.3.1.1 Infektionskrankheiten und ihre Bedeutung fuer die Behandlung erlaeutern. 3a",
    ]
)
VORLESUNG_PDF = mini_pdf(
    [
        "Querschnittsbereich Z2: Orale Medizin und systemische Aspekte",
        "Diabetes mellitus, kardio- und zerebrovaskulaere Erkrankungen, Schwangerschaft",
        "Parodontitis als Manifestation einer systemischen Erkrankung",
    ]
)
FOLIEN_PDF = pdf_mit_seiten(
    [
        ["Diabetes mellitus und Parodontitis", "Wechselwirkungen in beide Richtungen"],
        ["Schwangerschaft", "Gingivitis in der Schwangerschaft"],
        ["Infektionskrankheiten", "Bedeutung fuer die Behandlung"],
        ["Vielen Dank fuer die Aufmerksamkeit"],
    ]
)


def modellantwort(liste: Liste) -> str:
    """Erzeugt eine Antwort im Format des Prompts mit typischen Abweichungen.

    Jedes dritte Prüfziel ist nicht abgedeckt, eine Lernziel-ID ist unbekannt
    und eine Zeile gehört zu keinem Prüfziel der Liste.
    """
    zeilen = [
        "<think>Ich gehe die Liste Zeile für Zeile durch.</think>",
        "Prüfziele;Abdeckung;Begründung;Lernziel-ID_Kapitel",
    ]
    teil = None
    for i, eintrag in enumerate(liste.zaehlend):
        if eintrag["teil"] != teil:
            teil = eintrag["teil"]
            titel = "Erkrankungen" if teil == "VI" else "Übergeordnete Kompetenzen"
            zeilen.append(f"**{teil} {titel}**")
        name = f"{eintrag['nr']} {eintrag['name']}"
        if i % 3 == 0:
            zeilen.append(f"{name}; ;Keine direkte Abdeckung im zweiten Dokument.;")
        else:
            ids = "25.1.1.1, 25.2.1.5" if i % 2 else "25.3.1.1"
            if i == 1:
                ids += ", 25.9.9.9"
            zeilen.append(f"{name};X;Begründung zu {eintrag['name']}.;{ids}")
    zeilen.append("99.9.9 Erfundenes Prüfziel;X;Steht nicht in der Liste.;25.1.1.1")
    return "\n".join(zeilen)


# Testserver für den KI-Dienst


@dataclass
class Anfrage:
    """Eine beim Testserver eingegangene Anfrage."""

    pfad: str
    auth: str | None
    body: dict[str, Any]


@dataclass
class KiZustand:
    """Steuert die Antworten des Testservers und sammelt die Anfragen."""

    # "ok", "401" (Schlüssel abgelehnt) oder "length" (abgeschnittene Antwort)
    modus: str = "ok"
    antwort: str = ""
    # Funktion body -> Antworttext (None: Status 500), sonst gilt antwort
    antwort_fuer: Callable[[dict[str, Any]], str | None] | None = None
    # so viele der nächsten Anfragen erhalten Status 429, mit Retry-After falls gesetzt
    ueberlastet: int = 0
    retry_after: str | None = None
    anfragen: list[Anfrage] = field(default_factory=list)

    def zuruecksetzen(self) -> None:
        """Stellt den Ausgangszustand wieder her."""
        self.modus = "ok"
        self.antwort = ""
        self.antwort_fuer = None
        self.ueberlastet = 0
        self.retry_after = None
        self.anfragen.clear()


class KiHandler(http.server.BaseHTTPRequestHandler):
    """Beantwortet /chat/completions je nach Zustand gestreamt oder mit Fehler."""

    def log_message(self, *_args: Any) -> None:
        """Unterdrückt die Ausgabe der Zugriffe."""

    def do_post(self) -> None:
        """Verarbeitet eine Anfrage an den KI-Dienst."""
        zustand = cast(KiServer, self.server).zustand
        laenge = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(laenge))
        zustand.anfragen.append(Anfrage(self.path, self.headers.get("Authorization"), body))
        if zustand.modus == "401":
            self._fehler(401, "Invalid API key")
            return
        if zustand.ueberlastet:
            zustand.ueberlastet -= 1
            kopf = {"Retry-After": zustand.retry_after} if zustand.retry_after else {}
            self._fehler(429, f"Rate limit exceeded for user: {UEBERLASTET_KONTO}", kopf)
            return
        text = zustand.antwort_fuer(body) if zustand.antwort_fuer else zustand.antwort
        if text is None:
            self._fehler(500, "Interner Fehler")
        elif body.get("stream"):
            self._streamen(text, abschneiden=zustand.modus == "length")
        else:
            wahl = {"index": 0, "message": {"content": text}, "finish_reason": "stop"}
            self._json(200, {"choices": [wahl]})

    # Die Standardbibliothek ruft die Methode unter diesem Namen auf.
    do_POST = do_post  # noqa: N815

    def _json(
        self, status: int, inhalt: dict[str, Any], kopf: dict[str, str] | None = None
    ) -> None:
        """Sendet eine JSON-Antwort, kopf ergänzt Header."""
        daten = json.dumps(inhalt).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(daten)))
        for name, wert in (kopf or {}).items():
            self.send_header(name, wert)
        self.end_headers()
        self.wfile.write(daten)

    def _fehler(self, status: int, meldung: str, kopf: dict[str, str] | None = None) -> None:
        """Sendet eine Fehlerantwort im Format des Dienstes."""
        self._json(status, {"error": {"message": meldung}}, kopf)

    def _streamen(self, text: str, *, abschneiden: bool) -> None:
        """Sendet den Text in Stücken, bei abschneiden mit finish_reason length."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        grund = "length" if abschneiden else "stop"
        if abschneiden:
            text = text[: len(text) // 2]
        stuecke = [text[i : i + 400] for i in range(0, len(text), 400)]
        for nr, stueck in enumerate(stuecke):
            wahl = {"index": 0, "delta": {"content": stueck}, "finish_reason": None}
            if nr == len(stuecke) - 1:
                wahl["finish_reason"] = grund
            self.wfile.write(f"data: {json.dumps({'choices': [wahl]})}\n\n".encode())
            self.wfile.flush()
            time.sleep(0.01)
        self.wfile.write(b"data: [DONE]\n\n")


class KiServer(http.server.ThreadingHTTPServer):
    """Lokaler Testserver, der den KI-Dienst nachahmt."""

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), KiHandler)
        self.zustand = KiZustand()

    @property
    def url(self) -> str:
        """Basisadresse im Format von P1_LLM_URL."""
        return f"http://127.0.0.1:{self.server_address[1]}/v1"


@dataclass
class FolienDienst:
    """Antworten des Testservers für den Vorlesungsabgleich."""

    antworten: dict[int, str]
    # Folie, deren Zuordnung mit Status 500 fehlschlägt
    fehler_bei: int = 0
    folien: list[int] = field(default_factory=list)
    bilder: int = 0
    # alle Anfragen in der Reihenfolge des Eingangs
    bodies: list[dict[str, Any]] = field(default_factory=list)

    def __call__(self, body: dict[str, Any]) -> str | None:
        """Beantwortet eine Bildanfrage oder die Zuordnung einer Folie."""
        self.bodies.append(body)
        inhalt = body["messages"][1]["content"]
        if isinstance(inhalt, list):
            self.bilder += 1
            return BILD
        treffer = re.search(r"Folie (\d+) von \d+", inhalt)
        nr = int(treffer.group(1)) if treffer else 0
        if nr == self.fehler_bei:
            return None
        self.folien.append(nr)
        return self.antworten[nr]


@dataclass
class Lauf:
    """Ergebnis eines abgeschlossenen Durchlaufs oder Abgleichs."""

    token: str | None
    stand: dict[str, Any]
    anfragen: list[dict[str, Any]]


# Hilfen für Test-Client und Datenbank


def html_von(antwort: TestResponse) -> str:
    """Liefert den Text einer Antwort."""
    return antwort.get_data(as_text=True)


def csrf(client: FlaskClient, pfad: str) -> str:
    """Liest das CSRF-Token aus dem Formular einer Seite."""
    treffer = re.search(r'name="_csrf_token" value="([^"]+)"', html_von(client.get(pfad)))
    return treffer.group(1) if treffer else ""


def anmelden(client: FlaskClient, passwort: str = PASSWORT) -> TestResponse:
    """Meldet den Testbenutzer an."""
    daten = {"username": BENUTZER, "password": passwort, "_csrf_token": csrf(client, "/login")}
    return client.post("/login", data=daten)


def hintergrund_beenden(sekunden: float = 20.0) -> None:
    """Wartet, bis alle Hintergrund-Threads der Anwendung beendet sind."""
    for thread in threading.enumerate():
        if thread.name.startswith(HINTERGRUND_PRAEFIXE):
            thread.join(sekunden)


def abwarten(abfrage: Callable[[], dict[str, Any]], sekunden: float = 20.0) -> dict[str, Any]:
    """Fragt den Stand ab, bis der Durchlauf nicht mehr läuft oder die Zeit abgelaufen ist."""
    ende = time.monotonic() + sekunden
    stand = abfrage()
    while stand["status"] == "laeuft" and time.monotonic() < ende:
        time.sleep(0.02)
        stand = abfrage()
    hintergrund_beenden()
    return stand


def warten_bis_fertig(client: FlaskClient, token: str) -> dict[str, Any]:
    """Wartet auf das Ende einer Zuordnung und liefert den Stand."""
    return abwarten(lambda: client.get(f"/ergebnisse/{token}/stand").get_json())


def warten_bis_abgleich_fertig(client: FlaskClient, token: str) -> dict[str, Any]:
    """Wartet auf das Ende eines Vorlesungsabgleichs und liefert den Stand."""
    return abwarten(lambda: client.get(f"/folien/{token}/stand").get_json())


def _token_aus(antwort: TestResponse, bereich: str) -> str | None:
    """Liest das Token aus der Weiterleitung auf /<bereich>/<token>."""
    treffer = re.search(rf"/{bereich}/([A-Za-z0-9_-]{{16}})$", antwort.headers.get("Location", ""))
    return treffer.group(1) if treffer else None


def token_aus(antwort: TestResponse) -> str | None:
    """Liest das Token einer Zuordnung aus der Weiterleitung."""
    return _token_aus(antwort, "ergebnisse")


def abgleich_token(antwort: TestResponse) -> str | None:
    """Liest das Token eines Vorlesungsabgleichs aus der Weiterleitung."""
    return _token_aus(antwort, "folien")


def abfragen(app: Flask, sql: str, werte: Sequence[Any] = ()) -> list[sqlite3.Row]:
    """Führt eine Abfrage aus und liefert alle Zeilen."""
    with app.app_context():
        zeilen: list[sqlite3.Row] = get_db().execute(sql, werte).fetchall()
    return zeilen


def zahl(app: Flask, sql: str) -> int:
    """Liefert den ersten Wert einer Abfrage, etwa eine Anzahl."""
    return int(abfragen(app, sql)[0][0])


def ausfuehren(app: Flask, sql: str, werte: Sequence[Any] = ()) -> None:
    """Führt eine Änderung an der Datenbank aus."""
    with app.app_context():
        con = get_db()
        con.execute(sql, werte)
        con.commit()


def neue_zuordnung(client: FlaskClient, **ueberschreiben: Any) -> TestResponse:
    """Startet eine Zuordnung über das Formular unter /neu."""
    daten = {
        "_csrf_token": csrf(client, "/neu"),
        "prompt": "Liste mir alle Prüfziele auf und ordne die Lernziele zu.",
        "modell": MODELL,
        "temperatur": "0,5",
        "liste": pruefziele.STANDARD,
        "titel": "",
        "vorlesung": (io.BytesIO(VORLESUNG_PDF), "Vorlesung_1.pdf"),
        "lernziele": (io.BytesIO(LERNZIELE_PDF), "Lernziele_Kapitel_25.pdf"),
    }
    daten.update(ueberschreiben)
    return client.post("/neu", data=daten, content_type="multipart/form-data")


def neuer_abgleich(client: FlaskClient, **ueberschreiben: Any) -> TestResponse:
    """Startet einen Vorlesungsabgleich über das Formular unter /folien/neu."""
    daten = {
        "_csrf_token": csrf(client, "/folien/neu"),
        "ziel": "lernziele",
        "prompt": "Nenne die Lernziel-IDs, die auf der Folie gelehrt werden.",
        "modell": MODELL,
        "bildmodell": BILDMODELL,
        "temperatur": "0",
        "liste": pruefziele.STANDARD,
        "titel": "",
        "vorlesung": (io.BytesIO(FOLIEN_PDF), "Vorlesung_2.pdf"),
        "lernziele": (io.BytesIO(LERNZIELE_PDF), "Lernziele_Kapitel_25.pdf"),
    }
    daten.update(ueberschreiben)
    return client.post("/folien/neu", data=daten, content_type="multipart/form-data")


def uebernehmen(
    client: FlaskClient, datei: bytes, name: str, **ueberschreiben: Any
) -> TestResponse:
    """Übernimmt ein vorhandenes Ergebnis über /folien/import."""
    daten = {
        "_csrf_token": csrf(client, "/folien/import"),
        "ziel": "lernziele",
        "modell": MODELL,
        "liste": pruefziele.STANDARD,
        "titel": "",
        "ergebnis": (io.BytesIO(datei), name),
        "vorlesung": (io.BytesIO(FOLIEN_PDF), "Vorlesung_2.pdf"),
        "lernziele": (io.BytesIO(LERNZIELE_PDF), "Lernziele_Kapitel_25.pdf"),
    }
    daten.update(ueberschreiben)
    return client.post("/folien/import", data=daten, content_type="multipart/form-data")


def balkenwerte(client: FlaskClient, token: str) -> list[str]:
    """Liest die Zahlen der Balken in der Ansicht nach Zielen."""
    html = html_von(client.get(f"/folien/{token}?ansicht=ziele"))
    return re.findall(r'<span class="wert">(\d+)</span>', html)


# Lesen der Seiten


# Elemente ohne End-Tag; sie nehmen keinen Text auf.
LEERE_ELEMENTE = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "wbr"}
)


@dataclass
class Element:
    """Ein Element einer Seite mit seinen Klassen und dem enthaltenen Text."""

    tag: str
    klassen: frozenset[str]
    text: str = ""


class Seite(HTMLParser):
    """Liest eine Seite, damit Prüfungen nicht an der Formatierung des Markups hängen.

    ausgewaehlt enthält je Auswahlfeld den Wert der gewählten Option.
    """

    def __init__(self, html: str) -> None:
        super().__init__()
        self.ausgewaehlt: dict[str, str] = {}
        self._elemente: list[Element] = []
        self._offen: list[Element] = []
        self._auswahl: str | None = None
        self.feed(html)
        self.close()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Merkt sich das Element und die gewählte Option eines Auswahlfelds."""
        attribute = dict(attrs)
        if tag == "select":
            self._auswahl = attribute.get("name")
        elif tag == "option" and self._auswahl and "selected" in attribute:
            self.ausgewaehlt[self._auswahl] = attribute.get("value") or ""
        if tag not in LEERE_ELEMENTE:
            element = Element(tag, frozenset((attribute.get("class") or "").split()))
            self._elemente.append(element)
            self._offen.append(element)

    def handle_endtag(self, tag: str) -> None:
        """Schließt das zuletzt geöffnete Element mit diesem Tag."""
        if tag == "select":
            self._auswahl = None
        for stelle in range(len(self._offen) - 1, -1, -1):
            if self._offen[stelle].tag == tag:
                del self._offen[stelle:]
                break

    def handle_data(self, data: str) -> None:
        """Ergänzt den Text aller offenen Elemente."""
        for element in self._offen:
            element.text += data

    def texte(self, *klassen: str) -> list[str]:
        """Texte der Elemente mit allen angegebenen Klassen, Leerraum zusammengefasst."""
        gesucht = frozenset(klassen)
        return [" ".join(e.text.split()) for e in self._elemente if gesucht <= e.klassen]
