// Speichert die Eingaben eines Formulars als Entwurf im localStorage und stellt
// sie nach dem Neuladen wieder her. Absenden oder der Knopf .entwurf-verwerfen
// löschen den Entwurf. Von Dateifeldern bleibt nur der Dateiname für den
// Hinweis in .entwurf-hinweis.
function entwurfEinrichten(formular, schluessel) {
  const hinweis = formular.querySelector(".entwurf-hinweis");
  const typen = ["text", "search", "number", "textarea", "select-one", "file"];
  const felder = Array.from(formular.elements).filter(
    (el) => el.name && el.name !== "_csrf_token" && typen.includes(el.type),
  );
  let bereit = false;

  function lesen() {
    try {
      const roh = localStorage.getItem(schluessel);
      return roh ? JSON.parse(roh) : null;
    } catch {
      return null;
    }
  }

  function loeschen() {
    try {
      localStorage.removeItem(schluessel);
    } catch {
      // localStorage nicht verfügbar
    }
  }

  function speichern() {
    if (!bereit) {
      return;
    }
    const werte = {};
    const dateien = {};
    for (const el of felder) {
      if (el.type !== "file") {
        werte[el.name] = el.value;
      } else if (el.files.length) {
        dateien[el.name] = el.files[0].name;
      }
    }
    try {
      localStorage.setItem(schluessel, JSON.stringify({ zeit: Date.now(), werte, dateien }));
    } catch {
      // localStorage nicht verfügbar
    }
  }

  function anwenden(entwurf) {
    const werte = entwurf.werte || {};
    let geaendert = false;
    for (const el of felder) {
      if (el.type === "file" || !(el.name in werte) || el.value === werte[el.name]) {
        continue;
      }
      if (el.tagName === "SELECT" && !Array.from(el.options).some((o) => o.value === werte[el.name])) {
        continue;
      }
      el.value = werte[el.name];
      geaendert = true;
      const klappe = el.closest("details");
      if (klappe) {
        klappe.open = true;
      }
    }
    const namen = Object.values(entwurf.dateien || {});
    if (!hinweis || (!geaendert && !namen.length)) {
      return;
    }
    const saetze = [];
    if (geaendert) {
      const zeit = entwurf.zeit
        ? new Date(entwurf.zeit).toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" })
        : "vorhin";
      saetze.push(`Nicht abgeschickte Eingaben von ${zeit} wiederhergestellt.`);
    }
    if (namen.length) {
      saetze.push(`Dateien speichert der Browser nicht, bitte erneut auswählen: ${namen.join(", ")}.`);
    }
    if (geaendert) {
      saetze.push("Verwerfen stellt die Vorgaben wieder her.");
    }
    hinweis.textContent = saetze.join(" ");
    hinweis.hidden = false;
  }

  const entwurf = lesen();
  if (entwurf) {
    anwenden(entwurf);
  }
  bereit = true;

  formular.addEventListener("input", speichern);
  formular.addEventListener("change", speichern);
  formular.addEventListener("submit", loeschen);
  const verwerfen = formular.querySelector(".entwurf-verwerfen");
  if (verwerfen) {
    verwerfen.addEventListener("click", () => {
      if (confirm("Alle Eingaben in diesem Formular verwerfen und die Vorgaben wiederherstellen?")) {
        loeschen();
        // Per GET neu laden, data-ziel ersetzt bei Bedarf die aktuelle Adresse.
        location.assign(verwerfen.dataset.ziel || location.pathname + location.search);
      }
    });
  }
}
