"""
Invoice Parser Web App
A simple tool to extract structured data from invoice PDFs.

This is your first shipped product! 🚀
"""

import streamlit as st
import json
import pandas as pd
from parser import parse_invoice_with_claude, format_currency

# Page configuration - this must be the first Streamlit command
st.set_page_config(
    page_title="Invoice Parser",
    page_icon="📄",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">📄 Invoice Parser</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Upload an invoice PDF and extract structured data instantly using AI</p>', unsafe_allow_html=True)

# File uploader
uploaded_file = st.file_uploader(
    "Choose an invoice PDF",
    type=['pdf'],
    help="Upload a PDF invoice. Works with both digital and scanned invoices."
)

if uploaded_file is not None:
    # Show a spinner while processing
    with st.spinner("🔍 Analyzing invoice... This may take a few seconds."):
        result = parse_invoice_with_claude(uploaded_file)
    
    # Check for errors
    if "error" in result:
        st.error(f"❌ Error: {result['error']}")
        if "raw_response" in result:
            with st.expander("See raw API response"):
                st.code(result['raw_response'])
    else:
        # Success! Display the extracted data
        st.success("✅ Invoice parsed successfully!")
        
        # Create two columns for layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Basic Information")
            
            # Invoice details
            st.markdown(f"**Invoice Number:** {result.get('invoice_number', 'N/A')}")
            st.markdown(f"**Invoice Date:** {result.get('invoice_date', 'N/A')}")
            st.markdown(f"**Due Date:** {result.get('due_date', 'N/A')}")
            st.markdown(f"**Currency:** {result.get('currency', 'N/A')}")
            
            st.divider()
            
            # Vendor details
            st.subheader("🏢 Vendor Details")
            vendor = result.get('vendor', {})
            st.markdown(f"**Name:** {vendor.get('name', 'N/A')}")
            st.markdown(f"**Address:** {vendor.get('address', 'N/A')}")
            st.markdown(f"**GSTIN:** {vendor.get('gstin', 'N/A')}")
            
            st.divider()
            
            # Buyer details
            st.subheader("👤 Buyer Details")
            buyer = result.get('buyer', {})
            st.markdown(f"**Name:** {buyer.get('name', 'N/A')}")
            st.markdown(f"**Address:** {buyer.get('address', 'N/A')}")
            st.markdown(f"**GSTIN:** {buyer.get('gstin', 'N/A')}")
        
        with col2:
            st.subheader("💰 Financial Summary")
            
            # Create metrics for key financial data
            currency = result.get('currency', 'INR')
            
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric(
                    label="Subtotal",
                    value=format_currency(result.get('subtotal'), currency)
                )
            with metric_col2:
                tax_details = result.get('tax_details', {})
                st.metric(
                    label="Total Tax",
                    value=format_currency(tax_details.get('total_tax'), currency)
                )
            
            st.metric(
                label="Total Amount",
                value=format_currency(result.get('total_amount'), currency)
            )
            
            # Tax breakdown
            st.divider()
            st.subheader("📊 Tax Breakdown")
            tax_details = result.get('tax_details', {})
            
            tax_col1, tax_col2, tax_col3 = st.columns(3)
            with tax_col1:
                st.markdown(f"**CGST:** {format_currency(tax_details.get('cgst'), currency)}")
            with tax_col2:
                st.markdown(f"**SGST:** {format_currency(tax_details.get('sgst'), currency)}")
            with tax_col3:
                st.markdown(f"**IGST:** {format_currency(tax_details.get('igst'), currency)}")
        
        # Line items table
        st.divider()
        st.subheader("📦 Line Items")
        
        line_items = result.get('line_items', [])
        if line_items:
            # Convert to a format suitable for st.dataframe
            df = pd.DataFrame(line_items)
            
            # Rename columns for better display
            column_mapping = {
                'description': 'Description',
                'hsn_code': 'HSN Code',
                'quantity': 'Qty',
                'unit_price': 'Unit Price',
                'amount': 'Amount'
            }
            df = df.rename(columns=column_mapping)
            
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No line items extracted")
        
        # Additional info
        if result.get('payment_terms') or result.get('notes'):
            st.divider()
            st.subheader("📝 Additional Information")
            if result.get('payment_terms'):
                st.markdown(f"**Payment Terms:** {result.get('payment_terms')}")
            if result.get('notes'):
                st.markdown(f"**Notes:** {result.get('notes')}")
        
        # Raw JSON expander (useful for debugging)
        st.divider()
        with st.expander("🔧 View Raw JSON Data"):
            st.json(result)
        
        # Download button for JSON
        st.download_button(
            label="📥 Download as JSON",
            data=json.dumps(result, indent=2),
            file_name=f"invoice_{result.get('invoice_number', 'parsed')}.json",
            mime="application/json"
        )

# Footer with instructions
st.divider()
st.markdown("""
### How it works
1. **Upload** any invoice PDF (digital or scanned)
2. **AI extracts** key fields: vendor info, line items, taxes, totals
3. **Review** the structured data and download as JSON

### Supported Invoice Types
- GST invoices (Indian)
- International invoices
- Both digital PDFs and scanned documents

---
*Built during Week 1 of the Shipping Sprint 🚀*
""")