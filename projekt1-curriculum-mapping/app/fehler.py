"""Fehler, deren Meldung für die Oberfläche bestimmt ist."""


class EingabeFehler(ValueError):
    """Fehlende oder ungültige Eingabe, etwa ein Formularfeld oder eine unbrauchbare Datei.

    Die Seiten zeigen die Meldung unverändert an.
    """
