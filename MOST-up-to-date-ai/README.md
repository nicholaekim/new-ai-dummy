# PDF Metadata Extractor

A Python application that extracts metadata from PDF documents using OCR (Optical Character Recognition) and updates Google Sheets with the extracted information.

## Features

- Extracts text and metadata from PDF documents using Tesseract OCR
- Processes multiple PDFs in a directory
- Extracts titles from the first page of documents
- Updates Google Sheets with extracted metadata
- Configurable through environment variables
- Comprehensive test suite with unit and integration tests
- CI/CD pipeline with GitHub Actions

## Prerequisites

- Python 3.9+
- Tesseract OCR engine
- Google Cloud Platform project with Google Sheets API enabled
- Service account credentials with access to Google Sheets

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd MOST-up-to-date-ai
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Tesseract OCR:
   - **macOS**: `brew install tesseract tesseract-lang`
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr libtesseract-dev`
   - **Windows**: Download installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)

## Configuration

1. Copy the example environment file and update with your settings:
   ```bash
   cp .env.example .env
   ```

2. Update the `.env` file with your Google Sheets ID and other settings:
   ```env
   # Google Sheets Configuration
   GOOGLE_SHEET_ID=your_google_sheet_id_here
   
   # Optional: Path Configuration
   # PDF_ROOT_FOLDER=./scanned_pdfs
   # CRED_FOLDER=./credentials
   
   # Optional: Tesseract Configuration
   # TESSERACT_LANG=eng
   # TESSERACT_DPI=300
   # TESSERACT_CONFIG=--psm 6
   ```

3. Set up Google Sheets API credentials:
   - Create a service account in Google Cloud Console
   - Download the JSON key file
   - Place it in the `credentials` directory as `service_account_key.json`
   - Or set the `SERVICE_ACCOUNT_KEY` environment variable with the JSON content

## Usage

### Basic Usage

```bash
python main.py --folder /path/to/pdfs --tab "Sheet1"
```

### Command Line Arguments

- `--folder`: Path to the folder containing PDFs to process (required)
- `--tab`: Name of the Google Sheet tab to update (required)
- `--start-row`: Starting row number in the sheet (default: 3)
- `--dpi`: DPI for image conversion (default: 300)
- `--lang`: Language for OCR (default: 'eng')
- `--debug`: Enable debug logging

### Programmatic Usage

```python
from metadata_extractor import MetadataExtractor

# Initialize the extractor
extractor = MetadataExtractor()

# Process a folder of PDFs and update Google Sheets
metadata_list = extractor.process_folder("/path/to/pdfs", "Sheet1")

# Process a single PDF
metadata = extractor.process_pdf("/path/to/document.pdf")
```

## Project Structure

```
.
├── .github/                    # GitHub Actions workflows
│   └── workflows/
│       └── ci.yml             # CI/CD configuration
├── metadata_extractor/         # Main package
│   ├── __init__.py
│   ├── config/                 # Configuration settings
│   │   └── __init__.py
│   └── utils/                  # Utility modules
│       ├── __init__.py
│       ├── date_helpers.py     # Date parsing utilities
│       ├── ocr_helpers.py      # OCR processing functions
│       └── sheets_client.py    # Google Sheets integration
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   └── unit/                   # Unit tests
│       ├── test_date_helpers.py
│       ├── test_ocr_helpers.py
│       └── test_sheets_client.py
├── .env.example               # Example environment variables
├── .gitignore
├── main.py                    # Main script
├── pytest.ini                 # Pytest configuration
└── requirements.txt           # Project dependencies
```

## Testing

Run the test suite with coverage reporting:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=metadata_extractor --cov-report=term-missing

# Run a specific test file
pytest tests/unit/test_ocr_helpers.py -v
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [pdf2image](https://github.com/Belval/pdf2image)
- [pytest](https://docs.pytest.org/)
