#!/usr/bin/env python3
import os
import sys
import subprocess
import platform

def clear_screen():
    """Clear the terminal screen based on the operating system."""
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def open_file(file_path):
    """Open a file with the default application based on the operating system."""
    if platform.system() == "Windows":
        os.startfile(file_path)
    elif platform.system() == "Darwin":  # macOS
        subprocess.call(["open", file_path])
    else:  # Linux
        subprocess.call(["xdg-open", file_path])

def main():
    """Main function to help the user send slide content to ChatGPT-4o."""
    # Check if the prompts directory exists
    prompts_dir = "output/chatgpt_prompts"
    if not os.path.exists(prompts_dir):
        print(f"Error: Prompts directory '{prompts_dir}' not found.")
        print("Please run the chatgpt_script_generator.py script first.")
        return

    # Get all prompt files
    prompt_files = sorted([f for f in os.listdir(prompts_dir) if f.endswith("_prompt.txt")])
    if not prompt_files:
        print(f"No prompt files found in '{prompts_dir}'.")
        return

    # Create directory for saving responses
    responses_dir = "output/chatgpt_responses"
    os.makedirs(responses_dir, exist_ok=True)

    # Process each prompt file
    for i, prompt_file in enumerate(prompt_files):
        clear_screen()
        
        # Extract slide number
        slide_num = prompt_file.split("_")[1]
        
        # Paths
        prompt_path = os.path.join(prompts_dir, prompt_file)
        response_path = os.path.join(responses_dir, f"slide_{slide_num}_response.txt")
        
        # Display instructions
        print(f"\n=== Slide {slide_num} of {len(prompt_files)} ===\n")
        print(f"1. Opening prompt file: {prompt_file}")
        print("2. Copy the entire content of the file")
        print("3. Paste it into ChatGPT-4o")
        print("4. Copy the response from ChatGPT-4o")
        print(f"5. Save it to: {response_path}")
        print("\nPress Enter to open the prompt file...")
        input()
        
        # Open the prompt file
        open_file(prompt_path)
        
        # Wait for user to copy and paste to ChatGPT
        print("\nAfter sending to ChatGPT-4o and receiving a response:")
        print("1. Copy the entire response")
        print("2. Press Enter to create a file for the response...")
        input()
        
        # Create a file for the response
        try:
            with open(response_path, 'w') as f:
                pass  # Create an empty file
            
            # Open the response file for editing
            open_file(response_path)
            
            print("\nPaste the response into the opened file and save it.")
            print("Press Enter when you've saved the response...")
            input()
            
            print(f"\nResponse saved to: {response_path}")
            
        except Exception as e:
            print(f"Error creating response file: {e}")
        
        # Ask to continue to the next slide
        if i < len(prompt_files) - 1:
            print("\nPress Enter to continue to the next slide, or type 'q' to quit...")
            user_input = input()
            if user_input.lower() == 'q':
                break
    
    clear_screen()
    print("\n=== All slides processed ===\n")
    print(f"Prompt files are in: {prompts_dir}")
    print(f"Response files are in: {responses_dir}")
    print("\nYou can now use these responses as scripts for your video narration.")

if __name__ == "__main__":
    main()
