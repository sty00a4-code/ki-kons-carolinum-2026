"""Echter KI-Assistent für Studierende (Projektplan Phase 5, UNIFR-26).

Provider-Kette (erste verfügbare gewinnt):
1. Anthropic-SDK + API-Key  – aktiv, sobald `pip install anthropic` und
   ANTHROPIC_API_KEY gesetzt sind (Modell via BOT_MODEL, Standard claude-opus-5).
2. claude-CLI, falls auf dem Rechner installiert (Modell via BOT_CLI_MODEL,
   Standard "haiku" – schnellste Antworten).
3. Keiner verfügbar → None; die Route antwortet dann regelbasiert.

DATENSCHUTZ: Das Modell bekommt AUSSCHLIESSLICH die aggregierten Daten der/des
eingeloggten Studierenden (bot_context: eigener Fortschritt, eigene Lücken,
eigene Fall-Empfehlungen) – keine Klarnamen, keine fremden Daten, keine
Patientendaten. Die Guardrails stehen zusätzlich im System-Prompt.
"""

import json
import os
import shutil
import subprocess

SYSTEM = """Du bist der Studien-Assistent der Leistungserfassung IK (Projekt 2, Zahnmedizin, integrierte Kurse IK I–IV).
Du sprichst mit einer/einem Studierenden. Dir liegen AUSSCHLIESSLICH die eigenen, aggregierten Leistungsdaten dieser Person vor (JSON unten).

Regeln (verbindlich):
- Antworte nur auf Basis dieser Daten und der Punkteregeln: 1 Punkt entspricht etwa 45 Minuten klinischer Arbeit; Ampel: ab 75 % gut, 50–75 % mittel, unter 50 % gering; Gesamtziel 328 Punkte.
- Du kennst KEINE anderen Studierenden und machst keine Aussagen über sie.
- Keine medizinischen oder behandlungsbezogenen Ratschläge – dafür an die Betreuerin/den Betreuer verweisen.
- Fälle zuteilen kann nur die Betreuerin/der Betreuer; du nennst höchstens die Empfehlungen aus den Daten.
- Wenn etwas nicht in den Daten steht, sag das ehrlich.
- Antworte kurz (höchstens ~120 Wörter), freundlich, per Du, auf Deutsch, als reiner Text ohne Markdown.
"""


SYSTEM_LEHRENDE = """Du bist der Assistent der Betreuerin/des Betreuers in der Leistungserfassung IK (Projekt 2, Zahnmedizin, integrierte Kurse IK I–IV).
Du sprichst mit einer Lehrperson. Dir liegen die Leistungsdaten aller Studierenden des Jahrgangs (einzeln und gesamt) sowie die offenen Patientenfälle mit Matching-Empfehlung vor (JSON unten). Fragen zu einzelnen Studierenden (z. B. "Wie steht Stud. 1?") beantwortest du aus deren Einzeldaten.

Regeln (verbindlich):
- Antworte nur auf Basis dieser Daten und der Punkteregeln: 1 Punkt entspricht etwa 45 Minuten klinischer Arbeit; Ampel: ab 75 % gut, 50–75 % mittel, unter 50 % gering; Gesamtziel 328 Punkte je Person.
- Empfehlungen zur Fallzuteilung immer begründen (welche Lücke der Fall schließt); die Entscheidung trifft die Lehrperson.
- Keine medizinischen oder behandlungsbezogenen Ratschläge zum Patienten selbst.
- Wenn etwas nicht in den Daten steht, sag das ehrlich.
- Antworte kurz (höchstens ~150 Wörter), sachlich, per Du, auf Deutsch, als reiner Text ohne Markdown.
"""


def _build_prompt(question, ctx, system):
    return (
        system
        + "\nDATEN:\n"
        + json.dumps(ctx, ensure_ascii=False)
        + "\n\nFrage: "
        + question
    )


def _ask_sdk(question, ctx, system):
    """Anthropic-SDK, falls installiert und API-Key vorhanden."""
    try:
        import anthropic
    except ImportError:
        return None
    if not (
        os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    ):
        return None
    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=os.environ.get("BOT_MODEL", "claude-opus-5"),
            max_tokens=1024,
            system=system + "\nDATEN:\n" + json.dumps(ctx, ensure_ascii=False),
            messages=[{"role": "user", "content": question}],
        )
        if response.stop_reason == "refusal":
            return None
        text = "".join(b.text for b in response.content if b.type == "text").strip()
        return text or None
    except Exception:
        return None


def _find_cli():
    cli = shutil.which("claude")
    if cli:
        return cli
    for candidate in (
        "/opt/homebrew/bin/claude",
        "/usr/local/bin/claude",
    ):
        if os.path.exists(candidate):
            return candidate
    return None


def _ask_cli(question, ctx, system):
    """claude-CLI headless, falls lokal installiert."""
    cli = _find_cli()
    if cli is None:
        return None
    try:
        result = subprocess.run(
            [
                cli,
                "-p",
                "--model",
                os.environ.get("BOT_CLI_MODEL", "haiku"),
                _build_prompt(question, ctx, system),
            ],
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip() or None
    except (subprocess.TimeoutExpired, OSError):
        return None


def rule_answer(ctx):
    """Regelbasierte Ausweich-Antwort, wenn keine KI verfügbar ist."""
    lines = [
        "(Regelbasierte Antwort – die KI ist gerade nicht erreichbar.)",
        (
            f"Dein Stand: {ctx.get('overall', 0)} % ({ctx.get('total', 0)} von {ctx.get('target', 0)} Punkten), "
            f"{ctx.get('done_count', 0)} von {ctx.get('cat_count', 0)} Kategorien erfüllt."
        ),
    ]
    weakest = ctx.get("weakest") or []
    if weakest:
        w = weakest[0]
        lines.append(
            f"Größte Lücke: {w['name']} ({w['pct']} %, es fehlen {w['missing']} Punkte)."
        )
    recs = ctx.get("empfehlungen") or []
    if recs:
        r = recs[0]
        lines.append(f"Passender offener Fall: {r['ref']} ({r['match']} % Match).")
    lines.append("Für Details nutze bitte die Schnellfragen-Buttons.")
    return "\n".join(lines)


def _plain(text):
    """Entfernt Markdown-Reste – das Panel rendert reinen Text."""
    out = []
    for line in text.replace("**", "").splitlines():
        out.append(line.lstrip("#").strip() if line.startswith("#") else line)
    return "\n".join(out).strip()


def rule_answer_lehrende(ctx):
    """Regelbasierte Ausweich-Antwort für den Lehrenden-Bot."""
    lines = ["(Regelbasierte Antwort – die KI ist gerade nicht erreichbar.)"]
    students = sorted(ctx.get("studierende") or [], key=lambda s: s["gesamt_pct"])
    for s in students:
        lines.append(f"{s['name']}: {s['gesamt_pct']} % ({s['punkte']:g} P)")
    faelle = [f for f in (ctx.get("offene_faelle") or []) if f.get("empfohlen")]
    if faelle:
        f = faelle[0]
        lines.append(
            f"Nächster sinnvoller Fall: {f['fall']} → {f['empfohlen']['name']} "
            f"({f['empfohlen']['match_pct']} % Match)."
        )
    return "\n".join(lines)


def ask(question, ctx, allow_ai=True):
    """Studenten-Bot: beantwortet eine Freitext-Frage über die EIGENEN Daten.

    Rückgabe: (antwort, quelle) – quelle "ki" oder "regelwerk".
    """
    if allow_ai:
        for provider in (_ask_sdk, _ask_cli):
            answer = provider(question, ctx, SYSTEM)
            if answer:
                return _plain(answer), "ki"
    return rule_answer(ctx), "regelwerk"


def ask_lehrende(question, ctx, allow_ai=True):
    """Lehrenden-Bot: Jahrgangs-Übersicht + Zuteilungs-Empfehlungen."""
    if allow_ai:
        for provider in (_ask_sdk, _ask_cli):
            answer = provider(question, ctx, SYSTEM_LEHRENDE)
            if answer:
                return _plain(answer), "ki"
    return rule_answer_lehrende(ctx), "regelwerk"
