"""Vorlesungsabgleich: Wiederholen, Fortsetzen nach einem Abbruch, Prüfziele und Status 429."""

from types import SimpleNamespace

import pytest
from flask.testing import FlaskClient

from app.folien import lauf
from tests.hilfen import (
    BILDMODELL,
    PRUEFZIEL_ANTWORTEN,
    UEBERLASTET_KONTO,
    ZWEITES_MODELL,
    FolienDienst,
    KiZustand,
    Seite,
    abgleich_token,
    csrf,
    html_von,
    neuer_abgleich,
    neuer_pruefziel_abgleich,
    warten_bis_abgleich_fertig,
)


def _wiederholen(angemeldet: FlaskClient, token: str, **ueberschreiben: str) -> str | None:
    """Führt einen Abgleich erneut aus und liefert das Token des neuen Abgleichs."""
    daten = {
        "_csrf_token": csrf(angemeldet, f"/folien/{token}?ansicht=eingaben"),
        "modell": ZWEITES_MODELL,
        "bildmodell": BILDMODELL,
        "temperatur": "0,5",
        "prompt": "Nenne die passenden Lernziel-IDs.",
    }
    daten.update(ueberschreiben)
    return abgleich_token(angemeldet.post(f"/folien/{token}/wiederholen", data=daten))


@pytest.mark.usefixtures("folien_token")
def test_wiederholen_uebernimmt_bildbeschreibungen(
    angemeldet: FlaskClient, folien_token: str, dienst: FolienDienst
) -> None:
    """Mit gleichem Bildmodell werden die Bildbeschreibungen übernommen."""
    dienst.bilder = 0
    neu = _wiederholen(angemeldet, folien_token)
    assert neu is not None
    assert neu != folien_token
    assert warten_bis_abgleich_fertig(angemeldet, neu)["status"] == "fertig"
    assert dienst.bilder == 0
    assert dienst.bodies[-1]["temperature"] == 0.5


def test_wiederholen_ohne_bildmodell(
    angemeldet: FlaskClient, folien_token: str, dienst: FolienDienst
) -> None:
    """Ohne Bildmodell geht nur der Folientext in die Anfrage."""
    dienst.bilder = 0
    ohne = _wiederholen(angemeldet, folien_token, bildmodell="")
    assert ohne is not None
    warten_bis_abgleich_fertig(angemeldet, ohne)
    assert dienst.bilder == 0
    assert "Bild:" not in dienst.bodies[-1]["messages"][1]["content"]


def test_fortsetzen_nach_abbruch(angemeldet: FlaskClient, dienst: FolienDienst) -> None:
    """Nach einem Abbruch bei Folie 3 geht es mit Folie 3 weiter."""
    dienst.fehler_bei = 3
    abgebrochen = abgleich_token(neuer_abgleich(angemeldet, bildmodell=""))
    assert abgebrochen is not None
    stand = warten_bis_abgleich_fertig(angemeldet, abgebrochen)
    assert stand["status"] == "fehler"
    assert stand["fertig"] == 2
    assert stand["fehler"].startswith("Folie 3: "), stand
    assert "Fortsetzen" in html_von(angemeldet.get(f"/folien/{abgebrochen}"))

    dienst.fehler_bei, dienst.folien = 0, []
    angemeldet.post(
        f"/folien/{abgebrochen}/fortsetzen",
        data={"_csrf_token": csrf(angemeldet, f"/folien/{abgebrochen}")},
    )
    stand = warten_bis_abgleich_fertig(angemeldet, abgebrochen)
    assert stand["status"] == "fertig"
    assert dienst.folien == [3, 4], dienst.folien


def test_abgleich_mit_pruefzielen(angemeldet: FlaskClient, dienst: FolienDienst) -> None:
    """Der Abgleich mit Prüfzielen braucht keine Lernziel-Datei."""
    dienst.antworten = PRUEFZIEL_ANTWORTEN
    token = abgleich_token(neuer_pruefziel_abgleich(angemeldet))
    assert token is not None
    warten_bis_abgleich_fertig(angemeldet, token)
    inhalt = dienst.bodies[-1]["messages"][1]["content"]
    assert inhalt.startswith("Prüfziele (")
    assert "1.2.4 Parodontitis" in inhalt
    html = html_von(angemeldet.get(f"/folien/{token}"))
    assert ">VI 1.2.4</span>" in html
    assert ">VI 1.2.5</span>" in html
    assert "VIII 99.9" in Seite(html).texte("chip", "unbekannt")
    assert "Nach Prüfzielen" in html


@pytest.mark.parametrize(
    ("retry_after", "erwartet"),
    [
        ("7", 7.0),
        (None, lauf.WARTEN_BEI_UEBERLASTUNG),
        ("86400", lauf.MAX_WARTEN_SEKUNDEN),
    ],
)
@pytest.mark.usefixtures("dienst")
def test_wartet_nach_zu_vielen_anfragen(
    angemeldet: FlaskClient,
    ki_zustand: KiZustand,
    monkeypatch: pytest.MonkeyPatch,
    retry_after: str | None,
    erwartet: float,
) -> None:
    """Nach Status 429 wartet der Abgleich die verlangte Zeit, höchstens MAX_WARTEN_SEKUNDEN."""
    wartezeiten: list[float] = []
    monkeypatch.setattr(lauf, "WARTEN_BEI_UEBERLASTUNG", 60)
    monkeypatch.setattr(lauf, "time", SimpleNamespace(sleep=wartezeiten.append))
    ki_zustand.ueberlastet, ki_zustand.retry_after = 1, retry_after
    token = abgleich_token(neuer_abgleich(angemeldet))
    assert token is not None
    assert warten_bis_abgleich_fertig(angemeldet, token)["status"] == "fertig"
    assert wartezeiten == [erwartet]


@pytest.mark.usefixtures("dienst")
def test_bleibt_der_dienst_ueberlastet_endet_der_abgleich(
    angemeldet: FlaskClient, ki_zustand: KiZustand
) -> None:
    """Scheitert auch die Wiederholung an Status 429, endet der Abgleich mit eigener Meldung."""
    ki_zustand.ueberlastet = 2
    token = abgleich_token(neuer_abgleich(angemeldet))
    assert token is not None
    stand = warten_bis_abgleich_fertig(angemeldet, token)
    assert stand["status"] == "fehler"
    assert stand["fehler"].startswith("Folie 1: Der KI-Dienst nimmt gerade keine weiteren")
    assert UEBERLASTET_KONTO not in stand["fehler"]
