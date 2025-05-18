import os
import logging
from elevenlabs import ElevenLabs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load API key from config
import yaml
try:
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    API_KEY = config.get('elevenlabs', {}).get('api_key', '')
    if not API_KEY:
        logging.warning("No ElevenLabs API key found in config.yaml")
except Exception as e:
    logging.error(f"Error loading config: {e}")
    API_KEY = ""

def test_elevenlabs():
    try:
        logging.info("Initializing ElevenLabs client...")
        client = ElevenLabs(api_key=API_KEY)
        
        # Test account info - inspect raw response structure
        logging.info("Fetching account info...")
        account = client.user.get()
        logging.info("Account info raw structure:")
        logging.info(account)
        try:
            logging.info(f"Subscription tier: {account.subscription.tier}")
        except Exception as e:
            logging.warning("Could not get subscription info")
        
        # List available voices
        logging.info("Listing available voices...")
        voices = client.voices.get_all()
        if voices.voices:
            logging.info(f"Found {len(voices.voices)} voices:")
            for voice in voices.voices:
                logging.info(f"- {voice.name} (ID: {voice.voice_id})")
                logging.info(f"  Settings: {voice.settings}")
                logging.info(f"  Categories: {voice.category}")
        else:
            logging.warning("No voices found")
            
    except Exception as e:
        logging.error("Error testing ElevenLabs API")
        logging.exception(e)

if __name__ == "__main__":
    test_elevenlabs()
