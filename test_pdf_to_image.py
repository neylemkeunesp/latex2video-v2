#!/usr/bin/env python3
import os
import sys
import logging
import argparse
from pdf2image import convert_from_path
import shutil

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def check_poppler_installation():
    """Check if Poppler utilities are installed and available."""
    logging.info("Checking Poppler installation...")
    
    # Try to find pdftoppm (part of Poppler)
    try:
        import subprocess
        result = subprocess.run(['which', 'pdftoppm'], capture_output=True, text=True)
        if result.returncode == 0:
            pdftoppm_path = result.stdout.strip()
            logging.info(f"Found pdftoppm at: {pdftoppm_path}")
            return True
        else:
            logging.error("pdftoppm not found in PATH. Poppler utilities may not be installed.")
            
            # Try to find it in common locations
            common_locations = [
                '/usr/bin/pdftoppm',
                '/usr/local/bin/pdftoppm',
                '/opt/homebrew/bin/pdftoppm',  # macOS Homebrew
                '/opt/local/bin/pdftoppm',     # macOS MacPorts
                'C:\\Program Files\\poppler\\bin\\pdftoppm.exe',  # Windows
                'C:\\poppler\\bin\\pdftoppm.exe'  # Windows alternative
            ]
            
            for location in common_locations:
                if os.path.exists(location):
                    logging.info(f"Found pdftoppm at: {location}")
                    logging.warning(f"pdftoppm exists but is not in PATH. Add {os.path.dirname(location)} to your PATH.")
                    return True
            
            logging.error("Poppler utilities (pdftoppm) not found in common locations.")
            logging.error("Please install Poppler utilities:")
            logging.error("  - Ubuntu/Debian: sudo apt-get install poppler-utils")
            logging.error("  - macOS: brew install poppler")
            logging.error("  - Windows: Download from http://blog.alivate.com.au/poppler-windows/ and add to PATH")
            return False
    except Exception as e:
        logging.error(f"Error checking Poppler installation: {e}")
        return False

def test_pdf_to_image(pdf_path, output_dir, dpi=300):
    """Test converting a PDF to images using pdf2image."""
    if not os.path.exists(pdf_path):
        logging.error(f"PDF file not found: {pdf_path}")
        return False
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Clear output directory
    for file in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logging.error(f"Error clearing output directory: {e}")
    
    logging.info(f"Testing PDF to image conversion for: {pdf_path}")
    logging.info(f"Output directory: {output_dir}")
    logging.info(f"DPI: {dpi}")
    
    try:
        # First, try with default settings
        logging.info("Attempting conversion with default settings...")
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            output_folder=output_dir,
            fmt='png',
            paths_only=True
        )
        
        if images:
            logging.info(f"Successfully converted PDF to {len(images)} images with default settings")
            for i, img_path in enumerate(images):
                logging.info(f"Image {i+1}: {img_path}")
            return True
        else:
            logging.warning("No images returned with default settings")
    except Exception as e:
        logging.error(f"Error with default settings: {e}")
    
    # If default settings failed, try with different settings
    try:
        logging.info("Attempting conversion with alternative settings (single thread)...")
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            output_folder=output_dir,
            fmt='png',
            paths_only=True,
            thread_count=1,
            use_pdftocairo=False
        )
        
        if images:
            logging.info(f"Successfully converted PDF to {len(images)} images with alternative settings")
            for i, img_path in enumerate(images):
                logging.info(f"Image {i+1}: {img_path}")
            return True
        else:
            logging.warning("No images returned with alternative settings")
    except Exception as e:
        logging.error(f"Error with alternative settings: {e}")
    
    # Check if any images were created despite errors
    image_files = [f for f in os.listdir(output_dir) if f.endswith('.png')]
    if image_files:
        logging.info(f"Found {len(image_files)} PNG files in output directory despite errors:")
        for img in image_files:
            logging.info(f"  - {img}")
        return True
    
    logging.error("Failed to convert PDF to images with all methods")
    return False

def main():
    parser = argparse.ArgumentParser(description="Test PDF to image conversion")
    parser.add_argument("pdf_path", help="Path to the PDF file to convert")
    parser.add_argument("-o", "--output-dir", default="output/test_images", help="Output directory for images")
    parser.add_argument("-d", "--dpi", type=int, default=300, help="DPI for conversion (default: 300)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Set logging level based on debug flag
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.info("Debug logging enabled")
    
    # Check Poppler installation
    if not check_poppler_installation():
        logging.warning("Proceeding with test despite Poppler installation issues...")
    
    # Test PDF to image conversion
    success = test_pdf_to_image(args.pdf_path, args.output_dir, args.dpi)
    
    if success:
        print("\nPDF to image conversion test completed successfully!")
        print(f"Check the output directory: {os.path.abspath(args.output_dir)}")
    else:
        print("\nPDF to image conversion test failed.")
        print("Please check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
