# Metadata Extractor

A Python tool that monitors PDF folders, extracts metadata via Document AI (with AWS Textract fallback), and appends to Google Sheets.

## Project Structure
```
metadata_extractor/
├── credentials/
│   └── google-sa.json            # placeholder for Google service account JSON
├── config/
│   └── settings.py
├── input_dirs/
│   ├── local_drive/              # empty folder for local PDFs
│   └── shared_drive/             # empty folder for shared PDFs
└── src/
    ├── __init__.py
    ├── ocr_textract.py           # AWS Textract integration
    ├── sheets_writer.py          # Google Sheets integration
    ├── watcher.py                # File system monitoring
    └── main.py                   # Main application entry point
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up your Google Cloud credentials:
   - Place your service account JSON key in `credentials/google-sa.json`
   - Set up the Document AI processor in your GCP project

3. Configure environment variables in `config/settings.py` or as environment variables:
   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `DOCAI_PROCESSOR`: Your Document AI processor ID
   - `SHEET_ID`: (Optional) Your Google Sheet ID
   - `AWS_REGION`: (Optional) AWS region for Textract (default: us-east-1)
   - `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`: AWS credentials for Textract

4. Place PDFs in the appropriate subdirectory under `input_dirs/` (one subdirectory per tab)

## Usage

### Process PDFs for a Specific Tab
Process all PDFs in a tab's directory and append to the specified tab and FF#:
```bash
python -m src.main process "Tab Name" FF1
```

### Watch Mode
Continuously monitor the input directories for new PDFs:
```bash
python -m src.main watch
```

## How It Works

1. **Document Processing**
   - First attempts to use Google Document AI for structured extraction
   - Falls back to AWS Textract if Document AI fails or is not available
   - Extracts key metadata fields: Title, Date, Volume, Issue, and Description

2. **Output**
   - Appends extracted metadata to a Google Sheet
   - Each row contains: Filename, Title, Date, Volume, Issue, Description
   - Automatically creates folders for each tab in the Google Sheet

## AWS Credentials

To use the Textract fallback, you need to configure AWS credentials. You can do this by:

1. Setting environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key_id
   export AWS_SECRET_ACCESS_KEY=your_secret_access_key
   export AWS_REGION=us-east-1  # Optional, defaults to us-east-1
   ```

2. Or using the AWS credentials file at `~/.aws/credentials`:
   ```ini
   [default]
   aws_access_key_id = your_access_key_id
   aws_secret_access_key = your_secret_access_key
   region = us-east-1
   ```
