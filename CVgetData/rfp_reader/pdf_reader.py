from pathlib import Path
from typing import List
from unstructured.partition.pdf import partition_pdf

from .config_rfp import RFP_DIR

def list_rfp_files() -> List[Path]:
    return sorted(RFP_DIR.glob("*.pdf"))

def extract_text_from_pdf(pdf_path: Path) -> str:
    elements = partition_pdf(filename=str(pdf_path))
    text = "\n".join(
        el.text for el in elements
        if hasattr(el, "text") and el.text and el.text.strip()
    )
    return text
