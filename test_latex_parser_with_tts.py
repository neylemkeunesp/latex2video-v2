import os
import sys
import yaml
import logging
from src.latex_parser import parse_latex_file
from src.tts_provider import create_tts_provider
from src.chatgpt_script_generator import clean_chatgpt_response

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test the LaTeX parser with the ElevenLabs TTS provider."""
    logger.info("Starting LaTeX parser with ElevenLabs TTS test")
    
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
    output_dir = os.path.join('output', 'latex_tts_test')
    os.makedirs(output_dir, exist_ok=True)
    
    # Process a few slides
    for i, slide in enumerate(slides[:5]):  # Process first 5 slides
        logger.info(f"Processing slide {slide.frame_number}: {slide.title}")
        
        # Create a simple narration script
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
