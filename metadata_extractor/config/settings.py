import os
from pathlib import Path

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Input directory - using relative path within the project
INPUT_DIR = os.getenv("INPUT_DIR", str(BASE_DIR / "input_dirs"))

GCP_PROJECT_ID    = "mapping-and-location"
GCP_LOCATION      = "us"
DOCAI_PROCESSOR   = "7c981a4f8b986898"

SHEET_ID          = os.getenv("SHEET_ID", "1ipTfzA5qK8V7BvzuO-hiFCbG50qjhcQP_igndLquEj8")
SHEET_TAB         = os.getenv("SHEET_TAB", "Sheet1")  # Default tab name
FF_NUMBER         = os.getenv("FF_NUMBER", "FF1")      # Default FF#
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")
CHROMA_DIR        = "chroma_db"
AUTO_WATCH        = True

