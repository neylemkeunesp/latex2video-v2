#!/usr/bin/env python3
"""
Helper script to run the PyQt5 version of the LaTeX2Video GUI.
This script sets up the necessary environment variables and handles any potential errors.
"""

import os
import sys
import traceback

# Configure environment variables to help with X11/XCB issues
os.environ['QT_X11_NO_MITSHM'] = '1'  # For PyQt/PySide
os.environ['XDG_RUNTIME_DIR'] = '/tmp/runtime-dir'
os.environ['PYTHONUNBUFFERED'] = '1'  # Ensure output is not buffered

def check_display():
    """Check if a display server is available"""
    return os.environ.get('DISPLAY') is not None

def main():
    """Main function to run the PyQt GUI"""
    # Check if display is available
    if not check_display():
        print("ERROR: No display server available (DISPLAY environment variable not set).")
        print("You need a display server to run the GUI version.")
        print("\nOptions:")
        print("1. If you're using SSH, enable X11 forwarding with 'ssh -X' or 'ssh -Y'")
        print("2. If you're on a headless server, set up a VNC server")
        print("3. Use the command-line interface instead (recommended)")
        return 1
    
    try:
        print("Attempting to run PyQt5 LaTeX2Video GUI...")
        
        # Add the parent directory to the path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(script_dir)
        
        # Import and run the PyQt GUI
        from pyqt_latex2video import main as pyqt_main
        pyqt_main()
        
        return 0
        
    except ImportError as e:
        print(f"ERROR: Failed to import PyQt5 modules: {e}")
        print("Make sure you have installed all required packages:")
        print("  pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
