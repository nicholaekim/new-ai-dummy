"""Unit tests for Google Sheets client."""
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestSheetsClient(unittest.TestCase):
    """Test cases for Google Sheets client."""
    
    @patch('metadata_extractor.utils.sheets_client.build')
    @patch('metadata_extractor.utils.sheets_client.service_account.Credentials.from_service_account_file')
    def test_sheets_client_init(self, mock_creds, mock_build):
        """Test SheetsClient initialization with credentials file."""
        from metadata_extractor.utils.sheets_client import SheetsClient
        
        # Setup mocks
        mock_creds_instance = MagicMock()
        mock_creds.return_value = mock_creds_instance
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Test with service account file
        client = SheetsClient(credentials_path='dummy_creds.json')
        
        # Assertions
        mock_creds.assert_called_once_with(
            'dummy_creds.json',
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        mock_build.assert_called_once_with('sheets', 'v4', credentials=mock_creds_instance)
        self.assertEqual(client.service, mock_service)
    
    def test_sheets_client_init_with_service(self):
        """Test SheetsClient initialization with pre-configured service."""
        from metadata_extractor.utils.sheets_client import SheetsClient
        
        # Create a mock service
        mock_service = MagicMock()
        
        # Initialize with pre-configured service
        client = SheetsClient(service=mock_service)
        
        # Assertions
        self.assertEqual(client.service, mock_service)
    
    @patch('metadata_extractor.utils.sheets_client.build')
    @patch('metadata_extractor.utils.sheets_client.service_account.Credentials.from_service_account_file')
    def test_sheets_client_init_default_creds(self, mock_creds, mock_build):
        """Test SheetsClient initialization with default credentials."""
        from metadata_extractor.utils.sheets_client import SheetsClient
        from metadata_extractor.config import SERVICE_KEY
        
        # Setup mocks
        mock_creds_instance = MagicMock()
        mock_creds.return_value = mock_creds_instance
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Test with default credentials
        client = SheetsClient()
        
        # Assertions
        mock_creds.assert_called_once_with(
            str(SERVICE_KEY),
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        mock_build.assert_called_once_with('sheets', 'v4', credentials=mock_creds_instance)
    
    @patch('metadata_extractor.utils.sheets_client.build')
    @patch('metadata_extractor.utils.sheets_client.service_account.Credentials.from_service_account_file')
    def test_sheets_client_init_error(self, mock_creds, mock_build):
        """Test SheetsClient initialization with error."""
        from metadata_extractor.utils.sheets_client import SheetsClient
        
        # Setup mock to raise an exception
        mock_creds.side_effect = Exception("Credential error")
        
        # Test that the exception is raised
        with self.assertRaises(Exception) as context:
            SheetsClient(credentials_path='invalid_creds.json')
        
        self.assertIn("Credential error", str(context.exception))
    
    def test_update_sheet(self):
        """Test updating a sheet with data."""
        from metadata_extractor.utils.sheets_client import SheetsClient
        
        # Setup test data
        test_data = [
            ['Title', 'Date', 'Volume'],
            ['Doc 1', '2022-01-01', 1],
            ['Doc 2', '2022-01-02', 2]
        ]
        
        # Setup mocks
        mock_service = MagicMock()
        mock_sheets = MagicMock()
        mock_service.spreadsheets.return_value = mock_sheets
        mock_values = MagicMock()
        mock_sheets.values.return_value = mock_values
        mock_update = MagicMock()
        mock_values.update.return_value = mock_update
        mock_execute = MagicMock()
        mock_update.execute = mock_execute
        
        # Create client with mocked service
        client = SheetsClient(service=mock_service)
        
        # Call the method
        client.update_sheet('test_spreadsheet', 'Sheet1', test_data)
        
        # Assertions
        mock_sheets.values.assert_called_once()
        mock_values.update.assert_called_once()
        mock_execute.assert_called_once()
    
    def test_update_sheet_handles_errors(self):
        """Test error handling in update_sheet."""
        from googleapiclient.errors import HttpError
        from metadata_extractor.utils.sheets_client import SheetsClient
        
        # Setup mocks
        mock_service = MagicMock()
        mock_sheets = MagicMock()
        mock_service.spreadsheets.return_value = mock_sheets
        mock_values = MagicMock()
        mock_sheets.values.return_value = mock_values
        mock_update = MagicMock()
        mock_values.update.return_value = mock_update
        
        # Mock HTTP error
        error_content = b'{"error": {"code": 404, "message": "Not found"}}'
        mock_update.execute.side_effect = HttpError(
            resp=MagicMock(status=404, reason='Not Found'),
            content=error_content
        )
        
        # Create client with mocked service
        client = SheetsClient(service=mock_service)
        
        # Call the method and assert it raises HttpError
        with self.assertRaises(HttpError):
            client.update_sheet('test_spreadsheet', 'Sheet1', [['Test']])
    
    def test_get_all_tabs(self):
        """Test getting all sheet tabs."""
        from metadata_extractor.utils.sheets_client import SheetsClient
        
        # Setup mocks
        mock_service = MagicMock()
        mock_sheets = MagicMock()
        mock_service.spreadsheets.return_value = mock_sheets
        mock_get = MagicMock()
        mock_sheets.get.return_value = mock_get
        
        # Mock the response
        mock_response = {
            'sheets': [
                {'properties': {'title': 'Sheet1'}},
                {'properties': {'title': 'Sheet2'}},
                {'properties': {}}  # Should be skipped
            ]
        }
        mock_get.execute.return_value = mock_response
        
        # Create client with mocked service
        client = SheetsClient(service=mock_service)
        
        # Call the method
        tabs = client.get_all_tabs()
        
        # Assertions
        self.assertEqual(tabs, ['Sheet1', 'Sheet2'])
        mock_sheets.get.assert_called_once()
        
    def test_find_tab_by_identifier(self):
        """Test finding a tab by identifier in column C."""
        from metadata_extractor.utils.sheets_client import SheetsClient
        
        # Setup mocks
        mock_service = MagicMock()
        
        # Mock get_all_tabs
        with patch.object(SheetsClient, 'get_all_tabs', return_value=['Sheet1', 'Sheet2']):
            # Mock spreadsheets().values().get() responses
            mock_sheets = MagicMock()
            mock_service.spreadsheets.return_value = mock_sheets
            mock_values = MagicMock()
            mock_sheets.values.return_value = mock_values
            
            # First call returns empty values, second call returns our identifier
            mock_values.get.return_value.execute.side_effect = [
                {'values': [['Not it'], ['Still not']]},
                {'values': [['Not this one'], ['Our Identifier']]}
            ]
            
            # Create client with mocked service
            client = SheetsClient(service=mock_service)
            
            # Call the method
            result = client.find_tab_by_identifier('Our Identifier')
            
            # Assertions
            self.assertEqual(result, 'Sheet2')
            self.assertEqual(mock_values.get.call_count, 2)
            
    def test_get_row_mapping(self):
        """Test getting row mapping for filenames."""
        from metadata_extractor.utils.sheets_client import SheetsClient
        
        # Setup mocks
        mock_service = MagicMock()
        mock_sheets = MagicMock()
        mock_service.spreadsheets.return_value = mock_sheets
        mock_values = MagicMock()
        mock_sheets.values.return_value = mock_values
        
        # Mock the response
        mock_response = {
            'values': [
                ['file1.pdf'],
                [],
                ['file2.pdf'],
                ['file3.pdf']
            ]
        }
        mock_values.get.return_value.execute.return_value = mock_response
        
        # Test spreadsheet ID
        test_spreadsheet_id = 'test_spreadsheet_123'
        
        # Create client with mocked service and test spreadsheet ID
        client = SheetsClient(service=mock_service, spreadsheet_id=test_spreadsheet_id)
        
        # Call the method
        result = client.get_row_mapping('TestSheet', ['file2.pdf', 'file3.pdf'])
        
        # Assertions
        expected = {'file2.pdf': 3, 'file3.pdf': 4}
        self.assertEqual(result, expected)
        mock_values.get.assert_called_once_with(
            spreadsheetId=test_spreadsheet_id,
            range="'TestSheet'!C1:C1000"
        )
        
    def test_batch_update_cells(self):
        """Test batch updating cells."""
        from metadata_extractor.utils.sheets_client import SheetsClient
        
        # Setup mocks
        mock_service = MagicMock()
        mock_sheets = MagicMock()
        mock_service.spreadsheets.return_value = mock_sheets
        mock_values = MagicMock()
        mock_sheets.values.return_value = mock_values
        mock_batch_update = MagicMock()
        mock_values.batchUpdate.return_value = mock_batch_update
        mock_execute = MagicMock(return_value={'responses': [{}]})
        mock_batch_update.execute = mock_execute
        
        # Create test data
        updates = [
            {'range': 'A1', 'values': [['Value1']]},
            {'range': 'B2', 'values': [['Value2']]}
        ]
        
        # Create client with mocked service
        client = SheetsClient(service=mock_service, spreadsheet_id='test_spreadsheet_id')
        
        # Call the method
        result = client.batch_update_cells('TestSheet', updates)
        
        # Assertions
        self.assertTrue(result)
        mock_values.batchUpdate.assert_called_once_with(
            spreadsheetId='test_spreadsheet_id',
            body={
                'valueInputOption': 'USER_ENTERED',
                'data': [
                    {'range': "'TestSheet'!A1", 'values': [['Value1']]},
                    {'range': "'TestSheet'!B2", 'values': [['Value2']]}
                ]
            }
        )
        
    def test_batch_update_cells_empty(self):
        """Test batch updating with empty updates list."""
        from metadata_extractor.utils.sheets_client import SheetsClient
        
        # Create client with mocked service
        client = SheetsClient(service=MagicMock())
        
        # Call the method with empty updates
        result = client.batch_update_cells('TestSheet', [])
        
        # Assertions
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
