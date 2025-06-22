import os
import logging
from typing import Dict, Any
from google.cloud import documentai_v1 as documentai
from google.api_core.exceptions import GoogleAPICallError, PermissionDenied
from google.api_core.client_options import ClientOptions
from config.settings import GCP_PROJECT_ID, GCP_LOCATION, DOCAI_PROCESSOR
from .ocr_textract_llm import parse_with_textract

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_with_docai(pdf_path: str) -> Dict[str, Any]:
    """
    Extract metadata from PDF using Google Document AI with fallback to Textract+OpenAI.
    
    Args:
        pdf_path: Path to the PDF file to process
        
    Returns:
        dict: Extracted metadata with keys: Title, Date, Volume, Issue, Description
    """
    logger.info(f"Attempting to process {pdf_path} with Document AI...")
    
    # Initialize the Document AI client
    try:
        # Set up client options with the correct endpoint
        client_options = ClientOptions(api_endpoint=f"{GCP_LOCATION}-documentai.googleapis.com")
        client = documentai.DocumentProcessorServiceClient(client_options=client_options)
        
        # The full resource name of the processor
        name = f"projects/{GCP_PROJECT_ID}/locations/{GCP_LOCATION}/processors/{DOCAI_PROCESSOR}"
        
        # Read the file into memory
        with open(pdf_path, "rb") as f:
            file_content = f.read()
        
        # Configure the process request
        raw_document = documentai.RawDocument(
            content=file_content, 
            mime_type="application/pdf"
        )
        
        try:
            # Process the document
            logger.debug("Sending document to Document AI...")
            result = client.process_document(
                request={
                    "name": name,
                    "raw_document": raw_document
                }
            )
            
            # Extract text and metadata
            document = result.document
            text = document.text
            
            # Initialize metadata with default values
            metadata = {
                "Title": document.title or "",
                "Date": document.create_time.strftime("%Y-%m-%d") if document.create_time else "",
                "Volume": "",
                "Issue": "",
                "Description": text[:500] if text else ""  # First 500 chars as description
            }
            
            logger.info("Successfully processed document with Document AI")
            return metadata
            
        except (GoogleAPICallError, PermissionDenied) as e:
            logger.warning(f"Document AI failed (will try Textract+OpenAI fallback): {e}")
            # Fall back to Textract+OpenAI
            return parse_with_textract_llm(pdf_path)
            
        except Exception as e:
            logger.error(f"Unexpected error with Document AI: {e}")
            # Fall back to Textract+OpenAI
            return parse_with_textract_llm(pdf_path)
            
    except Exception as e:
        logger.error(f"Failed to initialize Document AI client: {e}")
        # Fall back to Textract
        return parse_with_textract(pdf_path)
