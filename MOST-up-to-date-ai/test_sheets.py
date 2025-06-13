"""
Tests for the metadata extractor Google Sheets integration.

This module contains tests for the SheetsClient class.
All tests use mocking to avoid making actual API calls.
"""
"""
Tests for the metadata extractor Google Sheets integration.

This module contains tests for the SheetsClient class.
All tests use mocking to avoid making actual API calls.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Mock the Google API imports before importing our modules
class MockCredentials:
    @staticmethod
    def from_service_account_file(*args, **kwargs):
        return MagicMock()

# Mock the Google API modules
sys.modules['google.oauth2.service_account'] = MagicMock()
sys.modules['google.oauth2.service_account'].Credentials = MockCredentials
sys.modules['googleapiclient.discovery'] = MagicMock()

# Now import our modules
from metadata_extractor.utils.sheets_client import SheetsClient
from metadata_extractor.config import SPREADSHEET_ID


class TestSheetsClient(unittest.TestCase):
    """Test cases for the SheetsClient class with proper mocking."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock credentials object
        self.mock_credentials = MagicMock()
        
        # Create a mock service object
        self.mock_service = MagicMock()
        self.mock_spreadsheets = MagicMock()
        self.mock_values = MagicMock()
        
        # Set up the mock chain
        self.mock_service.spreadsheets.return_value = self.mock_spreadsheets
        self.mock_spreadsheets.values.return_value = self.mock_values
        
        # Patch the Google API client
        self.patcher_build = patch('googleapiclient.discovery.build')
        self.mock_build = self.patcher_build.start()
        self.mock_build.return_value = self.mock_service
        
        # Patch the service account credentials
        self.patcher_creds = patch('google.oauth2.service_account.Credentials')
        self.mock_credentials = self.patcher_creds.start()
        
        # Initialize the client with the mock service
        self.credentials_path = Path('test_credentials.json')
        self.client = SheetsClient(credentials_path=self.credentials_path, service=self.mock_service)

        # Set up common test data
        self.test_tab = "Test Tab"
        self.test_identifier = "FF#123"
        self.test_filenames = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
    
    def tearDown(self):
        self.patcher_build.stop()
        self.patcher_creds.stop()
    
    def test_get_all_tabs_success(self):
        """Test getting all sheet tabs successfully."""
        print("\n=== Starting test_get_all_tabs_success ===")
        
        # Print initial mock setup
        print("\n=== Initial Mock Setup ===")
        print(f"self.mock_service: {self.mock_service}")
        print(f"self.mock_spreadsheets: {self.mock_spreadsheets}")
        print(f"self.mock_values: {self.mock_values}")
        
        # Mock the API response
        mock_response = {
            "sheets": [
                {"properties": {"title": "Sheet1"}},
                {"properties": {"title": "Sheet2"}},
            ]
        }
        print(f"\n=== Mock Response ===\n{mock_response}")
        
        # Set up the mock chain
        mock_get = MagicMock()
        mock_get.execute.return_value = mock_response
        
        # Configure the spreadsheets.get() to return our mock
        self.mock_spreadsheets.get.return_value = mock_get
        
        # Print mock setup for debugging
        print("\n=== Mock Chain Setup ===")
        print(f"self.mock_spreadsheets.get.return_value: {self.mock_spreadsheets.get.return_value}")
        print(f"mock_get.execute.return_value: {mock_get.execute.return_value}")
        
        # Verify the mock chain before the call
        print("\n=== Mock Chain Verification ===")
        print(f"self.client.service: {self.client.service}")
        print(f"self.client.service.spreadsheets: {self.client.service.spreadsheets}")
        print(f"self.client.service.spreadsheets().get: {self.client.service.spreadsheets().get}")
        
        # Call the method
        print("\n=== Calling client.get_all_tabs() ===")
        tabs = self.client.get_all_tabs()
        print(f"Returned tabs: {tabs}")
        
        # Print mock call information
        print("\n=== Mock Calls After Execution ===")
        print("mock_spreadsheets.get calls:")
        print(f"  - call_args: {self.mock_spreadsheets.get.call_args}")
        print(f"  - call_count: {self.mock_spreadsheets.get.call_count}")
        print("\nmock_get.execute calls:")
        print(f"  - call_args: {mock_get.execute.call_args}")
        print(f"  - call_count: {mock_get.execute.call_count}")
        
        # Print all calls to mock_service.spreadsheets
        print("\nAll calls to mock_service.spreadsheets:")
        print(f"  - call_args_list: {self.mock_service.spreadsheets.call_args_list}")
        print(f"  - call_count: {self.mock_service.spreadsheets.call_count}")
        
        # Print all calls to mock_spreadsheets.get
        print("\nAll calls to mock_spreadsheets.get:")
        print(f"  - call_args_list: {self.mock_spreadsheets.get.call_args_list}")
        print(f"  - call_count: {self.mock_spreadsheets.get.call_count}")
        
        # Assertions
        expected_tabs = ["Sheet1", "Sheet2"]
        print(f"\n=== Assertions ===\nAsserting tabs == {expected_tabs}")
        self.assertEqual(tabs, expected_tabs)
        
        print("\n=== Verifying Mock Calls ===")
        # Verify spreadsheets.get was called with correct arguments
        print("Verifying spreadsheets.get was called once with correct args...")
        self.mock_spreadsheets.get.assert_called_once_with(spreadsheetId=SPREADSHEET_ID)
        
        # Verify execute was called on the returned mock
        print("Verifying execute was called on the returned mock...")
        mock_get.execute.assert_called_once()
        
        # Verify the spreadsheets service was accessed
        print("\n=== Verifying Spreadsheets Service Access ===")
        print(f"mock_service.spreadsheets.call_count: {self.mock_service.spreadsheets.call_count}")
        self.assertGreaterEqual(self.mock_service.spreadsheets.call_count, 1, 
                              "Expected spreadsheets() to be called at least once")
        
        print("\n=== test_get_all_tabs_success completed ===\n")
    
    def test_find_tab_by_identifier_found(self):
        """Test finding a tab by identifier when it exists."""
        # Mock the API response for get_all_tabs
        mock_tabs_response = {
            "sheets": [
                {"properties": {"title": self.test_tab}},
                {"properties": {"title": "Other Tab"}}
            ]
        }
        # Mock the API response for values.get
        mock_values_response = {"values": [["doc1.pdf"], [self.test_identifier], ["doc3.pdf"]]}
        # Set up the mock chain for get_all_tabs
        mock_get_tabs = MagicMock()
        mock_get_tabs.execute.return_value = mock_tabs_response
        self.mock_spreadsheets.get.return_value = mock_get_tabs
        # Set up the mock chain for values.get
        mock_values_get = MagicMock()
        mock_values_get.execute.return_value = mock_values_response
        self.mock_values.get.return_value = mock_values_get
        # Call the method
        result = self.client.find_tab_by_identifier(self.test_identifier)
        # Assertions
        self.assertEqual(result, self.test_tab)
        self.mock_values.get.assert_called_once_with(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{self.test_tab}'!C:C"
        )
        mock_values_get.execute.assert_called_once()
    
    def test_get_row_mapping(self):
        """Test getting row mappings for filenames."""
        # Mock the API response
        mock_response = {
            "values": [
                ["doc1.pdf"],
                ["doc2.pdf"],
                ["doc3.pdf"],
                ["other.pdf"]
            ]
        }
        # Set up the mock chain
        mock_values_get = MagicMock()
        mock_values_get.execute.return_value = mock_response
        self.mock_values.get.return_value = mock_values_get
        # Call the method
        row_map = self.client.get_row_mapping(self.test_tab, self.test_filenames)
        # Assertions
        expected = {"doc1.pdf": 1, "doc2.pdf": 2, "doc3.pdf": 3}
        self.assertEqual(row_map, expected)
        self.mock_values.get.assert_called_once_with(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{self.test_tab}'!C1:C1000"
        )
        mock_values_get.execute.assert_called_once()
        
        # Verify the spreadsheets service was accessed
        self.mock_service.spreadsheets.assert_called_once()
        self.mock_spreadsheets.values.assert_called_once()
        
        # Verify the correct filenames were processed
        self.assertEqual(set(row_map.keys()), set(self.test_filenames))
    
    def test_batch_update_cells_success(self):
        """Test successful batch update of cells."""
        # Set up the mock chain
        mock_batch_update = MagicMock()
        mock_batch_update.execute.return_value = {
            'spreadsheetId': SPREADSHEET_ID,
            'totalUpdatedCells': 2,
            'responses': [{'updatedRange': f"'{self.test_tab}'!A1:B1"}]
        }
        self.mock_values.batchUpdate.return_value = mock_batch_update
        # Test data
        updates = [
            {"range": "A1:B1", "values": [["Test", "Value"]]}
        ]
        # Call the method
        result = self.client.batch_update_cells(self.test_tab, updates)
        # Assertions
        self.assertTrue(result)
        expected_body = {
            "valueInputOption": "RAW",
            "data": [{
                "range": f"'{self.test_tab}'!A1:B1",
                "values": [["Test", "Value"]]
            }]
        }
        self.mock_values.batchUpdate.assert_called_once_with(
            spreadsheetId=SPREADSHEET_ID,
            body=expected_body
        )
        mock_batch_update.execute.assert_called_once()
        
        # Verify the service was built with correct arguments
        
        # Verify the spreadsheets service was accessed
        self.mock_service.spreadsheets.assert_called_once()
        self.mock_spreadsheets.values.assert_called_once()
    
    @patch('metadata_extractor.utils.sheets_client.logger')
    def test_batch_update_error_handling(self, mock_logger):
        """Test error handling in batch_update_cells."""
        # Mock an API error
        mock_batch_update = MagicMock()
        mock_batch_update.execute.side_effect = Exception("API Error")
        self.mock_values.batchUpdate.return_value = mock_batch_update
        # Call the method with test data
        updates = [
            {"range": "A1:B1", "values": [["Test", "Value"]]}
        ]
        result = self.client.batch_update_cells(self.test_tab, updates)
        # Assertions
        self.assertFalse(result)
        mock_logger.error.assert_called_once_with("Error updating cells: API Error")
        self.mock_values.batchUpdate.assert_called_once()
        mock_batch_update.execute.assert_called_once()
        
        # Verify the service was built with correct arguments
        
        # Verify the spreadsheets service was accessed
        self.mock_service.spreadsheets.assert_called_once()
        self.mock_spreadsheets.values.assert_called_once()


if __name__ == "__main__":
    unittest.main()
