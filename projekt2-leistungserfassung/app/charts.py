"""Auswertungs-Grafiken (matplotlib, aus Code – überall wiederverwendbar).

Wird von der Web-App (Live-PNGs für Doktoranden) und vom Report-Skript
(scripts/student_report.py) genutzt – eine Quelle für alle Grafiken,
jederzeit aus dem Repo regenerierbar/anpassbar.

Diagramm-Satz (orientiert am Projekt-2-Kick-Off-Dashboard):
- cohort_comparison_figure : ALLE Studierenden nebeneinander (Gesamt-Fortschritt %)
- cohort_matrix_figure     : Kompetenzmatrix Studierende × Kategorien (Ampelfarben)
- cumulative_figure        : Verlauf über die Semester/Jahre (kumulierte Ziel-Erreichung)
- radar_figure             : Kompetenzradar eines Studierenden
- category_progress_figure : genehmigte Punkte vs. Soll je Kategorie

Ampel-Schwellen (wie Kick-Off): >= 75 % grün, 50–75 % gelb, < 50 % rot.
"""

import io

import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from .catalog import CATALOG, CATEGORY_TARGET, SEMESTERS, TOTAL_TARGET

CATS = [c for c, _ in CATALOG]

SHORT = {
    "Parodontologie": "Paro",
    "Zahnhartsubstanz/Prävention/Restauration": "ZHS/Präv.",
    "Endodontologie": "Endo",
    "Kinderzahnheilkunde": "Kinder",
    "Prothetik": "Prothetik",
    "Schnittmenge Restauration/Prothetik": "Schnittm.",
    "Chirurgie/Implantologie": "Chirurgie",
    "Kieferorthopädie (KFO)": "KFO",
}
GREEN, AMBER, RED, GREY, BLUE = "#2e7d32", "#e8a13c", "#c94f4a", "#9aa0ad", "#4a63b7"
NODATA = "#d7dae2"  # Folie: "keine Daten"

# Ampel-Legende wie auf der Kick-Off-Folie (Dashboard-Beispiele A und C)
AMPEL_HANDLES = [
    Patch(color=GREEN, label="≥ 75 % (gut)"),
    Patch(color=AMBER, label="50 – 75 % (mittel)"),
    Patch(color=RED, label="< 50 % (gering)"),
]


def _ampel(pct):
    """Ampelfarbe nach Kick-Off-Schwellen."""
    if pct >= 75:
        return GREEN
    if pct >= 50:
        return AMBER
    return RED


def approved_by_category(rows):
    """Summe genehmigter Punkte (points*count) je Kategorie."""
    agg = {c: 0.0 for c in CATS}
    for r in rows:
        if r["status"] == "approved" and r["category"] in agg:
            agg[r["category"]] += r["points"] * r["count"]
    return agg


def category_pcts(rows):
    """Ziel-Erreichung (%) je Kategorie, gedeckelt bei 100."""
    agg = approved_by_category(rows)
    return [
        min(100.0, agg[c] / CATEGORY_TARGET[c] * 100 if CATEGORY_TARGET.get(c) else 0.0)
        for c in CATS
    ]


def total_pct(rows):
    agg = approved_by_category(rows)
    return min(100.0, sum(agg.values()) / TOTAL_TARGET * 100)


# ---------------------------------------------------------------- Kohorte ---


def cohort_comparison_figure(
    stats, title="Alle Studierenden im Vergleich – Gesamt-Fortschritt"
):
    """Ein Balken pro Studierendem (Klarname), sortiert, mit Ampelfarbe.

    stats: Liste von dicts mit name, approved (Punkte), pct (0..100).
    """
    stats = sorted(stats, key=lambda s: s["pct"])
    names = [s["name"] for s in stats]
    pcts = [s["pct"] for s in stats]
    pts = [s["approved"] for s in stats]

    fig, ax = plt.subplots(figsize=(9, 1.2 + 0.62 * max(1, len(stats))))
    if not stats:
        ax.text(
            0.5,
            0.5,
            "Noch keine Studierenden vorhanden",
            ha="center",
            va="center",
            transform=ax.transAxes,
            color=GREY,
        )
        ax.set_axis_off()
        return fig
    y = np.arange(len(stats))
    ax.barh(y, pcts, color=[_ampel(p) for p in pcts], height=0.62)
    for i, (p, pt) in enumerate(zip(pcts, pts)):
        ax.text(
            p + 1.2,
            i,
            f"{p:.0f} %  ({pt:g} / {TOTAL_TARGET} P.)",
            va="center",
            fontsize=9,
            color="#333",
        )
    ax.axvline(100, color=GREY, linestyle="--", linewidth=1.2)
    ax.text(100, len(stats) - 0.25, " Ziel (100 %)", fontsize=8, color=GREY)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlim(0, 118)
    ax.set_xlabel("Ziel-Erreichung (%) – genehmigte Punkte von 328")
    ax.set_title(title)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def cohort_matrix_figure(
    names, matrix, title="Kompetenzmatrix – Kohorte (Ziel-Erreichung je Kategorie)"
):
    """Kompetenzmatrix wie auf der Kick-Off-Folie (Dashboard C): diskrete
    Ampel-Zellen Studierende × Kategorien, grau = "keine Daten".

    names: Klarnamen (Zeilen). matrix: list[list[float]] gleicher Reihenfolge.
    0 % bedeutet hier "keine genehmigten Punkte" -> Folien-Kachel "keine Daten".
    """
    m = np.array(matrix, dtype=float)
    labels = [SHORT.get(c, c) for c in CATS]

    fig, ax = plt.subplots(figsize=(9.4, 1.9 + 0.62 * max(1, len(names))))
    if m.size == 0:
        ax.text(
            0.5,
            0.5,
            "Noch keine Studierenden vorhanden",
            ha="center",
            va="center",
            transform=ax.transAxes,
            color=GREY,
        )
        ax.set_axis_off()
        return fig
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            v = m[i, j]
            color = NODATA if v <= 0 else _ampel(v)
            ax.add_patch(
                plt.Rectangle(
                    (j - 0.44, i - 0.38),
                    0.88,
                    0.76,
                    color=color,
                    ec="white",
                    lw=1.5,
                    joinstyle="round",
                )
            )
            if v > 0:
                ax.text(
                    j,
                    i,
                    f"{v:.0f}",
                    ha="center",
                    va="center",
                    fontsize=8.5,
                    color="white" if v >= 75 or v < 50 else "#1c2230",
                )
            else:
                ax.text(j, i, "–", ha="center", va="center", fontsize=9, color=GREY)
    ax.set_xlim(-0.5, len(labels) - 0.5)
    ax.set_ylim(len(names) - 0.5, -0.5)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=10)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(
        handles=AMPEL_HANDLES + [Patch(color=NODATA, label="keine Daten")],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.14),
        ncol=4,
        fontsize=8,
        frameon=False,
    )
    ax.set_title(title)
    fig.tight_layout()
    return fig


# ----------------------------------------------------- pro Studierende/r ---


def cumulative_figure(rows, title="Kompetenzentwicklung über die Zeit"):
    """Linien: kumulierte Ziel-Erreichung (%) je Kategorie über IK I–IV,
    plus dicke Gesamt-Linie. Zeigt die Entwicklung 'über die Jahre'."""
    per = {c: [0.0] * len(SEMESTERS) for c in CATS}
    for r in rows:
        if (
            r["status"] == "approved"
            and r["semester"] in SEMESTERS
            and r["category"] in per
        ):
            per[r["category"]][SEMESTERS.index(r["semester"])] += (
                r["points"] * r["count"]
            )

    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    cmap = plt.get_cmap("tab10")
    total_cum = np.zeros(len(SEMESTERS))
    for i, c in enumerate(CATS):
        cum = np.cumsum(per[c])
        total_cum += cum
        tgt = CATEGORY_TARGET.get(c, 0)
        pct = np.minimum(100, cum / tgt * 100) if tgt else np.zeros(len(SEMESTERS))
        ax.plot(
            SEMESTERS,
            pct,
            marker="o",
            markersize=4,
            linewidth=1.4,
            color=cmap(i % 10),
            label=SHORT.get(c, c),
        )
    ax.plot(
        SEMESTERS,
        np.minimum(100, total_cum / TOTAL_TARGET * 100),
        marker="s",
        markersize=5,
        linewidth=2.8,
        color="#1c2230",
        linestyle="--",
        label="GESAMT",
    )
    ax.set_ylim(0, 105)
    ax.set_ylabel("Ziel-Erreichung (%)")
    ax.set_xlabel("Semester (IK I = WiSe 2024/25 … IK IV = SoSe 2026)")
    ax.set_title(title)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, ncol=1, bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    return fig


def radar_figure(rows, title="Kompetenzradar – einzelner Studierender"):
    """Kompetenzradar wie auf der Kick-Off-Folie (Dashboard A): Prozent-Ringe,
    Ampel-Legende und die Box "Gesamtfortschritt aller Kompetenzen"."""
    labels = [SHORT.get(c, c) for c in CATS]
    vals = category_pcts(rows)
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    vals_c = vals + vals[:1]
    angles_c = angles + angles[:1]

    fig = plt.figure(figsize=(6, 6.6))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles_c, vals_c, color=BLUE, linewidth=2)
    ax.fill(angles_c, vals_c, color=BLUE, alpha=0.25)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25 %", "50 %", "75 %", "100 %"], fontsize=8)
    ax.set_ylim(0, 100)
    ax.set_title(title, pad=18)
    ax.legend(
        handles=AMPEL_HANDLES,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.08),
        ncol=3,
        fontsize=8,
        frameon=False,
    )
    fig.text(
        0.5,
        0.015,
        f"Gesamtfortschritt aller Kompetenzen: {total_pct(rows):.0f} %",
        ha="center",
        fontsize=11,
        fontweight="bold",
        color="#1c2230",
        bbox={"boxstyle": "round,pad=0.45", "fc": "#eef1f8", "ec": "#c5cbdd"},
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return fig


def category_progress_figure(
    rows, title="Fortschritt je Kategorie – genehmigt vs. Soll"
):
    agg = approved_by_category(rows)
    labels = [SHORT.get(c, c) for c in CATS]
    appr = [agg[c] for c in CATS]
    tgt = [CATEGORY_TARGET.get(c, 0) for c in CATS]
    y = np.arange(len(CATS))

    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    ax.barh(y, tgt, color="#e9ebf3", label="Soll")
    pcts = [(a / t * 100 if t else 0) for a, t in zip(appr, tgt)]
    ax.barh(
        y,
        [min(a, t) for a, t in zip(appr, tgt)],
        color=[_ampel(p) for p in pcts],
        label="genehmigt",
    )
    for i, (a, t) in enumerate(zip(appr, tgt)):
        ax.text(
            t + 1.5, i, f"{a:g} / {t:g} P.", va="center", fontsize=8.5, color="#444"
        )
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Punkte")
    ax.set_title(title)
    ax.legend(fontsize=8, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def figure_to_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=115)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


# Pro-Studierenden-Diagramme (Name -> Funktion(rows, title=...))
CHARTS = {
    "radar": radar_figure,
    "verlauf": cumulative_figure,
    "fortschritt": category_progress_figure,
}
