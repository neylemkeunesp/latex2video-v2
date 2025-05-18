#!/usr/bin/env python3
"""
A simple PyQt5 GUI for testing purposes.
"""

import sys
import os

# Configure environment variables to help with X11/XCB issues
os.environ['QT_X11_NO_MITSHM'] = '1'  # For PyQt/PySide
os.environ['XDG_RUNTIME_DIR'] = '/tmp/runtime-dir'
os.environ['PYTHONUNBUFFERED'] = '1'  # Ensure output is not buffered

try:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
    from PyQt5.QtCore import Qt
except ImportError:
    print("PyQt5 is not installed. Please install it with: pip install PyQt5")
    sys.exit(1)

class SimpleWindow(QMainWindow):
    """A simple PyQt5 window for testing purposes"""
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Simple PyQt5 Test")
        self.setGeometry(100, 100, 400, 300)
        
        # Create a central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create a layout
        layout = QVBoxLayout(central_widget)
        
        # Add a label
        label = QLabel("This is a simple PyQt5 GUI for testing purposes.")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # Add a button
        button = QPushButton("Click Me")
        button.clicked.connect(self.on_button_click)
        layout.addWidget(button)
        
        # Add a status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
    
    def on_button_click(self):
        """Handle button click event"""
        self.status_label.setText("Button clicked!")

def main():
    """Main function"""
    try:
        app = QApplication(sys.argv)
        window = SimpleWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    main()
