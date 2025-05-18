import unittest
import os
import subprocess
import shutil
import re
import logging

# Attempt to import from src, assuming tests are run from project root
try:
    from src.latex_parser import parse_latex_file, Slide
except ImportError:
    # Fallback for environments where src is not directly in PYTHONPATH
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
    from src.latex_parser import parse_latex_file, Slide


# Configure logging for tests (optional, can be quiet)
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
# To keep test output clean, might be better to set a higher level or disable for library code during tests
logging.getLogger().setLevel(logging.WARNING) # Reduce noise from the module's logging

TEST_DIR = "test_latex_parser_temp_output"
TEX_FILENAME = "test_presentation.tex"
PDF_FILENAME = "test_presentation.pdf"

# Helper function to get PDF page count directly using pdfinfo
def get_actual_pdf_page_count(pdf_path: str) -> int:
    if not os.path.exists(pdf_path):
        logging.warning(f"PDF file not found for page count: {pdf_path}")
        return 0
    try:
        # Ensure pdfinfo is available
        subprocess.run(['pdfinfo', '-h'], capture_output=True, text=True, check=True, timeout=5)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        logging.warning("pdfinfo command not found or not working. Cannot get actual PDF page count.")
        return -1 # Indicate pdfinfo is not available

    try:
        result = subprocess.run(['pdfinfo', pdf_path], capture_output=True, text=True, check=True, timeout=10)
        match = re.search(r'Pages:\s*(\d+)', result.stdout)
        if match:
            return int(match.group(1))
        else:
            logging.warning(f"Could not find 'Pages:' in pdfinfo output for {pdf_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running pdfinfo on {pdf_path}: {e}")
    except subprocess.TimeoutExpired:
        logging.error(f"Timeout running pdfinfo on {pdf_path}")
    except Exception as e:
        logging.error(f"Unexpected error in get_actual_pdf_page_count for {pdf_path}: {e}")
    return 0

class TestLatexParserSectionsAndPages(unittest.TestCase):
    pdf_compilation_success = False
    pdfinfo_available = True

    @classmethod
    def setUpClass(cls):
        if os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)
        os.makedirs(TEST_DIR, exist_ok=True)

        cls.tex_file_path = os.path.join(TEST_DIR, TEX_FILENAME)
        cls.pdf_file_path = os.path.join(TEST_DIR, PDF_FILENAME)

        cls.latex_content = r"""
\documentclass{beamer}
\usetheme{default} % Using a default theme for simplicity
\title{Test Presentation Title}
\author{Test Author Name}
\date{\today}

\begin{document}

\frame{\titlepage}

\frame{\tableofcontents}

\section{Section One}
\begin{frame}{Frame 1.1 Title}
Content of frame 1.1.
\end{frame}
\begin{frame}{Frame 1.2 Title}
Content of frame 1.2.
\end{frame}

\section{Section Two}
\begin{frame}{Frame 2.1 Title}
Content of frame 2.1.
\end{frame}
\begin{frame} % Untitled frame
Content of untitled frame in Section Two.
\end{frame}

\section{Section Three (Content Added)}
\begin{frame}{Content for Section Three}
Minimal content to ensure this section and frame generate pages.
\end{frame}

\end{document}
"""
        with open(cls.tex_file_path, 'w', encoding='utf-8') as f:
            f.write(cls.latex_content)

        # Check for pdflatex
        try:
            subprocess.run(['pdflatex', '-version'], capture_output=True, text=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            logging.warning(f"pdflatex command not found or not working: {e}. Skipping PDF compilation-dependent tests.")
            cls.pdf_compilation_success = False
            # To skip all tests in class: raise unittest.SkipTest("pdflatex not available")
            # Here, we'll let individual tests skip.
            return 

        # Compile LaTeX to PDF
        try:
            logging.info(f"Compiling {cls.tex_file_path} to PDF...")
            abs_test_dir = os.path.abspath(TEST_DIR)
            for _ in range(2): # Run pdflatex twice for TOC and references
                process = subprocess.run(
                    ['pdflatex', 
                     '-output-directory', '.', # Output to current working directory
                     '-interaction=nonstopmode', 
                     TEX_FILENAME], # TEX_FILENAME is basename, found in cwd
                    check=False, # Check manually
                    capture_output=True, text=True,
                    timeout=30, 
                    cwd=abs_test_dir # Set current working directory for pdflatex
                )
                if process.returncode != 0:
                    logging.error(f"PDF compilation failed on a pass. Output:\n{process.stdout}\n{process.stderr}")
                    raise subprocess.CalledProcessError(process.returncode, process.args, process.stdout, process.stderr)
            
            cls.pdf_compilation_success = os.path.exists(cls.pdf_file_path)
            if not cls.pdf_compilation_success:
                 logging.error(f"PDF file {cls.pdf_file_path} not created after compilation.")
            else:
                logging.info(f"PDF compiled successfully: {cls.pdf_file_path}")

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logging.error(f"PDF compilation failed: {e}")
            cls.pdf_compilation_success = False
        
        # Check pdfinfo availability for relevant tests
        if get_actual_pdf_page_count(cls.pdf_file_path) == -1 : # Uses our helper which returns -1 if pdfinfo fails
            cls.pdfinfo_available = False


    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)
        # Clean up specific file from output/temp_pdf if created by a test
        output_temp_pdf_dir_abs = os.path.abspath(os.path.join("output", "temp_pdf"))
        specific_output_pdf_path = os.path.join(output_temp_pdf_dir_abs, "temp_no_pdf.pdf")
        if os.path.exists(specific_output_pdf_path) and hasattr(cls, '_created_temp_no_pdf_placeholder') :
            os.remove(specific_output_pdf_path)


    def test_sections_are_parsed_as_slides(self):
        if not self.pdf_compilation_success:
            self.skipTest("PDF compilation failed, cannot reliably test section parsing from .tex.")
        
        parsed_slides = parse_latex_file(self.tex_file_path)
        self.assertIsNotNone(parsed_slides, "parse_latex_file should return a list of slides.")
        
        section_slides = [s for s in parsed_slides if s.slide_type == "section"]
        
        # Expected sections: "Section One", "Section Two", "Section Three (Content Added)"
        self.assertEqual(len(section_slides), 3, "Should find 3 sections.")
        
        expected_section_titles = ["Section One", "Section Two", "Section Three (Content Added)"]
        actual_section_titles = [s.title for s in section_slides]
        
        for expected_title in expected_section_titles:
            self.assertIn(expected_title, actual_section_titles, f"Expected section title '{expected_title}' not found.")

        for slide in section_slides:
            self.assertEqual(slide.content, slide.title, f"Content of section slide '{slide.title}' should be its title.")

    def test_slide_count_consistency_with_pdf_pages(self):
        if not self.pdf_compilation_success:
            self.skipTest("PDF compilation failed, cannot test slide count consistency.")
        if not self.pdfinfo_available:
            self.skipTest("pdfinfo is not available, cannot get actual PDF page count.")

        parsed_slides = parse_latex_file(self.tex_file_path)
        num_parsed_slides = len(parsed_slides)
        
        actual_pdf_pages = get_actual_pdf_page_count(self.pdf_file_path)
        
        # Expected structure: Title, TOC, Sec1, F1.1, F1.2, Sec2, F2.1, UntitledF, Sec3, F3.1 = 10
        # num_parsed_slides should be 10.
        # If pdfinfo is reliable and LaTeX produces 10 pages, this should pass.
        self.assertEqual(num_parsed_slides, 10, f"Parser should find 10 logical slides, found {num_parsed_slides}")
        if actual_pdf_pages > 0: # Only assert if pdfinfo returned a valid count
            self.assertEqual(num_parsed_slides, actual_pdf_pages, 
                             f"Number of parsed slides ({num_parsed_slides}) should match actual PDF pages ({actual_pdf_pages}). Mismatch may indicate PDF generation issue or pdfinfo reporting.")
        else:
            logging.warning(f"Could not verify PDF page count against parsed slides ({num_parsed_slides}) as actual_pdf_pages was {actual_pdf_pages}.")


    def test_frame_titles_and_content(self):
        if not self.pdf_compilation_success:
            self.skipTest("PDF compilation failed, cannot reliably test frame content.")
        
        parsed_slides = parse_latex_file(self.tex_file_path)
        frame_slides = [s for s in parsed_slides if s.slide_type == "frame"]

        # Check Title Page (Slide 1, Frame 0 in frame_slides list)
        self.assertEqual(frame_slides[0].title, "Title Page")
        self.assertIn("Test Presentation Title", frame_slides[0].content)
        self.assertIn("Test Author Name", frame_slides[0].content)

        # Check Outline Page (Slide 2, Frame 1)
        self.assertEqual(frame_slides[1].title, "Outline")
        self.assertIn("This slide shows the outline", frame_slides[1].content) # Default content

        # Check Frame 1.1 (after "Section One" slide)
        # Order: Title(0), Outline(1), Sec1(2), F1.1(3), F1.2(4), Sec2(5), F2.1(6), UntitledF(7), Sec3(8), F3.1(9)
        frame1_1 = parsed_slides[3] 
        self.assertEqual(frame1_1.title, "Frame 1.1 Title")
        self.assertEqual(frame1_1.slide_type, "frame")
        self.assertIn("Content of frame 1.1.", frame1_1.content.strip())
        
        # Check untitled frame
        untitled_frame = parsed_slides[7]
        self.assertEqual(untitled_frame.slide_type, "frame")
        self.assertEqual(untitled_frame.title, "Content of untitled frame in Section Two.")
        self.assertIn("Content of untitled frame in Section Two.", untitled_frame.content.strip())

        # Check new frame in Section Three
        frame3_1 = parsed_slides[9]
        self.assertEqual(frame3_1.title, "Content for Section Three")
        self.assertEqual(frame3_1.slide_type, "frame")
        self.assertIn("Minimal content to ensure", frame3_1.content.strip())


    def test_parse_tex_without_preexisting_pdf(self):
        # This test ensures .tex parsing logic works even if related PDFs aren't found by the parser
        temp_tex_filename = "temp_no_pdf.tex"
        temp_tex_path = os.path.join(TEST_DIR, temp_tex_filename)
        
        # This PDF path is where the parser might look if it's in the same dir as .tex
        associated_pdf_path_source = os.path.join(TEST_DIR, "temp_no_pdf.pdf")
        if os.path.exists(associated_pdf_path_source):
            os.remove(associated_pdf_path_source)

        # This PDF path is where the parser might look in output/temp_pdf
        output_temp_pdf_dir_abs = os.path.abspath(os.path.join("output", "temp_pdf"))
        os.makedirs(output_temp_pdf_dir_abs, exist_ok=True)
        associated_pdf_path_output = os.path.join(output_temp_pdf_dir_abs, "temp_no_pdf.pdf")
        if os.path.exists(associated_pdf_path_output):
            os.remove(associated_pdf_path_output)
            self._created_temp_no_pdf_placeholder = True # Mark for cleanup

        latex_content_simple = r"""
\documentclass{beamer}
\title{Simple Title}
\author{Simple Author}
\begin{document}
\frame{\titlepage} % Will be filtered by parser, manual title page used
\section{Only Section}
\begin{frame}{Only Frame}
Content here.
\end{frame}
\end{document}
"""
        with open(temp_tex_path, 'w', encoding='utf-8') as f:
            f.write(latex_content_simple)
        
        parsed_slides = parse_latex_file(temp_tex_path)
        
        # Expected: Title Page, Outline, Section, Frame
        self.assertEqual(len(parsed_slides), 4, "Expected 4 slides: Title, Outline, Section, Frame.")
        
        self.assertEqual(parsed_slides[0].title, "Title Page")
        self.assertIn("Simple Title", parsed_slides[0].content)
        self.assertIn("Simple Author", parsed_slides[0].content)
        self.assertEqual(parsed_slides[0].slide_type, "frame")

        self.assertEqual(parsed_slides[1].title, "Outline")
        self.assertEqual(parsed_slides[1].slide_type, "frame")

        self.assertEqual(parsed_slides[2].title, "Only Section")
        self.assertEqual(parsed_slides[2].slide_type, "section")
        self.assertEqual(parsed_slides[2].content, "Only Section")

        self.assertEqual(parsed_slides[3].title, "Only Frame")
        self.assertEqual(parsed_slides[3].slide_type, "frame")
        self.assertIn("Content here.", parsed_slides[3].content)

if __name__ == '__main__':
    unittest.main()
