#!/usr/bin/env python3
import os
import sys
import glob
from src.chatgpt_script_generator import clean_chatgpt_response

def clean_all_responses(responses_dir):
    """Clean all ChatGPT responses in the specified directory."""
    if not os.path.exists(responses_dir):
        print(f"Error: Directory '{responses_dir}' does not exist.")
        return False
    
    # Find all response files
    response_files = glob.glob(os.path.join(responses_dir, "slide_*_response.txt"))
    
    if not response_files:
        print(f"No response files found in '{responses_dir}'.")
        return False
    
    print(f"Found {len(response_files)} response files.")
    
    # Clean each file
    for file_path in sorted(response_files):
        print(f"Processing {os.path.basename(file_path)}...")
        
        try:
            # Read the original content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Clean the content
            cleaned_content = clean_chatgpt_response(original_content)
            
            # Create a backup of the original file
            backup_path = file_path + '.bak'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write the cleaned content back to the original file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            print(f"  ✓ Successfully cleaned and saved backup to {os.path.basename(backup_path)}")
        
        except Exception as e:
            print(f"  ✗ Error processing {os.path.basename(file_path)}: {e}")
    
    print("\nAll files processed. Original files were backed up with '.bak' extension.")
    return True

def main():
    """Main function to clean all ChatGPT responses."""
    responses_dir = "output/chatgpt_responses"
    
    if len(sys.argv) > 1:
        responses_dir = sys.argv[1]
    
    success = clean_all_responses(responses_dir)
    
    if success:
        print("\nSuccess! All ChatGPT responses have been cleaned of LaTeX control characters.")
        print("You can now proceed with generating the narration audio.")
    else:
        print("\nFailed to clean ChatGPT responses. Please check the error messages above.")

if __name__ == "__main__":
    main()
