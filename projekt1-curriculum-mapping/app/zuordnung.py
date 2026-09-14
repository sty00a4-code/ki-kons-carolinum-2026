"""Antwort des Modells lesen und als Zuordnung aufbereiten.

Erwartet werden Zeilen im Format Prüfziel;Abdeckung;Begründung;Lernziel-ID.
lesen() toleriert übliche Abweichungen wie Markdown-Tabellen, Überschriften,
Aufzählungszeichen, Fettdruck oder eine vorangestellte Teilnummer ("VIII.").

auswerten() ordnet die Zeilen der Prüfziel-Liste zu und zählt die Abdeckung,
vergleichen() stellt mehrere Durchläufe gegenüber.
"""

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

# Stufen der Abdeckung
ABGEDECKT, TEILWEISE, NICHT = 2, 1, 0

_EBENEN = ("teil", "bereich", "gruppe")

_PRUEFZIEL = re.compile(r"^(?:(VIII|VI)\s*\.?\s*)?(\d{1,2}(?:\s*\.\s*\d{1,2}){0,4})\.?\s+(\S.*)$")
_LERNZIEL_ID = re.compile(r"(?<![\d.])\d{1,2}(?:\.\d{1,2}){1,4}(?![\d])")
_AUFZAEHLUNG = re.compile(r"^(?:[-*•+]\s+|\d+\)\s+)")
_TRENNER = re.compile(r"^[\s|:=\-\u2013]+$")
_DENKEN = re.compile(r"<think>.*?</think>", re.DOTALL)


@dataclass
class Zeile:
    teil: str | None
    nr: str
    name: str
    stufe: int
    begruendung: str
    lernziele: list = field(default_factory=list)
    eintrag: dict | None = None


def stufe(text):
    """Wandelt den Inhalt der Spalte Abdeckung in eine Stufe um."""
    t = re.sub(r"[*_()\[\]]", "", text or "").strip().lower()
    if not t or "nicht" in t or "kein" in t or t in {"-", "\u2013", "nein", "no", "o", "/"}:
        return NICHT
    if "teil" in t or "partiell" in t:
        return TEILWEISE
    if t.startswith("x") or "✓" in t or "✔" in t or t in {"ja", "yes", "abgedeckt"}:
        return ABGEDECKT
    return NICHT


def beginnt_mit_pruefziel(text):
    """Prüft, ob der Text mit Nummer und Name eines Prüfziels beginnt."""
    return bool(_PRUEFZIEL.match(_AUFZAEHLUNG.sub("", text)))


def _markup_weg(text):
    text = text.replace("**", "").replace("__", "")
    return re.sub(r"^#+\s*", "", text).strip()


def _ohne_hervorhebung(text):
    """Entfernt Hervorhebung und äußere Klammern, etwa bei "*(Keine Abdeckung)*"."""
    t = text.strip().strip("*_ ").strip()
    if t.startswith("(") and t.endswith(")"):
        t = t[1:-1].strip()
    return t


def lesen(text):
    """Zerlegt den Antworttext in (erkannte Zeilen, nicht zuordenbare Zeilen)."""
    text = _DENKEN.sub("", text or "")
    zeilen, uebrig = [], []
    teil = None
    for roh in text.splitlines():
        s = _AUFZAEHLUNG.sub("", _markup_weg(roh.strip()))
        if not s or _TRENNER.match(s):
            continue
        if "|" in s and ";" not in s:
            zellen = [z.strip() for z in s.strip("|").split("|")]
        elif ";" in s:
            zellen = [z.strip() for z in s.split(";")]
        else:
            # Zeilen ohne Spalten zählen nur als Überschrift eines Teils.
            if re.match(r"^VIII\b", s):
                teil = "VIII"
            elif re.match(r"^VI\b", s):
                teil = "VI"
            continue
        kopf = zellen[0].lower()
        if kopf.startswith(("prüfziel", "pruefziel")):
            continue
        treffer = _PRUEFZIEL.match(_AUFZAEHLUNG.sub("", zellen[0]))
        if not treffer:
            uebrig.append(roh.strip())
            continue
        zeilen.append(_zeile(treffer, zellen[1:], teil))
    return zeilen, uebrig


def _zeile(treffer, rest, teil):
    nr = re.sub(r"\s+", "", treffer.group(2))
    name = treffer.group(3).strip().rstrip(":").strip()
    abdeckung = rest[0] if rest else ""
    begruendung, ids = "", ""
    if len(rest) >= 3:
        begruendung = "; ".join(r for r in rest[1:-1] if r.strip())
        ids = rest[-1]
    elif len(rest) == 2:
        # Bei nur zwei Spalten fehlen entweder die IDs oder die Begründung.
        nur_ids = _LERNZIEL_ID.search(rest[1]) and not _LERNZIEL_ID.sub("", rest[1]).strip(" ,/")
        if nur_ids:
            ids = rest[1]
        else:
            begruendung = rest[1]
    # Längerer Text in der Abdeckungsspalte ist eine Begründung ohne Abdeckung.
    if len(abdeckung) > 12 and stufe(abdeckung) == NICHT and not abdeckung.lower().startswith("x"):
        begruendung = "; ".join(x for x in (abdeckung, begruendung) if x.strip())
        abdeckung = ""
    lernziele = list(dict.fromkeys(_LERNZIEL_ID.findall(ids)))
    if not lernziele and ids.strip():
        begruendung = " ".join(x for x in (begruendung, _ohne_hervorhebung(ids)) if x.strip())
    return Zeile(
        teil=treffer.group(1) or teil,
        nr=nr,
        name=name,
        stufe=stufe(abdeckung),
        begruendung=_ohne_hervorhebung(begruendung),
        lernziele=lernziele,
    )


def lernziele_aus_text(text):
    """Liest {Lernziel-ID: Wortlaut} aus dem Text eines NKLZ-Kapitels.

    Die ID steht am Zeilenanfang. Der Wortlaut endet an der Kompetenzstufe
    (1, 2, 3a, 3b), an Querverweisen wie "5; 6; 7" oder an der nächsten ID.
    Bei einem abweichenden Aufbau bleibt das Ergebnis leer.
    """
    ergebnis = {}
    aktuell, teile = None, []

    def ablegen():
        if aktuell and teile:
            wortlaut = re.sub(r"\s+", " ", " ".join(teile)).strip()
            if len(wortlaut) > 8:
                ergebnis.setdefault(aktuell, wortlaut[:600])

    for zeile in (text or "").splitlines():
        s = zeile.strip()
        treffer = re.match(r"^(\d{1,2}(?:\.\d{1,2}){1,3})(?:\s+(.*))?$", s)
        if treffer and ";" not in s:
            ablegen()
            aktuell, teile = treffer.group(1), []
            rest = (treffer.group(2) or "").strip()
            if rest:
                ende = re.search(r"\s(1|2|3a|3b)$", rest)
                teile.append(rest[: ende.start()] if ende else rest)
                if ende:
                    ablegen()
                    aktuell = None
            continue
        if aktuell is None:
            continue
        if (
            re.match(r"^(1|2|3a|3b)(\s|$)", s)
            or re.match(r"^\d+[a-z]?;", s)
            or s.startswith("[Seite")
        ):
            ablegen()
            aktuell = None
            continue
        if s:
            teile.append(s)
    ablegen()
    return ergebnis


@dataclass
class Ergebnis:
    """Ausgewertete Antwort eines Durchlaufs.

    Die Zähler beziehen sich auf die Zeilen der Antwort. fehlend enthält die
    zählenden Prüfziele der Liste, zu denen keine Zeile vorliegt.
    """

    zeilen: list
    uebrig: list
    tabelle: list
    zaehlend: int
    abgedeckt: int
    teilweise: int
    nicht: int
    fehlend: list
    ohne_liste: list
    lernziele: list
    lernziel_texte: dict
    unbekannte_ids: set

    @property
    def anteil(self):
        return round(self.abgedeckt / len(self.zeilen) * 100) if self.zeilen else 0

    @property
    def ids_genannt(self):
        return sum(1 for lz in self.lernziele if lz["anzahl"])

    @property
    def ungenutzt(self):
        """Lernziele aus dem Dokument, die keinem Prüfziel zugeordnet sind."""
        return [lz for lz in self.lernziele if not lz["anzahl"]]


def auswerten(text, liste, lernziele_text=""):
    """Ordnet die Zeilen einer Antwort der Prüfziel-Liste zu und zählt die Abdeckung."""
    zeilen, uebrig = lesen(text)
    for z in zeilen:
        z.eintrag = liste.finde(z.teil, z.nr, z.name)

    je_eintrag = defaultdict(list)
    ohne_liste = []
    for z in zeilen:
        if z.eintrag:
            je_eintrag[z.eintrag["schluessel"]].append(z)
        else:
            ohne_liste.append(z)

    stufen = Counter(z.stufe for z in zeilen)
    fehlend = [e for e in liste.zaehlend if e["schluessel"] not in je_eintrag]

    texte = lernziele_aus_text(lernziele_text)
    bekannt = set(texte) or set(_LERNZIEL_ID.findall(lernziele_text or ""))
    alle_ids = Counter()
    je_id = defaultdict(list)
    for z in zeilen:
        if z.stufe == NICHT:
            continue
        for lid in z.lernziele:
            alle_ids[lid] += 1
            je_id[lid].append(z)
    unbekannt = {lid for lid in alle_ids if bekannt and lid not in bekannt}

    lernziele = [
        {
            "id": lid,
            "text": texte.get(lid, ""),
            "anzahl": alle_ids[lid],
            "zeilen": je_id[lid],
            "unbekannt": lid in unbekannt,
        }
        for lid in sorted(alle_ids, key=_id_sortierung)
    ]
    # Nicht zugeordnete Lernziele der untersten Ebene aus dem Dokument
    lernziele.extend(
        {"id": lid, "text": texte[lid], "anzahl": 0, "zeilen": [], "unbekannt": False}
        for lid in sorted(set(texte) - set(alle_ids), key=_id_sortierung)
        if lid.count(".") >= 3
    )

    return Ergebnis(
        zeilen=zeilen,
        uebrig=uebrig,
        tabelle=_tabelle(liste, je_eintrag, ohne_liste),
        zaehlend=len(liste.zaehlend),
        abgedeckt=stufen[ABGEDECKT],
        teilweise=stufen[TEILWEISE],
        nicht=stufen[NICHT],
        fehlend=fehlend,
        ohne_liste=ohne_liste,
        lernziele=lernziele,
        lernziel_texte=texte,
        unbekannte_ids=unbekannt,
    )


def _id_sortierung(lid):
    return tuple(int(x) for x in lid.split("."))


def _koepfe(offen, eintrag):
    """Liefert die offenen Kopfzeilen nach einem neuen Teil, Bereich oder einer Gruppe."""
    tiefe = _EBENEN.index(eintrag["ebene"])
    return [*(k for k in offen if _EBENEN.index(k["ebene"]) < tiefe), eintrag]


def _tabelle(liste, je_eintrag, ohne_liste):
    """Liefert die Zeilen der Ergebnistabelle in der Reihenfolge der Prüfziel-Liste.

    Kopfzeilen für Teil, Bereich und Gruppe erscheinen nur über belegten Zeilen.
    """
    ausgabe = []
    offen = []
    for e in liste.eintraege:
        if e["ebene"] != "pruefziel":
            offen = _koepfe(offen, e)
            continue
        treffer = je_eintrag.get(e["schluessel"], [])
        if not treffer and e.get("unterpunkte"):
            continue
        ausgabe.extend({"art": kopf["ebene"], "eintrag": kopf} for kopf in offen)
        offen = []
        if treffer:
            ausgabe.extend({"art": "zeile", "eintrag": e, "zeile": z} for z in treffer)
        else:
            ausgabe.append({"art": "fehlt", "eintrag": e})
    if ohne_liste:
        ausgabe.append(
            {"art": "teil", "eintrag": {"nr": "", "name": "Nicht in der Prüfziel-Liste"}}
        )
        ausgabe.extend({"art": "zeile", "eintrag": None, "zeile": z} for z in ohne_liste)
    return ausgabe


def kappa(a, b):
    """Berechnet Kappa nach Cohen für zwei gleich lange Listen von Stufen."""
    n = len(a)
    if not n:
        return None
    beobachtet = sum(x == y for x, y in zip(a, b, strict=True)) / n
    ca, cb = Counter(a), Counter(b)
    erwartet = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if erwartet >= 1:
        return 1.0 if beobachtet == 1 else None
    return (beobachtet - erwartet) / (1 - erwartet)


def vergleichen(laeufe, liste):
    """Stellt mehrere Durchläufe je Prüfziel gegenüber.

    laeufe ist eine Liste von (Auswertung, Ergebnis). Die Rückgabe enthält die
    Vergleichstabelle und die Übereinstimmung für jedes Paar von Durchläufen.
    """
    je_lauf = []
    for _, ergebnis in laeufe:
        erste = {}
        for z in ergebnis.zeilen:
            if z.eintrag and z.eintrag["schluessel"] not in erste:
                erste[z.eintrag["schluessel"]] = z
        je_lauf.append(erste)

    zeilen, gleich = [], 0
    offen = []
    for e in liste.eintraege:
        if e["ebene"] != "pruefziel":
            offen = _koepfe(offen, e)
            continue
        zellen = [lauf.get(e["schluessel"]) for lauf in je_lauf]
        if e.get("unterpunkte") and not any(zellen):
            continue
        werte = {z.stufe if z else None for z in zellen}
        einig = len(werte) == 1 and None not in werte
        if not e.get("unterpunkte"):
            gleich += einig
        zeilen.extend({"art": kopf["ebene"], "eintrag": kopf} for kopf in offen)
        offen = []
        zeilen.append({"art": "zeile", "eintrag": e, "zellen": zellen, "einig": einig})

    paare = []
    for i in range(len(laeufe)):
        for j in range(i + 1, len(laeufe)):
            gemeinsam = [
                e["schluessel"]
                for e in liste.zaehlend
                if e["schluessel"] in je_lauf[i] and e["schluessel"] in je_lauf[j]
            ]
            a = [je_lauf[i][s].stufe for s in gemeinsam]
            b = [je_lauf[j][s].stufe for s in gemeinsam]
            uebereinstimmung = sum(x == y for x, y in zip(a, b, strict=True))
            paare.append(
                {
                    "a": laeufe[i][0],
                    "b": laeufe[j][0],
                    "gemeinsam": len(gemeinsam),
                    "gleich": uebereinstimmung,
                    "anteil": round(uebereinstimmung / len(gemeinsam) * 100) if gemeinsam else 0,
                    "kappa": kappa(a, b),
                }
            )
    return {"zeilen": zeilen, "gleich": gleich, "zaehlend": len(liste.zaehlend), "paare": paare}
