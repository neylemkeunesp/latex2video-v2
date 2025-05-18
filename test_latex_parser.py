#!/usr/bin/env python3
import os
import sys
import logging

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.latex_parser import parse_latex_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Test the latex_parser module."""
    latex_file = "assets/presentation.tex"
    
    # Parse the LaTeX file
    slides = parse_latex_file(latex_file)
    
    # Print the slides
    print(f"Parsed {len(slides)} slides:")
    for slide in slides:
        print(f"--- Slide {slide.frame_number}: {slide.title} ---")
        print(slide.content[:100] + "..." if len(slide.content) > 100 else slide.content)
        print()

if __name__ == "__main__":
    main()
