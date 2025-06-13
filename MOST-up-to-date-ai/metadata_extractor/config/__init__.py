"""
Configuration settings for the metadata extractor package.
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent.parent
PDF_ROOT_FOLDER = BASE_DIR / "scanned_pdfs"
CRED_FOLDER = BASE_DIR / "credentials"
SERVICE_KEY = CRED_FOLDER / "service_account_key.json"

# Google Sheets configuration
SPREADSHEET_ID = os.getenv(
    "GOOGLE_SHEET_ID",
    "1ipTfzA5qK8V7BvzuO-hiFCbG50qjhcQP_igndLquEj8"
)

# Tesseract configuration
TESSERACT_CONFIG = {
    'lang': 'eng',
    'dpi': 300,
    'config': '--psm 6',  # Assume a single uniform block of text
}

# Date parsing configuration
DATE_PATTERNS = [
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b",  # MM/DD/YYYY or MM-DD-YYYY
    r"\b(\d{4}-\d{2}-\d{2})\b",           # YYYY-MM-DD
    r"\b([A-Za-z]+ \d{1,2}, \d{4})\b"     # Month DD, YYYY
]

# Logging configuration
LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO',
        },
    },
    'loggers': {
        'metadata_extractor': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
