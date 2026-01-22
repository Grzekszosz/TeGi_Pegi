from pathlib import Path
from typing import List
import os
from pypdf import PdfReader
from .config_rfp import RFP_DIR


#To delete -> correct version in `text_extractor.py`
def extract_text_from_pdf(pdf_path):
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

def list_rfp_files() -> List[Path]:
    return sorted(RFP_DIR.glob("*.pdf"))