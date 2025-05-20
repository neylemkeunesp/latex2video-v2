import os
import sys
import yaml
import logging
from src.tts_provider import create_tts_provider

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test the ElevenLabs TTS provider."""
    logger.info("Starting ElevenLabs TTS test")
    
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
    
    # Test text
    test_text = "Este é um teste do provedor de síntese de voz ElevenLabs. Vamos verificar se está funcionando corretamente."
    
    # Output path
    output_dir = os.path.join('output', 'elevenlabs_test')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'test_audio.mp3')
    
    # Generate audio
    logger.info(f"Generating audio to {output_path}")
    success = tts_provider.generate_audio(test_text, output_path)
    
    if success:
        logger.info(f"Successfully generated audio at {output_path}")
        print(f"Audio file created at: {output_path}")
    else:
        logger.error("Failed to generate audio")
        print("Failed to generate audio. Check logs for details.")

if __name__ == "__main__":
    main()
