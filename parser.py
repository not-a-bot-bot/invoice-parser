"""
Invoice Parser Module
Extracts structured data from invoice PDFs using Claude API.

Architecture:
1. Extract text/images from PDF
2. Send to Claude with a structured prompt
3. Parse Claude's response into a clean dictionary
"""

import os
import json
import base64
from io import BytesIO
from dotenv import load_dotenv
from anthropic import Anthropic
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
from PIL import Image

# Load environment variables from .env file
load_dotenv()

# Initialize the Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract raw text from a PDF file.
    
    This works well for digitally-created PDFs (not scanned images).
    Returns empty string if no text found (likely a scanned document).
    """
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""


def pdf_to_base64_image(pdf_file) -> str:
    """
    Convert first page of PDF to base64-encoded image.
    
    This is our fallback for scanned invoices where text extraction fails.
    Claude can read the image directly using its vision capabilities.
    """
    try:
        # Read PDF bytes
        pdf_bytes = pdf_file.read()
        pdf_file.seek(0)  # Reset file pointer for potential reuse
        
        # Convert first page to image
        images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1)
        
        if images:
            # Convert to base64
            img_buffer = BytesIO()
            images[0].save(img_buffer, format='PNG')
            img_buffer.seek(0)
            return base64.standard_b64encode(img_buffer.read()).decode('utf-8')
    except Exception as e:
        print(f"Error converting PDF to image: {e}")
    return None


def parse_invoice_with_claude(pdf_file) -> dict:
    """
    Main function: Extract invoice data using Claude.
    
    Strategy:
    1. First try text extraction (faster, cheaper)
    2. If text is too short/empty, fall back to image-based extraction
    3. Send to Claude with a structured extraction prompt
    4. Parse the JSON response
    """
    
    # Try text extraction first
    extracted_text = extract_text_from_pdf(pdf_file)
    
    # Define what fields we want to extract
    # This is customizable based on your needs
    extraction_prompt = """
    Extract the following information from this invoice. 
    Return ONLY a valid JSON object with these fields (use null if not found):
    
    {
        "invoice_number": "string - the invoice/bill number",
        "invoice_date": "string - date in YYYY-MM-DD format if possible",
        "due_date": "string - payment due date in YYYY-MM-DD format if possible, null if not mentioned",
        "vendor": {
            "name": "string - seller/vendor company name",
            "address": "string - vendor address",
            "gstin": "string - GST identification number if present"
        },
        "buyer": {
            "name": "string - buyer/customer name",
            "address": "string - buyer address", 
            "gstin": "string - buyer GSTIN if present"
        },
        "line_items": [
            {
                "description": "string - item/service description",
                "hsn_code": "string - HSN/SAC code if present",
                "quantity": "number",
                "unit_price": "number",
                "amount": "number - line total"
            }
        ],
        "subtotal": "number - sum before taxes",
        "tax_details": {
            "cgst": "number - Central GST amount",
            "sgst": "number - State GST amount", 
            "igst": "number - Integrated GST amount",
            "total_tax": "number - total tax amount"
        },
        "total_amount": "number - final payable amount",
        "currency": "string - INR, USD, etc.",
        "payment_terms": "string - any payment terms mentioned",
        "notes": "string - any additional notes or remarks"
    }
    
    Important:
    - Extract numbers as actual numbers, not strings
    - For Indian invoices, look for GSTIN (15-character alphanumeric)
    - HSN codes are typically 4-8 digit numbers
    - If a field is not present in the invoice, use null
    """
    
    # Decide whether to use text or image based on extraction quality
    if len(extracted_text) > 100:
        # Good text extraction - use text-based approach (faster, cheaper)
        messages = [
            {
                "role": "user",
                "content": f"{extraction_prompt}\n\nINVOICE TEXT:\n{extracted_text}"
            }
        ]
    else:
        # Poor text extraction - fall back to image (likely a scanned invoice)
        base64_image = pdf_to_base64_image(pdf_file)
        
        if not base64_image:
            return {"error": "Could not process PDF - neither text nor image extraction worked"}
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": extraction_prompt + "\n\nSee the invoice image below:"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_image
                        }
                    }
                ]
            }
        ]
    
    # Call Claude API
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",  # Good balance of speed and quality
            max_tokens=2000,
            messages=messages
        )
        
        # Extract the response text
        response_text = response.content[0].text
        
        # Claude sometimes wraps JSON in markdown code blocks - clean that up
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        # Parse JSON
        parsed_data = json.loads(response_text.strip())
        return parsed_data
        
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse Claude's response as JSON: {e}", "raw_response": response_text}
    except Exception as e:
        return {"error": f"API call failed: {str(e)}"}


def format_currency(amount, currency="INR") -> str:
    """Helper function to format currency amounts nicely."""
    if amount is None:
        return "N/A"
    if currency == "INR":
        return f"₹{amount:,.2f}"
    return f"{currency} {amount:,.2f}"