"""
DEPRECATED: This file is kept for backward compatibility only.
Please use the new modular structure:
- main.py: Main entry point
- metadata_extractor/utils/ocr_helpers.py: OCR functions
- metadata_extractor/utils/date_helpers.py: Date parsing
- metadata_extractor/utils/sheets_client.py: Google Sheets integration
"""

import warnings
from pathlib import Path

warnings.warn(
    "extract_metadata.py is deprecated. Please use the new modular structure.",
    DeprecationWarning,
    stacklevel=2
)

# Import from new modules
from metadata_extractor.utils.ocr_helpers import preprocess_page, ocr_pdf
from metadata_extractor.utils.date_helpers import regex_date, simple_metadata
from metadata_extractor.utils.sheets_client import SheetsClient
from metadata_extractor.config import (
    PDF_ROOT_FOLDER,
    SERVICE_KEY,
    SPREADSHEET_ID
)

# These functions are now imported from the respective modules
# and are kept here for backward compatibility.
def regex_date(text):
    """Try a simple dd/mm/yyyy or yyyy; fallback to UNKNOWN."""
    m = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4})\b", text)
    if m:
        try:
            return parse_date(m.group(), dayfirst=True).strftime("%Y/%m/%d")
        except:
            return m.group()
    return "UNKNOWN"


def simple_metadata(full_text):
    """First nonempty line as Title, first 100 chars as desc, date via regex."""
    lines = [l.strip() for l in full_text.splitlines() if l.strip()]
    title = lines[0] if lines else "UNKNOWN"
    desc  = (full_text.replace("\n"," ")[:100].strip() or "UNKNOWN")
    date  = regex_date(full_text)
    return {"Title": title, "Description": desc, "Date": date}


# ───────────────────────────────────────────────────────────────────────────
# 3) MAIN FUNCTION (Kept for backward compatibility)
# ─────────────────────────────────────────────────────────────────────────--
# The SheetsClient class is now used for all Google Sheets operations.
# These functions are kept for backward compatibility but use the new client.

def fetch_all_tab_names():
    """Get all tab names from the spreadsheet."""
    client = SheetsClient()
    return client.fetch_all_tab_names()

def append_rows_to_tab(tab_name, rows, start_row=3):
    """Append rows to the specified tab."""
    if not rows or not tab_name:
        return False
    client = SheetsClient()
    return client.append_rows_to_tab(tab_name, rows, start_row)


def main():
    """
    Main function kept for backward compatibility.
    New code should use main.py instead.
    """
    warnings.warn(
        "The main() function in extract_metadata.py is deprecated. "
        "Please use main.py instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Import here to avoid circular imports
    from metadata_extractor.config import ensure_directories
    from main import MetadataExtractor
    
    try:
        # Ensure required directories exist
        ensure_directories()
        
        # Initialize the metadata extractor
        extractor = MetadataExtractor()
        
        # Get all tab names from the spreadsheet
        tab_names = extractor.sheets_client.fetch_all_tab_names()
        print(f"Found {len(tab_names)} tabs: {', '.join(tab_names)}")
        
        # Process each tab
        for tab in tab_names:
            metadata_list = extractor.process_folder(
                PDF_ROOT_FOLDER / tab,
                tab
            )
            
            if metadata_list:
                success = extractor.update_sheets(tab, metadata_list)
                if success:
                    print(f"Successfully updated {len(metadata_list)} rows in '{tab}'")
                else:
                    print(f"Failed to update '{tab}'")
    
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
