# Metadata Extractor

A Python tool that monitors local & shared PDF folders, extracts metadata via Document AI (with Textract+LLM fallback), validates via RAG, and appends to Google Sheets.

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
├── chroma_db/                    # empty folder for persisted vectorstore
└── src/
    ├── __init__.py
    ├── ocr_docai.py
    ├── ocr_textract_llm.py
    ├── rag_feedback.py
    ├── sheets_writer.py
    ├── watcher.py
    └── main.py
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up your Google Cloud credentials:
   - Place your service account JSON key in `credentials/google-sa.json`
   - Set up the Document AI processor in your GCP project

3. Configure environment variables in `config/settings.py`:
   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `DOCAI_PROCESSOR`: Your Document AI processor ID
   - `SHEET_ID`: (Optional) Your Google Sheet ID
   - `OPENAI_API_KEY`: (Optional) Your OpenAI API key for LLM fallback

4. Place PDFs in either `input_dirs/local_drive/` or `input_dirs/shared_drive/`

## Usage

### Manual Mode
Process all PDFs in the input directories once:
```bash
python src/main.py --mode manual
```

### Watch Mode
Continuously monitor the input directories for new PDFs:
```bash
python src/main.py --mode watch
```

## How It Works

1. **Document Processing**
   - First attempts to use Google Document AI for structured extraction
   - Falls back to AWS Textract + OpenAI LLM if Document AI fails

2. **Quality Control**
   - Uses RAG (Retrieval-Augmented Generation) to validate and correct extracted metadata
   - Stores document embeddings in ChromaDB for future reference

3. **Output**
   - Appends extracted metadata to a Google Sheet
   - Each row contains: Filename, Title, Date, Volume, Issue, Description
