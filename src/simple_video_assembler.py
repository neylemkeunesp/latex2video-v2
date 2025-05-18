#!/usr/bin/env python3
import os
import logging
import subprocess
import tempfile
from typing import List, Dict
import yaml
import re

# Try to import natsort, but provide a fallback if it's not available
try:
    from natsort import natsorted
    
    def natural_sort(file_list):
        return natsorted(file_list)
except ImportError:
    # Fallback natural sorting implementation
    def natural_sort(file_list):
        def convert(text):
            return int(text) if text.isdigit() else text.lower()
        
        def alphanum_key(key):
            return [convert(c) for c in re.split('([0-9]+)', key)]
        
        return sorted(file_list, key=alphanum_key)

from PIL import Image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(config_path: str = '../config/config.yaml') -> Dict:
    """Loads configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logging.info(f"Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        return {}
    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration file {config_path}: {e}")
        return {}

def assemble_video(image_files: List[str], audio_files: List[str], config: Dict) -> str:
    """
    Assembles the video from images and audio using FFmpeg directly.
    This is a simplified version that avoids the moviepy library.
    """
    logging.info("[DEBUG] assemble_video started.")
    video_config = config.get('video', {})
    output_base_dir = config.get('output_dir', '../output')
    output_filename = video_config.get('output_filename', 'final_video.mp4')
    output_path = os.path.abspath(os.path.join(output_base_dir, output_filename))
    
    fps = video_config.get('fps', 30)
    resolution = video_config.get('resolution', '1920x1080')
    bg_color = video_config.get('background_color', '#FFFFFF')
    
    # Convert hex color to RGB tuple
    bg_color_rgb = tuple(int(bg_color[i:i+2], 16) for i in (1, 3, 5))
    width, height = map(int, resolution.split('x'))

    if len(image_files) != len(audio_files):
        logging.error(f"Mismatch between number of images ({len(image_files)}) and audio files ({len(audio_files)}). Cannot assemble video.")
        return ""
        
    if not image_files:
        logging.error("No image files provided for video assembly.")
        return ""

    logging.info(f"Assembling video: {len(image_files)} slides, Resolution: {resolution}, FPS: {fps}")

    # Sort files to ensure correct order
    logging.info("[DEBUG] Sorting image and audio files.")
    image_files = natural_sort(image_files)
    audio_files = natural_sort(audio_files)
    logging.info("[DEBUG] Files sorted.")

    # Create a temporary directory for processed files
    temp_dir = tempfile.mkdtemp()
    logging.info(f"Created temporary directory: {temp_dir}")
    
    # Process images to ensure they are all the same size and format
    processed_images = []
    total_slides = len(image_files)
    logging.info("[DEBUG] Starting image processing loop.")
    for i, img_path in enumerate(image_files):
        logging.info(f"[DEBUG] Processing image {i+1}/{total_slides}: {img_path}")
        try:
            # Open and convert to RGB
            img = Image.open(img_path).convert('RGB')
            
            # Calculate scaling to maintain aspect ratio
            img_width, img_height = img.size
            ratio = min(width/img_width, height/img_height)
            new_size = (int(img_width*ratio), int(img_height*ratio))
            
            # Resize image
            img = img.resize(new_size, Image.LANCZOS)
            
            # Create a new image with background color
            new_img = Image.new('RGB', (width, height), bg_color_rgb)
            
            # Paste the resized image in the center
            x_offset = (width - new_size[0]) // 2
            y_offset = (height - new_size[1]) // 2
            new_img.paste(img, (x_offset, y_offset))
            
            # Save processed image
            processed_path = os.path.join(temp_dir, f"slide_{i+1:03d}.png")
            new_img.save(processed_path)
            processed_images.append(processed_path)
            
            logging.info(f"Processed image {i+1}/{total_slides}: {os.path.basename(img_path)}")
        except Exception as e:
            logging.error(f"Error processing image {img_path}: {e}")
            # Create a fallback solid color image
            fallback = Image.new('RGB', (width, height), bg_color_rgb)
            processed_path = os.path.join(temp_dir, f"slide_{i+1:03d}.png")
            fallback.save(processed_path)
            processed_images.append(processed_path)
            logging.info(f"Created fallback image for {os.path.basename(img_path)}")
    logging.info("[DEBUG] Image processing loop finished.")
    
    # Create individual video segments for each slide with its audio
    video_segments = []
    total_segments = len(processed_images)
    logging.info("[DEBUG] Starting video segment creation loop.")
    for i, (img_path, audio_path) in enumerate(zip(processed_images, audio_files)):
        segment_path = os.path.join(temp_dir, f"segment_{i+1:03d}.mp4")
        logging.info(f"[DEBUG] Creating segment {i+1}/{total_segments} for image {img_path} and audio {audio_path}")
        try:
            # Use ffmpeg to create a video segment from the image and audio
            cmd = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', img_path,
                '-i', audio_path,
                '-c:v', 'libx264',
                '-tune', 'stillimage',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-pix_fmt', 'yuv420p',
                '-shortest',
                segment_path
            ]
            
            logging.info(f"Creating video segment {i+1}/{total_segments}")
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            video_segments.append(segment_path)
        except Exception as e:
            logging.error(f"Error creating video segment {i+1}: {e}")
    logging.info("[DEBUG] Video segment creation loop finished.")
    
    if not video_segments:
        logging.error("[DEBUG] No video segments were created. Aborting.")
        logging.error("No video segments were created.")
        return ""
    
    # Create a file listing all video segments
    segments_list_path = os.path.join(temp_dir, "segments.txt")
    with open(segments_list_path, 'w') as f:
        for segment in video_segments:
            f.write(f"file '{segment}'\n")
    
    # Concatenate all segments into the final video
    logging.info("[DEBUG] Starting concatenation of video segments.")
    try:
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', segments_list_path,
            '-c', 'copy',
            output_path
        ]
        
        logging.info(f"Concatenating {len(video_segments)} video segments")
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        logging.info(f"Video successfully assembled: {output_path}")
        logging.info("[DEBUG] assemble_video finished successfully.")
        return output_path
    except Exception as e:
        logging.error(f"Error concatenating video segments: {e}")
        logging.error("[DEBUG] assemble_video finished with error during concatenation.")
        return ""

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python simple_video_assembler.py <slides_dir> <audio_dir> [config_file]")
        sys.exit(1)
    
    slides_dir = sys.argv[1]
    audio_dir = sys.argv[2]
    config_file = sys.argv[3] if len(sys.argv) > 3 else '../config/config.yaml'
    
    config = load_config(config_file)
    if not config:
        print("Failed to load configuration.")
        sys.exit(1)
    
    image_files = natural_sort([os.path.join(slides_dir, f) for f in os.listdir(slides_dir) if f.endswith(('.png', '.jpg', '.jpeg'))])
    audio_files = natural_sort([os.path.join(audio_dir, f) for f in os.listdir(audio_dir) if f.endswith('.mp3')])
    
    if not image_files:
        print(f"No image files found in {slides_dir}")
        sys.exit(1)
    
    if not audio_files:
        print(f"No audio files found in {audio_dir}")
        sys.exit(1)
    
    if len(image_files) != len(audio_files):
        print(f"Mismatch between number of images ({len(image_files)}) and audio files ({len(audio_files)})")
        sys.exit(1)
    
    output_path = assemble_video(image_files, audio_files, config)
    if output_path:
        print(f"Video successfully created: {output_path}")
    else:
        print("Failed to create video.")
        sys.exit(1)
