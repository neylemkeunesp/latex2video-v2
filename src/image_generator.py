import os
import re
import subprocess
import logging
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont # Added ImageFont
from typing import List, Dict, Optional
import yaml
import shutil # Added for shutil.move

# Attempt to import Slide class for type hinting
try:
    from src.latex_parser import Slide
except ImportError:
    # Define a placeholder if Slide cannot be imported (e.g., during standalone execution)
    class Slide:
        def __init__(self, frame_number: int, title: str, content: str, slide_type: str = "frame"):
            self.frame_number = frame_number
            self.title = title
            self.content = content
            self.slide_type = slide_type

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("[MARKER] src/image_generator.py loaded and running from: " + os.path.abspath(__file__))
print("[PRINT-DEBUG] THIS IS THE ONLY src/image_generator.py:", os.path.abspath(__file__))

def load_config(config_path: str = '../config/config.yaml') -> Dict:
    """Loads configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logging.info(f"Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        return {}
    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration file {config_path}: {e}")
        return {}

def compile_latex_to_pdf(latex_file_path: str, output_dir: str) -> Optional[str]:
    """Compiles a LaTeX file to PDF using pdflatex."""
    if not os.path.exists(latex_file_path):
        logging.error(f"LaTeX source file not found: {latex_file_path}")
        return None

    file_name = os.path.basename(latex_file_path)
    base_name = os.path.splitext(file_name)[0]
    
    source_dir = os.path.dirname(os.path.abspath(latex_file_path))
    pdf_path_source = os.path.join(source_dir, f"{base_name}.pdf")
    pdf_path_output = os.path.join(output_dir, f"{base_name}.pdf")
    
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Compiling {latex_file_path} to PDF in source directory: {source_dir}...")
    
    for i in range(2):
        try:
            process = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', latex_file_path],
                cwd=source_dir, capture_output=True, text=True, timeout=60
            )
            if process.stdout: logging.debug(f"pdflatex run stdout:\n{process.stdout}")
            if process.stderr: logging.debug(f"pdflatex run stderr:\n{process.stderr}")
            if process.returncode != 0: logging.warning(f"pdflatex returned non-zero exit code: {process.returncode}")
        except FileNotFoundError:
            logging.error("pdflatex command not found. Ensure LaTeX is installed and in PATH.")
            return None
        except subprocess.TimeoutExpired:
            logging.error("pdflatex compilation timed out.")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred during pdflatex compilation: {e}")
    
    if os.path.exists(pdf_path_source):
        if os.path.getsize(pdf_path_source) > 0:
            logging.info(f"PDF successfully generated in source directory: {pdf_path_source}")
            try:
                shutil.copy2(pdf_path_source, pdf_path_output)
                logging.info(f"PDF copied to output directory: {pdf_path_output}")
                return pdf_path_output
            except Exception as e:
                logging.error(f"Error copying PDF to output directory: {e}")
                return pdf_path_source
        else:
            logging.error(f"PDF file was generated but is empty: {pdf_path_source}")
            return None
    else:
        log_file = os.path.join(source_dir, f"{base_name}.log")
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as lf: log_content = lf.read()
                logging.error(f"pdflatex log file ({log_file}):\n{log_content[-1000:]}")
            except Exception as e: logging.error(f"Error reading log file: {e}")
        logging.error(f"PDF file was not found after compilation. Tried: {pdf_path_source}")
        return None

def convert_pdf_to_images(pdf_path: str, output_folder: str, dpi: int, image_format: str) -> List[str]:
    if not os.path.exists(pdf_path):
        logging.error(f"PDF file not found for image conversion: {pdf_path}")
        return []
        
    logging.info(f"Converting PDF {pdf_path} to images (DPI: {dpi}, Format: {image_format})...")
    os.makedirs(output_folder, exist_ok=True)
    existing_files = set(os.listdir(output_folder))
    image_paths = []
    
    conversion_attempts = [
        {"settings_name": "default", "params": {}},
        {"settings_name": "alternative", "params": {"thread_count": 1, "use_pdftocairo": False}}
    ]

    for attempt in conversion_attempts:
        try:
            logging.info(f"Attempting conversion with {attempt['settings_name']} settings...")
            images = convert_from_path(
                pdf_path, dpi=dpi, output_folder=output_folder,
                fmt=image_format.lower(), paths_only=True, **attempt['params']
            )
            if images:
                logging.info(f"Successfully converted PDF to {len(images)} images with {attempt['settings_name']} settings")
                for i, img_path in enumerate(images):
                    temp_name = os.path.join(output_folder, f"raw_pdf_page_{i + 1:03d}.{image_format.lower()}")
                    try:
                        if os.path.abspath(img_path) != os.path.abspath(temp_name):
                            if os.path.exists(temp_name): os.remove(temp_name)
                            os.rename(img_path, temp_name)
                        image_paths.append(temp_name)
                        logging.debug(f"Renamed/confirmed {img_path} to temporary name {temp_name}")
                    except Exception as rename_error:
                        logging.error(f"Error renaming {img_path} to {temp_name}: {rename_error}. Adding original path {img_path}")
                        image_paths.append(img_path)
                return image_paths # Return on first successful conversion
            else:
                logging.warning(f"No images returned with {attempt['settings_name']} settings")
        except Exception as e:
            logging.error(f"Error with {attempt['settings_name']} settings: {e}")

    try: # Fallback: Check if any images were created despite errors
        new_files = set(os.listdir(output_folder)) - existing_files
        discovered_image_files = sorted([f for f in new_files if f.endswith(f'.{image_format.lower()}')])
        if discovered_image_files:
            logging.info(f"Found {len(discovered_image_files)} image files in output directory despite errors:")
            for i, img_file in enumerate(discovered_image_files):
                original_full_path = os.path.join(output_folder, img_file)
                temp_name = os.path.join(output_folder, f"raw_pdf_page_{i + 1:03d}.{image_format.lower()}")
                try:
                    if os.path.abspath(original_full_path) != os.path.abspath(temp_name):
                        if os.path.exists(temp_name): os.remove(temp_name)
                        os.rename(original_full_path, temp_name)
                    image_paths.append(temp_name)
                    logging.debug(f"Renamed/confirmed discovered file {original_full_path} to temporary name {temp_name}")
                except Exception as rename_error:
                    logging.error(f"Error renaming discovered file {original_full_path} to {temp_name}: {rename_error}. Adding original path {original_full_path}")
                    image_paths.append(original_full_path)
            return image_paths
    except Exception as e:
        logging.error(f"Error checking for created images: {e}")
    
    logging.error("Failed to convert PDF to images with all methods")
    return []

def generate_placeholder_image(title: str, output_path: str, width: int, height: int, bg_color: str, text_color: str):
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" 
        if not os.path.exists(font_path): font_path = "arial.ttf"
        font_size = 60
        try: font = ImageFont.truetype(font_path, font_size)
        except IOError: 
            logging.warning(f"Font {font_path} not found, using default PIL font.")
            font = ImageFont.load_default()
    except IOError:
        logging.warning(f"Specified font not found, using default PIL font.")
        font = ImageFont.load_default()

    try:
        text_bbox = draw.textbbox((0, 0), title, font=font)
        text_width = text_bbox[2] - text_bbox[0]; text_height = text_bbox[3] - text_bbox[1]
    except AttributeError:
        text_width, text_height = draw.textsize(title, font=font)
    x = (width - text_width) / 2; y = (height - text_height) / 2
    draw.text((x, y), title, fill=text_color, font=font)
    img.save(output_path)
    logging.info(f"Generated placeholder image: {output_path}")

def generate_slide_images(latex_file_path: str, slides_data: List[Slide], config: Dict) -> List[str]:
    output_base_dir = config.get('output_dir', '../output')
    pdf_output_dir = os.path.abspath(os.path.join(output_base_dir, 'temp_pdf'))
    slides_output_dir = os.path.abspath(os.path.join(output_base_dir, 'slides'))
    
    latex_config = config.get('latex', {})
    dpi = latex_config.get('dpi', 300)
    image_format = latex_config.get('image_format', 'png')

    pdf_path = compile_latex_to_pdf(latex_file_path, pdf_output_dir)
    logging.info(f"After compile_latex_to_pdf: pdf_path={pdf_path}, exists={os.path.exists(pdf_path) if pdf_path else False}")
    
    pdf_page_images = []
    pdf_conversion_successful = False
    if pdf_path and os.path.exists(pdf_path):
        try:
            pdf_page_images = convert_pdf_to_images(pdf_path, slides_output_dir, dpi, image_format)
            logging.info(f"convert_pdf_to_images returned {len(pdf_page_images)} images: {pdf_page_images}")
            if pdf_page_images: pdf_conversion_successful = True
        except Exception as e:
            logging.error(f"Exception in convert_pdf_to_images: {e}")
    else:
        logging.warning("PDF path is not valid or PDF does not exist. Skipping PDF to image conversion.")

    final_image_paths = []
    video_config = config.get('video', {})
    resolution_str = video_config.get('resolution', '1920x1080')
    img_width, img_height = map(int, resolution_str.split('x'))
    placeholder_bg_color = video_config.get('placeholder_bg_color', '#333333')
    placeholder_text_color = video_config.get('placeholder_text_color', '#FFFFFF')
    
    pdf_image_idx = 0
    logging.info(f"[DEBUG_IMG_GEN] Starting loop. slides_data: {len(slides_data)}, pdf_page_images: {len(pdf_page_images)}")

    for i, slide_info in enumerate(slides_data):
        slide_output_filename = f"slide_{i + 1:03d}.{image_format.lower()}"
        slide_output_path = os.path.join(slides_output_dir, slide_output_filename)
        logging.info(f"[DEBUG_IMG_GEN] Processing slide {i+1}/{len(slides_data)}: '{slide_info.title}' (Type: {slide_info.slide_type}). Target: '{slide_output_path}'")

        if pdf_conversion_successful and pdf_image_idx < len(pdf_page_images):
            raw_pdf_image_path = pdf_page_images[pdf_image_idx]
            logging.info(f"[DEBUG_IMG_GEN] Using PDF image '{raw_pdf_image_path}' for slide {i+1}.")
            if os.path.exists(raw_pdf_image_path):
                try:
                    os.makedirs(os.path.dirname(slide_output_path), exist_ok=True)
                    if os.path.exists(slide_output_path) and os.path.abspath(raw_pdf_image_path) != os.path.abspath(slide_output_path):
                        os.remove(slide_output_path)
                    shutil.move(raw_pdf_image_path, slide_output_path)
                    logging.info(f"Moved PDF image {raw_pdf_image_path} to {slide_output_path}.")
                    final_image_paths.append(slide_output_path)
                    pdf_image_idx += 1
                except Exception as e:
                    logging.error(f"[DEBUG_IMG_GEN] Error moving PDF image {raw_pdf_image_path} for slide {i+1}: {e}. Generating placeholder.")
                    placeholder_title = f"{slide_info.slide_type.capitalize() if slide_info.slide_type else 'Slide'}: {slide_info.title} (Move Error)"
                    generate_placeholder_image(placeholder_title, slide_output_path, img_width, img_height, placeholder_bg_color, placeholder_text_color)
                    final_image_paths.append(slide_output_path)
            else:
                logging.warning(f"[DEBUG_IMG_GEN] Raw PDF image {raw_pdf_image_path} not found for slide {i+1}. Generating placeholder.")
                placeholder_title = f"{slide_info.slide_type.capitalize() if slide_info.slide_type else 'Slide'}: {slide_info.title} (Raw Missing)"
                generate_placeholder_image(placeholder_title, slide_output_path, img_width, img_height, placeholder_bg_color, placeholder_text_color)
                final_image_paths.append(slide_output_path)
        else:
            status_reason = ""
            if not pdf_conversion_successful: status_reason = "(PDF Fail)"
            elif pdf_image_idx >= len(pdf_page_images): status_reason = "(No More PDFs)"
            logging.warning(f"[DEBUG_IMG_GEN] No PDF image for slide {i+1} {status_reason}. Generating placeholder for: '{slide_info.title}'")
            placeholder_title = f"{slide_info.slide_type.capitalize() if slide_info.slide_type else 'Slide'}: {slide_info.title} {status_reason}".strip()
            generate_placeholder_image(placeholder_title, slide_output_path, img_width, img_height, placeholder_bg_color, placeholder_text_color)
            final_image_paths.append(slide_output_path)
        
        logging.info(f"[DEBUG_IMG_GEN] Slide {i+1} processed. Total final images: {len(final_image_paths)}. PDF images used so far: {pdf_image_idx}")
            
    logging.info(f"[DEBUG_IMG_GEN] Finished loop. Total images in final_image_paths: {len(final_image_paths)}")
    return final_image_paths

if __name__ == '__main__':
    cfg = load_config()
    if cfg:
        latex_file = '../assets/presentation.tex' 
        cfg['output_dir'] = '../output' 
        os.makedirs(os.path.join(cfg['output_dir'], 'slides'), exist_ok=True)
        os.makedirs(os.path.join(cfg['output_dir'], 'temp_pdf'), exist_ok=True)
        
        # Dummy slides_data for testing standalone
        example_slides_data = [
            Slide(1, "Title Slide", "Content 1", "frame"),
            Slide(2, "Introduction Section", "Content 2", "section"),
            Slide(3, "Frame 2", "Content 3", "frame"),
            Slide(4, "Frame 3", "Content 4", "frame"),
        ]
        # To test with actual parsed data, you'd call latex_parser.parse_latex_file here
        # For now, this example_slides_data might not match a real presentation.tex
        
        # It's better to test generate_slide_images via the GUI or a dedicated test script
        # that prepares proper Slide objects if you don't want to call latex_parser here.
        # This __main__ block is more for basic invocation.
        print(f"Testing with {len(example_slides_data)} dummy slides_data items.")
        generated_images = generate_slide_images(latex_file, example_slides_data, cfg)
        if generated_images:
            print(f"Generated {len(generated_images)} images:")
            for img in generated_images:
                print(img)
        else:
            print("Image generation failed.")
