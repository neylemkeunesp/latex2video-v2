#!/usr/bin/env python3
import os
import sys
import logging
import yaml
import argparse
from typing import List, Dict
import time
from openai import OpenAI

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.latex_parser import parse_latex_file, Slide
from src.chatgpt_script_generator import format_slide_for_chatgpt
from src.simple_video_assembler import assemble_video

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(config_path: str) -> dict:
    """Loads configuration from YAML file."""
    logging.info(f"Attempting to load configuration from {config_path}")
    
    if not os.path.exists(config_path):
        logging.error(f"Configuration file not found: {config_path}")
        return {}
    
    try:
        logging.info(f"Opening configuration file: {config_path}")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logging.info(f"Configuration loaded successfully from {config_path}")
        
        # Log configuration details (excluding sensitive information)
        safe_config = config.copy()
        if 'openai' in safe_config and 'api_key' in safe_config['openai']:
            safe_config['openai']['api_key'] = '****'
        
        logging.info(f"Configuration contents: {safe_config}")
        
        # Check for required configuration sections
        if 'openai' not in config:
            logging.warning("OpenAI configuration section not found in config file")
        elif 'api_key' not in config['openai']:
            logging.warning("API key not found in OpenAI configuration section")
        
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        return {}
    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration file {config_path}: {e}")
        logging.error(f"Error details: {str(e)}")
        return {}
    except Exception as e:
        logging.error(f"An unexpected error occurred loading config: {e}")
        logging.error(f"Error details: {str(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return {}

def initialize_openai_client(config: Dict) -> OpenAI:
    """Initialize the OpenAI client with API key from config."""
    logging.info("Initializing OpenAI client...")
    
    openai_config = config.get('openai', {})
    logging.info(f"OpenAI config found: {bool(openai_config)}")
    
    api_key = openai_config.get('api_key')
    has_api_key = bool(api_key)
    logging.info(f"API key found: {has_api_key}")
    
    if not api_key:
        logging.error("OpenAI API key not found in config. Please add your API key to config/config.yaml")
        return None
    
    # Log a masked version of the API key for debugging (only first 4 and last 4 chars)
    if len(api_key) > 8:
        masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
    else:
        masked_key = '****'
    logging.info(f"Using API key: {masked_key}")
    
    try:
        logging.info("Creating OpenAI client...")
        client = OpenAI(api_key=api_key)
        logging.info("OpenAI client created successfully")
        return client
    except Exception as e:
        logging.error(f"Error initializing OpenAI client: {e}")
        logging.error(f"Error details: {str(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return None

def generate_script_with_openai(client: OpenAI, prompt: str, config: Dict) -> str:
    """Generate a script for a slide using the OpenAI API."""
    openai_config = config.get('openai', {})
    model = openai_config.get('model', 'gpt-4o')
    temperature = openai_config.get('temperature', 0.7)
    max_tokens = openai_config.get('max_tokens', 1000)
    
    logging.info(f"OpenAI API call details:")
    logging.info(f"  - Client: {client}")
    logging.info(f"  - Model: {model}")
    logging.info(f"  - Temperature: {temperature}")
    logging.info(f"  - Max tokens: {max_tokens}")
    logging.info(f"  - Prompt length: {len(prompt)} characters")
    
    try:
        logging.info("Sending request to OpenAI API...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert educational content creator who specializes in creating clear, concise narration scripts for educational videos. You explain complex concepts in an accessible way, with special attention to mathematical formulas."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        logging.info("Response received from OpenAI API")
        script = response.choices[0].message.content.strip()
        logging.info(f"Script generated successfully (length: {len(script)} characters)")
        return script
    except Exception as e:
        logging.error(f"Error generating script with OpenAI: {e}")
        logging.error(f"Error details: {str(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return ""

def generate_all_scripts(slides: List[Slide], client: OpenAI, config: Dict) -> List[str]:
    """Generate scripts for all slides using the OpenAI API."""
    scripts = []
    
    for i, slide in enumerate(slides):
        logging.info(f"Generating script for slide {i+1}/{len(slides)}: {slide.title}")
        
        # Format the slide content for ChatGPT
        prompt = format_slide_for_chatgpt(slide)
        
        # Generate script with OpenAI
        script = generate_script_with_openai(client, prompt, config)
        
        if script:
            scripts.append(script)
            logging.info(f"Successfully generated script for slide {i+1}")
        else:
            logging.error(f"Failed to generate script for slide {i+1}")
            # Add a placeholder script to maintain alignment with slides
            scripts.append(f"Script for slide {i+1} could not be generated.")
        
        # Add a small delay to avoid rate limiting
        time.sleep(1)
    
    return scripts

def save_scripts_to_files(scripts: List[str], output_dir: str) -> List[str]:
    """Save generated scripts to files."""
    os.makedirs(output_dir, exist_ok=True)
    
    file_paths = []
    for i, script in enumerate(scripts):
        file_name = f"slide_{i+1}_response.txt"
        file_path = os.path.join(output_dir, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(script)
        
        file_paths.append(file_path)
        logging.info(f"Saved script for slide {i+1} to {file_path}")
    
    return file_paths

def main():
    """Main function to generate scripts using the OpenAI API."""
    parser = argparse.ArgumentParser(description="Generate narration scripts for slides using the OpenAI API.")
    parser.add_argument("latex_file", help="Path to the input LaTeX (.tex) file.")
    parser.add_argument("-c", "--config", default="config/config.yaml", help="Path to the configuration YAML file.")
    parser.add_argument("-o", "--output", default="output/chatgpt_responses", help="Path to the directory to save the generated scripts.")
    
    args = parser.parse_args()
    
    # Handle paths
    latex_path = os.path.abspath(args.latex_file)
    config_path = os.path.abspath(args.config)
    output_dir = os.path.abspath(args.output)
    
    if not os.path.exists(latex_path):
        print(f"Error: LaTeX input file not found at {latex_path}")
        return
    elif not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}")
        return
    
    # Load configuration
    config = load_config(config_path)
    if not config:
        logging.error("Failed to load configuration. Exiting.")
        return
    
    # Initialize OpenAI client
    client = initialize_openai_client(config)
    if not client:
        logging.error("Failed to initialize OpenAI client. Exiting.")
        return
    
    # Parse LaTeX file
    logging.info(f"Parsing LaTeX file: {latex_path}")
    slides = parse_latex_file(latex_path)
    if not slides:
        logging.error("Failed to parse slides from LaTeX file. Exiting.")
        return
    
    # Generate scripts for all slides
    logging.info(f"Generating scripts for {len(slides)} slides...")
    scripts = generate_all_scripts(slides, client, config)
    
    # Save scripts to files
    logging.info(f"Saving scripts to {output_dir}...")
    file_paths = save_scripts_to_files(scripts, output_dir)
    
    logging.info(f"Successfully generated and saved {len(file_paths)} scripts.")
    print(f"\nScripts generated and saved to {output_dir}")
    print("\nYou can now run the following command to generate the video:")
    print(f"python -m src.use_chatgpt_scripts {latex_path}")

if __name__ == "__main__":
    main()
