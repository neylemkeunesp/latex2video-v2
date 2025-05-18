#!/usr/bin/env python3
import os
import sys
import logging
from src.chatgpt_script_generator import generate_chatgpt_prompts, save_prompts_to_files

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Test regenerating prompts for a PDF file."""
    # Get the PDF path from command line argument or use default
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "output/temp_pdf/gasessolidos.pdf"
    
    # Check if the file exists
    if not os.path.exists(pdf_path):
        logging.error(f"PDF file not found: {pdf_path}")
        return
    
    # Generate prompts
    logging.info(f"Generating prompts for: {pdf_path}")
    prompts = generate_chatgpt_prompts(pdf_path)
    
    if not prompts:
        logging.error("No prompts were generated.")
        return
    
    # Save prompts to files
    output_dir = "output/test_prompts"
    file_paths = save_prompts_to_files(prompts, output_dir)
    
    # Print summary
    logging.info(f"Generated {len(prompts)} prompts and saved them to {output_dir}")
    
    # Check a few prompts to verify content
    for i in range(min(3, len(prompts))):
        prompt = prompts[i]
        logging.info(f"Prompt {i+1} ({prompt['title']}):")
        # Print the first 200 characters of the prompt
        preview = prompt['prompt'][:200] + "..." if len(prompt['prompt']) > 200 else prompt['prompt']
        logging.info(f"Preview: {preview}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    main()
