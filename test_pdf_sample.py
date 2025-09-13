#!/usr/bin/env python3
"""
Create a sample PDF file for testing PDF upload functionality
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

def create_sample_pdf():
    """Create a sample PDF file for testing"""
    filename = "sample_test_document.pdf"
    
    # Create a PDF with sample content
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Page 1
    c.drawString(100, height - 100, "Sample PDF Document for Testing")
    c.drawString(100, height - 130, "This is a test document to verify PDF processing.")
    c.drawString(100, height - 160, "")
    c.drawString(100, height - 190, "Chapter 1: Introduction")
    c.drawString(100, height - 220, "This document contains sample text that should be")
    c.drawString(100, height - 250, "extracted and processed by the knowledge base system.")
    c.drawString(100, height - 280, "")
    c.drawString(100, height - 310, "Key topics covered:")
    c.drawString(120, height - 340, "• PDF text extraction")
    c.drawString(120, height - 370, "• Knowledge base integration")
    c.drawString(120, height - 400, "• Search functionality")
    c.drawString(120, height - 430, "• Content processing")
    
    c.showPage()  # Start new page
    
    # Page 2
    c.drawString(100, height - 100, "Chapter 2: Technical Details")
    c.drawString(100, height - 130, "")
    c.drawString(100, height - 160, "The PDF processing system uses PyPDF2 library")
    c.drawString(100, height - 190, "to extract text content from uploaded documents.")
    c.drawString(100, height - 220, "")
    c.drawString(100, height - 250, "Features include:")
    c.drawString(120, height - 280, "- Multi-page document support")
    c.drawString(120, height - 310, "- Text cleaning and formatting")
    c.drawString(120, height - 340, "- Metadata extraction")
    c.drawString(120, height - 370, "- Search indexing")
    c.drawString(100, height - 400, "")
    c.drawString(100, height - 430, "This content should be searchable after upload.")
    
    c.save()
    print(f"Created sample PDF: {filename}")
    return filename

if __name__ == "__main__":
    try:
        import reportlab
        create_sample_pdf()
    except ImportError:
        print("reportlab not installed. Installing...")
        import subprocess
        subprocess.run(["pip", "install", "reportlab"])
        create_sample_pdf()