#!/usr/bin/env python3
"""
Simple Tkinter test script for WSL2 environment.
"""

import os
import sys
import tkinter as tk

# Set environment variables for WSL2
os.environ['DISPLAY'] = ':0'
os.environ['LIBGL_ALWAYS_INDIRECT'] = '1'
os.environ['QT_X11_NO_MITSHM'] = '1'
os.environ['XDG_RUNTIME_DIR'] = '/tmp/runtime-dir'
os.environ['PYTHONUNBUFFERED'] = '1'

def main():
    """Create a simple Tkinter window"""
    try:
        print("Creating Tkinter window...")
        
        # Create a simple window
        root = tk.Tk()
        root.title("Tkinter Test")
        root.geometry("300x200")
        
        # Add a label
        label = tk.Label(root, text="If you can see this, Tkinter is working!")
        label.pack(pady=20)
        
        # Add a button to close the window
        button = tk.Button(root, text="Close", command=root.destroy)
        button.pack(pady=10)
        
        # Start the main loop
        print("Starting Tkinter main loop...")
        root.mainloop()
        print("Tkinter main loop ended.")
        
        return 0
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
