"""
Configuration settings for the metadata extractor.

This module handles configuration management, including loading from environment variables
and providing default values for all settings.
"""

import os
import logging
from pathlib import Path
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

# Base directories
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / 'data'

# Google Sheets API settings
GOOGLE_CREDENTIALS_ENV_VAR = 'GOOGLE_APPLICATION_CREDENTIALS'
DEFAULT_CREDENTIALS_PATH = PROJECT_ROOT / 'credentials' / 'service-account.json'

# Spreadsheet settings
DEFAULT_SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', 'your-default-spreadsheet-id')

# PDF processing settings
DEFAULT_PDF_ROOT = DATA_DIR / 'pdfs'
DEFAULT_START_ROW = 3  # 1-based row number to start writing data

# OCR settings
DEFAULT_DPI = 300
DEFAULT_LANG = 'eng'


def get_credentials_path() -> Path:
    """Get the path to the Google service account credentials.
    
    Checks environment variables first, then falls back to default location.
    
    Returns:
        Path to the credentials file
    """
    env_path = os.getenv(GOOGLE_CREDENTIALS_ENV_VAR)
    if env_path and Path(env_path).exists():
        return Path(env_path)
    return DEFAULT_CREDENTIALS_PATH


def ensure_directories() -> None:
    """Ensure all required directories exist."""
    directories = [
        DATA_DIR,
        DEFAULT_PDF_ROOT,
        get_credentials_path().parent
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")


# Initialize settings
SERVICE_ACCOUNT_FILE = get_credentials_path()
PDF_ROOT_FOLDER = DEFAULT_PDF_ROOT
SPREADSHEET_ID = DEFAULT_SPREADSHEET_ID
START_ROW = DEFAULT_START_ROW
DPI = DEFAULT_DPI
LANGUAGE = DEFAULT_LANG

# Export commonly used settings for backward compatibility
SERVICE_KEY = SERVICE_ACCOUNT_FILE

# Ensure required directories exist
try:
    ensure_directories()
except Exception as e:
    logger.warning(f"Failed to create required directories: {e}")
    raise
