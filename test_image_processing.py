import os
import logging
import numpy as np
from PIL import Image
from moviepy.editor import ImageClip, ColorClip, CompositeVideoClip

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_image(path):
    try:
        # Test with the problematic image
        img = Image.open(path).convert('RGB')
        print(f"Original image: {img.size}, mode: {img.mode}")

        # Resize to 1920x1080 maintaining aspect
        width, height = 1920, 1080
        img_width, img_height = img.size
        ratio = min(width/img_width, height/img_height)
        new_size = (int(img_width*ratio), int(img_height*ratio))
        img = img.resize(new_size, Image.LANCZOS)

        # Convert to numpy array
        img_array = np.array(img)
        print(f"Array shape: {img_array.shape}, dtype: {img_array.dtype}")

        # Create background
        bg_array = np.zeros((height, width, 3), dtype=np.uint8)
        bg_array[:] = [255, 255, 255] # White background
        
        # Center the image
        x_offset = (width - new_size[0]) // 2
        y_offset = (height - new_size[1]) // 2
        
        # Handle channel dimensions
        if len(img_array.shape) == 2:
            img_array = np.dstack([img_array]*3)
        img_array = img_array[:,:,:3] # Ensure only 3 channels
            
        # Paste into background
        bg_array[y_offset:y_offset+new_size[1], x_offset:x_offset+new_size[0]] = img_array
        
        # Create clips
        img_clip = ImageClip(bg_array, duration=2)
        background = ColorClip(size=(width, height), color=(255,255,255), duration=2)
        
        # Composite and write test video
        final = CompositeVideoClip([background, img_clip])
        test_path = os.path.join(os.path.dirname(path), 'test_output.mp4')
        final.write_videofile(test_path, fps=24, logger='bar')
        
        print(f"Successfully created test video at: {test_path}")
        return True
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return False

if __name__ == '__main__':
    image_path = '/home/lemke/latex2video/output/slides/slide_3.png'
    test_image(image_path)
