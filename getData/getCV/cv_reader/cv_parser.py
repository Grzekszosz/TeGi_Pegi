# cv_reader/cv_parser.py
import re
from typing import Dict, List

def extract_email(text: str) -> str | None:
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else None

SKILLS = ["Python", "Java", "SQL", "Docker", "AWS", "Kubernetes"]

def extract_skills(text: str) -> List[str]:
    found = []
    for skill in SKILLS:
        if re.search(rf"\b{skill}\b", text, re.IGNORECASE):
            found.append(skill)
    return found

def parse_cv(text: str) -> Dict:
    return {
        "email": extract_email(text),
        "skills": extract_skills(text),
        # później możesz dodać: name, phone, experience itd.
    }
