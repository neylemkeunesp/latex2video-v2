import os
import sys
from src.latex_parser import parse_latex_file, Slide

def test_latex_parser():
    """Test the latex_parser functionality with a sample LaTeX file."""
    print("Testing latex_parser.py...")
    
    # Path to the sample LaTeX file
    latex_file_path = os.path.join('assets', 'presentation.tex')
    
    # Check if the file exists
    if not os.path.exists(latex_file_path):
        print(f"Error: Sample LaTeX file not found at {latex_file_path}")
        return False
    
    print(f"Parsing LaTeX file: {latex_file_path}")
    
    # Parse the LaTeX file
    slides = parse_latex_file(latex_file_path)
    
    # Check if any slides were parsed
    if not slides:
        print("Error: No slides were parsed from the LaTeX file")
        return False
    
    print(f"Successfully parsed {len(slides)} slides from the LaTeX file")
    
    # Print information about each slide
    for i, slide in enumerate(slides):
        print(f"\nSlide {i+1}/{len(slides)}: {slide.title} (Type: {slide.slide_type})")
        print(f"Content length: {len(slide.content)} characters")
        print(f"Content preview: {slide.content[:100]}...")
    
    return True

if __name__ == "__main__":
    result = test_latex_parser()
    print(f"\nTest {'passed' if result else 'failed'}!")
