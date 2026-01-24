import os
from pathlib import Path
from pypdf import PdfReader
#Corrupted
def extract_text_from_pdf(pdf_path):
    """
    Wyodrębnia tekst z pliku PDF przy użyciu biblioteki pypdf.
    """
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"Błąd podczas odczytu pliku {pdf_path}: {e}")
    print(text)
    return text

def list_cv_files(directory_path: Path) -> list[Path]:
    return list(directory_path.glob("*.pdf"))