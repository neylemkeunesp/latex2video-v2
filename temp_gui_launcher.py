#!/usr/bin/env python3
import os
import sys
import tkinter as tk
from tkinter import ttk

# Add the parent directory to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Import the GUI module
from src.gui_final import LaTeX2VideoGUI

# Create the GUI
root = tk.Tk()
app = LaTeX2VideoGUI(root)
root.mainloop()
