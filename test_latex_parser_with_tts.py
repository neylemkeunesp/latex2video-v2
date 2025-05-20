import os
import sys
import yaml
from src.latex_parser import parse_latex_file, Slide
from src.tts_provider import create_tts_provider

def test_latex_parser_with_tts():
    """Test the latex_parser functionality with TTS generation."""
    print("Testing latex_parser.py with TTS generation...")
    
    # Load configuration
    config_path = os.path.join('config', 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create TTS provider
    print("Creating TTS provider...")
    provider = create_tts_provider(config)
    
    if provider is None:
        print("Failed to create TTS provider!")
        return False
    
    print(f"TTS provider created: {provider.__class__.__name__}")
    
    # Path to the sample LaTeX file
    latex_file_path = os.path.join('assets', 'presentation.tex')
    
    # Check if the file exists
    if not os.path.exists(latex_file_path):
        print(f"Error: Sample LaTeX file not found at {latex_file_path}")
        return False
    
    print(f"Parsing LaTeX file: {latex_file_path}")
    
    # Parse the LaTeX file
    slides = parse_latex_file(latex_file_path)
    
    # Check if any slides were parsed
    if not slides:
        print("Error: No slides were parsed from the LaTeX file")
        return False
    
    print(f"Successfully parsed {len(slides)} slides from the LaTeX file")
    
    # Create output directory for audio files if it doesn't exist
    output_dir = os.path.join('output', 'test_audio')
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate audio for the first 3 slides only (to avoid generating too many files)
    max_slides = min(3, len(slides))
    for i in range(max_slides):
        slide = slides[i]
        print(f"\nProcessing Slide {i+1}/{max_slides}: {slide.title} (Type: {slide.slide_type})")
        
        # Generate text for TTS
        if slide.slide_type == "section":
            tts_text = f"Seção: {slide.title}"
        else:
            tts_text = f"Slide {i+1}: {slide.title}. {slide.content}"
        
        # Generate audio file
        audio_path = os.path.join(output_dir, f"slide_{i+1}.mp3")
        print(f"Generating audio to {audio_path}...")
        
        success = provider.generate_audio(tts_text, audio_path)
        
        if success:
            print(f"Audio successfully generated at {audio_path}")
        else:
            print(f"Failed to generate audio for slide {i+1}")
            return False
    
    print(f"\nSuccessfully generated audio for {max_slides} slides")
    return True

if __name__ == "__main__":
    result = test_latex_parser_with_tts()
    print(f"\nTest {'passed' if result else 'failed'}!")
