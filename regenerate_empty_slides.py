#!/usr/bin/env python3
import os
import sys
import logging
import yaml
import argparse
import glob
import re
import time
from openai import OpenAI

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.latex_parser import parse_latex_file
from src.chatgpt_script_generator import generate_chatgpt_prompts, save_prompts_to_files
from src.automated_video_generation import generate_script_with_openai, initialize_openai_client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(config_path: str) -> dict:
    """Loads configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logging.info(f"Configuration loaded from {config_path}")
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

def find_empty_slides(prompts_dir: str) -> list:
    """Find slides that have empty content or are marked as empty."""
    empty_slides = []
    
    # Get all prompt files
    prompt_files = glob.glob(os.path.join(prompts_dir, "slide_*_prompt.txt"))
    
    for prompt_file in sorted(prompt_files):
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check if the prompt indicates an empty slide
            if "[ATTENTION: This slide appears to have no content" in content:
                # Extract slide number from filename
                match = re.search(r'slide_(\d+)_prompt\.txt', os.path.basename(prompt_file))
                if match:
                    slide_number = int(match.group(1))
                    empty_slides.append(slide_number)
                    logging.info(f"Found empty slide: {slide_number}")
        except Exception as e:
            logging.error(f"Error reading prompt file {prompt_file}: {e}")
    
    return empty_slides

def regenerate_prompts(latex_file_path: str, output_dir: str) -> list:
    """Regenerate prompts for all slides."""
    logging.info(f"Regenerating prompts from LaTeX file: {latex_file_path}")
    
    # Generate prompts
    prompts = generate_chatgpt_prompts(latex_file_path)
    if not prompts:
        logging.error("Failed to generate prompts.")
        return []
    
    # Save prompts to files
    prompt_file_paths = save_prompts_to_files(prompts, output_dir)
    logging.info(f"Generated and saved {len(prompts)} prompts to {output_dir}")
    
    return prompts

def regenerate_responses(prompts: list, empty_slides: list, client: OpenAI, config: dict, responses_dir: str) -> bool:
    """Regenerate responses for empty slides."""
    logging.info(f"Regenerating responses for {len(empty_slides)} empty slides...")
    
    success = True
    
    for slide_number in empty_slides:
        # Find the corresponding prompt
        prompt_data = None
        for p in prompts:
            if p["slide_number"] == slide_number:
                prompt_data = p
                break
        
        if not prompt_data:
            logging.error(f"Could not find prompt data for slide {slide_number}")
            success = False
            continue
        
        logging.info(f"Generating response for slide {slide_number}: {prompt_data['title']}")
        
        # Generate script with OpenAI
        raw_script = generate_script_with_openai(client, prompt_data, config)
        
        if not raw_script:
            logging.error(f"Failed to generate script for slide {slide_number}")
            success = False
            continue
        
        # Save the response to a file
        response_file = os.path.join(responses_dir, f"slide_{slide_number}_response.txt")
        try:
            with open(response_file, 'w', encoding='utf-8') as f:
                f.write(raw_script)
            logging.info(f"Saved response for slide {slide_number} to {response_file}")
        except Exception as e:
            logging.error(f"Error saving response for slide {slide_number}: {e}")
            success = False
        
        # Add a small delay to avoid rate limiting
        time.sleep(1)
    
    return success

def main():
    """Main function to regenerate prompts and responses for empty slides."""
    parser = argparse.ArgumentParser(description="Regenerate prompts and responses for slides with empty content.")
    parser.add_argument("latex_file", help="Path to the input LaTeX (.tex) file.")
    parser.add_argument("-c", "--config", default="config/config.yaml", help="Path to the configuration YAML file.")
    parser.add_argument("-o", "--output-dir", default="output", help="Path to the output directory.")
    
    args = parser.parse_args()
    
    # Handle paths
    latex_path = os.path.abspath(args.latex_file)
    config_path = os.path.abspath(args.config)
    output_dir = os.path.abspath(args.output_dir)
    
    if not os.path.exists(latex_path):
        print(f"Error: LaTeX input file not found at {latex_path}")
        return
    elif not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}")
        return
    
    # Ensure output directories exist
    prompts_dir = os.path.join(output_dir, 'chatgpt_prompts')
    responses_dir = os.path.join(output_dir, 'chatgpt_responses')
    os.makedirs(prompts_dir, exist_ok=True)
    os.makedirs(responses_dir, exist_ok=True)
    
    # Load configuration
    config = load_config(config_path)
    if not config:
        logging.error("Failed to load configuration. Exiting.")
        return
    
    # Add output_dir to config
    config['output_dir'] = output_dir
    
    # Initialize OpenAI client
    client = initialize_openai_client(config)
    if not client:
        logging.error("Failed to initialize OpenAI client. Exiting.")
        return
    
    # Find slides with empty content
    empty_slides = find_empty_slides(prompts_dir)
    if not empty_slides:
        logging.info("No empty slides found. Exiting.")
        return
    
    logging.info(f"Found {len(empty_slides)} slides with empty content: {empty_slides}")
    
    # Regenerate prompts for all slides
    prompts = regenerate_prompts(latex_path, prompts_dir)
    if not prompts:
        logging.error("Failed to regenerate prompts. Exiting.")
        return
    
    # Regenerate responses for empty slides
    success = regenerate_responses(prompts, empty_slides, client, config, responses_dir)
    
    if success:
        logging.info("Successfully regenerated responses for all empty slides.")
        print("\nSuccess! Responses regenerated for all empty slides.")
    else:
        logging.warning("Some responses could not be regenerated. Check the log for details.")
        print("\nWarning: Some responses could not be regenerated. Check the log for details.")

if __name__ == "__main__":
    main()
