#!/usr/bin/env python3
import os
import sys
import logging
import yaml
import argparse

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.image_generator import generate_slide_images

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(config_path: str) -> dict:
    """Loads configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logging.info(f"Configuration loaded from {config_path}")
        # Add absolute path for output_dir based on config location
        config_dir = os.path.dirname(os.path.abspath(config_path))
        config['output_dir'] = os.path.abspath(os.path.join(config_dir, '..', 'output'))
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        return {}
    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration file {config_path}: {e}")
        return {}
    except Exception as e:
        logging.error(f"An unexpected error occurred loading config: {e}")
        return {}

def main():
    """Main function to generate slide images from a LaTeX file."""
    parser = argparse.ArgumentParser(description="Generate slide images from a LaTeX presentation.")
    parser.add_argument("latex_file", help="Path to the input LaTeX (.tex) file.")
    parser.add_argument("-c", "--config", default="config/config.yaml", help="Path to the configuration YAML file.")
    
    args = parser.parse_args()
    
    # Handle paths
    latex_path = os.path.abspath(args.latex_file)
    config_path = os.path.abspath(args.config)
    
    if not os.path.exists(latex_path):
        print(f"Error: LaTeX input file not found at {latex_path}")
        return
    elif not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}")
        return
    
    # Load configuration
    logging.info("Loading configuration...")
    config = load_config(config_path)
    if not config:
        logging.error("Failed to load configuration. Exiting.")
        return
    
    # Ensure output directories exist
    output_dir = config.get('output_dir', 'output')
    slides_dir = os.path.join(output_dir, 'slides')
    temp_pdf_dir = os.path.join(output_dir, 'temp_pdf')
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(slides_dir, exist_ok=True)
    os.makedirs(temp_pdf_dir, exist_ok=True)
    
    # Generate slide images
    logging.info("Generating slide images...")
    image_paths = generate_slide_images(latex_path, config)
    
    if image_paths:
        logging.info(f"Successfully generated {len(image_paths)} slide images:")
        for i, path in enumerate(image_paths):
            logging.info(f"  Slide {i+1}: {path}")
        print(f"\nSuccess! Generated {len(image_paths)} slide images in {slides_dir}")
    else:
        logging.error("Failed to generate slide images.")
        print("\nFailed to generate slide images. Check the logs for details.")

if __name__ == "__main__":
    main()
