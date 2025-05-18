#!/usr/bin/env python3
import os
import sys
import unittest
import logging
import subprocess
from unittest.mock import patch, MagicMock, mock_open

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.image_generator import load_config, compile_latex_to_pdf, convert_pdf_to_images, generate_slide_images

class TestImageGenerator(unittest.TestCase):
    """Test the image_generator module comprehensively."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample config for testing
        self.sample_config = {
            'output_dir': 'test_output',
            'latex': {
                'dpi': 300,
                'image_format': 'png'
            }
        }
        
        # Create paths for testing
        self.test_latex_file = "test_presentation.tex"
        self.test_pdf_file = "test_presentation.pdf"
        self.test_output_dir = "test_output"
        self.test_slides_dir = os.path.join(self.test_output_dir, "slides")
        self.test_pdf_dir = os.path.join(self.test_output_dir, "temp_pdf")
        
        # Ensure test directories exist
        os.makedirs(self.test_slides_dir, exist_ok=True)
        os.makedirs(self.test_pdf_dir, exist_ok=True)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test directories if they exist
        import shutil
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)
    
    @patch('builtins.open', new_callable=mock_open, read_data='output_dir: test_output\nlatex:\n  dpi: 300\n  image_format: png')
    def test_load_config(self, mock_file):
        """Test the load_config function."""
        config = load_config('test_config.yaml')
        self.assertEqual(config['output_dir'], 'test_output')
        self.assertEqual(config['latex']['dpi'], 300)
        self.assertEqual(config['latex']['image_format'], 'png')
        
        # Test with nonexistent file
        mock_file.side_effect = FileNotFoundError
        config = load_config('nonexistent.yaml')
        self.assertEqual(config, {})
        
        # Test with invalid YAML
        mock_file.side_effect = None
        mock_file.return_value.read.return_value = 'invalid: yaml: content:'
        with patch('yaml.safe_load', side_effect=Exception("YAML Error")):
            config = load_config('invalid.yaml')
            self.assertEqual(config, {})
    
    @patch('os.path.getsize')
    @patch('shutil.copy2')
    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_compile_latex_to_pdf(self, mock_exists, mock_run, mock_copy, mock_getsize):
        """Test the compile_latex_to_pdf function."""
        # Helper to simulate file existence for different files
        def exists_side_effect(path):
            if path.endswith('.tex'):
                return self._tex_exists
            elif path.endswith('.pdf'):
                return self._pdf_exists
            else:
                return False

        # Test successful compilation
        self._tex_exists = True
        self._pdf_exists = True
        mock_exists.side_effect = exists_side_effect
        mock_getsize.return_value = 1024  # Non-empty file
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        pdf_path = compile_latex_to_pdf(self.test_latex_file, self.test_pdf_dir)
        self.assertIsNotNone(pdf_path)

        # Test nonexistent LaTeX file
        self._tex_exists = False
        self._pdf_exists = True
        pdf_path = compile_latex_to_pdf(self.test_latex_file, self.test_pdf_dir)
        self.assertIsNone(pdf_path)

        # Test empty PDF file
        self._tex_exists = True
        self._pdf_exists = True  # PDF exists, but is empty

        # Patch getsize to return 0 for both source and output PDF paths
        def getsize_side_effect(path):
            if path.endswith('.pdf'):
                return 0
            return 1024
        mock_getsize.side_effect = getsize_side_effect

        pdf_path = compile_latex_to_pdf(self.test_latex_file, self.test_pdf_dir)
        self.assertIsNone(pdf_path)

        # Test pdflatex command not found
        self._tex_exists = True
        self._pdf_exists = True
        mock_getsize.return_value = 1024
        mock_run.side_effect = FileNotFoundError
        pdf_path = compile_latex_to_pdf(self.test_latex_file, self.test_pdf_dir)
        self.assertIsNone(pdf_path)

        # Test pdflatex timeout
        mock_run.side_effect = subprocess.TimeoutExpired("pdflatex", 60)
        pdf_path = compile_latex_to_pdf(self.test_latex_file, self.test_pdf_dir)
        self.assertIsNone(pdf_path)

        # Test other exception
        mock_run.side_effect = Exception("Test exception")
        pdf_path = compile_latex_to_pdf(self.test_latex_file, self.test_pdf_dir)
        self.assertIsNone(pdf_path)

    @patch('os.rename')
    @patch('src.image_generator.convert_from_path')
    @patch('os.path.exists')
    def test_convert_pdf_to_images(self, mock_exists, mock_convert, mock_rename):
        """Test the convert_pdf_to_images function."""
        # Helper to simulate file existence for different files and directories
        def exists_side_effect(path):
            # Debug: print the path being checked
            # print(f"exists_side_effect called with: {path}")
            # Simulate PDF file exists (regardless of absolute/relative)
            if os.path.basename(path) == os.path.basename(self.test_pdf_file):
                return self._pdf_exists
            # Simulate output directory exists (robust to any path form)
            if "slides" in path:
                return True
            return False

        # Test successful conversion
        self._pdf_exists = True
        mock_exists.side_effect = exists_side_effect
        mock_convert.return_value = ["temp1.png", "temp2.png", "temp3.png"]
        image_paths = convert_pdf_to_images(self.test_pdf_file, self.test_slides_dir, 300, "png")
        self.assertEqual(len(image_paths), 3)

        # Test nonexistent PDF file
        self._pdf_exists = False
        image_paths = convert_pdf_to_images(self.test_pdf_file, self.test_slides_dir, 300, "png")
        self.assertEqual(image_paths, [])

        # Test conversion failure
        self._pdf_exists = True
        mock_convert.return_value = []
        image_paths = convert_pdf_to_images(self.test_pdf_file, self.test_slides_dir, 300, "png")
        self.assertEqual(image_paths, [])

        # Test exception in conversion
        mock_convert.side_effect = Exception("Test exception")
        image_paths = convert_pdf_to_images(self.test_pdf_file, self.test_slides_dir, 300, "png")
        self.assertEqual(image_paths, [])

        # Test exception in renaming
        mock_convert.side_effect = None
        mock_convert.return_value = ["temp1.png", "temp2.png", "temp3.png"]
        mock_rename.side_effect = Exception("Test exception")
        image_paths = convert_pdf_to_images(self.test_pdf_file, self.test_slides_dir, 300, "png")
        self.assertEqual(len(image_paths), 3)  # Should still return paths even if renaming fails
    
    @patch('src.image_generator.compile_latex_to_pdf')
    @patch('src.image_generator.convert_pdf_to_images')
    def test_generate_slide_images(self, mock_convert, mock_compile):
        """Test the generate_slide_images function."""
        # Mock successful compilation and conversion
        mock_compile.return_value = self.test_pdf_file
        mock_convert.return_value = ["slide_1.png", "slide_2.png", "slide_3.png"]
        
        # Test successful generation
        image_paths = generate_slide_images(self.test_latex_file, self.sample_config)
        self.assertEqual(len(image_paths), 3)
        
        # Test compilation failure
        mock_compile.return_value = None
        image_paths = generate_slide_images(self.test_latex_file, self.sample_config)
        self.assertEqual(image_paths, [])
        
        # Test conversion failure
        mock_compile.return_value = self.test_pdf_file
        mock_convert.return_value = []
        image_paths = generate_slide_images(self.test_latex_file, self.sample_config)
        self.assertEqual(image_paths, [])

if __name__ == "__main__":
    unittest.main()
