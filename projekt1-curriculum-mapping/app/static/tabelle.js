// Tabellen der Ergebnisseite: Kopfzeilen, Filter und Suche.

// Blendet die Kopfzeilen für Teil, Bereich und Gruppe aus, unter denen keine
// sichtbare Zeile mehr steht. Kopfzeilen haben die Klasse .kopf und in
// data-ebene ihre Tiefe (0 Teil, 1 Bereich, 2 Gruppe).
function kopfzeilenAnpassen(zeilen) {
  const belegt = [false, false, false];
  for (let i = zeilen.length - 1; i >= 0; i--) {
    const tr = zeilen[i];
    if (!tr.classList.contains("kopf")) {
      if (!tr.hidden) {
        belegt.fill(true);
      }
      continue;
    }
    const ebene = Number(tr.dataset.ebene);
    tr.hidden = !belegt[ebene];
    belegt.fill(false, ebene);
  }
}

// Filter und Suche für die Tabelle in einem Bereich mit data-filterbereich.
// Die Knöpfe tragen in data-filter den Wert, der in data-stufe einer Zeile
// stehen muss, oder "alle". Das Suchfeld ist input[type=search], der Hinweis
// für eine leere Auswahl hat die Klasse .keine-treffer.
export function tabellenfilterEinrichten(bereich) {
  const tabelle = bereich.querySelector("table");
  const knoepfe = bereich.querySelectorAll("[data-filter]");
  const suche = bereich.querySelector("input[type=search]");
  const leer = bereich.querySelector(".keine-treffer");
  const zeilen = Array.from(tabelle.tBodies[0].rows);
  let filter = "alle";

  function anwenden() {
    const begriff = suche ? suche.value.trim().toLowerCase() : "";
    let sichtbar = 0;
    for (const tr of zeilen) {
      if (tr.classList.contains("kopf")) {
        continue;
      }
      const passt =
        (filter === "alle" || tr.dataset.stufe === filter) &&
        (!begriff || tr.textContent.toLowerCase().includes(begriff));
      tr.hidden = !passt;
      if (passt) {
        sichtbar++;
      }
    }
    kopfzeilenAnpassen(zeilen);
    if (leer) {
      leer.hidden = sichtbar > 0;
    }
  }

  for (const knopf of knoepfe) {
    knopf.addEventListener("click", () => {
      filter = knopf.dataset.filter;
      for (const k of knoepfe) {
        k.classList.toggle("aktiv", k === knopf);
      }
      anwenden();
    });
  }
  if (suche) {
    suche.addEventListener("input", anwenden);
  }
}
