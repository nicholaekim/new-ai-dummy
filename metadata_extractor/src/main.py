import os
import sys
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from config.settings import INPUT_DIR, AUTO_WATCH
from src.ocr_docai import parse_with_docai
from src.ocr_textract_llm import parse_with_textract
from src.sheets_writer import append_metadata, ensure_folders_exist
from src.watcher import start_watcher

def process_pdf(path: str):
    print(f"\nProcessing: {os.path.basename(path)}")
    print("Extracting metadata with Document AI...")
    data = parse_with_docai(path)  # This will automatically fall back to Textract if needed
    
    if not data:
        print("Warning: No metadata could be extracted from the document")
        data = {
            'Title': os.path.basename(path).rsplit('.', 1)[0],
            'Date': '',
            'Volume': '',
            'Issue': '',
            'Description': ''
        }
    
    # Get tab and FF# from environment or use defaults
    tab_name = os.getenv('SHEET_TAB', 'Sheet1')
    ff_number = os.getenv('FF_NUMBER', 'FF1')
    
    print(f"Saving to Google Sheets - Tab: {tab_name}, FF#: {ff_number}")
    print(f"Extracted data: {data}")
    
    success = append_metadata(data, tab_name, ff_number)
    if success:
        print("Successfully saved to Google Sheets!")
    else:
        print("Failed to save to Google Sheets")

def process_tab_pdfs(tab_name: str, ff_number: str):
    """Process all PDFs in the specified tab's folder and save to the given FF#"""
    tab_dir = os.path.join(INPUT_DIR, tab_name)
    
    if not os.path.exists(tab_dir):
        print(f"Error: Directory for tab '{tab_name}' not found at {tab_dir}")
        return
    
    print(f"Processing PDFs in {tab_dir}...")
    print(f"Will save to tab: {tab_name}, FF#: {ff_number}")
    
    # Set environment variables for this processing run
    os.environ['SHEET_TAB'] = tab_name
    os.environ['FF_NUMBER'] = ff_number
    
    # Process all PDFs in the tab's directory
    processed_count = 0
    for filename in os.listdir(tab_dir):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(tab_dir, filename)
            print(f"\n{'='*50}")
            print(f"Processing: {filename}")
            print(f"Tab: {tab_name}, FF#: {ff_number}")
            print(f"{'='*50}")
            process_pdf(pdf_path)
            processed_count += 1
    
    if processed_count == 0:
        print(f"No PDFs found in {tab_dir}")
    else:
        print(f"\nProcessed {processed_count} PDF(s) from {tab_dir}")

def main():
    parser = argparse.ArgumentParser(description='Extract metadata from PDFs and save to Google Sheets.')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Watch mode command
    watch_parser = subparsers.add_parser('watch', help='Watch for new PDFs and process them automatically')
    watch_parser.add_argument("--tab", type=str, help="Google Sheet tab name")
    watch_parser.add_argument("--ff", type=str, help="FF number (e.g., FF1, FF2, etc.)")
    
    # Process tab command
    process_parser = subparsers.add_parser('process', help='Process all PDFs in a specific tab\'s folder')
    process_parser.add_argument('tab', nargs='+', help='Tab name to process (can contain spaces)')
    process_parser.add_argument('ff', type=str, help='FF number to save to (e.g., FF1, FF2, etc.)')
    
    args = parser.parse_args()
    
    # Ensure all required folders exist
    ensure_folders_exist()
    
    if args.command == 'watch':
        # Update settings from command line if provided
        if args.tab:
            os.environ['SHEET_TAB'] = args.tab
        if args.ff:
            os.environ['FF_NUMBER'] = args.ff
            
        print(f"Watching for PDFs in {INPUT_DIR}")
        print(f"Will save to tab: {args.tab or os.getenv('SHEET_TAB', 'Sheet1')}, FF#: {args.ff or os.getenv('FF_NUMBER', 'FF1')}")
        start_watcher(process_pdf, [INPUT_DIR])
    elif args.command == 'process':
        # Join the tab name parts with spaces if it was split
        tab_name = ' '.join(args.tab)
        process_tab_pdfs(tab_name, args.ff)
    else:
        parser.print_help()

if __name__=="__main__":
    main()
