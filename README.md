# 📄 Invoice Parser

AI-powered tool to extract structured data from invoice PDFs. Built with Python, Streamlit, and Claude API.

## Features

- Upload any invoice PDF (digital or scanned)
- Extracts: vendor details, buyer details, line items, taxes, totals
- Supports Indian GST invoices (GSTIN, HSN codes, CGST/SGST/IGST)
- Download extracted data as JSON

## Live Demo

🔗 [Try it here](YOUR_STREAMLIT_URL) *(link added after deployment)*

## Run Locally

### Prerequisites
- Python 3.9+
- Anthropic API key ([get one here](https://console.anthropic.com))

### Setup
```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/invoice-parser.git
cd invoice-parser

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Add your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the app
streamlit run app.py
```

## Tech Stack

- **Frontend:** Streamlit
- **AI:** Claude API (Anthropic)
- **PDF Processing:** PyPDF2, pdf2image

## Project Structure
```
invoice-parser/
├── app.py              # Streamlit web interface
├── parser.py           # Invoice parsing logic
├── requirements.txt    # Python dependencies
├── .env.example        # Template for environment variables
└── README.md           # This file
```

## Author

Built by [Your Name] during the Shipping Sprint 🚀

## License

MIT