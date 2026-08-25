"""Erzeugt die Erklär-Schaubilder AUS CODE (matplotlib) -> docs/diagrams/.

    python -m scripts.make_diagrams

Erstellt Workflow-, Architektur-, Datenfluss- und Auswertungs-Schaubild als
SVG + PNG. Farben/Texte hier anpassbar – alles reproduzierbar aus Code.
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "diagrams"
)
os.makedirs(OUT, exist_ok=True)

BLUE, PURPLE, GREEN, RED, GREY = "#4a63b7", "#6b4bb7", "#2e7d32", "#b3261e", "#8a8a8a"


def _new():
    fig, ax = plt.subplots(figsize=(11, 4.4))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 4.4)
    ax.axis("off")
    return fig, ax


def _box(ax, x, y, w, h, text, color):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            linewidth=1.5,
            edgecolor=color,
            facecolor=color + "22",
        )
    )
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=9.5,
        color="#1c2230",
    )


def _arrow(ax, x1, y1, x2, y2, color=GREY, text=None):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="-|>",
            mutation_scale=14,
            linewidth=1.4,
            color=color,
        )
    )
    if text:
        ax.text(
            (x1 + x2) / 2,
            (y1 + y2) / 2 + 0.12,
            text,
            ha="center",
            fontsize=8,
            color=color,
        )


# Zusätzlich in die App kopieren -> Seite "/ablauf" zeigt die Schaubilder live an
STATIC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app",
    "static",
    "diagrams",
)
os.makedirs(STATIC, exist_ok=True)


def _save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".svg"), bbox_inches="tight")
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=130, bbox_inches="tight")
    fig.savefig(os.path.join(STATIC, name + ".png"), dpi=130, bbox_inches="tight")
    plt.close(fig)


def workflow():
    fig, ax = _new()
    ax.text(5.5, 4.15, "Rollen & Rechte", ha="center", fontsize=13, weight="bold")
    _box(
        ax,
        0.4,
        2.2,
        3.0,
        1.1,
        "Studierende/r\nnur ansehen (read-only)\n+ Demo-Bot",
        BLUE,
    )
    _box(
        ax,
        4.0,
        2.2,
        3.0,
        1.1,
        "Doktorand/in\nträgt für jede/n ein\nsieht alle (Klarnamen)",
        PURPLE,
    )
    _box(ax, 7.6, 2.2, 3.0, 1.1, "Demo-Bot\nnur eigene Daten\ndes Studierenden", GREEN)
    ax.text(
        5.5,
        1.4,
        "Studierende können sich NICHT gegenseitig sehen · nur der Doktorand trägt Leistungen ein · "
        "der Bot kennt ausschließlich die Daten der/des eingeloggten Studierenden.",
        ha="center",
        fontsize=9,
        color="#444",
        bbox={"boxstyle": "round,pad=0.4", "fc": "#eef1fb", "ec": "#c7d0ee"},
    )
    _save(fig, "workflow")


def architecture():
    fig, ax = _new()
    ax.text(
        5.5,
        4.15,
        "Architektur & Sicherheits-Schichten",
        ha="center",
        fontsize=13,
        weight="bold",
    )
    _box(ax, 0.4, 2.3, 2.2, 1.0, "Browser\n(Studierende /\nDoktoranden)", BLUE)
    _box(
        ax,
        3.3,
        2.3,
        3.0,
        1.0,
        "Flask-App\nLogin · Rollen · CSRF\nEigentümer-Prüfung",
        PURPLE,
    )
    _box(ax, 7.0, 2.3, 2.4, 1.0, "SQLite\nPseudonyme +\nzufällige Tokens", GREEN)
    _arrow(ax, 2.6, 2.8, 3.3, 2.8, text="HTTPS")
    _arrow(ax, 6.3, 2.8, 7.0, 2.8)
    ax.text(
        5.5,
        1.5,
        "Sicherheit: keine hochzählbaren IDs · Zugriff nur über Session · "
        "nur Doktoranden genehmigen · Klarname nur für Prüfer · echte Daten nie im Repo",
        ha="center",
        fontsize=9,
        color="#444",
        bbox={"boxstyle": "round,pad=0.4", "fc": "#eef1fb", "ec": "#c7d0ee"},
    )
    _save(fig, "architektur")


def datenfluss():
    fig, ax = _new()
    ax.text(
        5.5,
        4.15,
        "Datenfluss: Eintragen durch den Doktoranden → Auswertung",
        ha="center",
        fontsize=13,
        weight="bold",
    )
    _box(
        ax,
        0.3,
        2.35,
        2.4,
        1.0,
        "Doktorand/in\nträgt Leistung ein\n(zählt sofort)",
        PURPLE,
    )
    _box(ax, 3.1, 2.35, 2.2, 1.0, "Datenbank\nsofort gespeichert\n(leistung.db)", GREY)
    _box(ax, 5.7, 2.35, 2.2, 1.0, "Auswertung\nVergleich · Matrix\n· Verlauf", BLUE)
    _box(
        ax,
        8.3,
        2.35,
        2.4,
        1.0,
        "Studierende/r\nsieht eigenen Stand\n(read-only) + Bot",
        GREEN,
    )
    _arrow(ax, 2.7, 2.85, 3.1, 2.85)
    _arrow(ax, 5.3, 2.85, 5.7, 2.85)
    _arrow(ax, 8.0, 2.85, 8.3, 2.85, text="eigene Daten")
    ax.text(
        5.5,
        1.45,
        "Nur der Doktorand schreibt. Studierende lesen ausschließlich ihre eigenen Daten; "
        "der Demo-Bot nutzt nur genau diese.",
        ha="center",
        fontsize=9,
        color="#444",
        bbox={"boxstyle": "round,pad=0.4", "fc": "#e6f4ea", "ec": "#bfe0c6"},
    )
    _save(fig, "datenfluss")


def auswertung_vision():
    fig, ax = _new()
    ax.text(
        5.5,
        4.15,
        "Auswertung: Kompetenzentwicklung sichtbar machen (Projekt-2-Ziel)",
        ha="center",
        fontsize=13,
        weight="bold",
    )
    _box(ax, 0.4, 2.1, 2.4, 1.1, "Genehmigte\nLeistungen\n(je Kategorie / IK)", GREEN)
    _box(ax, 4.2, 3.1, 3.0, 0.75, "Kompetenzradar\n(Ziel-Erreichung je Feld)", BLUE)
    _box(ax, 4.2, 2.15, 3.0, 0.75, "Entwicklung IK I–IV\n(Verlauf über Semester)", BLUE)
    _box(ax, 4.2, 1.2, 3.0, 0.75, "Fortschritt je Kategorie\n(genehmigt / Soll)", BLUE)
    _box(
        ax,
        8.1,
        2.1,
        2.6,
        1.1,
        "Kompetenz­entwicklung\nsichtbar →\ngezielte Förderung",
        PURPLE,
    )
    for yy in (3.475, 2.525, 1.575):
        _arrow(ax, 2.8, 2.65, 4.2, yy)
        _arrow(ax, 7.2, yy, 8.1, 2.65)
    _save(fig, "auswertung_vision")


def ablauf_rollen():
    """Schritt-für-Schritt: was Studierende tun und was Doktoranden tun."""
    fig, ax = _new()
    ax.text(
        5.5,
        4.15,
        "Wie es funktioniert: Doktorand trägt ein, Studierende sehen",
        ha="center",
        fontsize=13,
        weight="bold",
    )
    steps = [
        ("1  Doktorand\nmeldet sich an", PURPLE, "Doktorand/in"),
        ("2  Studierende/n\nauswählen", PURPLE, "Doktorand/in"),
        ("3  Leistung\neintragen", GREEN, "Doktorand/in"),
        ("4  zählt sofort\n(signiert)", GREEN, "System"),
        ("5  Student sieht\neigenen Stand", BLUE, "Studierende/r"),
        ("6  fragt Demo-Bot\n(eigene Daten)", BLUE, "Studierende/r"),
    ]
    w, h, y = 1.55, 1.0, 2.0
    xs = [0.3 + i * (w + 0.17) for i in range(len(steps))]
    for (text, color, actor), x in zip(steps, xs):
        ax.text(x + w / 2, 3.2, actor, ha="center", fontsize=8, color="#666")
        _box(ax, x, y, w, h, text, color)
    for i in range(len(steps) - 1):
        _arrow(ax, xs[i] + w, y + h / 2, xs[i + 1], y + h / 2)
    ax.text(
        5.5,
        1.35,
        "Nur der Doktorand trägt ein – Studierende können nichts ändern, nur ihren eigenen "
        "Stand ansehen und den Demo-Bot zu ihren eigenen Daten fragen.",
        ha="center",
        fontsize=9,
        color="#444",
        bbox={"boxstyle": "round,pad=0.4", "fc": "#eef1fb", "ec": "#c7d0ee"},
    )
    _save(fig, "ablauf_rollen")


if __name__ == "__main__":
    workflow()
    architecture()
    datenfluss()
    auswertung_vision()
    ablauf_rollen()
    print("Schaubilder erzeugt in", OUT)
