#!/usr/bin/env python3
"""
A very simple Tkinter GUI for testing purposes.
This script creates a minimal GUI without any threading.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Configure environment variables to help with X11/XCB issues
os.environ['QT_X11_NO_MITSHM'] = '1'  # For PyQt/PySide
os.environ['XDG_RUNTIME_DIR'] = '/tmp/runtime-dir'
os.environ['PYTHONUNBUFFERED'] = '1'  # Ensure output is not buffered

class SimpleGUI:
    """A very simple GUI for testing purposes"""
    def __init__(self, root):
        self.root = root
        self.root.title("Simple GUI Test")
        self.root.geometry("400x300")
        
        # Create a frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add a label
        ttk.Label(main_frame, text="This is a simple GUI for testing purposes.").pack(pady=10)
        
        # Add a button
        ttk.Button(main_frame, text="Click Me", command=self.on_button_click).pack(pady=10)
        
        # Add a text entry
        self.entry_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.entry_var).pack(pady=10)
        
        # Add a status label
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.status_var).pack(pady=10)
    
    def on_button_click(self):
        """Handle button click event"""
        text = self.entry_var.get()
        if text:
            messagebox.showinfo("Info", f"You entered: {text}")
            self.status_var.set(f"Last input: {text}")
        else:
            messagebox.showwarning("Warning", "Please enter some text.")
            self.status_var.set("No input provided")

def main():
    """Main function"""
    try:
        # Create the GUI
        root = tk.Tk()
        app = SimpleGUI(root)
        root.mainloop()
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
