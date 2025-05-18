#!/usr/bin/env python3
import os
import sys
import glob
import re

def replace_y_with_ipsilon(text):
    """Replace standalone 'y' with 'ipsilon' in the text."""
    # Replace standalone 'y' (surrounded by spaces, punctuation, or at beginning/end)
    # but not when it's part of a word
    text = re.sub(r'(?<!\w)y(?!\w)', 'ipsilon', text)
    
    # Special cases for common mathematical expressions
    text = re.sub(r'f\(x, y\)', 'f(x, ipsilon)', text)
    text = re.sub(r'g\(x, y\)', 'g(x, ipsilon)', text)
    text = re.sub(r'L\(x, y', 'L(x, ipsilon', text)  # Handle L(x, y, λ) case
    
    # Additional cases for mathematical expressions
    text = re.sub(r'xy', 'x·ipsilon', text)  # Replace xy with x·ipsilon
    text = re.sub(r'2y', '2·ipsilon', text)  # Replace 2y with 2·ipsilon
    
    return text

def process_all_responses(responses_dir):
    """Process all response files to replace 'y' with 'ipsilon'."""
    if not os.path.exists(responses_dir):
        print(f"Error: Directory '{responses_dir}' does not exist.")
        return False
    
    # Find all response files
    response_files = glob.glob(os.path.join(responses_dir, "slide_*_response.txt"))
    
    if not response_files:
        print(f"No response files found in '{responses_dir}'.")
        return False
    
    print(f"Found {len(response_files)} response files to process.")
    
    # Process each file
    for file_path in sorted(response_files):
        print(f"Processing {os.path.basename(file_path)}...")
        
        try:
            # Read the original content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Replace 'y' with 'ipsilon'
            processed_content = replace_y_with_ipsilon(original_content)
            
            # Count replacements
            original_y_count = len(re.findall(r'(?<!\w)y(?!\w)', original_content))
            processed_y_count = len(re.findall(r'(?<!\w)y(?!\w)', processed_content))
            replacements_made = original_y_count - processed_y_count
            
            # Create a backup of the original file
            backup_path = file_path + '.y_backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write the processed content back to the original file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            
            print(f"  ✓ Made {replacements_made} replacements and saved backup to {os.path.basename(backup_path)}")
        
        except Exception as e:
            print(f"  ✗ Error processing {os.path.basename(file_path)}: {e}")
    
    print("\nAll files processed. Original files were backed up with '.y_backup' extension.")
    return True

def main():
    """Main function to replace 'y' with 'ipsilon' in all response files."""
    responses_dir = "output/chatgpt_responses"
    
    if len(sys.argv) > 1:
        responses_dir = sys.argv[1]
    
    success = process_all_responses(responses_dir)
    
    if success:
        print("\nSuccess! All occurrences of 'y' have been replaced with 'ipsilon'.")
        print("You can now proceed with generating the narration audio.")
    else:
        print("\nFailed to process response files. Please check the error messages above.")

if __name__ == "__main__":
    main()
