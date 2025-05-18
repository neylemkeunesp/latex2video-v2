import os
import logging
import time
from typing import List, Dict, Optional # Added Optional
import yaml

# Import the TTS provider interface and factory
from .tts_provider import create_tts_provider, TTSProvider # Added TTSProvider for type hint

# Get a logger for this module
logger = logging.getLogger(__name__)

def generate_all_audio(narrations: List[str], config: Dict) -> List[str]:
    """Generates audio files for all narration scripts using the configured TTS provider."""
    logger.info("========== generate_all_audio CALLED ==========")
    # Attempt to flush all handlers of the root logger
    for handler in logging.getLogger().handlers:
        handler.flush()

    try:
        logger.info(f"[AUDIO-DEBUG] Top of generate_all_audio. Narrations count: {len(narrations) if narrations is not None else 'None'}")
        for handler in logging.getLogger().handlers: handler.flush()

        output_base_dir = config.get('output_dir', 'output') # Changed default to 'output' for safer relative path
        audio_output_dir = os.path.abspath(os.path.join(output_base_dir, 'audio'))
        logger.info(f"[AUDIO-DEBUG] audio_output_dir: {audio_output_dir}")
        os.makedirs(audio_output_dir, exist_ok=True)
        for handler in logging.getLogger().handlers: handler.flush()

        tts_config = config.get('tts', {})
        logger.info(f"[AUDIO] Configuração TTS global: {tts_config}")
        elevenlabs_specific_config = config.get('elevenlabs', {})
        logger.info(f"[AUDIO] Configuração ElevenLabs específica: {elevenlabs_specific_config}")
        for handler in logging.getLogger().handlers: handler.flush()
        
        tts_provider: Optional[TTSProvider] = None # Initialize with type hint
        logger.info("[AUDIO-DEBUG] Attempting to call create_tts_provider...")
        for handler in logging.getLogger().handlers: handler.flush()
        
        tts_provider = create_tts_provider(config) # This is a critical call
        
        if tts_provider:
            logger.info(f"[AUDIO] Provider TTS selecionado: {tts_provider.__class__.__name__}")
        else:
            logger.error("[AUDIO] Falha ao criar provider TTS. create_tts_provider retornou None.")
        for handler in logging.getLogger().handlers: handler.flush()

        if not tts_provider:
            logger.error("[AUDIO] Abortando geração de áudio devido à falha na criação do provider.")
            return []

        audio_paths = []
        total_narrations = len(narrations)
        logger.info(f"[AUDIO] Total de narrações para processar: {total_narrations}")
        for handler in logging.getLogger().handlers: handler.flush()
        
        for i, narration_text in enumerate(narrations):
            slide_num = i + 1
            output_file = os.path.join(audio_output_dir, f"audio_{slide_num}.mp3")
            logger.info(f"[AUDIO-DEBUG] Loop iteration: slide {slide_num}/{total_narrations}")
            logger.info(f"[AUDIO] --- Slide {slide_num}/{total_narrations} ---")
            logger.info(f"[AUDIO] Caminho de saída: {output_file}")
            # Limit log length for narration text to avoid overly verbose logs
            log_narration_text = narration_text[:200].replace(chr(10), ' ') + ('...' if len(narration_text) > 200 else '')
            logger.info(f"[AUDIO] Texto da narração (prévia): {log_narration_text}")
            for handler in logging.getLogger().handlers: handler.flush()
            
            start_time = time.time()
            success = False # Initialize
            logger.info(f"[AUDIO-DEBUG] Attempting to call tts_provider.generate_audio for slide {slide_num}")
            for handler in logging.getLogger().handlers: handler.flush()
            
            success = tts_provider.generate_audio(narration_text, output_file) # Critical call
            
            logger.info(f"[AUDIO-DEBUG] Retorno de tts_provider.generate_audio: {success} para {output_file}")
            for handler in logging.getLogger().handlers: handler.flush()
            
            elapsed = time.time() - start_time
            logger.info(f"[AUDIO-DEBUG] Tempo de execução para slide {slide_num}: {elapsed:.2f}s")
            
            if success:
                logger.info(f"[AUDIO] Áudio gerado com sucesso: {output_file}")
                audio_paths.append(output_file)
            else:
                logger.error(f"[AUDIO] Falha ao gerar áudio para o slide {slide_num}. Interrompendo o processo.")
                logger.info(f"[AUDIO-DEBUG] audio_paths até o erro: {audio_paths}")
                return [] 

            # Add a small delay between API calls to avoid rate limiting if using online services
            # Consider making this delay configurable or specific to certain providers
            time.sleep(config.get('tts', {}).get('delay_between_calls', 1))
            for handler in logging.getLogger().handlers: handler.flush()

        logger.info(f"[AUDIO] Geração de áudios finalizada. Total gerado: {len(audio_paths)}")
        logger.info(f"[AUDIO-DEBUG] Lista final de audio_paths: {audio_paths}")
        return audio_paths

    except Exception as e: # Catch Python-level exceptions
        logger.error(f"[AUDIO] Exceção Python não tratada em generate_all_audio: {e}", exc_info=True)
        return [] 
    finally:
        logger.info("========== generate_all_audio EXITED ==========")
        for handler in logging.getLogger().handlers:
            handler.flush()


if __name__ == '__main__':
    # Basic logging setup for standalone execution
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')
    logger.info("Executing audio_generator.py as standalone script.")

    # Example usage:
    # Needs narrations generated first
    # Adjust relative paths for standalone execution if necessary
    # This assumes the script is run from the project root (e.g., python src/audio_generator.py)
    # For consistency, paths should be relative to project root or absolute.
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logger.info(f"Project root (assumed for standalone): {project_root}")

    config_path = os.path.join(project_root, 'config', 'config.yaml')
    sample_latex_file = os.path.join(project_root, 'assets', 'presentation.tex')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f: # Added encoding
            cfg = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}", exc_info=True)
        cfg = {}

    if cfg:
        # Ensure output_dir is relative to project root or absolute
        # If config has 'output_dir', make it absolute if it's relative
        if 'output_dir' in cfg:
            if not os.path.isabs(cfg['output_dir']):
                cfg['output_dir'] = os.path.join(project_root, cfg['output_dir'])
        else: # Default if not in config
            cfg['output_dir'] = os.path.join(project_root, 'output')
        
        logger.info(f"Using output directory: {cfg['output_dir']}")
        os.makedirs(os.path.join(cfg['output_dir'], 'audio'), exist_ok=True)

        # Dynamically import latex_parser and narration_generator for standalone test
        try:
            from latex_parser import parse_latex_file 
            from narration_generator import generate_all_narrations
            
            logger.info(f"Parsing LaTeX file: {sample_latex_file}")
            parsed_slides = parse_latex_file(sample_latex_file)
            
            if parsed_slides:
                logger.info(f"Generating narrations for {len(parsed_slides)} slides.")
                narrations = generate_all_narrations(parsed_slides, cfg)
                if narrations:
                    logger.info(f"Generating audio for {len(narrations)} narrations.")
                    generated_audio = generate_all_audio(narrations, cfg)
                    if generated_audio:
                        logger.info(f"Generated {len(generated_audio)} audio files:")
                        for aud_path in generated_audio: # Renamed 'aud' to 'aud_path'
                            logger.info(aud_path)
                    else:
                        logger.error("Audio generation failed or produced no files.")
                else:
                    logger.error("Narration generation failed.")
            else:
                logger.error(f"Could not parse slides from {sample_latex_file}.")

        except ImportError as ie:
            logger.error(f"Failed to import modules for standalone test: {ie}. Ensure PYTHONPATH is set or run from project root.")
        except Exception as main_exc:
            logger.error(f"An error occurred during standalone execution: {main_exc}", exc_info=True)
            
    else:
        logger.error("Could not load configuration. Aborting standalone test.")
