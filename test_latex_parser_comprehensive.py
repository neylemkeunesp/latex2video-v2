#!/usr/bin/env python3
import os
import sys
import unittest
import logging
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.latex_parser import parse_latex_file, extract_frame_title, clean_latex_content, Slide

class TestLatexParser(unittest.TestCase):
    """Test the latex_parser module comprehensively."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample LaTeX content for testing
        self.sample_latex = r"""
\documentclass{beamer}
\title{Test Presentation}
\author{Test Author}
\begin{document}

\begin{frame}
\titlepage
\end{frame}

\begin{frame}
\frametitle{Outline}
\tableofcontents
\end{frame}

\section{Introdução}

\begin{frame}
\frametitle{Simple Slide}
This is a simple slide with text.
\begin{itemize}
\item Item 1
\item Item 2
\end{itemize}
\end{frame}

\begin{frame}
\frametitle{Math Slide}
Consider the equation:
$$E = mc^2$$
And also:
\begin{align}
a &= b + c \\
d &= e + f
\end{align}
\end{frame}

\begin{frame}[fragile]
\frametitle{Slide with Options}
This slide has frame options.
\end{frame}

\section{Conclusão}

\begin{frame}{Inline Title}
This slide has an inline title.
\end{frame}

\end{document}
"""
        # Create a temporary file
        self.temp_file = "temp_test.tex"
        with open(self.temp_file, "w") as f:
            f.write(self.sample_latex)
            
    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary file
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
    
    def test_extract_frame_title(self):
        """Test the extract_frame_title function."""
        # Test with simple frametitle
        content = r"\frametitle{Test Title} Some content"
        self.assertEqual(extract_frame_title(content), "Test Title")
        
        # Test with nested braces
        content = r"\frametitle{Test {Nested} Title} Some content"
        self.assertEqual(extract_frame_title(content), "Test {Nested} Title")
        
        # Test with no frametitle
        content = "Some content without frametitle"
        # The parser will use the first non-empty line as the title if no frametitle is found
        self.assertEqual(extract_frame_title(content), "Some content without frametitle")
        
        # Test with empty frametitle
        content = r"\frametitle{} Some content"
        self.assertEqual(extract_frame_title(content), "")
    
    def test_clean_latex_content(self):
        """Test the clean_latex_content function."""
        # Test with itemize environment
        content = r"\begin{itemize}\item Item 1\item Item 2\end{itemize}"
        expected = "- Item 1\n- Item 2"
        self.assertEqual(clean_latex_content(content), expected)
        
        # Test with math environment
        content = r"$E = mc^2$"
        expected = "E = mc^2"
        self.assertEqual(clean_latex_content(content), expected)
        
        # Test with frametitle
        content = r"\frametitle{Test Title} Some content"
        expected = "Some content"
        self.assertEqual(clean_latex_content(content), expected)
        
        # Test with comments
        content = "Line 1 % Comment\nLine 2"
        expected = "Line 1\nLine 2"
        self.assertEqual(clean_latex_content(content), expected)
    
    @patch('subprocess.run')
    def test_parse_latex_file(self, mock_run):
        """Test the parse_latex_file function."""
        # Mock subprocess.run to return a fixed page count
        mock_process = MagicMock()
        mock_process.stdout = "Pages: 6"
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Test with the sample file
        slides = parse_latex_file(self.temp_file)
        
        # The parser creates slides for all frames, sections, plus title and outline
        section_titles = [s.title for s in slides if getattr(s, "slide_type", None) == "section"]
        self.assertIn("Introdução", section_titles)
        self.assertIn("Conclusão", section_titles)
        self.assertTrue(any(s.slide_type == "section" for s in slides))

        # Check the total number of slides (2 manual + 2 sections + 6 frames = 10)
        self.assertEqual(len(slides), 10)

        # Check the titles of the first few slides
        self.assertEqual(slides[0].title, "Title Page")
        self.assertEqual(slides[1].title, "Outline")
        self.assertIn("Simple Slide", [s.title for s in slides])
        self.assertIn("Math Slide", [s.title for s in slides])
        self.assertIn("Slide with Options", [s.title for s in slides])
        self.assertTrue(any("Inline Title" in s.title or s.title == "{Inline Title}" for s in slides))

        # Check the content of a specific slide (should appear in at least one slide)
        self.assertTrue(any("Item 1" in s.content for s in slides))
        self.assertTrue(any("Item 2" in s.content for s in slides))

        # Check that math content is properly handled in at least one slide
        self.assertTrue(any("E = mc^2" in s.content for s in slides))
    
    def test_parse_latex_file_nonexistent(self):
        """Test parse_latex_file with a nonexistent file."""
        slides = parse_latex_file("nonexistent.tex")
        self.assertEqual(slides, [])
    
    @patch('subprocess.run', side_effect=Exception("Test exception"))
    def test_parse_latex_file_subprocess_error(self, mock_run):
        """Test parse_latex_file when subprocess.run raises an exception."""
        # This should still return slides based on the LaTeX content
        slides = parse_latex_file(self.temp_file)
        self.assertGreater(len(slides), 0)

if __name__ == "__main__":
    unittest.main()
