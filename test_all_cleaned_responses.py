#!/usr/bin/env python3
import os
import sys
import glob
import re

def check_for_latex_control_chars(text):
    """Check if the text contains any LaTeX control characters."""
    # Define patterns to look for
    latex_patterns = [
        r'\\[a-zA-Z]+',  # LaTeX commands like \lambda, \alpha, etc.
        r'\\[\(\)\[\]]',  # Math delimiters \(, \), \[, \]
        r'\\\{', r'\\\}',  # Escaped braces \{, \}
        r'\\[,;]',  # Spacing commands \, \;
        r'\$\$.*?\$\$',  # Display math $$...$$
        r'\$.*?\$',  # Inline math $...$
    ]
    
    # Check each pattern
    for pattern in latex_patterns:
        matches = re.findall(pattern, text)
        if matches:
            return True, matches
    
    return False, []

def test_all_responses(responses_dir):
    """Test all cleaned response files for LaTeX control characters."""
    if not os.path.exists(responses_dir):
        print(f"Error: Directory '{responses_dir}' does not exist.")
        return False
    
    # Find all response files
    response_files = glob.glob(os.path.join(responses_dir, "slide_*_response.txt"))
    
    if not response_files:
        print(f"No response files found in '{responses_dir}'.")
        return False
    
    print(f"Found {len(response_files)} response files to test.")
    
    all_clean = True
    
    # Test each file
    for file_path in sorted(response_files):
        print(f"Testing {os.path.basename(file_path)}...")
        
        try:
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for LaTeX control characters
            has_latex, matches = check_for_latex_control_chars(content)
            
            if has_latex:
                print(f"  ✗ Found LaTeX control characters: {matches[:5]}" + 
                      (f" and {len(matches) - 5} more..." if len(matches) > 5 else ""))
                all_clean = False
            else:
                print(f"  ✓ No LaTeX control characters found")
        
        except Exception as e:
            print(f"  ✗ Error processing {os.path.basename(file_path)}: {e}")
            all_clean = False
    
    return all_clean

def main():
    """Main function to test all cleaned response files."""
    responses_dir = "output/chatgpt_responses"
    
    if len(sys.argv) > 1:
        responses_dir = sys.argv[1]
    
    all_clean = test_all_responses(responses_dir)
    
    if all_clean:
        print("\nSuccess! All response files are clean of LaTeX control characters.")
    else:
        print("\nSome response files still contain LaTeX control characters.")
        print("Please run clean_all_latex.py again to clean them.")

if __name__ == "__main__":
    main()
