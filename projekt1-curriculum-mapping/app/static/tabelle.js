// Blendet in Tabellen nach der Prüfziel-Liste die Kopfzeilen für Teil, Bereich
// und Gruppe aus, unter denen keine sichtbare Zeile mehr steht. Kopfzeilen haben
// die Klasse .kopf und in data-ebene ihre Tiefe (0 Teil, 1 Bereich, 2 Gruppe).
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
