#!/usr/bin/env python3
import os
import sys
import logging
import yaml

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.latex_parser import parse_latex_file
from src.narration_generator import generate_all_narrations

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(config_path: str) -> dict:
    """Loads configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logging.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return {}

def main():
    """Test the narration generation."""
    latex_file = "assets/presentation.tex"
    config_file = "config/config.yaml"
    
    # Load configuration
    config = load_config(config_file)
    if not config:
        logging.error("Failed to load configuration. Exiting.")
        return
    
    # Parse the LaTeX file
    slides = parse_latex_file(latex_file)
    if not slides:
        logging.error("Failed to parse slides from LaTeX file. Exiting.")
        return
    
    # Generate narrations
    narrations = generate_all_narrations(slides, config)
    
    # Print the narrations
    print(f"Generated {len(narrations)} narrations:")
    for i, narration in enumerate(narrations):
        print(f"--- Narration for Slide {i+1}: {slides[i].title} ---")
        print(narration[:100] + "..." if len(narration) > 100 else narration)
        print()

if __name__ == "__main__":
    main()
