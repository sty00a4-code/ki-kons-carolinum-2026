"""Prüfziel-Listen aus dem Text einer Datei."""

import pytest

from app import pruefziele
from app.pruefziele import Eintrag, Liste

# Auszug im Format des IMPP-Katalogs mit Querverweisen, Unterpunkten und einer Seitenzahl
IMPP_AUSZUG = """\
Gegenstandskatalog Zahnmedizin
VI Erkrankungen
VI.1 Erkrankungen der Zähne (2.1)
VI.1.1 Zahnhartsubstanzen
VI.1.1.1 Karies (2.1.1, 2.1.2)
VI.1.1.2 Erosion, Abrasion, Attrition
VI.1.1.2.1 Erosion durch Säuren
VI.1.1.3 ab
12
1.1.4 Zeile ohne Teil, etwa aus dem Inhaltsverzeichnis
VIII Übergeordnete Kompetenzen
VIII.4.5.7 Behinderung und Gesundheit (4.5) ........ 31
"""


def _kurz(eintraege: list[Eintrag]) -> list[tuple[str, str, str]]:
    return [(e["teil"], e["nr"], e["name"]) for e in eintraege]


@pytest.fixture(name="kapitel")
def fixture_kapitel() -> Liste:
    """Die Liste aus dem Auszug."""
    return pruefziele.aus_text(IMPP_AUSZUG, "Kapitel_1.pdf")


def test_liste_aus_datei_traegt_den_dateinamen(kapitel: Liste) -> None:
    """Der Titel einer Liste ist der Dateiname."""
    assert kapitel.titel == "Kapitel_1.pdf"


def test_ebenen_nach_der_tiefe_der_nummer(kapitel: Liste) -> None:
    """Teile, Bereiche, Gruppen und Prüfziele ergeben sich aus der Nummer."""
    ebenen = [(e["ebene"], e["nr"]) for e in kapitel.eintraege]
    assert ebenen == [
        ("teil", "VI"),
        ("bereich", "1"),
        ("gruppe", "1.1"),
        ("pruefziel", "1.1.1"),
        ("pruefziel", "1.1.2"),
        ("pruefziel", "1.1.2.1"),
        ("teil", "VIII"),
        ("pruefziel", "4.5.7"),
    ]


def test_querverweise_und_seitenzahlen_entfernt(kapitel: Liste) -> None:
    """Querverweise in Klammern, Punktleisten und Seitenzahlen gehören nicht zum Namen."""
    assert _kurz(kapitel.zaehlend) == [
        ("VI", "1.1.1", "Karies"),
        ("VI", "1.1.2.1", "Erosion durch Säuren"),
        ("VIII", "4.5.7", "Behinderung und Gesundheit"),
    ]


def test_pruefziel_mit_unterpunkten_zaehlt_nicht(kapitel: Liste) -> None:
    """Prüfziele mit Unterpunkten zählen nicht mit."""
    erosion = next(e for e in kapitel.pruefziele if e["nr"] == "1.1.2")
    assert erosion["unterpunkte"]
    assert erosion not in kapitel.zaehlend


def test_ohne_teil_zaehlen_alle_nummern() -> None:
    """Nennt die Datei keinen Teil, zählen alle Zeilen mit Nummer und Name."""
    liste = pruefziele.aus_text("1.1.1 Karies\n1.1.2 Erosion\nSeite 3\n", "eigene.txt")
    assert _kurz(liste.zaehlend) == [("", "1.1.1", "Karies"), ("", "1.1.2", "Erosion")]


def test_ohne_teil_zaehlt_keine_einzelne_zahl() -> None:
    """Ohne Teil gilt eine Zeile mit nur einer Zahl als Aufzählung im Fließtext."""
    text = "1 Einleitung\n3 Patienten wurden untersucht\n1.1 Karies\n1.1.1 Initialkaries\n"
    liste = pruefziele.aus_text(text, "eigene.txt")
    assert _kurz(liste.eintraege) == [("", "1.1", "Karies"), ("", "1.1.1", "Initialkaries")]


def test_unterpunkte_auch_ueber_mehrere_ebenen() -> None:
    """Ein Prüfziel hat Unterpunkte, wenn darunter eine längere Nummer desselben Teils steht."""
    text = (
        "VI.1.1.1 Karies\nVI.1.1.1.1 Initialkaries\nVI.1.1.2 Erosion\nVIII.1.1.2.1 Anderer Teil\n"
    )
    liste = pruefziele.aus_text(text, "eigene.txt")
    unterpunkte = {e["nr"]: e["unterpunkte"] for e in liste.pruefziele}
    assert unterpunkte == {"1.1.1": True, "1.1.1.1": False, "1.1.2": False, "1.1.2.1": False}


def test_text_fuer_das_modell_laesst_sich_wieder_einlesen(kapitel: Liste) -> None:
    """Der Text für das Modell ergibt beim Einlesen dieselben Prüfziele."""
    eingelesen = pruefziele.aus_text(kapitel.text_fuer_modell(), "Liste.txt")
    assert _kurz(eingelesen.zaehlend) == _kurz(kapitel.zaehlend)


def test_text_ohne_pruefziele_ergibt_leere_liste() -> None:
    """Fließtext ohne Nummern ergibt keine zählenden Prüfziele."""
    assert not pruefziele.aus_text("Ein Text ohne Nummern.\nNoch eine Zeile.", "x.txt").zaehlend


def test_aehnlichkeit_leerer_namen() -> None:
    """Ein fehlender Name ist keinem anderen ähnlich."""
    assert pruefziele.aehnlichkeit("", "Karies") == 0.0
    assert pruefziele.aehnlichkeit(None, None) == 0.0
