#!/usr/bin/env python3
"""
PyQt5 version of the LaTeX2Video GUI.
This version avoids the XCB issues that occur with Tkinter.
"""

import os
import sys
import logging
import re
import yaml
import threading
import queue
import time
import shutil
from typing import List, Dict, Optional
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("[MARKER] pyqt_latex2video.py loaded and running from: " + os.path.abspath(__file__))
print("[PRINT-MARKER] pyqt_latex2video.py loaded and running from:", os.path.abspath(__file__))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLineEdit, QTextEdit, QFileDialog, QMessageBox, QSplitter, QGridLayout,
    QFrame, QStatusBar, QAction, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QSettings, QTimer
from PyQt5.QtGui import QIcon, QPixmap

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.latex_parser import parse_latex_file, Slide
from src.chatgpt_script_generator import format_slide_for_chatgpt, clean_chatgpt_response
from src.openai_script_generator import initialize_openai_client, generate_script_with_openai
from src.image_generator import generate_slide_images
from src.audio_generator import generate_all_audio
from src.simple_video_assembler import assemble_video, natural_sort # Import natural_sort

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'latex2video_gui.log'))
    ]
)

class Worker(QObject):
    """Worker thread for background tasks"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)
    progress = pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        print("[PRINT-DEBUG] Worker.__init__ called")
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """Run the worker function"""
        logging.info("[PYQT_DEBUG] Worker.run: Method entered. Starting task execution.") # Changed to logging.info
        try:
            logging.info(f"[PYQT_DEBUG] Worker.run: About to call self.fn: {self.fn.__name__ if hasattr(self.fn, '__name__') else 'unknown_fn'}") # Changed
            result = self.fn(*self.args, **self.kwargs)
            logging.info(f"[PYQT_DEBUG] Worker.run: self.fn call completed. Result: {type(result)}") # Changed
            self.result.emit(result)
            logging.info(f"[PYQT_DEBUG] Worker.run: self.result signal emitted.") # Changed
        except Exception as e:
            logging.error(f"[PYQT_DEBUG] Worker.run: Exception caught: {e}", exc_info=True) # Changed to logging.error and added exc_info
            self.error.emit(str(e))
            logging.info(f"[PYQT_DEBUG] Worker.run: self.error signal emitted.") # Changed
            # logging.error already called above, this is redundant if we keep the one above.
        finally:
            logging.info("[PYQT_DEBUG] Worker.run: Emitting finished signal.") # Changed
            self.finished.emit()
            logging.info("[PYQT_DEBUG] Worker.run: self.finished signal emitted. Exiting run method.") # Changed

class RedirectText(QObject): # Inherit from QObject
    """Class to redirect stdout/stderr to a QTextEdit widget safely from threads"""
    textWritten = pyqtSignal(str) # Signal to emit text

    def __init__(self, text_widget_append_slot):
        super().__init__()
        # self.text_widget = text_widget # No longer needed directly
        self.textWritten.connect(text_widget_append_slot) # Connect to the slot in the main GUI

    def write(self, string):
        self.textWritten.emit(string) # Emit the signal

    def flush(self):
        pass # sys.stdout.flush() will be handled by the original stdout

# Define stylesheets for light and dark modes
LIGHT_STYLE = """
QMainWindow, QWidget {
    background-color: #f0f0f0;
    color: #202020;
}
QTextEdit, QLineEdit {
    background-color: #ffffff;
    color: #202020;
    border: 1px solid #c0c0c0;
}
QPushButton {
    background-color: #e0e0e0;
    color: #202020;
    border: 1px solid #c0c0c0;
    padding: 5px;
}
QPushButton:hover {
    background-color: #d0d0d0;
}
QTabWidget::pane {
    border: 1px solid #c0c0c0;
    background-color: #f0f0f0;
}
QTabBar::tab {
    background-color: #e0e0e0;
    color: #202020;
    padding: 5px 10px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #f0f0f0;
    border-bottom: 2px solid #505050;
}
QSplitter::handle {
    background-color: #c0c0c0;
}
QStatusBar {
    background-color: #e0e0e0;
    color: #202020;
}
"""

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #2d2d2d;
    color: #e0e0e0;
}
QTextEdit, QLineEdit {
    background-color: #3d3d3d;
    color: #e0e0e0;
    border: 1px solid #505050;
}
QPushButton {
    background-color: #3d3d3d;
    color: #e0e0e0;
    border: 1px solid #505050;
    padding: 5px;
}
QPushButton:hover {
    background-color: #4d4d4d;
}
QTabWidget::pane {
    border: 1px solid #505050;
    background-color: #2d2d2d;
}
QTabBar::tab {
    background-color: #3d3d3d;
    color: #e0e0e0;
    padding: 5px 10px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #2d2d2d;
    border-bottom: 2px solid #a0a0a0;
}
QSplitter::handle {
    background-color: #505050;
}
QStatusBar {
    background-color: #3d3d3d;
    color: #e0e0e0;
}
"""

class LaTeX2VideoGUI(QMainWindow):
    """Main GUI application for LaTeX2Video using PyQt5"""
    def __init__(self):
        super().__init__()
        
        # Initialize variables
        self.latex_file_path = ""
        self.config_file_path = ""
        self.output_dir = ""
        self.current_slide_index = 0
        self.slides = []
        self.narrations = []
        self.prompts = []
        self.config = {}
        self.threads = []
        self.dark_mode = False
        
        # Set default paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file_path = os.path.join(script_dir, "config", "config.yaml")
        self.output_dir = os.path.join(script_dir, "output")
        
        # Load settings
        self.settings = QSettings("LaTeX2Video", "PyQt5GUI")
        self.dark_mode = self.settings.value("dark_mode", False, type=bool)
        
        # Set up the UI
        self.init_ui() # self.log_text is created here
        
        # Redirect stdout and stderr AFTER self.log_text is created
        # Pass the method that will append text to the log widget
        self.stdout_redirect = RedirectText(self.appendTextToLog)
        self.stderr_redirect = RedirectText(self.appendTextToLog) # Can use the same slot
        sys.stdout = self.stdout_redirect
        sys.stderr = self.stderr_redirect

        # Apply the appropriate theme
        self.apply_theme()
        
        # Load config if exists
        self.load_config()
        
        # Initialize status
        self.update_status("Ready")

        # Pre-initialize GTTSProvider in main thread if gtts is the provider
        if self.config.get('tts', {}).get('provider', '').lower() == 'gtts':
            try:
                print("[PYQT_DEBUG] __init__: Attempting to pre-initialize GTTSProvider in main thread...")
                from src.tts_provider import GTTSProvider as MainThreadGTTSProvider 
                lang = self.config.get('tts', {}).get('language', 'pt')
                slow_mode = self.config.get('tts', {}).get('slow', False)
                _ = MainThreadGTTSProvider(language=lang, slow=slow_mode) 
                print(f"[PYQT_DEBUG] __init__: GTTSProvider pre-initialized successfully in main thread with lang='{lang}'.")
            except Exception as e_main_gtts_init:
                print(f"[PYQT_DEBUG] __init__: Failed to pre-initialize GTTSProvider in main thread: {e_main_gtts_init}")
                logging.error(f"Failed to pre-initialize GTTSProvider in main thread: {e_main_gtts_init}", exc_info=True)

    def appendTextToLog(self, text):
        """Slot to append text to the log_text QTextEdit widget."""
        self.log_text.append(text)
        self.log_text.ensureCursorVisible()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("LaTeX2Video (PyQt5)")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        menubar = self.menuBar()
        view_menu = menubar.addMenu("View")
        
        self.dark_mode_action = QAction("Dark Mode", self, checkable=True)
        self.dark_mode_action.setChecked(self.dark_mode)
        self.dark_mode_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(self.dark_mode_action)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        top_frame = QFrame()
        top_layout = QGridLayout(top_frame)
        
        top_layout.addWidget(QLabel("LaTeX File:"), 0, 0)
        self.latex_file_edit = QLineEdit()
        top_layout.addWidget(self.latex_file_edit, 0, 1)
        latex_browse_button = QPushButton("Browse...")
        latex_browse_button.clicked.connect(self.browse_latex_file)
        top_layout.addWidget(latex_browse_button, 0, 2)
        
        top_layout.addWidget(QLabel("Config File:"), 1, 0)
        self.config_file_edit = QLineEdit()
        self.config_file_edit.setText(self.config_file_path)
        top_layout.addWidget(self.config_file_edit, 1, 1)
        config_browse_button = QPushButton("Browse...")
        config_browse_button.clicked.connect(self.browse_config_file)
        top_layout.addWidget(config_browse_button, 1, 2)
        
        top_layout.addWidget(QLabel("Output Directory:"), 2, 0)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText(self.output_dir)
        top_layout.addWidget(self.output_dir_edit, 2, 1)
        output_browse_button = QPushButton("Browse...")
        output_browse_button.clicked.connect(self.browse_output_dir)
        top_layout.addWidget(output_browse_button, 2, 2)
        
        top_layout.setColumnStretch(1, 1)
        main_layout.addWidget(top_frame)
        
        self.tab_widget = QTabWidget()
        
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        
        editor_controls = QWidget()
        editor_controls_layout = QHBoxLayout(editor_controls)
        editor_controls_layout.setContentsMargins(0, 0, 0, 0)
        
        parse_button = QPushButton("Parse LaTeX")
        parse_button.clicked.connect(self.parse_latex)
        editor_controls_layout.addWidget(parse_button)
        
        generate_scripts_button = QPushButton("Generate Scripts")
        generate_scripts_button.clicked.connect(self.generate_scripts)
        editor_controls_layout.addWidget(generate_scripts_button)
        
        save_scripts_button = QPushButton("Save Scripts")
        save_scripts_button.clicked.connect(self.save_scripts)
        editor_controls_layout.addWidget(save_scripts_button)
        
        load_scripts_button = QPushButton("Load Scripts")
        load_scripts_button.clicked.connect(self.load_scripts)
        editor_controls_layout.addWidget(load_scripts_button)
        
        editor_controls_layout.addStretch()
        
        prev_button = QPushButton("< Prev")
        prev_button.clicked.connect(self.prev_slide)
        editor_controls_layout.addWidget(prev_button)
        
        self.slide_label = QLabel("Slide: 0/0")
        editor_controls_layout.addWidget(self.slide_label)
        
        next_button = QPushButton("Next >")
        next_button.clicked.connect(self.next_slide)
        editor_controls_layout.addWidget(next_button)
        
        editor_layout.addWidget(editor_controls)
        
        editor_splitter = QSplitter(Qt.Vertical)
        top_splitter = QSplitter(Qt.Horizontal)
        
        image_widget = QWidget()
        image_layout = QVBoxLayout(image_widget)
        image_layout.addWidget(QLabel("Slide Image:"))
        self.image_scroll_area = QScrollArea()
        self.image_scroll_area.setWidgetResizable(True)
        self.image_scroll_area.setMinimumHeight(300)
        self.slide_image_label = QLabel()
        self.slide_image_label.setAlignment(Qt.AlignCenter)
        self.slide_image_label.setMinimumSize(400, 300)
        self.slide_image_label.setStyleSheet("background-color: #ffffff;")
        self.slide_image_label.setText("No image available")
        self.image_scroll_area.setWidget(self.slide_image_label)
        image_layout.addWidget(self.image_scroll_area)
        top_splitter.addWidget(image_widget)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.addWidget(QLabel("ChatGPT Response:"))
        self.slide_content_text = QTextEdit()
        self.slide_content_text.setReadOnly(True)
        content_layout.addWidget(self.slide_content_text)
        top_splitter.addWidget(content_widget)
        editor_splitter.addWidget(top_splitter)
        
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.addWidget(QLabel("ChatGPT Prompt:"))
        self.narration_text = QTextEdit()
        bottom_layout.addWidget(self.narration_text)
        editor_splitter.addWidget(bottom_widget)
        editor_layout.addWidget(editor_splitter)
        self.tab_widget.addTab(editor_widget, "ChatGPT Editor")
        
        generation_widget = QWidget()
        generation_layout = QVBoxLayout(generation_widget)
        gen_controls = QWidget()
        gen_controls_layout = QHBoxLayout(gen_controls)
        gen_controls_layout.setContentsMargins(0, 0, 0, 0)
        
        gen_images_button = QPushButton("Generate Images")
        gen_images_button.clicked.connect(self.generate_images)
        gen_controls_layout.addWidget(gen_images_button)

        load_images_button = QPushButton("Load Existing Images")
        load_images_button.clicked.connect(self.load_existing_images_qt)
        gen_controls_layout.addWidget(load_images_button)
        
        gen_audio_button = QPushButton("Generate Audio")
        gen_audio_button.clicked.connect(self.generate_audio)
        gen_controls_layout.addWidget(gen_audio_button)

        load_audio_button = QPushButton("Load Existing Audio")
        load_audio_button.clicked.connect(self.load_existing_audio_qt)
        gen_controls_layout.addWidget(load_audio_button)
        
        assemble_button = QPushButton("Assemble Video")
        assemble_button.clicked.connect(self.assemble_video)
        gen_controls_layout.addWidget(assemble_button)
        
        gen_all_button = QPushButton("Generate All")
        gen_all_button.clicked.connect(self.generate_all)
        gen_controls_layout.addWidget(gen_all_button)
        
        gen_controls_layout.addStretch()
        generation_layout.addWidget(gen_controls)
        
        generation_layout.addWidget(QLabel("Log Output:"))
        self.log_text = QTextEdit() # self.log_text is created here
        self.log_text.setReadOnly(True)
        generation_layout.addWidget(self.log_text)
        self.tab_widget.addTab(generation_widget, "Video Generation")
        main_layout.addWidget(self.tab_widget)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.show()

    def apply_theme(self):
        if self.dark_mode:
            self.setStyleSheet(DARK_STYLE)
        else:
            self.setStyleSheet(LIGHT_STYLE)
        self.settings.setValue("dark_mode", self.dark_mode)
    
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        mode_name = "dark" if self.dark_mode else "light"
        self.update_status(f"Switched to {mode_name} mode")

    def update_status(self, message):
        self.status_bar.showMessage(message)
        logging.info(message)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'current_image_path') and self.current_image_path:
            try:
                pixmap = QPixmap(self.current_image_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(
                        self.slide_image_label.width(), 
                        self.slide_image_label.height(),
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    )
                    self.slide_image_label.setPixmap(pixmap)
            except Exception as e:
                logging.error(f"Error resizing image: {e}")
    
    def closeEvent(self, event):
        # Restore stdout and stderr before closing
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        event.accept()

    def browse_latex_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select LaTeX File", "", "LaTeX Files (*.tex);;All Files (*.*)")
        if file_path:
            for outdir in ["output", "output-lagrange", "output-test"]:
                abs_outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), outdir)
                if os.path.exists(abs_outdir):
                    shutil.rmtree(abs_outdir)
                os.makedirs(abs_outdir, exist_ok=True)
            self.latex_file_path = file_path
            self.latex_file_edit.setText(file_path)
            self.update_status(f"LaTeX file selected: {file_path}")
            self.parse_latex()
            self.generate_images()

    def browse_config_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Config File", "", "YAML Files (*.yaml);;All Files (*.*)")
        if file_path:
            self.config_file_path = file_path
            self.config_file_edit.setText(file_path)
            self.load_config()
            self.update_status(f"Config file selected: {file_path}")

    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory", "")
        if dir_path:
            self.output_dir = dir_path
            self.output_dir_edit.setText(dir_path)
            self.config['output_dir'] = dir_path
            os.makedirs(dir_path, exist_ok=True)
            for sub_dir in ['slides', 'audio', 'temp_pdf', 'chatgpt_prompts', 'chatgpt_responses']:
                os.makedirs(os.path.join(dir_path, sub_dir), exist_ok=True)
            self.update_status(f"Output directory selected: {dir_path}")

    def load_config(self):
        config_path = self.config_file_path
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
                logging.info(f"Configuration loaded from {config_path}")
                self.config['output_dir'] = self.output_dir
                os.makedirs(self.output_dir, exist_ok=True)
                for sub_dir in ['slides', 'audio', 'temp_pdf', 'chatgpt_prompts', 'chatgpt_responses']:
                    os.makedirs(os.path.join(self.output_dir, sub_dir), exist_ok=True)
                return True
            except Exception as e:
                logging.error(f"Error loading config: {e}")
                QMessageBox.critical(self, "Error", f"Failed to load configuration: {e}")
                return False
        else:
            logging.warning(f"Config file not found: {config_path}")
            return False

    def parse_latex(self):
        latex_file = self.latex_file_path
        if not latex_file or not os.path.exists(latex_file):
            QMessageBox.critical(self, "Error", "Please select a LaTeX file first." if not latex_file else f"LaTeX file not found: {latex_file}")
            return
        self.update_status("Parsing LaTeX file...")
        try:
            self.slides = parse_latex_file(latex_file)
            if not self.slides:
                QMessageBox.critical(self, "Error", "Failed to parse slides from LaTeX file.")
                self.update_status("Failed to parse LaTeX file.")
                return
            
            # Initialize narrations
            self.narrations = [""] * len(self.slides)
            
            # Generate prompts immediately after parsing
            temp_prompts = []
            if self.slides: # Ensure slides were actually parsed
                logging.info(f"Generating prompts for {len(self.slides)} slides immediately after parsing.")
                for i, slide_obj in enumerate(self.slides):
                    prompt_content = format_slide_for_chatgpt(slide_obj, self.slides, i)
                    temp_prompts.append(prompt_content)
                self.prompts = temp_prompts
                logging.info(f"Successfully generated {len(self.prompts)} prompts and stored them.")
                
                # Optionally, save these initial prompts to files
                prompts_dir = os.path.join(self.output_dir, 'chatgpt_prompts')
                os.makedirs(prompts_dir, exist_ok=True)
                for i, prompt_text in enumerate(self.prompts):
                    try:
                        with open(os.path.join(prompts_dir, f"slide_{i+1}_prompt.txt"), 'w', encoding='utf-8') as f:
                            f.write(prompt_text)
                    except Exception as e_save:
                        logging.error(f"Error saving initial prompt for slide {i+1}: {e_save}")
                logging.info(f"Initial prompts saved to {prompts_dir}")
            else:
                self.prompts = [] # Ensure prompts is empty if no slides

            self.current_slide_index = 0
            self.update_slide_display() # This will now show the generated prompts
            self.update_status(f"Successfully parsed {len(self.slides)} slides and generated initial prompts.")
            QMessageBox.information(self, "Success", f"Successfully parsed {len(self.slides)} slides.")
            try:
                base_name = os.path.splitext(os.path.basename(self.latex_file_path))[0]
                src_pdf = os.path.join(os.path.dirname(self.latex_file_path), f"{base_name}.pdf")
                dest_dir = os.path.join(self.output_dir, "temp_pdf")
                dest_pdf = os.path.join(dest_dir, f"{base_name}.pdf")
                if os.path.exists(src_pdf):
                    os.makedirs(dest_dir, exist_ok=True)
                    shutil.copy2(src_pdf, dest_pdf)
                    logging.info(f"[PARSE_LATEX] Copied PDF from {src_pdf} to {dest_pdf}")
                else:
                    logging.warning(f"[PARSE_LATEX] PDF not found to copy: {src_pdf}")
            except Exception as e:
                logging.error(f"[PARSE_LATEX] Error copying PDF after parse: {e}")
        except Exception as e:
            logging.error(f"Error parsing LaTeX file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to parse LaTeX file: {e}")

    def _generate_scripts_worker(self, client):
        try:
            logging.info(f"Starting script generation for {len(self.slides)} slides.")
            narrations = []
            prompts = []
            for i, slide in enumerate(self.slides):
                formatted_content = format_slide_for_chatgpt(slide, self.slides, i)
                prompts.append(formatted_content)
                logging.info(f"Generating script for slide {i+1}/{len(self.slides)}")
                script = generate_script_with_openai(client, formatted_content, self.config)
                if script:
                    cleaned_script = clean_chatgpt_response(script)
                    narrations.append(cleaned_script)
                else:
                    narrations.append(f"Script for slide {i+1} could not be generated.")
                prompts_dir = os.path.join(self.output_dir, 'chatgpt_prompts')
                os.makedirs(prompts_dir, exist_ok=True)
                with open(os.path.join(prompts_dir, f"slide_{i+1}_prompt.txt"), 'w', encoding='utf-8') as f:
                    f.write(formatted_content)
            return {"narrations": narrations, "prompts": prompts}
        except Exception as e:
            logging.error(f"Error in _generate_scripts_worker: {e}", exc_info=True)
            raise
    
    def _on_scripts_generated(self, result):
        narrations = result.get("narrations", [])
        prompts = result.get("prompts", [])
        if not narrations:
            QMessageBox.critical(self, "Error", "Failed to generate narration scripts.")
            self.update_status("Failed to generate narration scripts.")
            return
        self.narrations = narrations
        self.prompts = prompts
        self.update_slide_display()
        self.update_status(f"Generated {len(narrations)} narration scripts.")
        QMessageBox.information(self, "Success", f"Generated {len(narrations)} narration scripts.")

    def _on_error(self, error_msg):
        QMessageBox.critical(self, 'Error', f'An error occurred: {error_msg}')
        self.update_status(f'Error: {error_msg}')

    def save_scripts(self):
        if not self.slides or not self.narrations:
            QMessageBox.critical(self, "Error", "No narration scripts to save.")
            return
        output_dir_path = os.path.join(self.output_dir, 'chatgpt_responses')
        os.makedirs(output_dir_path, exist_ok=True)
        try:
            for i, narration in enumerate(self.narrations):
                with open(os.path.join(output_dir_path, f"slide_{i+1}_response.txt"), 'w', encoding='utf-8') as f:
                    f.write(narration)
            self.update_status("Narration scripts saved.")
            QMessageBox.information(self, "Success", f"Narration scripts saved to {output_dir_path}")
        except Exception as e:
            logging.error(f"Error saving scripts: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save scripts: {e}")

    def load_scripts(self):
        import traceback
        from PyQt5.QtCore import QThread, QTimer, QCoreApplication
        try:
            responses_dir = os.path.join(self.output_dir, 'chatgpt_responses')
            prompts_dir = os.path.join(self.output_dir, 'chatgpt_prompts')
            if not os.path.exists(responses_dir):
                QMessageBox.critical(self, "Error", f"Responses directory not found: {responses_dir}")
                return
            if not self.slides:
                files = sorted([f for f in os.listdir(responses_dir) if f.startswith("slide_") and f.endswith("_response.txt")])
                self.narrations = [open(os.path.join(responses_dir, fname), 'r', encoding='utf-8').read().strip() for fname in files]
                self.current_slide_index = 0
                self.update_status(f'Scripts loaded (no LaTeX slides). Total: {len(self.narrations)}')
                QMessageBox.information(self, 'Success', f'Scripts loaded (no LaTeX slides). Total: {len(self.narrations)}')
                QTimer.singleShot(0, self.update_slide_display) if QThread.currentThread() != QCoreApplication.instance().thread() else self.update_slide_display()
                return
            self.narrations = [""] * len(self.slides)
            self.prompts = [""] * len(self.slides)
            for i in range(len(self.slides)):
                resp_path = os.path.join(responses_dir, f'slide_{i+1}_response.txt')
                if os.path.exists(resp_path): self.narrations[i] = open(resp_path, 'r', encoding='utf-8').read().strip()
                if os.path.exists(prompts_dir):
                    prompt_path = os.path.join(prompts_dir, f'slide_{i+1}_prompt.txt')
                    if os.path.exists(prompt_path): self.prompts[i] = open(prompt_path, 'r', encoding='utf-8').read().strip()
            self.current_slide_index = 0
            QTimer.singleShot(0, self.update_slide_display) if QThread.currentThread() != QCoreApplication.instance().thread() else self.update_slide_display()
            self.update_status('Scripts loaded.')
            QMessageBox.information(self, 'Success', 'Scripts and prompts loaded.')
        except Exception as e:
            logging.error(f'Error loading scripts: {e}', exc_info=True)
            QMessageBox.critical(self, 'Error', f'Failed to load scripts: {e}')

    def prev_slide(self):
        if not self.slides: return
        current_prompt_text = self.narration_text.toPlainText().strip()
        if self.current_slide_index < len(self.prompts): self.prompts[self.current_slide_index] = current_prompt_text
        if self.current_slide_index > 0:
            self.current_slide_index -= 1
            self.update_slide_display()

    def next_slide(self):
        if not self.slides: return
        current_prompt_text = self.narration_text.toPlainText().strip()
        if self.current_slide_index < len(self.prompts): self.prompts[self.current_slide_index] = current_prompt_text
        if self.current_slide_index < len(self.slides) - 1:
            self.current_slide_index += 1
            self.update_slide_display()

    def update_slide_display(self):
        if not self.slides or self.current_slide_index >= len(self.slides): return
        slide = self.slides[self.current_slide_index]
        narration = self.narrations[self.current_slide_index] if self.current_slide_index < len(self.narrations) else ""
        prompt = self.prompts[self.current_slide_index] if self.current_slide_index < len(self.prompts) else ""
        if not prompt:
            prompt_path = os.path.join(self.output_dir, 'chatgpt_prompts', f'slide_{self.current_slide_index + 1}_prompt.txt')
            if os.path.exists(prompt_path):
                try:
                    with open(prompt_path, 'r', encoding='utf-8') as f: prompt = f.read().strip()
                    if len(self.prompts) <= self.current_slide_index: self.prompts.extend([''] * (self.current_slide_index + 1 - len(self.prompts)))
                    self.prompts[self.current_slide_index] = prompt
                except Exception as e: logging.error(f'Error loading prompt: {e}')
        self.slide_content_text.clear()
        self.slide_content_text.append(narration)
        self.narration_text.clear()
        self.narration_text.append(prompt)
        self.slide_label.setText(f'Slide: {self.current_slide_index + 1}/{len(self.slides)}')
        self.load_slide_image()

    def load_slide_image(self):
        logging.info(f"[PYQT_DEBUG] load_slide_image: Attempting to load image for slide index {self.current_slide_index}")
        self.slide_image_label.clear()
        self.slide_image_label.setText('No image available')
        self.current_image_path = None 

        slides_dir = os.path.join(self.output_dir, 'slides')
        if not os.path.exists(slides_dir):
            logging.warning(f"[PYQT_DEBUG] load_slide_image: Slides directory not found: {slides_dir}")
            return

        slide_number = self.current_slide_index + 1
        image_loaded = False

        for ext in ['png', 'jpg', 'jpeg']:
            for image_name_format in [f'slide_{slide_number:03d}.{ext}', f'slide_{slide_number}.{ext}']:
                image_path = os.path.join(slides_dir, image_name_format)
                logging.info(f"[PYQT_DEBUG] load_slide_image: Checking for image: {image_path}")
                if os.path.exists(image_path):
                    try:
                        logging.info(f"[PYQT_DEBUG] load_slide_image: Found image {image_path}. Attempting to load QPixmap.")
                        pixmap = QPixmap(image_path)
                        if pixmap.isNull():
                            logging.error(f"[PYQT_DEBUG] load_slide_image: QPixmap isNull for {image_path}.")
                            continue

                        self.current_image_path = image_path
                        label_width = self.slide_image_label.width()
                        label_height = self.slide_image_label.height()
                        logging.info(f"[PYQT_DEBUG] load_slide_image: Label size: {label_width}x{label_height}")

                        if label_width > 0 and label_height > 0:
                            pixmap = pixmap.scaled(label_width, label_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            logging.info(f"[PYQT_DEBUG] load_slide_image: Pixmap scaled for {image_path}.")
                        else:
                            logging.warning(f"[PYQT_DEBUG] load_slide_image: Label has zero size. Using original pixmap size for {image_path}.")
                        
                        self.slide_image_label.setPixmap(pixmap)
                        self.slide_image_label.setText('') 
                        self.update_status(f'Loaded slide image: {image_path}')
                        logging.info(f"[PYQT_DEBUG] load_slide_image: Successfully set pixmap for {image_path}.")
                        image_loaded = True
                        return 
                    except Exception as e:
                        logging.error(f"[PYQT_DEBUG] load_slide_image: Exception loading/setting pixmap for {image_path}: {e}", exc_info=True)
                        self.slide_image_label.setText('Error loading image')
            if image_loaded: break
        
        if not image_loaded:
            logging.warning(f"[PYQT_DEBUG] load_slide_image: No image found for slide {slide_number} in {slides_dir}")

    def generate_scripts(self):
        if not self.slides: QMessageBox.critical(self, "Error", "No slides available. Please parse a LaTeX file first."); return
        if not self.load_config(): QMessageBox.critical(self, "Error", "Failed to load configuration."); return
        try: client = initialize_openai_client(self.config)
        except Exception as e: QMessageBox.critical(self, "Error", f"Failed to initialize OpenAI client: {e}"); return
        if not client: QMessageBox.critical(self, "Error", "Failed to initialize OpenAI client. Check API key."); return
        self.update_status("Generating narration scripts with OpenAI API...")
        thread = QThread(); worker = Worker(self._generate_scripts_worker, client); worker.moveToThread(thread)
        self._current_scripts_thread = thread; self._current_scripts_worker = worker
        thread.started.connect(worker.run); worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater); thread.finished.connect(thread.deleteLater)
        worker.result.connect(self._on_scripts_generated); worker.error.connect(self._on_error)
        worker.progress.connect(self.update_status); thread.start(); self.threads.append(thread)

    def generate_images(self):
        if not self.load_config(): return
        latex_file = self.latex_file_path
        if not latex_file or not os.path.exists(latex_file): QMessageBox.critical(self, 'Error', 'Please select a valid LaTeX file first.'); return
        self.update_status('Generating slide images...')
        thread = QThread(); worker = Worker(self._generate_images_worker, latex_file); worker.moveToThread(thread)
        self._current_image_thread = thread; self._current_image_worker = worker
        thread.started.connect(worker.run); worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater); thread.finished.connect(thread.deleteLater)
        worker.result.connect(self._on_images_generated); worker.error.connect(self._on_error)
        thread.start(); self.threads.append(thread)

    def _generate_images_worker(self, latex_file):
        config_copy = self.config.copy()
        config_copy['latex_file_path'] = os.path.abspath(latex_file)
        # Pass self.slides as the second argument
        return generate_slide_images(latex_file, self.slides, config_copy)

    def _on_images_generated(self, image_paths):
        logging.info(f"[PYQT_DEBUG] _on_images_generated: Current thread ID: {threading.get_ident()}, Main thread ID: {QApplication.instance().thread().currentThreadId()}")
        if not image_paths:
            QMessageBox.critical(self, 'Error', 'Failed to generate slide images.')
            self.update_status('Failed to generate slide images.')
            return
        self.update_status(f'Generated {len(image_paths)} slide images.')
        self.load_slide_image()
        QMessageBox.information(self, 'Success', f'Generated {len(image_paths)} slide images.')

    def generate_audio(self):
        if not self.load_config(): return
        if not self.slides or not self.narrations: QMessageBox.critical(self, 'Error', 'No narration scripts available.'); return
        valid_narrations = [n for n in self.narrations if n.strip() and not n.strip().startswith("Script for slide") and not n.strip().startswith("Error generating script")]
        if len(valid_narrations) < len(self.narrations): QMessageBox.critical(self, 'Error', 'Some narrations are empty or invalid.'); return
        self.save_scripts(); self.update_status('Generating audio files...')
        thread = QThread(); worker = Worker(self._generate_audio_worker); worker.moveToThread(thread)
        self._current_audio_thread = thread; self._current_audio_worker = worker
        thread.started.connect(worker.run); worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater); thread.finished.connect(thread.deleteLater)
        worker.result.connect(self._on_audio_generated); worker.error.connect(self._on_error)
        thread.start(); self.threads.append(thread)

    def _generate_audio_worker(self):
        narrations_copy = self.narrations.copy(); config_copy = self.config.copy()
        return generate_all_audio(narrations_copy, config_copy)

    def _on_audio_generated(self, audio_paths):
        if not audio_paths:
            QMessageBox.critical(self, 'Error', 'Failed to generate audio files. See log.')
            self.update_status('Failed to generate audio files.'); return
        self.update_status(f'Generated {len(audio_paths)} audio files.')
        QMessageBox.information(self, 'Success', f'Generated {len(audio_paths)} audio files.')

    def assemble_video(self):
        if not self.load_config(): return
        slides_dir = os.path.join(self.output_dir, 'slides'); audio_dir = os.path.join(self.output_dir, 'audio')
        if not os.path.exists(slides_dir) or not os.listdir(slides_dir): QMessageBox.critical(self, 'Error', 'No slide images found.'); return
        if not os.path.exists(audio_dir) or not os.listdir(audio_dir): QMessageBox.critical(self, 'Error', 'No audio files found.'); return
        self.update_status('Assembling video in pyqt_latex2video.py...')
        logging.info("[PYQT_DEBUG] assemble_video: Before QThread creation.")
        
        # Store thread and worker as instance variables to manage lifetime
        self.current_assemble_thread = QThread(self) # Parent to self for good measure
        logging.info(f"[PYQT_DEBUG] assemble_video: QThread object created: {self.current_assemble_thread}")
        self.update_status('Assembling video in pyqt_latex2video.py 2... (QThread created)')
        
        self.current_assemble_worker = Worker(self._assemble_video_worker, slides_dir, audio_dir)
        logging.info(f"[PYQT_DEBUG] assemble_video: Worker object created: {self.current_assemble_worker}")
        
        self.current_assemble_worker.moveToThread(self.current_assemble_thread)
        logging.info(f"[PYQT_DEBUG] assemble_video: Worker moved to thread. Is worker in thread? {self.current_assemble_worker.thread() == self.current_assemble_thread}. Is thread running? {self.current_assemble_thread.isRunning()}")
        self.update_status('Assembling video in pyqt_latex2video.py 3... (Worker moved to thread)')
        
        # Ensure the worker's run method is connected
        logging.info(f"[PYQT_DEBUG] assemble_video: Connecting thread.started to worker.run: {self.current_assemble_worker.run}")
        self.current_assemble_thread.started.connect(self.current_assemble_worker.run)
        logging.info("[PYQT_DEBUG] assemble_video: thread.started.connect(worker.run) connection established.")
        self.update_status('Assembling video in pyqt_latex2video.py 4... (thread.started connected)')
        
        # Connections for cleanup and results
        self.current_assemble_worker.finished.connect(self.current_assemble_thread.quit)
        self.current_assemble_worker.finished.connect(self.current_assemble_worker.deleteLater)
        self.current_assemble_thread.finished.connect(self.current_assemble_thread.deleteLater) 
        self.current_assemble_worker.result.connect(self._on_video_assembled)
        self.current_assemble_worker.error.connect(self._on_error)
        logging.info("[PYQT_DEBUG] assemble_video: All signals connected.")
        
        logging.info(f"[PYQT_DEBUG] assemble_video: About to call thread.start(). Current thread state: {self.current_assemble_thread.isRunning()}")
        self.current_assemble_thread.start()
        logging.info(f"[PYQT_DEBUG] assemble_video: thread.start() called. Is thread running now? {self.current_assemble_thread.isRunning()}")
        # self.threads.append(self.current_assemble_thread) 


    def _assemble_video_worker(self, slides_dir, audio_dir):
        logging.info("[PYQT_DEBUG] _assemble_video_worker: Method entered (this is the function run by the worker).") # Changed print to logging
        image_files = natural_sort([os.path.join(slides_dir, f) for f in os.listdir(slides_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]) # Use natural_sort
        audio_files = natural_sort([os.path.join(audio_dir, f) for f in os.listdir(audio_dir) if f.endswith('.mp3')]) # Use natural_sort
        if len(image_files) != len(audio_files): raise ValueError(f'Image/audio file count mismatch.')
        return assemble_video(image_files, audio_files, self.config.copy())

    def _on_video_assembled(self, output_path):
        if not output_path: QMessageBox.critical(self, 'Error', 'Failed to assemble video.'); self.update_status('Failed to assemble video.'); return
        self.update_status(f'Video assembled: {output_path}'); QMessageBox.information(self, 'Success', f'Video assembled: {output_path}')

    def generate_all(self):
        if not self.load_config(): return
        if not self.latex_file_path or not os.path.exists(self.latex_file_path): QMessageBox.critical(self, 'Error', 'Select LaTeX file.'); return
        if not self.slides or not self.narrations: QMessageBox.critical(self, 'Error', 'Parse LaTeX and generate scripts first.'); return
        current_prompt_text = self.narration_text.toPlainText().strip()
        if self.current_slide_index < len(self.prompts): self.prompts[self.current_slide_index] = current_prompt_text
        self.save_scripts(); self.update_status('Generating everything...')
        self.update_status('Step 1: Generating slide images...')
        thread1 = QThread(); worker1 = Worker(self._generate_images_worker, self.latex_file_path); worker1.moveToThread(thread1)
        thread1.started.connect(worker1.run); worker1.finished.connect(thread1.quit)
        worker1.finished.connect(worker1.deleteLater); thread1.finished.connect(thread1.deleteLater)
        worker1.result.connect(lambda image_paths: self._continue_with_audio(image_paths)); worker1.error.connect(self._on_error)
        thread1.start(); self.threads.append(thread1)

    def load_existing_images_qt(self):
        if not self.load_config(): return
        slides_dir = os.path.join(self.output_dir, 'slides')
        if not os.path.exists(slides_dir):
            QMessageBox.information(self, "Info", f"Slides directory not found: {slides_dir}\nNo existing images loaded.")
            self.update_status("Slides directory not found."); return
        try:
            image_files = [f for f in os.listdir(slides_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
            if image_files:
                QMessageBox.information(self, "Success", f"Found {len(image_files)} existing images in {slides_dir}.")
                self.update_status(f"Checked for existing images: {len(image_files)} found.")
                if self.slides: self.load_slide_image()
            else:
                QMessageBox.information(self, "Info", f"No existing images found in {slides_dir}.")
                self.update_status("No existing images found in slides directory.")
        except Exception as e:
            logging.error(f"Error loading existing images: {e}")
            QMessageBox.critical(self, "Error", f"Failed to check for existing images: {e}")

    def load_existing_audio_qt(self):
        if not self.load_config(): return
        audio_dir = os.path.join(self.output_dir, 'audio')
        if not os.path.exists(audio_dir):
            QMessageBox.information(self, "Info", f"Audio directory not found: {audio_dir}\nNo existing audio loaded.")
            self.update_status("Audio directory not found."); return
        try:
            audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.mp3')]
            if audio_files:
                QMessageBox.information(self, "Success", f"Found {len(audio_files)} existing audio files in {audio_dir}.")
                self.update_status(f"Checked for existing audio: {len(audio_files)} files found.")
            else:
                QMessageBox.information(self, "Info", f"No existing audio files found in {audio_dir}.")
                self.update_status("No existing audio files found in audio directory.")
        except Exception as e:
            logging.error(f"Error loading existing audio: {e}")
            QMessageBox.critical(self, "Error", f"Failed to check for existing audio: {e}")
    
    def _continue_with_audio(self, image_paths):
        if not image_paths: QMessageBox.critical(self, 'Error', 'Failed to generate slide images.'); self.update_status('Failed to generate slide images.'); return
        self.update_status(f'Generated {len(image_paths)} slide images.')
        self.update_status('Step 2: Generating audio files...')
        thread2 = QThread(); worker2 = Worker(self._generate_audio_worker); worker2.moveToThread(thread2)
        thread2.started.connect(worker2.run); worker2.finished.connect(thread2.quit)
        worker2.finished.connect(worker2.deleteLater); thread2.finished.connect(thread2.deleteLater)
        worker2.result.connect(lambda audio_paths_res: self._continue_with_video(image_paths, audio_paths_res)); worker2.error.connect(self._on_error)
        thread2.start(); self.threads.append(thread2)
    
    def _continue_with_video(self, image_paths, audio_paths):
        if not audio_paths: QMessageBox.critical(self, 'Error', 'Failed to generate audio files.'); self.update_status('Failed to generate audio files.'); return
        self.update_status(f'Generated {len(audio_paths)} audio files.')
        self.update_status('Step 3: Assembling final video...')
        if len(image_paths) != len(audio_paths):
            QMessageBox.warning(self, 'Warning', f'Image/audio file count mismatch. Using min count.')
            count = min(len(image_paths), len(audio_paths))
            image_paths = image_paths[:count]; audio_paths = audio_paths[:count]
        slides_dir = os.path.join(self.output_dir, 'slides'); audio_dir = os.path.join(self.output_dir, 'audio')
        thread3 = QThread(); worker3 = Worker(self._assemble_video_worker, slides_dir, audio_dir); worker3.moveToThread(thread3)
        thread3.started.connect(worker3.run); worker3.finished.connect(thread3.quit)
        worker3.finished.connect(worker3.deleteLater); thread3.finished.connect(thread3.deleteLater)
        worker3.result.connect(self._on_video_assembled); worker3.error.connect(self._on_error)
        thread3.start(); self.threads.append(thread3)

from PyQt5.QtGui import QFont

def main():
    app = QApplication(sys.argv)
    font = QFont(); font.setPointSize(16); app.setFont(font)
    window = LaTeX2VideoGUI()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
