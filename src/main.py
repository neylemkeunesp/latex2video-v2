import os
import logging
import yaml
import argparse

# Setup logging as early as possible
# Ensure the root logger is configured so that module-level loggers inherit its settings.
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler() # Ensure logs go to console
    ]
)
# Get a logger for this module
logger = logging.getLogger(__name__)

# Log before any local imports that might be problematic
logger.info("[MAIN_IMPORT] Starting imports in main.py...")
for handler in logging.getLogger().handlers: handler.flush()

try:
    from .latex_parser import parse_latex_file
    logger.info("[MAIN_IMPORT] Imported latex_parser.")
    from .image_generator import generate_slide_images
    logger.info("[MAIN_IMPORT] Imported image_generator.")
    from .narration_generator import generate_all_narrations
    logger.info("[MAIN_IMPORT] Imported narration_generator.")
    
    logger.info("[MAIN_IMPORT] Attempting to import audio_generator...")
    for handler in logging.getLogger().handlers: handler.flush()
    from .audio_generator import generate_all_audio
    logger.info("[MAIN_IMPORT] Successfully imported audio_generator.")
    for handler in logging.getLogger().handlers: handler.flush()
    
    from .video_assembler import assemble_video
    logger.info("[MAIN_IMPORT] Imported video_assembler.")
    logger.info("[MAIN_IMPORT] All main imports in main.py completed.")
    for handler in logging.getLogger().handlers: handler.flush()

except ImportError as e:
    logger.critical(f"[MAIN_IMPORT] CRITICAL: Failed to import a module in main.py: {e}", exc_info=True)
    for handler in logging.getLogger().handlers: handler.flush()
    # If imports fail, the application likely cannot continue.
    # Consider exiting or raising the error.
    raise
except Exception as e_imp: # Catch any other exception during imports
    logger.critical(f"[MAIN_IMPORT] CRITICAL: Unexpected error during imports in main.py: {e_imp}", exc_info=True)
    for handler in logging.getLogger().handlers: handler.flush()
    raise


def load_config(config_path: str) -> dict:
    """Loads configuration from YAML file."""
    logger.info(f"[CONFIG] Attempting to load configuration from {config_path}")
    try:
        with open(config_path, 'r', encoding='utf-8') as f: # Added encoding
            config = yaml.safe_load(f)
        logger.info(f"[CONFIG] Configuration loaded successfully from {config_path}")
        
        config_dir = os.path.dirname(os.path.abspath(config_path))
        # Default output dir relative to project root (one level up from src, then into output)
        default_output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output'))
        
        # If output_dir is in config and relative, make it relative to config file's location's parent (project root)
        # If output_dir is absolute, use it as is.
        # If output_dir is not in config, use default.
        if 'output_dir' in config:
            if not os.path.isabs(config['output_dir']):
                # Assuming output_dir in config is relative to project root
                project_root_from_config = os.path.dirname(config_dir) # Parent of config dir
                config['output_dir'] = os.path.abspath(os.path.join(project_root_from_config, config['output_dir']))
            # else: it's absolute, use as is
        else:
            config['output_dir'] = default_output_dir
            
        logger.info(f"[CONFIG] Final output directory set to: {config['output_dir']}")
        return config
    except FileNotFoundError:
        logger.error(f"[CONFIG] Configuration file not found: {config_path}")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"[CONFIG] Error parsing configuration file {config_path}: {e}", exc_info=True)
        return {}
    except Exception as e:
        logger.error(f"[CONFIG] An unexpected error occurred loading config: {e}", exc_info=True)
        return {}
    finally:
        for handler in logging.getLogger().handlers: handler.flush()

def main(latex_file: str, config_file: str):
    """Main function to generate video from LaTeX presentation."""
    logger.info("--- Starting LaTeX to Video Generation ---")
    for handler in logging.getLogger().handlers: handler.flush()
    
    # --- 1. Load Configuration ---
    config = load_config(config_file)
    if not config:
        logger.error("Failed to load configuration. Exiting.")
        return
    
    config['latex_file_path'] = os.path.abspath(latex_file)
    logger.info(f"[MAIN] LaTeX file path set in config: {config['latex_file_path']}")

    output_dir = config.get('output_dir') # Should be absolute now
    slides_dir = os.path.join(output_dir, 'slides')
    audio_dir = os.path.join(output_dir, 'audio')
    temp_pdf_dir = os.path.join(output_dir, 'temp_pdf')
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(slides_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(temp_pdf_dir, exist_ok=True)
        logger.info(f"Ensured output directories exist in: {output_dir}")
    except OSError as e:
        logger.error(f"Error creating output directories: {e}", exc_info=True)
        return
    finally:
        for handler in logging.getLogger().handlers: handler.flush()

    # --- 2. Parse LaTeX File ---
    logger.info("Step 1: Parsing LaTeX file...")
    for handler in logging.getLogger().handlers: handler.flush()
    slides = parse_latex_file(latex_file)
    if not slides:
        logger.error("Failed to parse slides from LaTeX file. Exiting.")
        return
    logger.info(f"Successfully parsed {len(slides)} slides.")
    for handler in logging.getLogger().handlers: handler.flush()

    # --- 3. Generate Slide Images ---
    logger.info("Step 2: Generating slide images...")
    for handler in logging.getLogger().handlers: handler.flush()
    abs_latex_file_path = os.path.abspath(latex_file)
    image_paths = generate_slide_images(abs_latex_file_path, config)
    if not image_paths:
        logger.error("Failed to generate slide images. Exiting.")
        return
    logger.info(f"Generated {len(image_paths)} raw slide images.")
    for handler in logging.getLogger().handlers: handler.flush()
        
    content_image_paths = []
    if len(image_paths) == len(slides):
        logger.info("Number of images matches number of slides. All slides will be included in the video.")
        content_image_paths = image_paths
    else:
        logger.warning(f"Mismatch between images ({len(image_paths)}) and slides ({len(slides)}). Attempting to adjust...")
        if len(image_paths) > len(slides):
            logger.info(f"Using only the first {len(slides)} images, assuming extra images are non-content (e.g. title pages not in parsed slides).")
            content_image_paths = image_paths[:len(slides)]
        elif len(slides) > len(image_paths):
            logger.info(f"More slides parsed ({len(slides)}) than images generated ({len(image_paths)}). Using only the first {len(image_paths)} slides for narration and video.")
            slides = slides[:len(image_paths)] # Trim slides to match available images
            content_image_paths = image_paths
    logger.info(f"Successfully prepared {len(content_image_paths)} slides with matching images for video.")
    for handler in logging.getLogger().handlers: handler.flush()


    # --- 4. Generate Narration Scripts ---
    logger.info("Step 3: Generating narration scripts...")
    for handler in logging.getLogger().handlers: handler.flush()
    narrations = generate_all_narrations(slides, config) # Pass potentially trimmed slides
    if not narrations or len(narrations) != len(slides): # Compare with (potentially trimmed) slides
        logger.error(f"Failed to generate narration scripts or mismatch in count (Narrations: {len(narrations) if narrations else 0}, Slides: {len(slides)}). Exiting.")
        return
    logger.info(f"Successfully generated {len(narrations)} narration scripts.")
    for handler in logging.getLogger().handlers: handler.flush()

    # --- 5. Generate Audio Files ---
    logger.info("Step 4: Generating audio files...") # This is the message seen in user feedback
    logger.info(f"Preparing to generate audio for {len(narrations)} narration scripts. Output directory: {audio_dir}")
    for handler in logging.getLogger().handlers: handler.flush()
    
    audio_paths = None
    try:
        logger.info("[MAIN_AUDIO_CALL] >>> Calling generate_all_audio now...")
        for handler in logging.getLogger().handlers: handler.flush()
        
        audio_paths = generate_all_audio(narrations, config) # THE CRITICAL CALL
        
        logger.info(f"[MAIN_AUDIO_CALL] <<< Returned from generate_all_audio. Result: {'Success' if audio_paths else 'Failure/Empty'}")
        if audio_paths: logger.info(f"[MAIN_AUDIO_CALL] audio_paths count: {len(audio_paths)}")
        for handler in logging.getLogger().handlers: handler.flush()

    except Exception as e_audio_gen: # Catch any Python exception from generate_all_audio
        logger.error(f"[MAIN_AUDIO_CALL] !!!! Exception during generate_all_audio call: {e_audio_gen}", exc_info=True)
        for handler in logging.getLogger().handlers: handler.flush()
        # Decide if to exit or try to continue if partial audio is acceptable (currently, it's not)
        logger.error("Audio generation step failed critically. Exiting.")
        return

    if not audio_paths or len(audio_paths) != len(narrations):
        logger.error(f"Failed to generate all audio files or mismatch in count (Audio files: {len(audio_paths) if audio_paths else 0}, Narrations: {len(narrations)}). Exiting.")
        return
    logger.info(f"Successfully generated {len(audio_paths)} audio files.")
    for handler in logging.getLogger().handlers: handler.flush()

    # --- 6. Assemble Final Video ---
    logger.info("Step 5: Assembling final video...")
    for handler in logging.getLogger().handlers: handler.flush()
    final_video_path = assemble_video(content_image_paths, audio_paths, config)
    if not final_video_path:
        logger.error("Failed to assemble the final video. Exiting.")
        return
        
    logger.info(f"--- Video Generation Complete ---")
    logger.info(f"Final video saved to: {final_video_path}")
    print(f"\nSuccess! Final video available at: {final_video_path}")
    for handler in logging.getLogger().handlers: handler.flush()


if __name__ == "__main__":
    # This basicConfig in __main__ will only take effect if the script is run directly
    # and no other logging config has been set. If this module is imported,
    # the basicConfig at the top of the file will have already run.
    # For consistency, the top-level config is preferred.
    # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s')
    
    logger.info("[MAIN_SCRIPT_EXEC] main.py is being run as a script.")
    for handler in logging.getLogger().handlers: handler.flush()

    parser = argparse.ArgumentParser(description="Generate a narrated video from a LaTeX Beamer presentation.")
    parser.add_argument("latex_file", help="Path to the input LaTeX (.tex) file.")
    parser.add_argument("-c", "--config", default="config/config.yaml", 
                        help="Path to the configuration YAML file (default: config/config.yaml relative to project root).")
    
    args = parser.parse_args()
    logger.info(f"[MAIN_SCRIPT_EXEC] Parsed arguments: {args}")

    # Determine project root (assuming main.py is in a 'src' directory)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ../ from src/
    logger.info(f"[MAIN_SCRIPT_EXEC] Determined project root: {project_root}")

    config_path_arg = args.config
    if not os.path.isabs(config_path_arg):
        config_path = os.path.join(project_root, config_path_arg)
        logger.info(f"[MAIN_SCRIPT_EXEC] Relative config path '{config_path_arg}' resolved to absolute: {config_path}")
    else:
        config_path = config_path_arg
        logger.info(f"[MAIN_SCRIPT_EXEC] Absolute config path provided: {config_path}")
        
    latex_path_arg = args.latex_file
    if not os.path.isabs(latex_path_arg):
        # If latex_file is relative, assume it's relative to the current working directory
        # from where the script was invoked, not necessarily project_root.
        latex_path = os.path.abspath(latex_path_arg)
        logger.info(f"[MAIN_SCRIPT_EXEC] Relative LaTeX path '{latex_path_arg}' resolved to absolute (from CWD): {latex_path}")
    else:
        latex_path = latex_path_arg
        logger.info(f"[MAIN_SCRIPT_EXEC] Absolute LaTeX path provided: {latex_path}")


    if not os.path.exists(latex_path):
         logger.error(f"[MAIN_SCRIPT_EXEC] Error: LaTeX input file not found at {latex_path}")
         print(f"Error: LaTeX input file not found at {latex_path}")
    elif not os.path.exists(config_path):
         logger.error(f"[MAIN_SCRIPT_EXEC] Error: Config file not found at {config_path}")
         print(f"Error: Config file not found at {config_path}")
    else:
         logger.info(f"[MAIN_SCRIPT_EXEC] Calling main_function with LaTeX: {latex_path}, Config: {config_path}")
         for handler in logging.getLogger().handlers: handler.flush()
         main(latex_path, config_path)
         logger.info("[MAIN_SCRIPT_EXEC] main_function finished.")
         for handler in logging.getLogger().handlers: handler.flush()
