import os
import sys
import unittest
from src.latex_parser import parse_latex_file, Slide

class TestSlideTextExtraction(unittest.TestCase):
    def test_text_extraction_from_slides(self):
        """Test that text is properly extracted from LaTeX slides."""
        # Use one of the existing LaTeX files
        latex_file = "multiplicadores_lagrange.tex"
        
        # Parse the LaTeX file
        slides = parse_latex_file(latex_file)
        
        # Verify that we have slides
        self.assertTrue(len(slides) > 0, "No slides were parsed from the LaTeX file")
        
        # Check that each slide has content
        for slide in slides:
            print(f"Slide {slide.frame_number}: {slide.title}")
            print(f"Content length: {len(slide.content)}")
            print(f"Content: {slide.content[:100]}...")  # Print first 100 chars
            print("-" * 80)
            
            # Verify that the slide has a title and content
            self.assertTrue(slide.title, f"Slide {slide.frame_number} has no title")
            self.assertTrue(slide.content, f"Slide {slide.frame_number} has no content")
            
            # Verify that the content is not just the default placeholder
            if slide.frame_number > 2:  # Skip title and outline slides
                self.assertNotEqual(
                    slide.content, 
                    f"This slide covers {slide.title}.",
                    f"Slide {slide.frame_number} has only placeholder content"
                )

if __name__ == "__main__":
    unittest.main()
