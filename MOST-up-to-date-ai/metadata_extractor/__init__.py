"""
Metadata Extractor - A package for extracting metadata from PDFs and updating Google Sheets.

This package provides functionality to:
- Perform OCR on PDF files
- Extract dates and other metadata from text
- Update Google Sheets with extracted information
"""

__version__ = "0.2.0"  # Bumped version for major refactoring

# Set up logging configuration
import logging

# Configure basic logging - will be overridden by main application if needed
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import main components
from .utils.ocr_helpers import preprocess_page, ocr_pdf
from .utils.date_helpers import (
    regex_date,
    simple_metadata
)
from .utils.sheets_client import SheetsClient

__all__ = [
    'preprocess_page',
    'ocr_pdf',
    'regex_date',
    'simple_metadata',
    'SheetsClient',
]
