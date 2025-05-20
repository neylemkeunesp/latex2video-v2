#!/usr/bin/env python3
import os
import sys
import yaml
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.latex_parser import parse_latex_file, Slide
from src.tts_provider import create_tts_provider

class TestLatexParserWithElevenLabs(unittest.TestCase):
    """Test the integration of latex_parser with ElevenLabs TTS provider."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample LaTeX content for testing
        self.sample_latex = r"""
\documentclass{beamer}
\title{Test Presentation}
\author{Test Author}
\begin{document}

\begin{frame}
\titlepage
\end{frame}

\begin{frame}
\frametitle{Outline}
\tableofcontents
\end{frame}

\section{Introduction}

\begin{frame}
\frametitle{Simple Slide}
This is a simple slide with text.
\begin{itemize}
\item Item 1
\item Item 2
\end{itemize}
\end{frame}

\end{document}
"""
        # Create a temporary file
        self.temp_file = "temp_test_elevenlabs.tex"
        with open(self.temp_file, "w") as f:
            f.write(self.sample_latex)
            
        # Create output directory for audio files
        self.output_dir = os.path.join('output', 'test_elevenlabs_audio')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load configuration
        config_path = os.path.join('config', 'config.yaml')
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary file
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
    
    def test_parse_and_generate_audio(self):
        """Test parsing LaTeX and generating audio with ElevenLabs."""
        print("Testing LaTeX parsing and audio generation with ElevenLabs...")
        
        # Create TTS provider
        print("Creating TTS provider...")
        provider = create_tts_provider(self.config)
        
        self.assertIsNotNone(provider, "Failed to create TTS provider")
        print(f"TTS provider created: {provider.__class__.__name__}")
        
        # Parse the LaTeX file
        print(f"Parsing LaTeX file: {self.temp_file}")
        slides = parse_latex_file(self.temp_file)
        
        self.assertGreater(len(slides), 0, "No slides were parsed from the LaTeX file")
        print(f"Successfully parsed {len(slides)} slides from the LaTeX file")
        
        # Generate audio for each slide
        for i, slide in enumerate(slides):
            print(f"\nProcessing Slide {i+1}/{len(slides)}: {slide.title} (Type: {slide.slide_type})")
            
            # Generate text for TTS
            if slide.slide_type == "section":
                tts_text = f"Section: {slide.title}"
            else:
                tts_text = f"Slide {i+1}: {slide.title}. {slide.content}"
            
            # Generate audio file
            audio_path = os.path.join(self.output_dir, f"slide_{i+1}.mp3")
            print(f"Generating audio to {audio_path}...")
            
            success = provider.generate_audio(tts_text, audio_path)
            
            self.assertTrue(success, f"Failed to generate audio for slide {i+1}")
            self.assertTrue(os.path.exists(audio_path), f"Audio file was not created at {audio_path}")
            self.assertGreater(os.path.getsize(audio_path), 0, f"Audio file is empty at {audio_path}")
            
            print(f"Audio successfully generated at {audio_path}")
        
        print(f"\nSuccessfully generated audio for {len(slides)} slides")

if __name__ == "__main__":
    unittest.main()
