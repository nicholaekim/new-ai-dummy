import boto3
import os
import re
from typing import Dict, Any
from datetime import datetime

def extract_text_with_textract(pdf_path: str) -> str:
    """
    Extract text from PDF using AWS Textract.
    
    Args:
        pdf_path: Path to the PDF file to process
        
    Returns:
        str: Extracted text from the document
    """
    try:
        from config.settings import AWS_REGION
        # Initialize Textract client with region from settings
        textract = boto3.client('textract', region_name=AWS_REGION)
        
        # Read the PDF file
        with open(pdf_path, 'rb') as file:
            img_bytes = file.read()
        
        # Call Textract
        response = textract.detect_document_text(Document={'Bytes': img_bytes})
        
        # Extract text from response
        text = ''
        for item in response.get('Blocks', []):
            if item['BlockType'] == 'LINE':
                text += item['Text'] + '\n'
                
        return text.strip()
    except Exception as e:
        print(f"Error extracting text with Textract: {e}")
        return ""

def extract_metadata_from_text(text: str, filename: str) -> Dict[str, Any]:
    """
    Extract metadata directly from text using pattern matching.
    
    Args:
        text: Extracted text from the document
        filename: Original filename for fallback title
        
    Returns:
        dict: Extracted metadata with keys: Title, Date, Volume, Issue, Description
    """
    metadata = {
        'Title': '',
        'Date': '',
        'Volume': '',
        'Issue': '',
        'Description': text[:200]  # First 200 chars as description
    }
    
    # Try to extract title (first non-empty line)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        metadata['Title'] = lines[0]
    else:
        metadata['Title'] = os.path.splitext(os.path.basename(filename))[0]
    
    # Try to find date patterns (YYYY-MM-DD, MM/DD/YYYY, etc.)
    date_patterns = [
        r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b',  # YYYY-MM-DD or YYYY/MM/DD
        r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',  # MM-DD-YYYY or MM/DD/YYYY
        r'\b(\d{1,2}\s+[A-Za-z]+\s+\d{4})\b',  # DD Month YYYY
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                # Try to parse the date and format it consistently
                date_str = match.group(1)
                # Try different date formats
                for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d %B %Y', '%B %d, %Y'):
                    try:
                        date_obj = datetime.strptime(date_str, fmt)
                        metadata['Date'] = date_obj.strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        continue
                if metadata['Date']:
                    break
            except (IndexError, ValueError):
                continue
    
    # Try to find volume/issue numbers
    vol_issue_patterns = [
        (r'\b[Vv]ol\.?\s*(\d+)\b', 'Volume'),
        (r'\b[Vv](?:olume)?\s*(\d+)\b', 'Volume'),
        (r'\b[Nn]o\.?\s*(\d+)\b', 'Issue'),
        (r'\b[Ii]ssue\s*(\d+)\b', 'Issue'),
    ]
    
    for pattern, field in vol_issue_patterns:
        match = re.search(pattern, text)
        if match:
            metadata[field] = match.group(1)
    
    return metadata

def parse_with_textract(pdf_path: str) -> dict:
    """
    Extract metadata from PDF using AWS Textract.
    
    This is the fallback method when Document AI fails.
    
    Args:
        pdf_path: Path to the PDF file to process
        
    Returns:
        dict: Extracted metadata with keys: Title, Date, Volume, Issue, Description
    """
    print(f"Extracting text from {pdf_path} using Textract...")
    text = extract_text_with_textract(pdf_path)
    
    if not text:
        print("No text could be extracted from the document")
        return {}
    
    # Extract metadata from the extracted text
    print("Extracting metadata from text...")
    metadata = extract_metadata_from_text(text, pdf_path)
    
    return metadata
