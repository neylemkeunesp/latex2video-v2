#!/usr/bin/env python3
import os
import sys
import subprocess
import re

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using pdftotext."""
    try:
        result = subprocess.run(
            ['pdftotext', pdf_path, '-'],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def count_pages_in_pdf(pdf_path):
    """Count the number of pages in a PDF file using pdfinfo."""
    try:
        result = subprocess.run(
            ['pdfinfo', pdf_path],
            capture_output=True, text=True, check=True
        )
        
        # Extract the page count from the output
        match = re.search(r'Pages:\s+(\d+)', result.stdout)
        if match:
            return int(match.group(1))
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error counting pages in PDF: {e}")
        return 0

def analyze_pdf_structure(pdf_path):
    """Analyze the structure of the PDF file."""
    # Count pages
    page_count = count_pages_in_pdf(pdf_path)
    print(f"PDF has {page_count} pages.")
    
    # Extract text
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print("Failed to extract text from PDF.")
        return
    
    # Split text by page (pdftotext adds form feeds between pages)
    pages = text.split('\f')
    
    # Analyze each page
    for i, page_text in enumerate(pages):
        if not page_text.strip():
            continue
        
        print(f"\n--- Page {i+1} ---")
        # Extract title if present
        title_match = re.search(r'^(.*?)$', page_text.strip(), re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
            print(f"Title: {title}")
        
        # Print first few lines of content
        content_lines = page_text.strip().split('\n')
        content_preview = '\n'.join(content_lines[:5])
        print(f"Content preview:\n{content_preview}")
        
        if len(content_lines) > 5:
            print(f"... ({len(content_lines) - 5} more lines)")

def main():
    pdf_path = "output/temp_pdf/multiplicadores_lagrange.pdf"
    output_dir = "output/debug"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract text from PDF
    print("Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    if text:
        # Save text to file
        with open(os.path.join(output_dir, "pdf_text.txt"), 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Text saved to {os.path.join(output_dir, 'pdf_text.txt')}")
    
    # Analyze PDF structure
    print("\nAnalyzing PDF structure...")
    analyze_pdf_structure(pdf_path)
    
    print("\nDone!")

if __name__ == "__main__":
    main()
