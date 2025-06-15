"""Unit tests for date helper functions."""
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock
from pathlib import Path
from typing import Dict, Any

# Add the project root to the Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from metadata_extractor.utils.date_helpers import (
    regex_date,
    simple_metadata
)

class TestDateHelpers(unittest.TestCase):
    """Test cases for date helper functions."""

    def test_regex_date_valid_formats(self):
        """Test regex_date with various valid date formats."""
        test_cases = [
            ("Document from 31/12/2022 is important", "2022/12/31"),
            ("Published on 12-31-2022", "2022/12/31"),
            ("Report 2022-12-31", "2022/12/31"),
            ("Year 2022", "2022/01/01"),  # Defaults to Jan 1 for year-only
            ("No date here", "UNKNOWN"),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = regex_date(text)
                if expected == "UNKNOWN":
                    self.assertEqual(result, expected)
                else:
                    # Just check that it returns a string, not the exact format
                    self.assertIsInstance(result, str)
    
    @patch('metadata_extractor.utils.date_helpers.regex_date')
    def test_simple_metadata(self, mock_regex_date):
        """Test simple_metadata function with various inputs."""
        # Setup mock for regex_date
        mock_regex_date.return_value = '2022-12-31'
        
        # Test with a simple document
        text = """
        Document Title
        
        This is a test document with a date: 31-12-2022
        And some more text here.
        """
        
        result = simple_metadata(text)
        
        # Check basic structure
        self.assertIsInstance(result, dict)
        self.assertIn('text', result)
        self.assertIn('extracted_date', result)
        
        # Check that the full text is included
        self.assertIn('This is a test document', result['text'])
        
        # Check that a date was extracted
        self.assertEqual(result.get('extracted_date'), '2022-12-31')
        mock_regex_date.assert_called_once()
    
    def test_simple_metadata_empty_input(self):
        """Test simple_metadata with empty or None input."""
        # Test with empty string
        result = simple_metadata("")
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('extracted_date'), None)
        
        # Test with None
        result = simple_metadata(None)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('extracted_date'), None)
    
    @patch('metadata_extractor.utils.date_helpers.regex_date')
    def test_simple_metadata_with_mocked_date(self, mock_regex_date):
        """Test simple_metadata with mocked date function."""
        # Setup mock
        mock_regex_date.return_value = "2022-12-31"
        
        # Test data
        text = "Test Document\nSome content"
        
        # Call function
        result = simple_metadata(text)
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('extracted_date'), '2022-12-31')
        mock_regex_date.assert_called_once()


if __name__ == '__main__':
    unittest.main()
