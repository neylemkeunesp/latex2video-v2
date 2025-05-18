#!/usr/bin/env python3
import os
import sys
import logging
from src.latex_parser import parse_latex_file

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_pdf_parsing(pdf_path):
    """Test parsing a PDF file directly."""
    logging.info(f"Testing PDF parsing for: {pdf_path}")
    
    # Parse the PDF
    slides = parse_latex_file(pdf_path)
    
    # Check if we got any slides
    if not slides:
        logging.error("No slides were parsed from the PDF.")
        return False
    
    # Print the slides
    logging.info(f"Successfully parsed {len(slides)} slides from PDF.")
    for slide in slides:
        print(f"--- Slide {slide.frame_number}: {slide.title} ---")
        print(f"Content length: {len(slide.content)}")
        print(f"Content preview: {slide.content[:100]}...")
        print("-" * 80)
    
    return True

def main():
    # Get the PDF path from command line argument or use default
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "output/temp_pdf/gasessolidos.pdf"
    
    # Check if the file exists
    if not os.path.exists(pdf_path):
        logging.error(f"PDF file not found: {pdf_path}")
        return
    
    # Test PDF parsing
    success = test_pdf_parsing(pdf_path)
    
    if success:
        print("\nPDF parsing test completed successfully!")
    else:
        print("\nPDF parsing test failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
