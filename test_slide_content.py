#!/usr/bin/env python3
import os
import sys
import logging
from src.latex_parser import parse_latex_file
from src.chatgpt_script_generator import format_slide_for_chatgpt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Test script to check slide content and prompts."""
    if len(sys.argv) < 2:
        print("Usage: python test_slide_content.py <path_to_latex_file>")
        sys.exit(1)
    
    latex_file_path = sys.argv[1]
    output_dir = "output/test_prompts"
    
    # Parse the LaTeX file
    slides = parse_latex_file(latex_file_path)
    if not slides:
        print("No slides parsed. Exiting.")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate and save prompts
    for i, slide in enumerate(slides):
        print(f"\n--- Slide {i+1}/{len(slides)}: {slide.title} ---")
        print(f"Content: {slide.content[:100]}...")  # Print first 100 chars of content
        
        # Format the slide for ChatGPT
        prompt = format_slide_for_chatgpt(slide, slides, i)
        
        # Save the prompt to a file
        file_name = f"slide_{i+1}_prompt.txt"
        file_path = os.path.join(output_dir, file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        print(f"Saved prompt to {file_path}")
    
    print(f"\nGenerated {len(slides)} prompt files in {output_dir}")

if __name__ == "__main__":
    main()
