from pathlib import Path
import json


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
