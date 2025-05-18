import os
import sys
import logging
from video_assembler import assemble_video, load_config

# Configure logging to show debug output and print to console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

def main():
    config = load_config('../config/config.yaml')
    if not config:
        return

    # Set default output directory if not specified
    config['output_dir'] = config.get('output_dir', '../output')

    # Get existing files
    slides_dir = os.path.abspath(os.path.join(config['output_dir'], 'slides'))
    audio_dir = os.path.abspath(os.path.join(config['output_dir'], 'audio'))
    
    image_files = sorted([os.path.join(slides_dir, f) for f in os.listdir(slides_dir) 
                         if f.startswith('slide_') and f.endswith('.png')])
    audio_files = sorted([os.path.join(audio_dir, f) for f in os.listdir(audio_dir)
                         if f.startswith('audio_') and f.endswith('.mp3')])

    # Handle case where there's an extra title slide
    if len(image_files) == len(audio_files) + 1:
        logging.info("Excluding first slide (likely title page)")
        image_files = image_files[1:]
    elif len(image_files) != len(audio_files):
        logging.error(f"Mismatch: {len(image_files)} slides vs {len(audio_files)} audio files")
        return

    logging.info(f"Assembling video from {len(image_files)} existing slides/audio pairs")
    final_video = assemble_video(image_files, audio_files, config)
    
    if final_video:
        logging.info(f"Successfully created video at: {final_video}")
    else:
        logging.error("Video assembly failed")

if __name__ == "__main__":
    main()
