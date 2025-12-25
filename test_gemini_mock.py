import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.automated_video_generation import initialize_llm_client, generate_script_with_llm

class TestGeminiIntegration(unittest.TestCase):
    def setUp(self):
        self.config_gemini = {
            'llm_provider': 'gemini',
            'gemini': {
                'api_key': 'fake_key',
                'model': 'gemini-3.0-flash',
                'temperature': 0.7
            }
        }
        self.config_openai = {
            'llm_provider': 'openai',
            'openai': {
                'api_key': 'fake_key',
                'model': 'gpt-4o'
            }
        }

    @patch('src.automated_video_generation.genai')
    def test_initialize_client_gemini(self, mock_genai):
        client = initialize_llm_client(self.config_gemini)
        mock_genai.configure.assert_called_with(api_key='fake_key')
        self.assertIsNotNone(client)

    @patch('src.automated_video_generation.OpenAI')
    def test_initialize_client_openai(self, mock_openai):
        client = initialize_llm_client(self.config_openai)
        mock_openai.assert_called_with(api_key='fake_key')
        self.assertIsNotNone(client)

    def test_generate_script_gemini(self):
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Generated script content"
        mock_model.generate_content.return_value = mock_response
        mock_client.GenerativeModel.return_value = mock_model

        prompt_data = {
            "prompt": "Test Prompt",
            "title": "Test Title",
            "slide_number": 1
        }

        # We pass our mock_client which mimics the 'genai' module behavior expected
        script = generate_script_with_llm(mock_client, prompt_data, self.config_gemini)
        
        self.assertEqual(script, "Generated script content")
        mock_client.GenerativeModel.assert_called_with('gemini-3.0-flash')
        mock_model.generate_content.assert_called()

    @patch('src.automated_video_generation.PIL.Image.open')
    @patch('src.automated_video_generation.os.path.exists')
    def test_generate_script_gemini_with_image(self, mock_exists, mock_open):
        mock_exists.return_value = True
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Generated script with image"
        mock_model.generate_content.return_value = mock_response
        mock_client.GenerativeModel.return_value = mock_model

        prompt_data = {
            "prompt": "Test Prompt",
            "title": "Test Title",
            "slide_number": 1,
            "image_path": "/fake/path/to/image.png"
        }

        script = generate_script_with_llm(mock_client, prompt_data, self.config_gemini)
        
        self.assertEqual(script, "Generated script with image")
        # Check that generate_content was called with a list (text + image)
        args, kwargs = mock_model.generate_content.call_args
        self.assertIsInstance(args[0], list)
        self.assertEqual(len(args[0]), 2) # Text + Image

if __name__ == '__main__':
    unittest.main()
