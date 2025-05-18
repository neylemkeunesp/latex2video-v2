import sys
# Attempt to add user's local site-packages to path for pydub
user_site_packages = "/home/lemke/.local/lib/python3.10/site-packages"
if user_site_packages not in sys.path:
    sys.path.insert(0, user_site_packages)

import unittest
import os
import shutil
import tempfile
from PIL import Image
from pydub import AudioSegment
import yaml

# Adjust the import path if necessary
from src.simple_video_assembler import assemble_video, load_config

class TestVideoAssembler(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_video_assembler_")
        self.slides_dir = os.path.join(self.test_dir, "slides")
        self.audio_dir = os.path.join(self.test_dir, "audio")
        self.output_dir = "output"  # Changed to project's output directory
        
        os.makedirs(self.slides_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True) # Ensure project's output dir exists

        # Create dummy config for testing
        self.config = {
            "video": {
                "output_filename": "test_video.mp4",
                "fps": 30,
                "resolution": "320x240", # Smaller resolution for faster testing
                "background_color": "#000000"
            },
            "output_dir": self.output_dir
        }

        # Create dummy image files
        self.image_files = []
        for i in range(2): # Create 2 dummy images
            img = Image.new('RGB', (100, 100), color = ('red' if i % 2 == 0 else 'blue'))
            img_path = os.path.join(self.slides_dir, f"slide_{i+1:03d}.png")
            img.save(img_path)
            self.image_files.append(img_path)

        # Create dummy audio files (e.g., 1 second of silence)
        self.audio_files = []
        silence = AudioSegment.silent(duration=1000) # 1 second
        for i in range(2): # Create 2 dummy audio files
            audio_path = os.path.join(self.audio_dir, f"audio_{i+1:03d}.mp3")
            try:
                with open(audio_path, "wb") as f:
                    silence.export(f, format="mp3")
            except Exception as e:
                # Fallback if opening as binary fails for some reason, though unlikely
                print(f"Warning: Could not export audio properly for {audio_path}: {e}")
                silence.export(audio_path, format="mp3") # Try original way
            self.audio_files.append(audio_path)

    def tearDown(self):
        # Clean up the specific test video file from the output directory
        output_video_path = os.path.join(self.output_dir, self.config['video']['output_filename'])
        if os.path.exists(output_video_path):
            os.remove(output_video_path)
        
        # Clean up the temporary directory used for slides and audio
        shutil.rmtree(self.test_dir)

    def test_assemble_video_creates_output(self):
        output_video_path = assemble_video(self.image_files, self.audio_files, self.config)
        
        self.assertTrue(os.path.exists(output_video_path), "Video file was not created.")
        self.assertTrue(os.path.getsize(output_video_path) > 0, "Video file is empty.")
        
        # Basic check if it's a valid mp4 (can be extended with ffprobe if needed)
        with open(output_video_path, 'rb') as f:
            header = f.read(12) # Read first 12 bytes
            # A common MP4 signature starts with bytes like ftypisom or ftypmp42
            # This is a very basic check.
            self.assertIn(b'ftyp', header[4:8], "Video file does not appear to be a valid MP4 (basic check).")

    def test_assemble_video_mismatch_files(self):
        # Test with one less audio file
        output_video_path = assemble_video(self.image_files, self.audio_files[:-1], self.config)
        self.assertEqual(output_video_path, "", "Video assembly should fail with mismatched file counts.")

    def test_assemble_video_no_images(self):
        output_video_path = assemble_video([], [], self.config)
        self.assertEqual(output_video_path, "", "Video assembly should fail with no image files.")

if __name__ == '__main__':
    unittest.main()
