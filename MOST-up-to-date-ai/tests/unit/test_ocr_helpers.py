"""Unit tests for OCR helper functions."""
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import numpy as np
from PIL import Image

# Add the project root to the Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestOCRHelpers(unittest.TestCase):
    """Test cases for OCR helper functions."""
    
    @patch('metadata_extractor.utils.ocr_helpers.cv2')
    def test_preprocess_page(self, mock_cv2):
        """Test the image preprocessing function."""
        from metadata_extractor.utils.ocr_helpers import preprocess_page
        
        # Create a mock PIL Image
        pil_img = Image.new('RGB', (100, 100), color='white')
        
        # Mock cv2 functions
        mock_cv2.COLOR_RGB2BGR = 'rgb2bgr'
        mock_cv2.COLOR_BGR2GRAY = 'bgr2gray'
        mock_cv2.ADAPTIVE_THRESH_GAUSSIAN_C = 'gaussian'
        mock_cv2.THRESH_BINARY = 'binary'
        mock_cv2.THRESH_OTSU = 'otsu'
        mock_cv2.THRESH_BINARY_INV = 'binary_inv'
        mock_cv2.RETR_EXTERNAL = 'retr_external'
        mock_cv2.CHAIN_APPROX_SIMPLE = 'chain_approx_simple'
        
        # Mock cv2 function returns
        mock_cv2.cvtColor.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv2.threshold.return_value = (0, np.zeros((100, 100), dtype=np.uint8))
        mock_cv2.adaptiveThreshold.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv2.getStructuringElement.return_value = np.ones((3, 3), dtype=np.uint8)
        mock_cv2.dilate.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv2.erode.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv2.GaussianBlur.return_value = np.zeros((100, 100), dtype=np.uint8)
        
        # Mock the return value for minAreaRect
        rect_mock = MagicMock()
        rect_mock[1] = (10, 10)  # width, height
        rect_mock[2] = 0  # angle
        mock_cv2.minAreaRect.return_value = rect_mock
        
        # Mock cv2.warpAffine to return a numpy array
        def mock_warp_affine(img, M, *args, **kwargs):
            return np.zeros_like(img) if len(img.shape) == 2 else np.zeros((*img.shape[:2], 1), dtype=np.uint8)
            
        mock_cv2.warpAffine.side_effect = mock_warp_affine
        
        # Mock cv2.getRotationMatrix2D to return a simple matrix
        mock_cv2.getRotationMatrix2D.return_value = np.eye(2, 3)
        
        # Call the function
        result = preprocess_page(pil_img)
        
        # Assertions
        self.assertIsInstance(result, np.ndarray)
        self.assertIn(len(result.shape), [2, 3])  # Can be grayscale (2D) or color (3D)
    
    @patch('metadata_extractor.utils.ocr_helpers.convert_from_path')
    @patch('metadata_extractor.utils.ocr_helpers.pytesseract')
    @patch('metadata_extractor.utils.ocr_helpers.preprocess_page')
    def test_ocr_pdf(self, mock_preprocess, mock_pytesseract, mock_convert):
        """Test the PDF OCR function."""
        from metadata_extractor.utils.ocr_helpers import ocr_pdf
        
        # Create a temporary test PDF file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            pdf_path = tmp.name
        
        try:
            # Setup mocks
            mock_img = MagicMock()
            mock_convert.return_value = [mock_img] * 2  # Two pages
            
            # Mock preprocess_page to return a numpy array
            mock_preprocess.return_value = np.zeros((100, 100), dtype=np.uint8)
            
            # Mock pytesseract output
            mock_pytesseract.image_to_data.return_value = {
                'text': ['Hello', 'World'],
                'conf': [90, 80]
            }
            mock_pytesseract.image_to_string.return_value = 'Hello\nWorld'
            
            # Call the function
            text, confidence = ocr_pdf(pdf_path)
            
            # Assertions
            self.assertIsInstance(text, str)
            self.assertIsInstance(confidence, float)
            self.assertGreaterEqual(confidence, 0)
            self.assertLessEqual(confidence, 100)
            
            mock_convert.assert_called_once()
            self.assertEqual(mock_pytesseract.image_to_data.call_count, 2)
            
        finally:
            # Clean up the temporary file
            import os
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
    
    @patch('metadata_extractor.utils.ocr_helpers.convert_from_path')
    @patch('metadata_extractor.utils.ocr_helpers.pytesseract')
    @patch('metadata_extractor.utils.ocr_helpers.preprocess_page')
    def test_extract_title_from_first_page(self, mock_preprocess, mock_pytesseract, mock_convert):
        """Test title extraction from first page."""
        from metadata_extractor.utils.ocr_helpers import extract_title_from_first_page
        
        # Create a temporary test PDF file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            pdf_path = tmp.name
        
        try:
            # Setup mocks
            mock_img = MagicMock()
            mock_convert.return_value = [mock_img]  # Single page
            
            # Mock preprocess_page to return a numpy array
            mock_preprocess.return_value = np.zeros((100, 100), dtype=np.uint8)
            
            # Mock pytesseract output with title-like text
            mock_pytesseract.image_to_data.return_value = {
                'text': ['', 'Document', 'Title', '', 'Subtitle', ''],
                'conf': [0, 95, 92, 0, 90, 0],
                'line_num': [0, 1, 1, 2, 2, 3],
            }
            mock_pytesseract.image_to_string.return_value = 'Document Title'
            
            # Call the function
            title = extract_title_from_first_page(pdf_path)
            
            # Assertions
            self.assertIsNotNone(title)
            self.assertIn('Document', title)
            self.assertIn('Title', title)
            mock_convert.assert_called_once()
            mock_pytesseract.image_to_data.assert_called_once()
            
        finally:
            # Clean up the temporary file
            import os
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
    
    def test_extract_title_no_pages(self):
        """Test title extraction when no pages are found."""
        from metadata_extractor.utils.ocr_helpers import extract_title_from_first_page
        
        with patch('metadata_extractor.utils.ocr_helpers.convert_from_path') as mock_convert:
            mock_convert.return_value = []  # No pages
            
            title = extract_title_from_first_page('nonexistent.pdf')
            self.assertIsNone(title)


if __name__ == '__main__':
    unittest.main()
