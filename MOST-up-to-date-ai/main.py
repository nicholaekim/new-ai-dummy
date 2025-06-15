#!/usr/bin/env python3
"""
Main script for the metadata extractor.

This script processes PDF files, extracts metadata using OCR,
and optionally updates Google Sheets with the extracted information.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd  # Add pandas for Excel export

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from metadata_extractor.config import PDF_ROOT_FOLDER, ensure_directories
from metadata_extractor.utils.ocr_helpers import ocr_pdf
from metadata_extractor.utils.date_helpers import simple_metadata
from openpyxl import load_workbook


# Try to import Google Sheets client (optional)
try:
    from metadata_extractor.utils.sheets_client import SheetsClient
    HAS_GOOGLE_SHEETS = True
except ImportError:
    HAS_GOOGLE_SHEETS = False
    logger = logging.getLogger(__name__)
    logger.warning("Google Sheets integration disabled. Running in offline mode.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('metadata_extractor.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class MetadataExtractor:
    """Main class for the metadata extraction process."""

    def __init__(self, sheets_client=None):
        """Initialize the metadata extractor.
        
        Args:
            sheets_client: Optional SheetsClient instance. If None, runs in offline mode.
        """
        self.sheets_client = sheets_client if HAS_GOOGLE_SHEETS and sheets_client is not None else None
        if self.sheets_client is None and HAS_GOOGLE_SHEETS:
            try:
                self.sheets_client = SheetsClient()
            except Exception as e:
                logger.warning(f"Failed to initialize Google Sheets client: {e}")
                logger.warning("Running in offline mode. Results will be saved to JSON files.")
                self.sheets_client = None

    def process_pdf(self, pdf_path: Path, year: int, folder_number: str) -> Optional[Dict[str, Any]]:
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return None
        try:
            logger.info(f"Processing PDF: {pdf_path.name}")
            text, confidence = ocr_pdf(str(pdf_path))
            
            # Extract metadata
            metadata = simple_metadata(text)
            
            # Set standard fields
            metadata.update({
                "Filename": pdf_path.name,
                "Confidence": f"{confidence:.1f}%",
                "Folder Number": folder_number,
                "Year": str(year),
                "Document Date": f"{year}/01/01"  # Default to Jan 1st of the year
            })
            
            # Try to extract more specific date if available
            if "Date" in metadata and metadata["Date"]:
                try:
                    # If we found a date in the document, use it
                    doc_date = metadata["Date"]
                    # If it's just a year, use the first day of the year
                    if len(doc_date) == 4 and doc_date.isdigit():
                        metadata["Document Date"] = f"{doc_date}/01/01"
                    # Otherwise try to parse the date
                    else:
                        # Try to parse various date formats
                        from datetime import datetime
                        for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
                            try:
                                dt = datetime.strptime(doc_date, fmt)
                                metadata["Document Date"] = dt.strftime("%Y/%m/%d")
                                break
                            except ValueError:
                                continue
                except Exception as e:
                    logger.warning(f"Could not parse date: {e}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}", exc_info=True)
            return None

    def process_folder(self, folder_path: Path, tab_name: str, year: int, folder_number: str) -> List[Dict[str, Any]]:
        if not folder_path.is_dir():
            logger.error(f"Folder not found: {folder_path}")
            return []
            
        pdf_files = list(folder_path.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {folder_path}")
            return []
            
        logger.info(f"Found {len(pdf_files)} PDF files in {folder_path.name}")
        
        results = []
        for pdf_file in sorted(pdf_files):  # Sort files for consistent ordering
            meta = self.process_pdf(pdf_file, year, folder_number)
            if meta:
                results.append(meta)
                
        return results

    def save_metadata(self, metadata_list: List[Dict[str, Any]], output_file: str = None) -> bool:
        """Save metadata to a file (Excel or JSON).
        
        Args:
            metadata_list: List of metadata dictionaries
            output_file: Output file path (if None, will use tab name)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not output_file:
            return False
            
        try:
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(metadata_list)
            
            # Reorder columns to put important info first
            columns_order = ['Filename', 'Title', 'Description', 'Document Date', 'Year', 
                           'Folder Number', 'Confidence', 'Tab', 'Folder']
            
            # Add any missing columns to the end
            extra_columns = [col for col in df.columns if col not in columns_order]
            columns_order.extend(extra_columns)
            
            # Reorder the DataFrame
            df = df[columns_order]
            
            # Ensure we have proper file extensions
            base_name = output_file
            if '.' in base_name:
                base_name = base_name.rsplit('.', 1)[0]
                
            # Save to Excel
            excel_file = f"{base_name}.xlsx"
            df.to_excel(excel_file, index=False)
            
            # Also save as JSON for reference
            json_file = f"{base_name}.json"
            df.to_json(json_file, orient='records', indent=2)
            
            logger.info(f"Saved metadata to {excel_file} and {json_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving metadata: {e}", exc_info=True)
            return False

    def update_sheets(
        self,
        tab_name: str,
        metadata_list: List[Dict[str, Any]],
        start_row: int = 3
    ) -> bool:
        """Update Google Sheets with the extracted metadata.
        
        If Google Sheets is not available, saves to a JSON file instead.
        
        Args:
            tab_name: Name of the sheet tab to update
            metadata_list: List of metadata dictionaries
            start_row: Starting row number (1-based)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not metadata_list:
            logger.warning("No metadata to update")
            return False
            
        # Prepare the data for output
        rows = []
        for meta in metadata_list:
            rows.append({
                "Filename": meta.get("Filename", ""),
                "Title": meta.get("Title", ""),
                "Description": meta.get("Description", ""),
                "Date": meta.get("Date", ""),
                "Volume": meta.get("Volume", ""),
                "Issue": meta.get("Issue", ""),
                "Confidence": meta.get("Confidence", "")
            })
        
        # Try to update Google Sheets if available
        if self.sheets_client is not None:
            try:
                # Convert to list of lists for Google Sheets
                sheet_rows = [
                    [
                        meta.get("Filename", ""),
                        meta.get("Title", ""),
                        meta.get("Description", ""),
                        meta.get("Date", ""),
                        meta.get("Volume", ""),
                        meta.get("Issue", ""),
                        meta.get("Confidence", "")
                    ] for meta in rows
                ]
                return self.sheets_client.append_rows_to_tab(tab_name, sheet_rows, start_row)
            except Exception as e:
                logger.error(f"Error updating Google Sheets: {e}")
                logger.info("Falling back to saving to JSON file")
                
        # Fall back to saving as JSON
        output_file = f"{tab_name}_metadata.json"
        return self.save_to_json(rows, output_file)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Extract metadata from PDFs and optionally update Google Sheets.'
    )
    parser.add_argument(
        '--folder',
        type=str,
        help='Folder containing PDFs to process (e.g. ./scanned_pdfs/SOL Box27c)'
    )
    parser.add_argument(
        '--tab',
        type=str,
        default='default',
        help='Name of the sheet tab to update (default: default)'
    )
    parser.add_argument(
        '--start-row',
        type=int,
        default=1,
        help='Starting row number in the sheet (default: 1)'
    )
    parser.add_argument(
        '--offline',
        action='store_true',
        help='Run in offline mode (save to JSON instead of Google Sheets)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output JSON file path (default: <tab_name>_metadata.json)'
    )
    parser.add_argument(
        '--year',
        type=int,
        required=True,
        help='Year of the documents (e.g., 1986)'
    )
    parser.add_argument(
        '--folder-number',
        type=str,
        required=True,
        help='Folder number (e.g., FF6)'
    )

    parser.add_argument(
        '--start-row', type=int, default=3,
        help='Starting row number in the sheet (default: 3)'
    )
    parser.add_argument(
        '--offline', action='store_true',
        help='Run in offline mode (write to local Excel/JSON instead of Google Sheets)'
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='Base filename (without .xlsx) for offline Excel/JSON output'
    )
    
    return parser.parse_args()

def main():
    args = parse_arguments()

    # Ensure our folders (scanned_pdfs, credentials) are in place
    ensure_directories()

    # Initialize extractor (with or without Google Sheets)
    extractor = MetadataExtractor(sheets_client=None if args.offline else None)

    # If no tab is specified and not in offline mode, list available tabs
    if not args.offline and args.tab == 'default' and hasattr(extractor, 'sheets_client') and extractor.sheets_client:
        try:
            tabs = extractor.sheets_client.get_all_tabs()
            print("Available tabs:")
            for t in tabs:
                print(f" - {t}")
            return
        except Exception as e:
            logger.warning(f"Could not fetch tabs from Google Sheets: {e}")
            logger.info("Falling back to default tab name")
            args.offline = True

    # Process the specified folder or use scanned_pdfs
    if args.folder:
        folder_path = Path(args.folder)
    else:
        folder_path = PDF_ROOT_FOLDER / args.tab
        
    if not folder_path.exists():
        logger.error(f"Folder not found: {folder_path}")
        logger.info(f"Creating folder: {folder_path}")
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created folder: {folder_path}")
            logger.info(f"Please add PDF files to {folder_path} and run the script again")
            return
        except Exception as e:
            logger.error(f"Failed to create folder: {e}")
            sys.exit(1)

    # Process the folder
    logger.info(f"Processing folder: {folder_path}")
    logger.info(f"Year: {args.year}, Folder Number: {args.folder_number}")
    
    metas = extractor.process_folder(folder_path, args.tab, args.year, args.folder_number)
    
    if not metas:
        logger.warning("No PDF files processed")
        return
    
    # Add folder and tab information to each metadata entry
    for meta in metas:
        meta["Tab"] = args.tab
        meta["Folder"] = folder_path.name
    
    # Save the results
    folder_safe = args.folder_number.replace(" ", "_")
    base_filename = f"{args.tab.replace(' ', '_')}_{folder_safe}_{args.year}_metadata"
    output_file = args.output or base_filename
    
    if args.offline or extractor.sheets_client is None:
        extractor.save_metadata(metas, output_file)
    else:
        extractor.update_sheets(args.tab, metas, args.start_row)

if __name__ == "__main__":
    main()
