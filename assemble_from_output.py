import sys
import os
# Attempt to add user's local site-packages to path for pydub
user_site_packages = "/home/lemke/.local/lib/python3.10/site-packages"
if user_site_packages not in sys.path:
    sys.path.insert(0, user_site_packages)

import logging

# Assuming simple_video_assembler is in src and this script is at the project root
from src.simple_video_assembler import assemble_video, load_config, natural_sort

# Setup logging
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assemble_from_output.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler(sys.stdout)  # Also print to console
    ]
)

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    logging.info(f"Project root: {project_root}")
    slides_dir = os.path.join(project_root, "output", "slides")
    audio_dir = os.path.join(project_root, "output", "audio")
    
    # Configuration - use default from simple_video_assembler or load a specific one
    # For this specific request, we'll use a modified config to change the output filename
    # and ensure the output_dir is set correctly.
    config_path = os.path.join(project_root, 'config', 'config.yaml')
    config = load_config(config_path)
    if not config:
        logging.warning("Could not load config/config.yaml. Using default video settings.")
        config = {
            "video": {
                "output_filename": "final_video_from_output.mp4",
                "fps": 30,
                "resolution": "1920x1080", 
                "background_color": "#000000"
            },
            "output_dir": os.path.join(project_root, "output") # Ensure output is in project/output
        }
    else:
        # Override filename and ensure output_dir is correct
        config['video']['output_filename'] = "final_video_from_output.mp4"
        config['output_dir'] = os.path.join(project_root, "output")

    logging.info(f"Using slides from: {slides_dir}")
    logging.info(f"Using audio from: {audio_dir}")
    logging.info(f"Using configuration: {config}")

    try:
        image_files = natural_sort([os.path.join(slides_dir, f) for f in os.listdir(slides_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        audio_files = natural_sort([os.path.join(audio_dir, f) for f in os.listdir(audio_dir) if f.lower().endswith('.mp3')])

        if not image_files:
            logging.error(f"No image files found in {slides_dir}")
            return
        
        if not audio_files:
            logging.error(f"No audio files found in {audio_dir}")
            return
        
        if len(image_files) != len(audio_files):
            logging.error(f"Mismatch between number of images ({len(image_files)}) and audio files ({len(audio_files)}). Cannot assemble video.")
            return

        logging.info(f"Found {len(image_files)} image files and {len(audio_files)} audio files.")

        output_path = assemble_video(image_files, audio_files, config)

        if output_path and os.path.exists(output_path):
            logging.info(f"Video successfully assembled: {output_path}")
        else:
            logging.error(f"Failed to assemble video. Result from assemble_video: {output_path}")
            if output_path:
                 logging.error(f"assemble_video returned a path ({output_path}) but it does not exist.")
            else:
                 logging.error("assemble_video returned an empty path or None.")


    except Exception as e:
        logging.error(f"An error occurred during script execution: {e}", exc_info=True)

if __name__ == "__main__":
    main()
