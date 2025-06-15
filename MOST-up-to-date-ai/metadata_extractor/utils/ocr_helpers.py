"""
OCR (Optical Character Recognition) helper functions for the metadata extractor.

This module provides functions to preprocess images and perform OCR on PDF documents,
including extracting titles from the first page of PDFs.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, cast

import cv2
import numpy as np
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError

from ..config import TESSERACT_CONFIG

logger = logging.getLogger(__name__)

def preprocess_page(pil_page: Image.Image) -> np.ndarray:
    """
    Preprocess a page image for better OCR results.
    
    This function performs the following preprocessing steps:
    1. Convert PIL Image to OpenCV format (BGR)
    2. Convert to grayscale
    3. Apply adaptive thresholding
    4. Optional: Deskew the image
    
    Args:
        pil_page: PIL Image object to preprocess
        
    Returns:
        Preprocessed image as a numpy array
        
    Raises:
        ValueError: If input image is invalid
        cv2.error: If OpenCV operations fail
    """
    try:
        if not isinstance(pil_page, Image.Image):
            raise ValueError("Input must be a PIL Image")
            
        # Convert PIL Image to OpenCV format (BGR)
        img = cv2.cvtColor(np.array(pil_page), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding with Gaussian
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 51, 10
        )
        
        # Deskew the image
        coords = np.column_stack(np.where(binary > 0))
        if len(coords) > 0:  # Check if we have any white pixels
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle += 90
            elif angle > 45:
                angle -= 90
                
            (h, w) = binary.shape
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            binary = cv2.warpAffine(binary, M, (w, h),
                                 flags=cv2.INTER_CUBIC,
                                 borderMode=cv2.BORDER_REPLICATE)
        
        return binary
        
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}", exc_info=True)
        raise

def ocr_pdf(
    pdf_path: Union[str, Path],
    dpi: int = 300,
    lang: str = 'eng'
) -> Tuple[str, float]:
    """
    Perform OCR on a PDF file and return the extracted text and average confidence.
    
    Args:
        pdf_path: Path to the PDF file
        dpi: DPI for image conversion (default: 300)
        lang: Language for OCR (default: 'eng')
        
    Returns:
        Tuple of (extracted_text, average_confidence)
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        PDFPageCountError: If PDF is empty or corrupted
        RuntimeError: If OCR processing fails
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    try:
        # Convert PDF to images
        logger.info(f"Converting PDF to images: {pdf_path}")
        pages = convert_from_path(pdf_path, dpi=dpi)
        
        full_text = ""
        confs = []
        
        for i, pil_page in enumerate(pages, 1):
            logger.debug(f"Processing page {i}")
            
            # Preprocess the image
            img = preprocess_page(pil_page)
            
            # Run Tesseract OCR
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            txt = pytesseract.image_to_string(img, lang=lang)
            full_text += txt + "\n\n"
            
            # Collect per-word confidences (handle both str and int)
            word_confs = []
            for c in data.get("conf", []):
                try:
                    ci = int(c)
                    if ci >= 0:  # Negative values indicate errors
                        word_confs.append(ci)
                except (ValueError, TypeError):
                    continue
            
            # Calculate average confidence for this page
            if word_confs:
                confs.append(sum(word_confs) / len(word_confs))
            else:
                confs.append(0)
        
        # Calculate overall average confidence
        avg_conf = sum(confs) / len(confs) if confs else 0
        
        return full_text.strip(), avg_conf
        
    except PDFPageCountError as e:
        logger.error(f"Invalid or empty PDF: {pdf_path}")
        raise RuntimeError(f"Failed to process PDF (may be empty or corrupted): {str(e)}")
    except Exception as e:
        logger.error(f"Error in ocr_pdf: {str(e)}")
        raise RuntimeError(f"OCR processing failed: {str(e)}")


def extract_title_from_first_page(
    pdf_path: Union[str, Path],
    dpi: int = 300,
    lang: str = 'eng',
    max_lines: int = 10,
    min_confidence: float = 70.0
) -> Optional[str]:
    """
    Extract a title from the first page of a PDF document.
    
    This function performs OCR on the first page of the PDF and attempts to identify
    the title by looking for the first significant line of text with sufficient confidence.
    
    Args:
        pdf_path: Path to the PDF file
        dpi: DPI for image conversion (default: 300)
        lang: Language for OCR (default: 'eng')
        max_lines: Maximum number of lines to consider from the top of the page
        min_confidence: Minimum confidence threshold for OCR results (0-100)
        
    Returns:
        Extracted title as a string, or None if no suitable title could be found
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        PDFPageCountError: If PDF is empty or corrupted
        RuntimeError: If OCR processing fails
    """
    try:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        # Convert only the first page of the PDF to an image
        images = convert_from_path(
            str(pdf_path),
            first_page=1,
            last_page=1,
            dpi=dpi,
            thread_count=1
        )
        
        if not images:
            logger.warning(f"No pages found in PDF: {pdf_path}")
            return None
            
        # Preprocess the first page image
        img = preprocess_page(images[0])
        
        # Configure Tesseract
        custom_config = TESSERACT_CONFIG.copy()
        custom_config.update({
            'lang': lang,
            'dpi': dpi,
            'config': '--psm 6 --oem 1'  # Assume a single uniform block of text, use LSTM OCR Engine
        })
        
        # Get OCR data including text and confidence
        data = pytesseract.image_to_data(
            img,
            output_type=pytesseract.Output.DICT,
            **custom_config
        )
        
        # Extract text with confidence scores
        lines: Dict[int, Dict[str, List[Any]]] = {}
        
        for i in range(len(data['text'])):
            # Skip empty text
            if not data['text'][i].strip():
                continue
                
            # Get line number and text
            line_num = data['line_num'][i]
            conf = data['conf'][i]
            text = data['text'][i].strip()
            
            # Skip low confidence results
            if conf < min_confidence:
                continue
                
            if line_num not in lines:
                lines[line_num] = {'text': [], 'confidence': []}
                
            lines[line_num]['text'].append(text)
            lines[line_num]['confidence'].append(conf)
        
        # Process lines to find the most likely title
        for line_num in sorted(lines.keys())[:max_lines]:
            line_data = lines[line_num]
            confidences = cast(List[float], line_data['confidence'])
            avg_confidence = sum(confidences) / len(confidences)
            
            if avg_confidence >= min_confidence:
                title = ' '.join(cast(List[str], line_data['text'])).strip()
                
                # Skip very short lines (likely not a title)
                if len(title) < 5:
                    continue
                    
                # Clean up the title
                title = re.sub(r'\s+', ' ', title)  # Normalize whitespace
                title = title.strip('"\'.,;:!?()[]{}')  # Remove surrounding punctuation
                
                logger.debug(f"Potential title found: {title} (confidence: {avg_confidence:.1f}%)")
                return title
        
        logger.warning(f"No suitable title found in first {max_lines} lines of {pdf_path}")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting title from {pdf_path}: {str(e)}")
        return None

def extract_title(pdf_path: str) -> str:
    images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=1)
    text = pytesseract.image_to_string(images[0])
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""
