import os
import logging
from moviepy.editor import *
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from typing import List, Dict
import yaml
from natsort import natsorted
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
    """Assembles the video from images and audio."""
    
    video_config = config.get('video', {})
    output_base_dir = config.get('output_dir', '../output')
    output_filename = video_config.get('output_filename', 'final_video.mp4')
    output_path = os.path.abspath(os.path.join(output_base_dir, output_filename))
    
    fps = video_config.get('fps', 30)
    resolution = tuple(map(int, video_config.get('resolution', '1920x1080').split('x')))
    transition_duration = video_config.get('transition_duration', 1.0)
    bg_color = video_config.get('background_color', '#FFFFFF')
    
    # Convert hex color to RGB tuple
    bg_color_rgb = tuple(int(bg_color[i:i+2], 16) for i in (1, 3, 5))

    if len(image_files) != len(audio_files):
        logging.error(f"Mismatch between number of images ({len(image_files)}) and audio files ({len(audio_files)}). Cannot assemble video.")
        return ""
        
    if not image_files:
        logging.error("No image files provided for video assembly.")
        return ""

    logging.info(f"Assembling video: {len(image_files)} slides, Resolution: {resolution}, FPS: {fps}")

    clips = []
    total_duration = 0
    
    image_files = natsorted(image_files)
    audio_files = natsorted(audio_files)

    # Create a temporary directory for processed images
    import tempfile
    temp_dir = tempfile.mkdtemp()
    logging.info(f"Created temporary directory for processed images: {temp_dir}")
    
    processed_image_files = []

    # Pre-process all images to ensure they are compatible
    for i, img_path in enumerate(image_files):
        try:
            # Use PIL to open, convert to RGB, and resize the image
            img = Image.open(img_path).convert('RGB')
            
            # Calculate scaling factors while maintaining aspect ratio
            width, height = resolution
            img_width, img_height = img.size
            ratio = min(width/img_width, height/img_height)
            new_size = (int(img_width*ratio), int(img_height*ratio))
            
            # Resize with high-quality filtering
            img = img.resize(new_size, Image.LANCZOS)
            
            # Create a new image with the background color
            new_img = Image.new('RGB', resolution, bg_color_rgb)
            
            # Paste the resized image in the center
            x_offset = (width - new_size[0]) // 2
            y_offset = (height - new_size[1]) // 2
            new_img.paste(img, (x_offset, y_offset))
            
            # Save the processed image to the temporary directory
            processed_img_path = os.path.join(temp_dir, f"processed_slide_{i+1}.png")
            new_img.save(processed_img_path)
            processed_image_files.append(processed_img_path)
            
            logging.info(f"Processed image {i+1}/{len(image_files)}: {os.path.basename(img_path)} -> {os.path.basename(processed_img_path)}")
            
        except Exception as e:
            logging.error(f"Error processing image {i+1} ({img_path}): {e}")
            # Create a solid color image as fallback
            fallback_img = Image.new('RGB', resolution, bg_color_rgb)
            processed_img_path = os.path.join(temp_dir, f"processed_slide_{i+1}.png")
            fallback_img.save(processed_img_path)
            processed_image_files.append(processed_img_path)
            logging.info(f"Created fallback image for slide {i+1}")

    # Now create video clips using the processed images
    for i, (img_path, audio_path) in enumerate(zip(processed_image_files, audio_files)):
        logging.info(f"Creating clip for slide {i+1}: Image='{os.path.basename(img_path)}', Audio='{os.path.basename(audio_path)}'")
        
        try:
            # Load audio
            audio_clip = AudioFileClip(audio_path)
            slide_duration = audio_clip.duration
            
            # Create image clip directly from the processed image file
            img_clip = ImageClip(img_path, duration=slide_duration)
            
            # Set audio
            img_clip = img_clip.set_audio(audio_clip)
            img_clip = img_clip.set_start(total_duration)
            
            # Validate durations match
            if abs(audio_clip.duration - img_clip.duration) > 0.1:
                logging.warning(f"Duration mismatch: audio={audio_clip.duration:.2f}s, image={img_clip.duration:.2f}s")
                # Adjust to match audio duration
                img_clip = img_clip.set_duration(audio_clip.duration)
            
            clips.append(img_clip)
            total_duration += slide_duration
            
        except Exception as e:
            logging.error(f"Error creating clip for slide {i+1} (Image: {img_path}, Audio: {audio_path}): {e}")
            # Create a fallback clip with solid color
            try:
                color_clip = ColorClip(size=resolution, color=bg_color, duration=audio_clip.duration if 'audio_clip' in locals() else 5)
                if 'audio_clip' in locals():
                    color_clip = color_clip.set_audio(audio_clip)
                color_clip = color_clip.set_start(total_duration)
                clips.append(color_clip)
                total_duration += color_clip.duration
                logging.info(f"Created fallback clip for slide {i+1}")
            except Exception as e2:
                logging.error(f"Error creating fallback clip for slide {i+1}: {e2}")

    if not clips:
        logging.error("No video clips were created.")
        return ""

    logging.info(f"Concatenating {len(clips)} clips. Total duration: {total_duration:.2f}s")
    
    # Create the final video with concatenated clips
    final_clip = concatenate_videoclips(clips, method="compose")
    
    if not final_clip:
        logging.error("Failed to concatenate video clips.")
        return ""
        
    logging.info(f"Final video duration: {final_clip.duration:.2f}s")

    logging.info(f"Writing final video to: {output_path}")
    try:
        final_clip.write_videofile(
            output_path,
            fps=fps,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            threads=4,
            logger='bar'
        )
        logging.info("Video assembly completed successfully.")
        return output_path
    except Exception as e:
        logging.error(f"Error writing final video file: {e}")
        return ""
    finally:
        for clip in clips:
            clip.close()
        if 'audio_clip' in locals() and audio_clip:
             audio_clip.close()

if __name__ == '__main__':
    cfg = load_config()
    if cfg:
        cfg['output_dir'] = '../output'
        slides_dir = os.path.abspath(os.path.join(cfg['output_dir'], 'slides'))
        audio_dir = os.path.abspath(os.path.join(cfg['output_dir'], 'audio'))

        image_files = natsorted([os.path.join(slides_dir, f) for f in os.listdir(slides_dir) if f.endswith('.png')])
        audio_files = natsorted([os.path.join(audio_dir, f) for f in os.listdir(audio_dir) if f.endswith('.mp3')])

        if image_files and audio_files:
            final_video_path = assemble_video(image_files, audio_files, cfg)
            if final_video_path:
                print(f"Final video saved to: {final_video_path}")
            else:
                print("Video assembly failed.")
        else:
            print("Could not find generated image or audio files.")
    else:
        print("Could not load configuration.")
