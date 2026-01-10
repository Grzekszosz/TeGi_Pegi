import os
from pypdf import PdfReader

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
    return text

def list_cv_files(directory_path):
    """
    Listuje wszystkie pliki PDF w podanym katalogu.
    """
    return [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.endswith('.pdf')]