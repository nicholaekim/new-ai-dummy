import os
from pathlib import Path

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Input directory - using relative path within the project
INPUT_DIR = os.getenv("INPUT_DIR", str(BASE_DIR / "input_dirs"))

# Google Cloud Document AI settings
GCP_PROJECT_ID = "mapping-and-location"  # Replace with your GCP project ID if different
GCP_LOCATION = "us"  # Region where your Document AI processor is located
DOCAI_PROCESSOR = "7c981a4f8b986898"  # Your Document AI processor ID

# Google Sheets settings
SHEET_ID = os.getenv("SHEET_ID", "1ipTfzA5qK8V7BvzuO-hiFCbG50qjhcQP_igndLquEj8")  # Your Google Sheet ID
SHEET_TAB = os.getenv("SHEET_TAB", "Sheet1")  # Default tab name in the sheet
FF_NUMBER = os.getenv("FF_NUMBER", "FF1")  # Default FF# (field/row identifier)

# AWS Region for Textract (fallback)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")  # Default to us-east-1 if not specified

# Watch for new files in the input directory
AUTO_WATCH = True  # Set to False to disable automatic file watching
