#!/usr/bin/env python3
import os
import sys
import logging

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.chatgpt_script_generator import clean_chatgpt_response

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Test the clean_chatgpt_response function."""
    # Test with a response file
    response_file = "output/chatgpt_responses/slide_11_response.txt"
    output_file = "output/test_clean_response_output.txt"
    
    try:
        with open(response_file, 'r', encoding='utf-8') as f:
            raw_response = f.read()
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=== Original Response ===\n")
            f.write(raw_response)
            f.write("\n\n=== Cleaned Response ===\n")
            cleaned_response = clean_chatgpt_response(raw_response)
            f.write(cleaned_response)
            f.write("\n\n=== Marker Check ===\n")
            
            # Check if the markers were removed
            markers = [
                "[Início do Script de Narração]",
                "[Fim do Script de Narração]",
                "{Início do Video]",
                "{Fim do Video]",
                "[Início da Narração]",
                "[Fim da Narração]",
                "[Início]",
                "[Fim]",
                "{Início]",
                "{Fim]",
            ]
            
            for marker in markers:
                if marker.lower() in cleaned_response.lower():
                    f.write(f"WARNING: Marker '{marker}' still present in cleaned response!\n")
                else:
                    f.write(f"Marker '{marker}' successfully removed.\n")
        
        print(f"Test results written to {output_file}")
    
    except FileNotFoundError:
        print(f"File not found: {response_file}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
