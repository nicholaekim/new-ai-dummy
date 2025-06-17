import boto3
import openai
import json
import os
from typing import Dict, Any
from config.settings import OPENAI_API_KEY

def extract_text_with_textract(pdf_path: str) -> str:
    """Extract text from PDF using AWS Textract."""
    try:
        # Initialize Textract client with explicit region
        textract = boto3.client('textract', region_name='us-east-1')  # or your preferred AWS region
        
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

def extract_metadata_with_openai(text: str) -> Dict[str, Any]:
    """Extract structured metadata from text using OpenAI."""
    try:
        # Prepare the prompt
        prompt = f"""Extract the following metadata from the text below. 
        Return the result as a JSON object with these exact keys: "Title", "Date", "Volume", "Issue", "Description".
        If a field cannot be determined, use an empty string.
        
        Text:
        {text}
        
        JSON Response:"""
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts metadata from documents."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        # Parse the response
        result = response.choices[0].message.content.strip()
        
        # Sometimes the response includes markdown code blocks, so we need to extract the JSON
        if '```json' in result:
            result = result.split('```json')[1].split('```')[0].strip()
        
        # Parse the JSON string to a dictionary
        metadata = json.loads(result)
        
        # Ensure all required fields are present
        required_fields = ["Title", "Date", "Volume", "Issue", "Description"]
        for field in required_fields:
            if field not in metadata:
                metadata[field] = ""
                
        return metadata
        
    except Exception as e:
        print(f"Error extracting metadata with OpenAI: {e}")
        return {field: "" for field in ["Title", "Date", "Volume", "Issue", "Description"]}

def parse_with_textract_llm(pdf_path: str) -> dict:
    """
    Fallback: use AWS Textract + OpenAI LLM to extract metadata fields.
    
    Args:
        pdf_path: Path to the PDF file to process
        
    Returns:
        dict: Extracted metadata with keys: Title, Date, Volume, Issue, Description
    """
    print("Using Textract+OpenAI fallback for metadata extraction...")
    
    # First, extract text using Textract
    print(f"Extracting text from {pdf_path} using Textract...")
    text = extract_text_with_textract(pdf_path)
    
    if not text:
        print("No text could be extracted from the document")
        return {}
    
    # Then, extract metadata using OpenAI
    metadata = extract_metadata_with_openai(text)
    
    print(f"Extracted metadata: {metadata}")
    return metadata
