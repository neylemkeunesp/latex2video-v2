#!/usr/bin/env python3
import os
import sys
import logging

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.chatgpt_script_generator import clean_chatgpt_response

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Clean all ChatGPT response files in the output directory."""
    responses_dir = "output/chatgpt_responses"
    cleaned_dir = "output/cleaned_responses"
    
    # Create output directory if it doesn't exist
    os.makedirs(cleaned_dir, exist_ok=True)
    
    # Get all response files
    try:
        response_files = [f for f in os.listdir(responses_dir) if f.endswith("_response.txt")]
        if not response_files:
            print(f"No response files found in '{responses_dir}'.")
            return
        
        print(f"Found {len(response_files)} response files.")
        
        for response_file in response_files:
            input_path = os.path.join(responses_dir, response_file)
            output_path = os.path.join(cleaned_dir, response_file)
            
            try:
                with open(input_path, 'r', encoding='utf-8') as f:
                    raw_response = f.read()
                
                cleaned_response = clean_chatgpt_response(raw_response)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_response)
                
                print(f"Cleaned {response_file} and saved to {output_path}")
            except Exception as e:
                print(f"Error processing {response_file}: {e}")
        
        print(f"\nAll responses cleaned and saved to {cleaned_dir}")
        print("You can now use these cleaned responses for generating audio.")
    
    except FileNotFoundError:
        print(f"Directory not found: {responses_dir}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
