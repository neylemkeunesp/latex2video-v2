import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Any # Added Any for ElevenLabs client type hint
import re

# Get a logger for this module
logger = logging.getLogger(__name__)
print("[TTS_PROVIDER_PRINT] src/tts_provider.py top-level execution.")

# Attempt to import ElevenLabs and gTTS, logging before and after
ELEVENLABS_AVAILABLE = False
gTTS = None # Initialize to None

try:
    print("[TTS_PROVIDER_PRINT] Attempting to import gTTS...")
    logger.info("[TTS_PROVIDER_IMPORT] Attempting to import gTTS...")
    for handler in logging.getLogger().handlers: handler.flush()
    from gtts import gTTS as gTTS_imported
    gTTS = gTTS_imported # Assign if import successful
    print("[TTS_PROVIDER_PRINT] gTTS imported successfully.")
    logger.info("[TTS_PROVIDER_IMPORT] gTTS imported successfully.")
    for handler in logging.getLogger().handlers: handler.flush()
except ImportError as e_gtts:
    print(f"[TTS_PROVIDER_PRINT] Failed to import gTTS: {e_gtts}")
    logger.error(f"[TTS_PROVIDER_IMPORT] Failed to import gTTS: {e_gtts}. gTTS provider will not be available.", exc_info=True)
    for handler in logging.getLogger().handlers: handler.flush()

# try:
#     print("[TTS_PROVIDER_PRINT] Attempting to import ElevenLabs...")
#     logger.info("[TTS_PROVIDER_IMPORT] Attempting to import ElevenLabs...")
#     for handler in logging.getLogger().handlers: handler.flush()
#     from elevenlabs import ElevenLabs, Voice, save # Keep specific imports if needed
#     ELEVENLABS_AVAILABLE = True
#     print("[TTS_PROVIDER_PRINT] ElevenLabs imported successfully.")
#     logger.info("[TTS_PROVIDER_IMPORT] ElevenLabs imported successfully.")
#     for handler in logging.getLogger().handlers: handler.flush()
# except ImportError as e_eleven:
#     print(f"[TTS_PROVIDER_PRINT] ElevenLabs import error: {e_eleven}")
#     logger.warning(f"[TTS_PROVIDER_IMPORT] ElevenLabs import error: {e_eleven}. ElevenLabs provider will not be available.")
#     for handler in logging.getLogger().handlers: handler.flush()
# except Exception as e_eleven_other: # Catch other potential errors during import
#     print(f"[TTS_PROVIDER_PRINT] An unexpected error occurred during ElevenLabs import: {e_eleven_other}")
#     logger.error(f"[TTS_PROVIDER_IMPORT] An unexpected error occurred during ElevenLabs import: {e_eleven_other}", exc_info=True)
#     for handler in logging.getLogger().handlers: handler.flush()
print("[TTS_PROVIDER_PRINT] ElevenLabs import block is COMMENTED OUT for testing.")
logger.info("[TTS_PROVIDER_IMPORT] ElevenLabs import block is COMMENTED OUT for testing. ELEVENLABS_AVAILABLE will remain False.")


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""
    
    @abstractmethod
    def generate_audio(self, text: str, output_path: str) -> bool:
        """Generate audio for the given text and save to output_path."""
        pass
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text to handle SSML tags and other provider-specific requirements."""
        logger.debug(f"Preprocessing text (original): {text[:100]}...")
        return text

class GTTSProvider(TTSProvider):
    """Google Text-to-Speech provider implementation."""
    
    def __init__(self, language: str = 'pt', slow: bool = False):
        print(f"[TTS_PROVIDER_PRINT] GTTSProvider.__init__ called. Language: {language}, Slow: {slow}")
        logger.info(f"[GTTSProvider] Initializing with language: {language}, slow: {slow}")
        for handler in logging.getLogger().handlers: handler.flush()
        if gTTS is None:
            print("[TTS_PROVIDER_PRINT] GTTSProvider.__init__: gTTS library is NOT available!")
            logger.error("[GTTSProvider] gTTS library is not available. Cannot initialize GTTSProvider.")
            # Potentially raise an error here or ensure create_tts_provider handles this
            raise ImportError("gTTS library failed to import. GTTSProvider cannot be used.")
        self.language = language
        self.slow = slow
        print(f"[TTS_PROVIDER_PRINT] GTTSProvider initialized. Language: {self.language}")
        logger.info(f"[GTTSProvider] Initialized gTTS provider with language: {language}")
        for handler in logging.getLogger().handlers: handler.flush()
    
    def preprocess_text(self, text: str) -> str:
        """Remove SSML tags that gTTS doesn't support."""
        logger.debug(f"[GTTSProvider] Preprocessing text for gTTS (original): {text[:100]}...")
        # Remove <break> tags but add periods for pauses
        processed_text = re.sub(r'<break time="([0-9\.]+)s"/>', '. ', text)
        # Remove any other XML/SSML tags
        processed_text = re.sub(r'<[^>]+>', '', processed_text)
        logger.debug(f"[GTTSProvider] Preprocessed text for gTTS (processed): {processed_text[:100]}...")
        return processed_text
    
    def generate_audio(self, text: str, output_path: str) -> bool:
        """Generate audio using Google Text-to-Speech."""
        print(f"[TTS_PROVIDER_PRINT] GTTSProvider.generate_audio called for: {output_path}")
        logger.info(f"[GTTSProvider] Attempting to generate audio for: {output_path}")
        for handler in logging.getLogger().handlers: handler.flush()
        if gTTS is None:
            print("[TTS_PROVIDER_PRINT] GTTSProvider.generate_audio: gTTS library not available!")
            logger.error("[GTTSProvider] gTTS library not available. Cannot generate audio.")
            return False
        try:
            processed_text = self.preprocess_text(text)
            print(f"[TTS_PROVIDER_PRINT] GTTSProvider.generate_audio: Text after preprocessing (len={len(processed_text)}): {processed_text[:60]}...")
            logger.debug(f"[GTTSProvider] Text for gTTS (after preprocessing, len={len(processed_text)}): {processed_text[:200]}...")
            
            print("[TTS_PROVIDER_PRINT] GTTSProvider.generate_audio: Creating gTTS object...")
            logger.info("[GTTSProvider] Creating gTTS object...")
            for handler in logging.getLogger().handlers: handler.flush()
            tts_obj = gTTS(text=processed_text, lang=self.language, slow=self.slow) # Renamed tts to tts_obj
            print("[TTS_PROVIDER_PRINT] GTTSProvider.generate_audio: gTTS object created.")
            
            output_dir = os.path.dirname(os.path.abspath(output_path))
            if not os.path.exists(output_dir):
                print(f"[TTS_PROVIDER_PRINT] GTTSProvider.generate_audio: Creating output directory: {output_dir}")
                logger.info(f"[GTTSProvider] Creating output directory: {output_dir}")
                os.makedirs(output_dir, exist_ok=True)
            
            print(f"[TTS_PROVIDER_PRINT] GTTSProvider.generate_audio: Saving audio to {output_path}...")
            logger.info(f"[GTTSProvider] Saving audio to {output_path}...")
            for handler in logging.getLogger().handlers: handler.flush()
            tts_obj.save(output_path)
            print(f"[TTS_PROVIDER_PRINT] GTTSProvider.generate_audio: Audio successfully saved to {output_path}")
            
            logger.info(f"[GTTSProvider] Audio successfully saved to {output_path}")
            return True
        except Exception as e:
            print(f"[TTS_PROVIDER_PRINT] GTTSProvider.generate_audio: Exception: {e}")
            logger.error(f"[GTTSProvider] gTTS error generating audio for {output_path}: {e}", exc_info=True)
            return False
        finally:
            print(f"[TTS_PROVIDER_PRINT] GTTSProvider.generate_audio finished for: {output_path}")
            for handler in logging.getLogger().handlers: handler.flush()

class ElevenLabsProvider(TTSProvider):
    """ElevenLabs provider implementation."""
    
    def __init__(self, api_key: str, voice_id: str, model_id: str):
        logger.info(f"[ElevenLabsProvider] Initializing with voice_id: {voice_id}, model_id: {model_id}")
        for handler in logging.getLogger().handlers: handler.flush()

        if not ELEVENLABS_AVAILABLE:
            logger.error("[ElevenLabsProvider] ElevenLabs package is not installed or failed to import. Cannot initialize.")
            raise ImportError("ElevenLabs package is not available. ElevenLabsProvider cannot be used.")
        
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        self.client: Optional[Any] = None # Using Any for ElevenLabs client type

        try:
            logger.info("[ElevenLabsProvider] Attempting to create ElevenLabs client...")
            for handler in logging.getLogger().handlers: handler.flush()
            self.client = ElevenLabs(api_key=api_key) # Critical SDK call
            logger.info("[ElevenLabsProvider] ElevenLabs client object created. Testing connection by listing voices...")
            for handler in logging.getLogger().handlers: handler.flush()
            
            # Test connection by listing voices (optional but good for diagnostics)
            # This can be a network call and might fail
            voices_list = self.client.voices.get_all()
            logger.info(f"[ElevenLabsProvider] ElevenLabs client initialized successfully. Found {len(voices_list.voices)} voices.")
            for handler in logging.getLogger().handlers: handler.flush()
        except Exception as e:
            logger.error(f"[ElevenLabsProvider] Failed to initialize ElevenLabs client or test connection: {e}", exc_info=True)
            self.client = None # Ensure client is None on failure
            for handler in logging.getLogger().handlers: handler.flush()
            raise # Re-raise the exception to be caught by create_tts_provider
    
    def generate_audio(self, text: str, output_path: str) -> bool:
        """Generate audio using ElevenLabs API."""
        logger.info(f"[ElevenLabsProvider] Attempting to generate audio for: {output_path}")
        for handler in logging.getLogger().handlers: handler.flush()

        if not self.client:
            logger.error("[ElevenLabsProvider] ElevenLabs client is not initialized. Cannot generate audio.")
            return False
            
        logger.debug(f"[ElevenLabsProvider] Generating audio with ElevenLabs for text (len: {len(text)} chars): {text[:200]}...")
        
        try:
            logger.info("[ElevenLabsProvider] Calling ElevenLabs text_to_speech.convert...")
            for handler in logging.getLogger().handlers: handler.flush()
            # ElevenLabs Python SDK v1+ handles SSML tags like <break> automatically
            audio_data = self.client.text_to_speech.convert( # Renamed audio to audio_data
                text=text,
                voice_id=self.voice_id,
                model_id=self.model_id
            )
            logger.info("[ElevenLabsProvider] text_to_speech.convert call successful.")
            for handler in logging.getLogger().handlers: handler.flush()
            
            output_dir = os.path.dirname(os.path.abspath(output_path))
            if not os.path.exists(output_dir):
                logger.info(f"[ElevenLabsProvider] Creating output directory: {output_dir}")
                os.makedirs(output_dir, exist_ok=True)
            
            logger.info(f"[ElevenLabsProvider] Saving audio to {output_path}...")
            for handler in logging.getLogger().handlers: handler.flush()
            save(audio_data, output_path) # save is from elevenlabs import
            
            logger.info(f"[ElevenLabsProvider] Audio successfully saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"[ElevenLabsProvider] ElevenLabs API error generating audio for {output_path}: {e}", exc_info=True)
            return False
        finally:
            for handler in logging.getLogger().handlers: handler.flush()

def create_tts_provider(config: dict) -> Optional[TTSProvider]: # Return Optional[TTSProvider]
    """Factory function to create the appropriate TTS provider based on configuration."""
    print("[TTS_PROVIDER_PRINT] create_tts_provider called.")
    logger.info("[create_tts_provider] Called.")
    for handler in logging.getLogger().handlers: handler.flush()
    
    tts_config = config.get('tts', {})
    provider_name = tts_config.get('provider', 'gtts').lower()
    print(f"[TTS_PROVIDER_PRINT] create_tts_provider: Requested provider from config: '{provider_name}'")
    logger.info(f"[create_tts_provider] Requested provider: {provider_name}")
    
    if provider_name == 'elevenlabs':
        # This path should ideally not be taken if ELEVENLABS_AVAILABLE is False due to commented out import
        print("[TTS_PROVIDER_PRINT] create_tts_provider: ElevenLabs path selected by config.")
        if not ELEVENLABS_AVAILABLE: # ELEVENLABS_AVAILABLE is now hardcoded to False
            print("[TTS_PROVIDER_PRINT] create_tts_provider: ElevenLabs provider requested, but ELEVENLABS_AVAILABLE is False (import commented out). Falling back to gTTS.")
            logger.error("[create_tts_provider] ElevenLabs provider requested, but ELEVENLABS_AVAILABLE is False. Falling back to gTTS if possible.")
            provider_name = 'gtts' 
        else:
            # This 'else' block should not be reachable if the import is commented out.
            # Keeping it for structural integrity, but it's effectively dead code.
            print("[TTS_PROVIDER_PRINT] create_tts_provider: WARNING - ELEVENLABS_AVAILABLE is True despite import being commented. This is unexpected.")
            logger.warning("[create_tts_provider] WARNING - ELEVENLABS_AVAILABLE is True despite import being commented. Proceeding with ElevenLabs config but expecting failure.")
            elevenlabs_config = config.get('elevenlabs', {})
            api_key = elevenlabs_config.get('api_key')
            voice_id = elevenlabs_config.get('voice_id') 
            model_id = elevenlabs_config.get('model_id', 'eleven_multilingual_v2')
            
            print(f"[TTS_PROVIDER_PRINT] create_tts_provider: ElevenLabs config: voice_id={voice_id}, model_id={model_id}, api_key_present={bool(api_key)}")
            logger.info(f"[create_tts_provider] ElevenLabs config: voice_id={voice_id}, model_id={model_id}, api_key_present={bool(api_key)}")

            if not api_key:
                print("[TTS_PROVIDER_PRINT] create_tts_provider: ElevenLabs API key missing. Falling back to gTTS.")
                logger.warning("[create_tts_provider] ElevenLabs API key is missing. Falling back to gTTS.")
                provider_name = 'gtts' 
            elif not voice_id:
                print("[TTS_PROVIDER_PRINT] create_tts_provider: ElevenLabs Voice ID missing. Falling back to gTTS.")
                logger.warning("[create_tts_provider] ElevenLabs Voice ID is missing. Falling back to gTTS.")
                provider_name = 'gtts' 
            else:
                try:
                    print("[TTS_PROVIDER_PRINT] create_tts_provider: Attempting to instantiate ElevenLabsProvider.")
                    logger.info("[create_tts_provider] Attempting to instantiate ElevenLabsProvider.")
                    for handler in logging.getLogger().handlers: handler.flush()
                    return ElevenLabsProvider(api_key, voice_id, model_id)
                except ImportError: 
                    print("[TTS_PROVIDER_PRINT] create_tts_provider: ImportError during ElevenLabsProvider instantiation. Falling back to gTTS.")
                    logger.error("[create_tts_provider] ImportError during ElevenLabsProvider instantiation. Falling back to gTTS.", exc_info=True)
                    provider_name = 'gtts'
                except Exception as e:
                    print(f"[TTS_PROVIDER_PRINT] create_tts_provider: Failed to initialize ElevenLabsProvider: {e}. Falling back to gTTS.")
                    logger.error(f"[create_tts_provider] Failed to initialize ElevenLabsProvider: {e}. Falling back to gTTS.", exc_info=True)
                    provider_name = 'gtts' 
    
    if provider_name == 'gtts':
        print("[TTS_PROVIDER_PRINT] create_tts_provider: gTTS path selected (either directly or as fallback).")
        if gTTS is None:
            print("[TTS_PROVIDER_PRINT] create_tts_provider: gTTS provider requested, but gTTS library is NOT available. Cannot create provider.")
            logger.error("[create_tts_provider] gTTS provider requested or fallback, but gTTS library is not available. Cannot create provider.")
            for handler in logging.getLogger().handlers: handler.flush()
            return None 
        try:
            print("[TTS_PROVIDER_PRINT] create_tts_provider: Attempting to instantiate GTTSProvider.")
            logger.info("[create_tts_provider] Attempting to instantiate GTTSProvider.")
            for handler in logging.getLogger().handlers: handler.flush()
            return GTTSProvider(
                language=tts_config.get('language', 'pt'),
                slow=tts_config.get('slow', False)
            )
        except ImportError: 
             print("[TTS_PROVIDER_PRINT] create_tts_provider: ImportError during GTTSProvider instantiation (gTTS lib likely missing).")
             logger.error("[create_tts_provider] ImportError during GTTSProvider instantiation (gTTS lib likely missing).", exc_info=True)
             for handler in logging.getLogger().handlers: handler.flush()
             return None
        except Exception as e_gtts_init:
            print(f"[TTS_PROVIDER_PRINT] create_tts_provider: Failed to initialize GTTSProvider: {e_gtts_init}. No provider created.")
            logger.error(f"[create_tts_provider] Failed to initialize GTTSProvider: {e_gtts_init}. No provider created.", exc_info=True)
            for handler in logging.getLogger().handlers: handler.flush()
            return None

    print(f"[TTS_PROVIDER_PRINT] create_tts_provider: Unknown or uninitializable provider: {provider_name}. No provider created.")
    logger.error(f"[create_tts_provider] Unknown or uninitializable provider: {provider_name}. No provider created.")
    for handler in logging.getLogger().handlers: handler.flush()
    return None
