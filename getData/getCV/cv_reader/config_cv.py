# cv_reader/config_cv.py
import os
from pathlib import Path

# katalog główny projektu (plik config_cv.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# katalog z CV
CV_DIR = BASE_DIR / "data" / "cvs"

# możesz zmienić na inny, jeśli chcesz
