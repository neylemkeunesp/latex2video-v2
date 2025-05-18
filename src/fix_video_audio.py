import os
import sys
import logging
from moviepy.editor import *
from natsort import natsorted

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

def main():
    # Paths
    output_dir = '../output'
    slides_dir = os.path.join(output_dir, 'slides')
    audio_dir = os.path.join(output_dir, 'audio')
    output_path = os.path.join(output_dir, 'final_video_with_audio.mp4')
    
    # Get files
    image_files = natsorted([os.path.join(slides_dir, f) for f in os.listdir(slides_dir) 
                           if f.startswith('slide_') and f.endswith('.png')])
    audio_files = natsorted([os.path.join(audio_dir, f) for f in os.listdir(audio_dir)
                           if f.startswith('audio_') and f.endswith('.mp3')])
    
    # Handle case where there's an extra title slide
    if len(image_files) == len(audio_files) + 1:
        logging.info("Excluding first slide (likely title page)")
        image_files = image_files[1:]
    
    if len(image_files) != len(audio_files):
        logging.error(f"Mismatch: {len(image_files)} slides vs {len(audio_files)} audio files")
        return
    
    logging.info(f"Creating video from {len(image_files)} slides and audio files")
    
    # Create clips
    clips = []
    for i, (img_path, audio_path) in enumerate(zip(image_files, audio_files)):
        logging.info(f"Processing slide {i+1}: {os.path.basename(img_path)} with {os.path.basename(audio_path)}")
        
        # Load audio to get duration
        audio = AudioFileClip(audio_path)
        
        # Create image clip with duration matching audio
        img_clip = ImageClip(img_path, duration=audio.duration)
        
        # Set audio
        video_clip = img_clip.set_audio(audio)
        
        clips.append(video_clip)
    
    # Concatenate clips
    final_clip = concatenate_videoclips(clips, method="compose")
    
    # Write final video
    logging.info(f"Writing final video to {output_path}")
    final_clip.write_videofile(
        output_path,
        fps=30,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True
    )
    
    logging.info("Video creation complete!")

if __name__ == "__main__":
    main()
