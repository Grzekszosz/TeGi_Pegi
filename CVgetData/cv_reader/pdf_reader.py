from unstructured.partition.pdf import partition_pdf
from pathlib import Path
from typing import List

from .config_cv import CV_DIR


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Czyta PDF i zwraca tekst."""
    elements = partition_pdf(filename=str(pdf_path))

    text = "\n".join(
        el.text for el in elements
        if hasattr(el, "text") and el.text and el.text.strip()
    )
    return text


def list_cv_files() -> List[Path]:
    """Zwraca listę PDF-ów w katalogu data/cvs."""
    return sorted(CV_DIR.glob("*.pdf"))
