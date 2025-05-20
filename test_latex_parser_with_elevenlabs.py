import os
import sys
import yaml
import logging
import argparse
from src.latex_parser import parse_latex_file
from src.tts_provider import create_tts_provider
from src.chatgpt_script_generator import clean_chatgpt_response, format_slide_for_chatgpt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test the LaTeX parser with the ElevenLabs TTS provider using ChatGPT-formatted prompts."""
    parser = argparse.ArgumentParser(description='Generate audio for slides using ElevenLabs TTS')
    parser.add_argument('--slide', type=int, help='Specific slide number to process (optional)')
    parser.add_argument('--script', type=str, help='Path to a script file to use instead of generating one (optional)')
    args = parser.parse_args()
    
    logger.info("Starting LaTeX parser with ElevenLabs TTS test using ChatGPT-formatted prompts")
    
    # Load configuration
    config_path = os.path.join('config', 'config.yaml')
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return
    
    # Force the provider to be ElevenLabs
    config['tts']['provider'] = 'elevenlabs'
    
    # Create TTS provider
    tts_provider = create_tts_provider(config)
    if not tts_provider:
        logger.error("Failed to create ElevenLabs TTS provider")
        return
    
    # Parse LaTeX file
    latex_file_path = os.path.join('assets', 'presentation.tex')
    slides = parse_latex_file(latex_file_path)
    if not slides:
        logger.error("Failed to parse LaTeX file")
        return
    
    # Create output directory
    output_dir = os.path.join('output', 'elevenlabs_test')
    os.makedirs(output_dir, exist_ok=True)
    
    # Process slides
    if args.slide:
        # Process only the specified slide
        slide_to_process = next((s for s in slides if s.frame_number == args.slide), None)
        if slide_to_process:
            process_slide(slide_to_process, slides, tts_provider, output_dir, args.script)
        else:
            logger.error(f"Slide {args.slide} not found")
    else:
        # Process all slides (limit to 3 for testing)
        for i, slide in enumerate(slides[:3]):
            process_slide(slide, slides, tts_provider, output_dir, args.script)

def process_slide(slide, all_slides, tts_provider, output_dir, script_path=None):
    """Process a single slide and generate audio."""
    logger.info(f"Processing slide {slide.frame_number}: {slide.title}")
    
    # Get the slide index
    slide_index = next((i for i, s in enumerate(all_slides) if s.frame_number == slide.frame_number), None)
    
    if script_path:
        # Use the provided script
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                narration = f.read()
            logger.info(f"Using script from {script_path}")
        except Exception as e:
            logger.error(f"Failed to read script file: {e}")
            return
    else:
        # Format the slide for ChatGPT
        formatted_content = format_slide_for_chatgpt(slide, all_slides, slide_index)
        
        # Save the formatted content to a file for reference
        prompt_path = os.path.join(output_dir, f"slide_{slide.frame_number}_prompt.txt")
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        
        # For testing purposes, create a simple narration
        narration = f"Slide {slide.frame_number}: {slide.title}. "
        
        # Add slide content to narration
        if slide.content:
            # Clean up the content for narration
            content = clean_chatgpt_response(slide.content)
            narration += content
    
    # Generate audio for the slide
    output_path = os.path.join(output_dir, f"slide_{slide.frame_number}.mp3")
    logger.info(f"Generating audio for slide {slide.frame_number} to {output_path}")
    
    success = tts_provider.generate_audio(narration, output_path)
    
    if success:
        logger.info(f"Successfully generated audio for slide {slide.frame_number}")
        print(f"Audio file created for slide {slide.frame_number} at: {output_path}")
    else:
        logger.error(f"Failed to generate audio for slide {slide.frame_number}")
        print(f"Failed to generate audio for slide {slide.frame_number}. Check logs for details.")

if __name__ == "__main__":
    main()
