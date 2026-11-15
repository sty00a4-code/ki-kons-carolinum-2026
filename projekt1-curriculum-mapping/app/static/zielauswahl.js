// Formulare des Vorlesungsabgleichs: Felder je nach gewählten Zielen.

// Zeigt die Elemente mit data-fuer="lernziele" nur beim Abgleich mit
// Lernzielen, die mit data-fuer="pruefziele" nur beim Abgleich mit
// Prüfzielen. Dateifelder mit data-pflicht sind nur sichtbar Pflicht. Ist der
// Prompt unverändert, wird er gegen die Vorgabe für die neuen Ziele getauscht;
// die Vorgaben stehen als JSON in data-vorgaben des Prompts.
export function zielauswahlEinrichten(formular) {
  const auswahl = formular.elements.ziel;
  const prompt = formular.elements.prompt;
  const vorgaben = prompt ? JSON.parse(prompt.dataset.vorgaben) : {};
  let bisher = auswahl.value;

  function anzeigen() {
    for (const element of formular.querySelectorAll("[data-fuer]")) {
      const aktiv = element.dataset.fuer === auswahl.value;
      element.hidden = !aktiv;
      for (const feld of element.querySelectorAll("input[data-pflicht]")) {
        feld.required = aktiv;
      }
    }
  }

  auswahl.addEventListener("change", () => {
    if (prompt && prompt.value.trim() === (vorgaben[bisher] || "").trim()) {
      prompt.value = vorgaben[auswahl.value] || prompt.value;
    }
    bisher = auswahl.value;
    anzeigen();
  });
  anzeigen();
}
