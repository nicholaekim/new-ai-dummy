"""
OCR (Optical Character Recognition) helper functions for the metadata extractor.

This module provides functions to preprocess images and perform OCR on PDF documents.
"""

import logging
import os
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional, Union
import cv2
import numpy as np
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError, PDFSyntaxError

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
    if not os.path.exists(pdf_path):
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
        logger.error(f"Error during OCR processing of {pdf_path}: {str(e)}", exc_info=True)
        raise RuntimeError(f"OCR processing failed: {str(e)}")
        
        # Calculate overall confidence
        overall_confidence = (total_confidence / total_chars) if total_chars > 0 else 0
        
        # Prepare metadata
        metadata = {
            'num_pages': len(images),
            'ocr_confidence': overall_confidence,
            'language': lang,
            'dpi': dpi,
            'preprocessing': 'adaptive_thresholding'
        }
        
        return '\n\n'.join(all_text), metadata
        
    except Exception as e:
        logger.error(f"Error during OCR processing of {pdf_path}: {e}")
        raise
