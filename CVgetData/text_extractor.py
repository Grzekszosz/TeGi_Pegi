import json
from pathlib import Path

from pypdf import PdfReader


def extract_text_auto(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    if ext == ".txt":
        return extract_text_from_txt(path)
    if ext == ".json":
        return extract_text_from_json(path)

    raise ValueError(f"Unsupported file type: {ext}")

def extract_text_from_txt(path: Path) -> str:
    print (path.read_text(encoding="utf-8", errors="ignore"))
    return path.read_text(encoding="utf-8", errors="ignore")

def extract_text_from_json(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))

    if isinstance(data, dict):
        parts = []
        for k, v in data.items():
            if isinstance(v, (str, int, float)):
                parts.append(f"{k}: {v}")
            elif isinstance(v, list):
                parts.append(f"{k}: " + ", ".join(map(str, v)))
        return "\n".join(parts)

    return json.dumps(data, ensure_ascii=False, indent=2)

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
