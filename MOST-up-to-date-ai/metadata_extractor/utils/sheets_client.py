"""
Google Sheets API client for the metadata extractor.

This module provides a client class for interacting with Google Sheets API
to read and update spreadsheet data.
"""

import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build

from ..config import SPREADSHEET_ID, SERVICE_KEY

logger = logging.getLogger(__name__)

class SheetsClient:
    """Client for interacting with Google Sheets API."""
    
    def __init__(self, credentials_path: Path = None, service=None):
        """
        Initialize the Google Sheets client.
        
        Args:
            credentials_path: Path to service account credentials JSON file.
                            If not provided, uses the default from config.
            service: Optional pre-configured service object (used for testing)
        """
        self.credentials_path = credentials_path or SERVICE_KEY
        self._service = service
        
        if self._service is None:
            try:
                creds = service_account.Credentials.from_service_account_file(
                    str(self.credentials_path),
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self._service = build('sheets', 'v4', credentials=creds)
                logger.debug("Google Sheets service created")
            except Exception as e:
                logger.error(f"Failed to create Google Sheets service: {e}")
                raise
    
    @property
    def service(self):
        """Get the Google Sheets service."""
        return self._service
    
    def get_all_tabs(self) -> List[str]:
        """
        Get all sheet tabs in the spreadsheet.
        
        Returns:
            List of sheet tab names
        """
        try:
            # Get the spreadsheets resource
            spreadsheets = self.service.spreadsheets()
            
            # Call the get method to retrieve spreadsheet metadata
            request = spreadsheets.get(spreadsheetId=SPREADSHEET_ID)
            
            # Execute the request
            response = request.execute()
            
            # Extract sheet titles from the response
            sheets = response.get('sheets', [])
            
            titles = [sheet['properties']['title'] for sheet in sheets
                    if 'properties' in sheet and 'title' in sheet['properties']]
            
            logger.debug(f"Found {len(titles)} sheets in spreadsheet")
            return titles
            
        except Exception as e:
            logger.error(f"Error getting sheet tabs: {e}", exc_info=True)
            return []
    
    def find_tab_by_identifier(self, identifier: str) -> Optional[str]:
        """
        Find a tab by searching for an identifier in column C.
        
        Args:
            identifier: The identifier to search for in column C
            
        Returns:
            Name of the tab containing the identifier, or None if not found
        """
        if not identifier:
            return None
            
        try:
            tabs = self.get_all_tabs()
            for tab in tabs:
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"'{tab}'!C:C"
                ).execute()
                
                values = result.get('values', [])
                # Check if any cell in column C contains the identifier
                for row in values:
                    if row and identifier in str(row[0]):
                        return tab
            return None
            
        except Exception as e:
            logger.error(f"Error finding tab by identifier: {e}")
            return None
    
    def get_row_mapping(self, tab_name: str, filenames: List[str]) -> Dict[str, int]:
        """
        Get a mapping of filenames to their row numbers in column A.
        
        Args:
            tab_name: Name of the sheet tab
            filenames: List of filenames to search for in column A
            
        Returns:
            Dictionary mapping filenames to their 1-based row numbers
        """
        if not tab_name or not filenames:
            return {}
            
        try:
            # Get all values from column C (C1:C1000)
            result = self.service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'{tab_name}'!C1:C1000"
            ).execute()
            
            values = result.get('values', [])
            row_map = {}
            filename_set = set(filenames)
            
            # Map filenames to their 1-based row numbers
            for i, row in enumerate(values, 1):  # 1-based indexing
                if row and row[0] in filename_set:
                    row_map[row[0]] = i
                    
            return row_map
            
        except Exception as e:
            logger.error(f"Error getting row mapping: {e}")
            return {}
    
    def batch_update_cells(self, tab_name: str, updates: List[Dict[str, Any]]) -> bool:
        """
        Update multiple cells in a batch operation.
        
        Args:
            tab_name: Name of the sheet tab
            updates: List of update dictionaries with 'range' and 'values' keys
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not tab_name or not updates:
            return False
            
        try:
            # Prepare the request body
            data = []
            for update in updates:
                if 'range' not in update or 'values' not in update:
                    continue
                data.append({
                    'range': f"'{tab_name}'!{update['range']}",
                    'values': update['values']
                })
            
            if not data:
                return False
            
            body = {
                'valueInputOption': 'RAW',
                'data': data
            }
            
            # Make the batch update request
            result = self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=body
            ).execute()
            
            total_updated = result.get('totalUpdatedCells', 0)
            logger.info(f"Updated {total_updated} cells")
            return True
            
        except Exception as e:
            logger.error(f"Error updating cells: {e}")
            return False
            
    def fetch_all_tab_names(self) -> List[str]:
        """
        Get all tab names from the spreadsheet.
        
        This is a convenience method that wraps get_all_tabs() for backward compatibility.
        
        Returns:
            List of sheet tab names
        """
        return self.get_all_tabs()
        
    def append_rows_to_tab(self, tab_name: str, rows: List[List[Any]], start_row: int = 3) -> bool:
        """
        Append multiple rows to a specific tab in the spreadsheet.
        
        Args:
            tab_name: Name of the sheet tab
            rows: List of rows to append (each row is a list of cell values)
            start_row: Starting row number (1-based, default is 3)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not tab_name or not rows:
            return False
            
        try:
            # Calculate the range to update (C3:G{N} where N = start_row + len(rows) - 1)
            end_row = start_row + len(rows) - 1
            write_range = f"'{tab_name}'!C{start_row}:G{end_row}"
            logger.info(f"Writing {len(rows)} rows to {write_range}")
            
            # Prepare the request body
            body = {
                'range': write_range,
                'majorDimension': 'ROWS',
                'values': rows
            }
            
            # Make the update request
            self.service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=write_range,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Successfully wrote {len(rows)} rows to {tab_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error appending rows to {tab_name}: {e}", exc_info=True)
            return False
