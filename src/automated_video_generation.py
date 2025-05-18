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
from src.chatgpt_script_generator import format_slide_for_chatgpt, clean_chatgpt_response
from src.image_generator import generate_slide_images
from src.audio_generator import generate_all_audio
from src.simple_video_assembler import assemble_video

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

def initialize_openai_client(config: Dict) -> OpenAI:
    """Initialize the OpenAI client with API key from config."""
    openai_config = config.get('openai', {})
    api_key = openai_config.get('api_key')
    
    if not api_key:
        logging.error("OpenAI API key not found in config. Please add your API key to config/config.yaml")
        return None
    
    try:
        client = OpenAI(api_key=api_key)
        return client
    except Exception as e:
        logging.error(f"Error initializing OpenAI client: {e}")
        return None

def generate_script_with_openai(client: OpenAI, prompt_data: Dict, config: Dict) -> str:
    """Generate a script for a slide using the OpenAI API."""
    openai_config = config.get('openai', {})
    model = openai_config.get('model', 'gpt-4o')
    temperature = openai_config.get('temperature', 0.7)
    max_tokens = openai_config.get('max_tokens', 1000)
    
    prompt = prompt_data["prompt"]
    slide_title = prompt_data["title"]
    slide_number = prompt_data["slide_number"]
    
    # Check if this is an empty slide that needs a transition script
    is_empty_slide = "[ATTENTION: This slide appears to have no content" in prompt
    
    # Adjust system message based on slide content
    system_message = "You are an expert educational content creator who specializes in creating clear, concise narration scripts for educational videos. You explain complex concepts in an accessible way, with special attention to mathematical formulas. DO NOT include any markers like '[Início do Script de Narração]' or '[Fim do Script de Narração]' in your response. Just provide the narration script directly."
    
    if is_empty_slide:
        # Add specific instructions for empty slides
        system_message += " For this empty slide, create a brief transition (2-3 sentences) that connects the previous topic to the next one. Do not invent content that isn't there, just create a smooth transition between concepts."
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        script = response.choices[0].message.content.strip()
        
        # For empty slides, ensure we have at least some content
        if is_empty_slide and (not script or len(script) < 10):
            logging.warning(f"Generated script for empty slide {slide_number} was too short. Using default transition.")
            script = f"Agora que vimos {slide_title}, vamos avançar para o próximo conceito. Esta transição nos ajuda a conectar as ideias e manter o fluxo da apresentação."
        
        return script
    except Exception as e:
        logging.error(f"Error generating script with OpenAI: {e}")
        return ""

def generate_all_scripts(slides: List[Slide], client: OpenAI, config: Dict) -> List[str]:
    """Generate scripts for all slides using the OpenAI API."""
    scripts = []
    
    # Create directory for prompts
    output_dir = config.get('output_dir', 'output')
    prompts_dir = os.path.join(output_dir, 'chatgpt_prompts')
    os.makedirs(prompts_dir, exist_ok=True)
    
    # Generate prompts for all slides
    from src.chatgpt_script_generator import generate_chatgpt_prompts, save_prompts_to_files
    
    # Get the LaTeX file path or PDF file path
    file_path = config.get('latex_file_path', '')
    if not file_path:
        logging.warning("LaTeX file path not found in config. Using the first slide's content directly.")
        # Generate prompts directly from slides
        prompts = []
        for i, slide in enumerate(slides):
            # Format the slide content for ChatGPT
            prompt = format_slide_for_chatgpt(slide, slides, i)
            prompts.append({
                "slide_number": i+1,
                "title": slide.title,
                "prompt": prompt
            })
    else:
        logging.info(f"Generating prompts from file: {file_path}")
        prompts = generate_chatgpt_prompts(file_path)
    
    # Save prompts to files
    prompt_file_paths = save_prompts_to_files(prompts, prompts_dir)
    logging.info(f"Generated and saved {len(prompts)} prompts to {prompts_dir}")
    
    for i, prompt in enumerate(prompts):
        slide_number = prompt["slide_number"]
        slide_title = prompt["title"]
        logging.info(f"Generating script for slide {slide_number}/{len(prompts)}: {slide_title}")
        
        # Generate script with OpenAI - pass the prompt data dictionary
        raw_script = generate_script_with_openai(client, prompt, config)
        
        if raw_script:
            # Clean up the response to remove any ChatGPT-specific formatting or markers
            cleaned_script = clean_chatgpt_response(raw_script)
            
            if cleaned_script:
                scripts.append(cleaned_script)
                logging.info(f"Successfully generated and cleaned script for slide {i+1}")
            else:
                logging.warning(f"Script for slide {i+1} was empty after cleaning. Using placeholder.")
                scripts.append(f"Script for slide {i+1} could not be generated properly.")
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

def process_scripts_for_narration(scripts_dir: str) -> bool:
    """Process scripts to prepare them for narration.
    
    This function:
    1. Removes any remaining LaTeX control characters
    2. Replaces 'y' with 'ipsilon' for proper Portuguese pronunciation
    3. Tests the processed scripts to ensure they're ready for narration
    """
    import re
    import glob
    
    logging.info("Processing scripts for narration...")
    
    # Step 1: Remove LaTeX control characters
    logging.info("Step 1: Removing LaTeX control characters...")
    try:
        # Define function to clean LaTeX control characters
        def clean_latex_control_chars(text):
            # Remove LaTeX math delimiters and control characters
            # Inline math delimiters: \( ... \) or $ ... $
            text = re.sub(r'\\\((.*?)\\\)', r'\1', text, flags=re.DOTALL)
            text = re.sub(r'\$(.*?)\$', r'\1', text, flags=re.DOTALL)
            
            # Display math delimiters: \[ ... \] or $$ ... $$
            text = re.sub(r'\\\[(.*?)\\\]', r'\1', text, flags=re.DOTALL)
            text = re.sub(r'\$\$(.*?)\$\$', r'\1', text, flags=re.DOTALL)
            
            # Remove LaTeX commands that might remain
            text = re.sub(r'\\[a-zA-Z]+', '', text)  # Remove LaTeX commands like \lambda, \alpha, etc.
            text = re.sub(r'\\[^a-zA-Z]', '', text)  # Remove LaTeX special characters like \{, \}, etc.
            
            return text
        
        # Find all response files
        response_files = glob.glob(os.path.join(scripts_dir, "slide_*_response.txt"))
        
        if not response_files:
            logging.error(f"No response files found in '{scripts_dir}'.")
            return False
        
        # Clean each file
        for file_path in sorted(response_files):
            # Read the original content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Clean the content
            cleaned_content = clean_latex_control_chars(original_content)
            
            # Write the cleaned content back to the original file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            logging.info(f"Cleaned LaTeX control characters from {os.path.basename(file_path)}")
        
        logging.info("Successfully removed LaTeX control characters from all scripts.")
    
    except Exception as e:
        logging.error(f"Error removing LaTeX control characters: {e}")
        return False
    
    # Step 2: Replace 'y' with 'ipsilon'
    logging.info("Step 2: Replacing 'y' with 'ipsilon' for proper Portuguese pronunciation...")
    try:
        # Define function to replace 'y' with 'ipsilon'
        def replace_y_with_ipsilon(text):
            # Replace standalone 'y' (surrounded by spaces, punctuation, or at beginning/end)
            # but not when it's part of a word
            text = re.sub(r'(?<!\w)y(?!\w)', 'ipsilon', text)
            
            # Special cases for common mathematical expressions
            text = re.sub(r'f\(x, y\)', 'f(x, ipsilon)', text)
            text = re.sub(r'g\(x, y\)', 'g(x, ipsilon)', text)
            text = re.sub(r'L\(x, y', 'L(x, ipsilon', text)  # Handle L(x, y, λ) case
            
            # Additional cases for mathematical expressions
            text = re.sub(r'xy', 'x·ipsilon', text)  # Replace xy with x·ipsilon
            text = re.sub(r'2y', '2·ipsilon', text)  # Replace 2y with 2·ipsilon
            
            return text
        
        # Find all response files
        response_files = glob.glob(os.path.join(scripts_dir, "slide_*_response.txt"))
        
        # Process each file
        for file_path in sorted(response_files):
            # Read the original content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Replace 'y' with 'ipsilon'
            processed_content = replace_y_with_ipsilon(original_content)
            
            # Write the processed content back to the original file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            
            logging.info(f"Replaced 'y' with 'ipsilon' in {os.path.basename(file_path)}")
        
        logging.info("Successfully replaced 'y' with 'ipsilon' in all scripts.")
    
    except Exception as e:
        logging.error(f"Error replacing 'y' with 'ipsilon': {e}")
        return False
    
    # Step 3: Test the processed scripts
    logging.info("Step 3: Testing processed scripts...")
    try:
        # Define function to check for remaining issues
        def check_for_issues(text):
            issues = []
            
            # Check for LaTeX control characters
            latex_patterns = [
                r'\\[a-zA-Z]+',  # LaTeX commands like \lambda, \alpha, etc.
                r'\\[\(\)\[\]]',  # Math delimiters \(, \), \[, \]
                r'\\\{', r'\\\}',  # Escaped braces \{, \}
                r'\\[,;]',  # Spacing commands \, \;
                r'\$\$.*?\$\$',  # Display math $$...$$
                r'\$.*?\$',  # Inline math $...$
            ]
            
            for pattern in latex_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    issues.append(f"Found LaTeX control characters: {matches[:3]}")
            
            # Check for standalone 'y'
            y_matches = re.findall(r'(?<!\w)y(?!\w)', text)
            if y_matches:
                issues.append(f"Found standalone 'y' characters: {y_matches[:3]}")
            
            # Check for 'xy' or '2y' patterns
            xy_matches = re.findall(r'xy', text)
            if xy_matches:
                issues.append(f"Found 'xy' patterns: {xy_matches[:3]}")
            
            two_y_matches = re.findall(r'2y', text)
            if two_y_matches:
                issues.append(f"Found '2y' patterns: {two_y_matches[:3]}")
            
            return issues
        
        # Find all response files
        response_files = glob.glob(os.path.join(scripts_dir, "slide_*_response.txt"))
        
        all_clean = True
        
        # Test each file
        for file_path in sorted(response_files):
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for issues
            issues = check_for_issues(content)
            
            if issues:
                logging.warning(f"Issues found in {os.path.basename(file_path)}:")
                for issue in issues:
                    logging.warning(f"  - {issue}")
                all_clean = False
            else:
                logging.info(f"No issues found in {os.path.basename(file_path)}")
        
        if all_clean:
            logging.info("All scripts are clean and ready for narration.")
        else:
            logging.warning("Some scripts have issues that may affect narration quality.")
            # We continue with the process, but log the warning
        
        return True
    
    except Exception as e:
        logging.error(f"Error testing processed scripts: {e}")
        return False

def main():
    """Main function to automate the entire video generation process."""
    parser = argparse.ArgumentParser(description="Automate the entire process of generating a narrated video from a LaTeX presentation.")
    parser.add_argument("latex_file", help="Path to the input LaTeX (.tex) file.")
    parser.add_argument("-c", "--config", default="config/config.yaml", help="Path to the configuration YAML file.")
    parser.add_argument("-s", "--save-scripts", action="store_true", help="Save the generated scripts to files.")
    
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
    
    # --- 1. Load Configuration ---
    logging.info("Step 1: Loading configuration...")
    config = load_config(config_path)
    if not config:
        logging.error("Failed to load configuration. Exiting.")
        return
    
    # Ensure output directories exist
    output_dir = config.get('output_dir', 'output')
    slides_dir = os.path.join(output_dir, 'slides')
    audio_dir = os.path.join(output_dir, 'audio')
    temp_pdf_dir = os.path.join(output_dir, 'temp_pdf')
    scripts_dir = os.path.join(output_dir, 'chatgpt_responses')
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(slides_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(temp_pdf_dir, exist_ok=True)
    os.makedirs(scripts_dir, exist_ok=True)
    
    # --- 2. Initialize OpenAI Client ---
    logging.info("Step 2: Initializing OpenAI client...")
    client = initialize_openai_client(config)
    if not client:
        logging.error("Failed to initialize OpenAI client. Exiting.")
        return
    
    # --- 3. Parse LaTeX File ---
    logging.info("Step 3: Parsing LaTeX file...")
    slides = parse_latex_file(latex_path)
    if not slides:
        logging.error("Failed to parse slides from LaTeX file. Exiting.")
        return
    
    # --- 4. Generate Slide Images ---
    logging.info("Step 4: Generating slide images...")
    abs_latex_file_path = os.path.abspath(latex_path)
    # Pass the parsed 'slides' list to generate_slide_images
    image_paths = generate_slide_images(abs_latex_file_path, slides, config)
    if not image_paths:
        logging.error("Failed to generate slide images. Exiting.")
        return
    
    # With the updated generate_slide_images, image_paths should now always match the length of 'slides'
    # (either from PDF or as placeholders). So, the reconciliation logic below might be simplified or removed.
    # For now, let's assume generate_slide_images correctly provides a matching list.
    if len(image_paths) != len(slides):
        logging.error(f"Critical mismatch between generated images ({len(image_paths)}) and parsed slides ({len(slides)}). This should not happen with the new image generator. Exiting.")
        return
    
    content_image_paths = image_paths
    logging.info(f"Successfully prepared {len(content_image_paths)} images for {len(slides)} slides.")
    
    # --- 5. Generate Scripts with OpenAI ---
    logging.info("Step 5: Generating scripts with OpenAI...")
    scripts = generate_all_scripts(slides, client, config)
    
    # Save scripts if requested
    if args.save_scripts:
        logging.info(f"Saving scripts to {scripts_dir}...")
        script_paths = save_scripts_to_files(scripts, scripts_dir)
        
        # --- 5a. Process Scripts for Narration ---
        logging.info("Step 5a: Processing scripts for narration...")
        if not process_scripts_for_narration(scripts_dir):
            logging.error("Failed to process scripts for narration. Exiting.")
            return
        
        # Read the processed scripts back
        processed_scripts = []
        for script_path in script_paths:
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    processed_scripts.append(f.read())
            except Exception as e:
                logging.error(f"Error reading processed script {script_path}: {e}")
                return
        
        # Use the processed scripts instead of the original ones
        scripts = processed_scripts
    else:
        # If scripts are not saved to files, process them in memory
        logging.info("Processing scripts in memory...")
        # Process each script to remove LaTeX control characters and replace 'y' with 'ipsilon'
        import re
        
        def process_script(text):
            # Remove LaTeX control characters
            text = re.sub(r'\\\((.*?)\\\)', r'\1', text, flags=re.DOTALL)
            text = re.sub(r'\$(.*?)\$', r'\1', text, flags=re.DOTALL)
            text = re.sub(r'\\\[(.*?)\\\]', r'\1', text, flags=re.DOTALL)
            text = re.sub(r'\$\$(.*?)\$\$', r'\1', text, flags=re.DOTALL)
            text = re.sub(r'\\[a-zA-Z]+', '', text)
            text = re.sub(r'\\[^a-zA-Z]', '', text)
            
            # Replace 'y' with 'ipsilon'
            text = re.sub(r'(?<!\w)y(?!\w)', 'ipsilon', text)
            text = re.sub(r'f\(x, y\)', 'f(x, ipsilon)', text)
            text = re.sub(r'g\(x, y\)', 'g(x, ipsilon)', text)
            text = re.sub(r'L\(x, y', 'L(x, ipsilon', text)
            text = re.sub(r'xy', 'x·ipsilon', text)
            text = re.sub(r'2y', '2·ipsilon', text)
            
            return text
        
        processed_scripts = []
        for script in scripts:
            processed_scripts.append(process_script(script))
        
        scripts = processed_scripts
    
    # --- 6. Generate Audio Files ---
    logging.info("Step 6: Generating audio files from scripts...")
    audio_paths = generate_all_audio(scripts, config)
    if not audio_paths:
        logging.error("Failed to generate audio files. Exiting.")
        return

    # Ensure the number of image paths matches the number of successfully generated audio files
    if len(content_image_paths) > len(audio_paths):
        logging.warning(f"Number of images ({len(content_image_paths)}) is greater than successfully generated audio files ({len(audio_paths)}).")
        logging.info(f"Adjusting image list to match the {len(audio_paths)} available audio files.")
        content_image_paths = content_image_paths[:len(audio_paths)]
    elif len(audio_paths) > len(content_image_paths):
        # This case should ideally not happen if image generation was successful and audio generation failed partially
        # but as a safeguard:
        logging.warning(f"Number of audio files ({len(audio_paths)}) is greater than available images ({len(content_image_paths)}).")
        logging.info(f"Adjusting audio list to match the {len(content_image_paths)} available image files.")
        audio_paths = audio_paths[:len(content_image_paths)]

    if len(content_image_paths) != len(audio_paths):
        logging.error(f"Critical mismatch after adjustment: {len(content_image_paths)} images vs {len(audio_paths)} audio. Cannot proceed.")
        return
    
    # --- 7. Assemble Final Video ---
    logging.info("Step 7: Assembling final video...")
    final_video_path = assemble_video(content_image_paths, audio_paths, config)
    if not final_video_path:
        logging.error("Failed to assemble the final video. Exiting.")
        return
    
    logging.info(f"--- Video Generation Complete ---")
    logging.info(f"Final video saved to: {final_video_path}")
    print(f"\nSuccess! Final video available at: {final_video_path}")

if __name__ == "__main__":
    main()
