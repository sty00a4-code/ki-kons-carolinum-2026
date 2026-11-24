// Zeigt das Dateifeld für die Prüfziele nur, wenn Prüfziele gewählt sind.
const auswahl = document.getElementById("auswahl");
const feld = document.getElementById("pruefziele-feld");
const datei = document.getElementById("pruefziele");

function anpassen() {
  const pruefziele = auswahl.value === "pruefziele";
  feld.hidden = !pruefziele;
  datei.required = pruefziele;
}

if (auswahl) {
  auswahl.addEventListener("change", anpassen);
  anpassen();
}

// Fragt alle fünf Sekunden nach, ob der Vergleich fertig ist, und lädt dann das Ergebnis.
if (document.getElementById("laeuft")) {
  const takt = setInterval(async () => {
    const antwort = await fetch("/stand");
    const stand = await antwort.json();
    if (!stand.laeuft) {
      clearInterval(takt);
      location.reload();
    }
  }, 5000);
}
