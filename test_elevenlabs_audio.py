import os
import logging
import yaml
from src.tts_provider import ElevenLabsProvider, ELEVENLABS_AVAILABLE

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_elevenlabs_audio():
    # Load config
    try:
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return
    
    # Get ElevenLabs config
    elevenlabs_config = config.get('elevenlabs', {})
    api_key = elevenlabs_config.get('api_key')
    # Use the correct voice ID for "Ney" that we found in the test_elevenlabs.py output
    voice_id = "4BGVHcW2xjlsh3CQ2d0i"  # Override the config value since it might be outdated
    model_id = elevenlabs_config.get('model_id', 'eleven_multilingual_v2')
    
    if not api_key:
        logging.error("No ElevenLabs API key found in config")
        return
    
    if not ELEVENLABS_AVAILABLE:
        logging.error("ElevenLabs package is not available")
        return
    
    # Create output directory
    os.makedirs('output/audio', exist_ok=True)
    
    # Create ElevenLabs provider
    try:
        provider = ElevenLabsProvider(api_key, voice_id, model_id)
    except Exception as e:
        logging.error(f"Failed to initialize ElevenLabs provider: {e}")
        return
    
    # Generate audio
    test_text = "Este é um teste de geração de áudio com ElevenLabs. Espero que funcione corretamente."
    output_path = 'output/audio/test_elevenlabs.mp3'
    
    success = provider.generate_audio(test_text, output_path)
    
    if success:
        logging.info(f"Audio successfully generated at {output_path}")
    else:
        logging.error("Failed to generate audio")

if __name__ == "__main__":
    test_elevenlabs_audio()
