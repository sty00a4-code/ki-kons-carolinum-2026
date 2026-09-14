from PyPDF2 import PdfReader, PdfWriter
import os

def pdf_in_einzelne_seiten_aufteilen(input_pdf, output_ordner="einzelne_seiten_vorlesung"):
    """Teilt eine PDF in einzelne PDFs pro Seite auf."""
    # Ausgabeordner erstellen
    os.makedirs(output_ordner, exist_ok=True)

    # PDF-Datei öffnen
    with open(input_pdf, "rb") as f:
        reader = PdfReader(f)

        # Jede Seite als separate PDF speichern
        for seite_nummer, page in enumerate(reader.pages, start=1):
            writer = PdfWriter()
            writer.add_page(page)

            #output Dateiname erstellen
            output_pfad = os.path.join(output_ordner, f"Seite_{seite_nummer}.pdf")

            # PDF speichern
            with open(output_pfad, "wb") as out_f:
                writer.write(out_f)

    print(f"Erfolgreich! {len(reader.pages)} Seiten wurden nach '{output_ordner}' gespeichert.")

# Beispielaufruf
pdf_in_einzelne_seiten_aufteilen("assets/Vorlesung_1_OraleMedizinUndSystemischeAspekte.pdf")