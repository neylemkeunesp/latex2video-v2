#!/usr/bin/env python3
"""
Simple GTK test script to check if GTK works with the current display.
"""

import os
import sys
import gi

# Set environment variables
os.environ['DISPLAY'] = ':0'
os.environ['PYTHONUNBUFFERED'] = '1'

try:
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except Exception as e:
    print(f"ERROR: Failed to import GTK: {e}")
    sys.exit(1)

class TestWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="GTK Test")
        self.set_default_size(300, 200)
        
        # Create a vertical box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)
        self.add(vbox)
        
        # Add a label
        label = Gtk.Label(label="If you can see this, GTK is working!")
        vbox.pack_start(label, True, True, 0)
        
        # Add a button to close the window
        button = Gtk.Button(label="Close")
        button.connect("clicked", self.on_close_clicked)
        vbox.pack_start(button, False, False, 0)
    
    def on_close_clicked(self, widget):
        Gtk.main_quit()

def main():
    """Create a simple GTK window"""
    try:
        print("Creating GTK window...")
        
        # Create the window
        win = TestWindow()
        win.connect("destroy", Gtk.main_quit)
        win.show_all()
        
        # Start the main loop
        print("Starting GTK main loop...")
        Gtk.main()
        print("GTK main loop ended.")
        
        return 0
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
