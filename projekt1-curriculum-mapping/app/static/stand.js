// Stand eines laufenden Durchlaufs auf der Ergebnisseite.

const ABFRAGE_MS = 3000;
const MAX_FEHLVERSUCHE = 5;

// Fragt den Stand unter der Adresse in data-stand der Karte ab, zeigt den
// Fortschritt in [data-stand-zahl] und [data-stand-balken] und lädt die
// Seite neu, sobald der Durchlauf beendet ist. Die Antwort enthält status,
// fertig und gesamt.
export function standAbfragen(karte) {
  const zahl = karte.querySelector("[data-stand-zahl]");
  const balken = karte.querySelector("[data-stand-balken]");
  let fehlversuche = 0;

  async function abfragen() {
    try {
      const antwort = await fetch(karte.dataset.stand, { headers: { Accept: "application/json" } });
      const stand = await antwort.json();
      fehlversuche = 0;
      if (zahl) {
        zahl.textContent = stand.fertig;
      }
      if (balken) {
        balken.style.width = `${Math.min(100, (stand.fertig / Math.max(1, stand.gesamt)) * 100)}%`;
      }
      if (stand.status !== "laeuft") {
        location.reload();
        return;
      }
    } catch {
      // Server kurz nicht erreichbar oder Sitzung abgelaufen
      fehlversuche++;
      if (fehlversuche >= MAX_FEHLVERSUCHE) {
        location.reload();
        return;
      }
    }
    setTimeout(abfragen, ABFRAGE_MS);
  }

  setTimeout(abfragen, ABFRAGE_MS);
}
