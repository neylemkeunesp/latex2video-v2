import yaml
import os
from src.tts_provider import create_tts_provider

def test_elevenlabs_provider():
    """Test if ElevenLabs provider can be initialized and used."""
    print("Loading configuration...")
    
    # Load configuration
    config_path = os.path.join('config', 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print("Creating TTS provider...")
    # Create TTS provider
    provider = create_tts_provider(config)
    
    if provider is None:
        print("Failed to create TTS provider!")
        return False
    
    print(f"TTS provider created: {provider.__class__.__name__}")
    
    # Test generating a short audio clip
    test_text = "Este é um teste do provedor de voz ElevenLabs."
    test_output_path = os.path.join('output', 'elevenlabs_test.mp3')
    
    print(f"Generating audio to {test_output_path}...")
    success = provider.generate_audio(test_text, test_output_path)
    
    if success:
        print(f"Audio successfully generated at {test_output_path}")
        return True
    else:
        print("Failed to generate audio!")
        return False

if __name__ == "__main__":
    print("Testing ElevenLabs TTS provider...")
    result = test_elevenlabs_provider()
    print(f"Test {'passed' if result else 'failed'}!")
