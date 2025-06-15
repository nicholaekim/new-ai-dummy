"""
Configuration settings for the metadata extractor package.
"""
import os
import json
import logging
import logging.config
from pathlib import Path
from typing import Dict, Any, Optional

# Load environment variables from .env file if it exists
from dotenv import load_dotenv

# Import settings from settings.py
from .settings import (
    ensure_directories,
    get_credentials_path,
    PROJECT_ROOT,
    DATA_DIR,
    GOOGLE_CREDENTIALS_ENV_VAR,
    DEFAULT_CREDENTIALS_PATH,
    DEFAULT_SPREADSHEET_ID,
    DEFAULT_PDF_ROOT,
    DEFAULT_START_ROW,
    DEFAULT_DPI,
    DEFAULT_LANG,
    SERVICE_ACCOUNT_FILE,
    PDF_ROOT_FOLDER,
    SPREADSHEET_ID,
    START_ROW,
    DPI,
    LANGUAGE
)

load_dotenv()

# Base directories for backward compatibility
BASE_DIR = PROJECT_ROOT
CRED_FOLDER = DEFAULT_CREDENTIALS_PATH.parent
SERVICE_KEY = SERVICE_ACCOUNT_FILE

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
        'root': {
            'handlers': ['console'],
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
    },
}

def get_service_account_info() -> Optional[Dict[str, Any]]:
    """Get service account info from environment variable or file.
    
    Returns:
        dict: Service account info if available, None otherwise.
    """
    # First try to get from environment variable
    SERVICE_ACCOUNT_KEY = os.getenv('SERVICE_ACCOUNT_KEY')
    if SERVICE_ACCOUNT_KEY:
        try:
            return json.loads(SERVICE_ACCOUNT_KEY)
        except json.JSONDecodeError:
            logging.warning("Failed to parse SERVICE_ACCOUNT_KEY from environment")
    
    # Then try to read from file
    if SERVICE_KEY.exists():
        try:
            with open(SERVICE_KEY, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Failed to load service account key from {SERVICE_KEY}: {e}")
    
    return None


def create_service_key_template() -> None:
    """Create a template for the service account key if it doesn't exist."""
    if not SERVICE_KEY.exists():
        template = {
            "type": "service_account",
            "project_id": "your-project-id",
            "private_key_id": "your-private-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\nYour private key here\n-----END PRIVATE KEY-----\n",
            "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
            "client_id": "your-client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
        }
        
        try:
            with open(SERVICE_KEY.with_suffix('.json.example'), 'w') as f:
                json.dump(template, f, indent=2)
            logging.info(f"Created service account key template at {SERVICE_KEY}.example")
        except IOError as e:
            logging.error(f"Failed to create service account key template: {e}")

# Create template service account key if it doesn't exist
create_service_key_template()

# Configure logging
logging.config.dictConfig(LOG_CONFIG)
