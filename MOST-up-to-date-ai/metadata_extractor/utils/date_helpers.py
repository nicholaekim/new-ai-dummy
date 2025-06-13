"""
Date parsing and metadata extraction utilities for the metadata extractor.

This module provides functions to extract and parse dates from text using
regex patterns and fuzzy parsing, as well as simple metadata extraction.
"""

import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Union
from dateutil.parser import parse as parse_date
from dateutil.parser._parser import ParserError

logger = logging.getLogger(__name__)

def regex_date(text: str) -> str:
    """
    Extract a date from text using simple regex patterns.
    
    Tries to find dates in common formats like dd/mm/yyyy or yyyy.
    
    Args:
        text: Text to search for dates
        
    Returns:
        Formatted date string (YYYY/MM/DD) or "UNKNOWN" if no date found
    """
    if not text:
        return "UNKNOWN"
        
    try:
        # Try to find dates in format dd/mm/yyyy, dd-mm-yyyy, or yyyy
        match = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4})\b", text)
        if match:
            try:
                # Parse the matched date and reformat it
                date_str = match.group(1)
                dt = parse_date(date_str, dayfirst=True, yearfirst=False)
                return dt.strftime("%Y/%m/%d")
            except (ValueError, ParserError) as e:
                logger.debug(f"Failed to parse date '{match.group(0)}': {e}")
                return match.group(0)  # Return the matched string if parsing fails
    except Exception as e:
        logger.error(f"Error in regex_date: {e}", exc_info=True)
        
    return "UNKNOWN"

def simple_metadata(full_text: str) -> Dict[str, str]:
    """
    Extract basic metadata from text.
    
    Extracts:
    - Title: First non-empty line
    - Description: First 100 characters of text
    - Date: Extracted using regex_date
    
    Args:
        full_text: Text to extract metadata from
        
    Returns:
        Dictionary with 'Title', 'Description', and 'Date' keys
    """
    if not full_text:
        return {
            "Title": "UNKNOWN",
            "Description": "UNKNOWN",
            "Date": "UNKNOWN"
        }
    
    try:
        # Get first non-empty line as title
        lines = [line.strip() for line in full_text.splitlines() if line.strip()]
        title = lines[0] if lines else "UNKNOWN"
        
        # Get first 100 chars as description
        desc = full_text.replace("\n", " ")[:100].strip() or "UNKNOWN"
        
        # Extract date
        date = regex_date(full_text)
        
        return {
            "Title": title,
            "Description": desc,
            "Date": date
        }
    except Exception as e:
        logger.error(f"Error in simple_metadata: {e}", exc_info=True)
        return {
            "Title": "ERROR",
            "Description": str(e),
            "Date": "UNKNOWN"
        }

def simple_metadata(
    text: str, 
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Extract basic metadata including dates from text.
    
    Args:
        text: Text to analyze
        year: Optional expected year for date extraction
        
    Returns:
        Dictionary containing extracted metadata
    """
    if not text:
        return {}
    
    # Extract date
    date_obj = extract_date(text, year=year)
    
    # Prepare result
    result = {
        'text_length': len(text),
        'date_found': date_obj is not None,
        'date': date_obj.isoformat() if date_obj else None,
    }
    
    # Add year if available
    if date_obj:
        result['year'] = date_obj.year
    
    return result
