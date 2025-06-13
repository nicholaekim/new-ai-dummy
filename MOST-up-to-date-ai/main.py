#!/usr/bin/env python3
"""
Main entry point for the metadata extractor application.

This script processes PDF files, extracts metadata using OCR,
and updates Google Sheets with the extracted information.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from metadata_extractor.config import (
    PDF_ROOT_FOLDER,
    SERVICE_KEY,
    SPREADSHEET_ID,
    ensure_config_directories
)
from metadata_extractor.utils.sheets_client import SheetsClient
from metadata_extractor.utils.ocr_helpers import ocr_pdf
from metadata_extractor.utils.date_helpers import simple_metadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('metadata_extractor.log')
    ]
)
logger = logging.getLogger(__name__)

class MetadataExtractor:
    """Main class for the metadata extraction process."""
    
    def __init__(self, sheets_client: Optional[SheetsClient] = None):
        """Initialize the metadata extractor.
        
        Args:
            sheets_client: Optional pre-configured SheetsClient instance
        """
        self.sheets_client = sheets_client or SheetsClient()
        
    def process_pdf(self, pdf_path: Path) -> Optional[Dict[str, Any]]:
        """Process a single PDF file and extract metadata.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing the extracted metadata, or None if processing failed
        """
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return None
            
        try:
            logger.info(f"Processing PDF: {pdf_path.name}")
            
            # Extract text using OCR
            text, confidence = ocr_pdf(str(pdf_path))
            
            # Extract metadata from text
            metadata = simple_metadata(text)
            metadata["Confidence"] = f"{confidence:.1f}%"
            metadata["Filename"] = pdf_path.name
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}", exc_info=True)
            return None
    
    def process_folder(self, folder_path: Path, tab_name: str) -> List[Dict[str, Any]]:
        """Process all PDF files in a folder.
        
        Args:
            folder_path: Path to the folder containing PDFs
            tab_name: Name of the sheet tab to update
            
        Returns:
            List of metadata dictionaries for processed files
        """
        if not folder_path.is_dir():
            logger.error(f"Folder not found: {folder_path}")
            return []
            
        pdf_files = list(folder_path.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {folder_path}")
            return []
            
        logger.info(f"Found {len(pdf_files)} PDF files in {folder_path.name}")
        
        results = []
        for pdf_file in pdf_files:
            metadata = self.process_pdf(pdf_file)
            if metadata:
                results.append(metadata)
                
        return results
    
    def update_sheets(self, tab_name: str, metadata_list: List[Dict[str, Any]], start_row: int = 3) -> bool:
        """Update Google Sheets with the extracted metadata.
        
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
            
        try:
            # Prepare rows for Google Sheets
            rows = []
            for meta in metadata_list:
                row = [
                    meta.get("Filename", ""),
                    meta.get("Title", ""),
                    meta.get("Description", ""),
                    meta.get("Date", ""),
                    meta.get("Confidence", "")
                ]
                rows.append(row)
            
            # Update Google Sheets
            return self.sheets_client.append_rows_to_tab(tab_name, rows, start_row)
            
        except Exception as e:
            logger.error(f"Error updating Google Sheets: {e}", exc_info=True)
            return False

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Extract metadata from PDFs and update Google Sheets.')
    parser.add_argument('--folder', type=str, help='Folder containing PDFs to process')
    parser.add_argument('--tab', type=str, help='Name of the sheet tab to update')
    parser.add_argument('--start-row', type=int, default=3, help='Starting row number (default: 3)')
    return parser.parse_args()

def main():
    """Main entry point for the script."""
    args = parse_arguments()
    
    try:
        # Ensure required directories exist
        ensure_config_directories()
        
        # Initialize the metadata extractor
        extractor = MetadataExtractor()
        
        # Get list of tabs if not specified
        if not args.tab:
            tabs = extractor.sheets_client.fetch_all_tab_names()
            print("Available tabs:")
            for tab in tabs:
                print(f" - {tab}")
            return
        
        # Process the specified folder or all folders
        if args.folder:
            folder_path = Path(args.folder)
            if not folder_path.exists():
                raise FileNotFoundError(f"Folder not found: {folder_path}")
                
            metadata_list = extractor.process_folder(folder_path, args.tab)
            if metadata_list:
                extractor.update_sheets(args.tab, metadata_list, args.start_row)
        else:
            # Process all folders that match tab names
            tabs = extractor.sheets_client.fetch_all_tab_names()
            for tab in tabs:
                folder_path = PDF_ROOT_FOLDER / tab
                if folder_path.exists():
                    logger.info(f"Processing folder: {folder_path}")
                    metadata_list = extractor.process_folder(folder_path, tab)
                    if metadata_list:
                        extractor.update_sheets(tab, metadata_list)
    
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
