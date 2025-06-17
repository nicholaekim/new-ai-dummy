import gspread
import os
import re
from oauth2client.service_account import ServiceAccountCredentials
from config.settings import SHEET_ID, SHEET_TAB, FF_NUMBER, INPUT_DIR
from typing import List, Optional, Set

def sanitize_folder_name(name: str) -> str:
    """Convert a sheet name to a valid folder name."""
    # Remove invalid filename characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Remove leading/trailing whitespace
    return name.strip()

def ensure_folders_exist():
    """Ensure local folder exists for each worksheet."""
    try:
        client = get_sheet_client()
        sheet = client.open_by_key(SHEET_ID)
        worksheets = sheet.worksheets()
        
        # Create base directory if it doesn't exist
        os.makedirs(INPUT_DIR, exist_ok=True)
        
        # Track created folders to avoid duplicates
        created_folders: Set[str] = set()
        
        for worksheet in worksheets:
            tab_name = worksheet.title
            folder_name = sanitize_folder_name(tab_name)
            
            # Skip if we've already created a folder for this tab
            if folder_name in created_folders:
                continue
                
            # Create folder for this tab
            tab_folder = os.path.join(INPUT_DIR, folder_name)
            os.makedirs(tab_folder, exist_ok=True)
            created_folders.add(folder_name)
            
            print(f"Created folder: {tab_folder}")
            
    except Exception as e:
        print(f"Error ensuring folders exist: {str(e)}")
        raise

def get_sheet_client():
    """Authenticate and return the Google Sheet client."""
    creds_path = os.path.join(os.path.dirname(__file__), '..', 'credentials', 'google-sa.json')
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    return gspread.authorize(creds)

def get_or_create_worksheet(client, sheet_id: str, tab_name: str):
    """Get or create a worksheet with the given name."""
    try:
        sheet = client.open_by_key(sheet_id)
        try:
            worksheet = sheet.worksheet(tab_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=tab_name, rows=1000, cols=20)
            
        # Ensure folders exist for this worksheet
        ensure_folders_exist()
        return worksheet
        
    except Exception as e:
        print(f"Error accessing Google Sheet: {e}")
        raise

def append_metadata(data: dict, tab_name: Optional[str] = None, ff_number: Optional[str] = None):
    """
    Append metadata to the specified worksheet.
    
    Args:
        data: Dictionary containing metadata fields
        tab_name: Name of the worksheet tab (defaults to SHEET_TAB from settings)
        ff_number: FF# to use (defaults to FF_NUMBER from settings)
    """
    tab_name = tab_name or SHEET_TAB
    ff_number = ff_number or FF_NUMBER
    
    # Prepare the row with FF# and extracted metadata
    row = [
        ff_number,  # FF#
        data.get("Title", ""),
        data.get("Date", ""),
        data.get("Volume", ""),
        data.get("Issue", ""),
        data.get("Description", ""),
        "",  # Empty column for notes
        "AI Extracted"  # Source of the data
    ]
    
    try:
        client = get_sheet_client()
        worksheet = get_or_create_worksheet(client, SHEET_ID, tab_name)
        
        # Append the new row
        worksheet.append_row(row)
        print(f"Successfully added metadata to {tab_name} for {ff_number}")
        return True
    except Exception as e:
        print(f"Error writing to Google Sheet: {e}")
        return False
