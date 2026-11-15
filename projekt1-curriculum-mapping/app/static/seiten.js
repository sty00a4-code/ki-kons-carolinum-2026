// Richtet die Bausteine der Seiten über data-Attribute ein. Die Seiten
// enthalten weder eigenes Skript noch Inline-Styles, damit die Content
// Security Policy nur Skripte und Styles aus diesem Ordner zulässt.

import { entwurfEinrichten } from "./entwurf.js";
import { standAbfragen } from "./stand.js";
import { abweichungenFiltern, tabellenfilterEinrichten } from "./tabelle.js";
import { zielauswahlEinrichten } from "./zielauswahl.js";

// Sperrt beim Absenden den Knopf und zeigt den Text aus data-warten; ein
// Element mit data-warten-hinweis zeigt dann seinen Hinweis.
function wartenAnzeigen(formular) {
  formular.addEventListener("submit", () => {
    const knopf = formular.querySelector("button[type=submit]");
    knopf.disabled = true;
    knopf.textContent = formular.dataset.warten;
    const hinweis = formular.querySelector("[data-warten-hinweis]");
    if (hinweis) {
      hinweis.textContent = hinweis.dataset.wartenHinweis;
    }
  });
}

// Fragt vor dem Absenden mit dem Text aus data-bestaetigen nach.
function bestaetigenLassen(formular) {
  formular.addEventListener("submit", (ereignis) => {
    if (!confirm(formular.dataset.bestaetigen)) {
      ereignis.preventDefault();
    }
  });
}

// Schaltet die Klasse aus data-klasse an der Tabelle mit der ID aus
// data-tabelle, je nachdem, ob das Kästchen angehakt ist.
function klasseUmschalten(schalter) {
  const tabelle = document.getElementById(schalter.dataset.tabelle);
  const anwenden = () => tabelle.classList.toggle(schalter.dataset.klasse, schalter.checked);
  schalter.addEventListener("change", anwenden);
  anwenden();
}

// Breite der Balken aus data-breite, etwa "40%" oder "120px"
for (const balken of document.querySelectorAll("[data-breite]")) {
  balken.style.width = balken.dataset.breite;
}
for (const formular of document.querySelectorAll("form[data-bestaetigen]")) {
  bestaetigenLassen(formular);
}
for (const formular of document.querySelectorAll("form[data-entwurf]")) {
  entwurfEinrichten(formular, formular.dataset.entwurf);
}
for (const formular of document.querySelectorAll("form[data-zielauswahl]")) {
  zielauswahlEinrichten(formular);
}
for (const formular of document.querySelectorAll("form[data-warten]")) {
  wartenAnzeigen(formular);
}
for (const karte of document.querySelectorAll("[data-stand]")) {
  standAbfragen(karte);
}
for (const bereich of document.querySelectorAll("[data-filterbereich]")) {
  tabellenfilterEinrichten(bereich);
}
for (const schalter of document.querySelectorAll("input[data-klasse]")) {
  klasseUmschalten(schalter);
}
for (const schalter of document.querySelectorAll("input[data-nur-abweichungen]")) {
  abweichungenFiltern(schalter, document.getElementById(schalter.dataset.nurAbweichungen));
}
