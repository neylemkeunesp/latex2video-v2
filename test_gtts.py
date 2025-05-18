#!/usr/bin/env python3
"""
Test script to demonstrate the gTTS (Google Text-to-Speech) functionality.
This script generates audio for a sample text in Portuguese using gTTS.
"""

import os
import logging
from gtts import gTTS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # Sample text in Portuguese with some mathematical content
    sample_text = """
    Bem-vindos à nossa apresentação sobre cálculo diferencial.
    
    Hoje vamos falar sobre a derivada de uma função.
    A derivada de uma função f de x é definida como o limite da razão entre a variação da função
    e a variação da variável independente, quando esta variação tende a zero.
    
    Por exemplo, a derivada de x ao quadrado é igual a 2x.
    """
    
    # Ensure output directory exists
    output_dir = "output/audio"
    os.makedirs(output_dir, exist_ok=True)
    
    # Output file path
    output_file = os.path.join(output_dir, "gtts_test.mp3")
    
    try:
        # Create gTTS object
        logging.info(f"Generating audio using gTTS for sample text...")
        tts = gTTS(text=sample_text, lang='pt', slow=False)
        
        # Save to file
        tts.save(output_file)
        
        logging.info(f"Audio successfully generated and saved to {output_file}")
        print(f"\nAudio file created: {output_file}")
        print("You can play this file to test the gTTS functionality.")
        
    except Exception as e:
        logging.error(f"Failed to generate audio: {e}")

if __name__ == "__main__":
    main()
