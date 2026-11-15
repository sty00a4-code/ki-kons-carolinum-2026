"""Vorlesungsabgleich: die Folien einer Vorlesung mit Lernzielen oder Prüfzielen abgleichen.

Beim Anlegen werden je Folie der Text und ein Vorschaubild gespeichert (pdf,
speicher). Im Hintergrund beschreibt ein Bildmodell jede Folie, danach nennt
das Modell die Ziele, die dort gelehrt werden (lauf, anfragen). Die Ziele
stammen aus einem Lernziel-Kapitel, einer eingebauten Prüfziel-Liste oder
einer hochgeladenen Prüfziel-Datei (katalog). auswertung fasst die Antworten
je Folie und je Ziel zusammen, uebernahme liest fertige Ergebnisse ein.
"""
