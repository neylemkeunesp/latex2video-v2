import sys
# Attempt to add user's local site-packages to path for pydub
user_site_packages = "/home/lemke/.local/lib/python3.10/site-packages"
if user_site_packages not in sys.path:
    sys.path.insert(0, user_site_packages)

import os
import shutil
import tempfile
from PIL import Image
from pydub import AudioSegment
# Assuming simple_video_assembler is in src and src is in PYTHONPATH or script is run from project root
from src.simple_video_assembler import assemble_video 

def generate_video():
    # Determine the project's base directory dynamically
    # This script is expected to be in /home/lemke/latex2video
    base_dir = os.path.dirname(os.path.abspath(__file__)) 
    
    # Temporary directory for slides and audio assets
    temp_creation_dir = tempfile.mkdtemp(prefix="playback_video_assets_")
    slides_dir = os.path.join(temp_creation_dir, "slides")
    audio_dir = os.path.join(temp_creation_dir, "audio")
    
    # Output directory for the final video, relative to the project root
    final_output_dir = os.path.join(base_dir, "output") 
    
    os.makedirs(slides_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(final_output_dir, exist_ok=True)

    config = {
        "video": {
            "output_filename": "test_video.mp4", # Consistent with the test video name
            "fps": 30,
            "resolution": "320x240", # Smaller resolution for quick generation
            "background_color": "#000000"
        },
        "output_dir": final_output_dir # Absolute path to the output directory
    }

    # Create dummy image files
    image_files = []
    for i in range(2): # Create 2 dummy images
        img = Image.new('RGB', (100, 100), color = ('red' if i % 2 == 0 else 'blue'))
        img_path = os.path.join(slides_dir, f"slide_{i+1:03d}.png")
        img.save(img_path)
        image_files.append(img_path)

    # Create dummy audio files (e.g., 1 second of silence)
    audio_files = []
    silence = AudioSegment.silent(duration=1000) # 1 second
    for i in range(2): # Create 2 dummy audio files
        audio_path = os.path.join(audio_dir, f"audio_{i+1:03d}.mp3")
        try:
            with open(audio_path, "wb") as f: # Ensure binary mode for export
                silence.export(f, format="mp3")
        except Exception as e:
            print(f"Warning: Could not export audio properly for {audio_path}: {e}. Trying alternative.")
            # Fallback if opening as binary fails for some reason
            silence.export(audio_path, format="mp3") 
        audio_files.append(audio_path)
    
    print(f"Attempting to assemble video with images: {image_files} and audio: {audio_files}")
    print(f"Using config: {config}")

    # Call the video assembly function
    output_video_path = assemble_video(image_files, audio_files, config)

    if output_video_path and os.path.exists(output_video_path):
        print(f"Video successfully generated for playback: {output_video_path}")
    else:
        print(f"Failed to generate video for playback. Result from assemble_video: {output_video_path}")

    # Clean up the temporary directory used for slides and audio assets
    # The generated video in 'output/' will remain.
    shutil.rmtree(temp_creation_dir)
    print(f"Cleaned up temporary asset directory: {temp_creation_dir}")

if __name__ == "__main__":
    generate_video()
