import re
import os
import logging
import subprocess
from typing import List, Dict, Any, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """Extract text from PDF using pdftotext."""
    try:
        logging.info(f"Extracting text from PDF: {pdf_path}")
        result = subprocess.run(
            ['pdftotext', pdf_path, '-'],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error extracting text from PDF: {e}")
        return None

class Slide:
    """Represents a single slide with its content."""
    def __init__(self, frame_number: int, title: str, content: str):
        self.frame_number = frame_number
        self.title = title
        self.content = content

    def __repr__(self):
        return f"Slide(frame_number={self.frame_number}, title='{self.title}', content_len={len(self.content)})"

def extract_frame_title(frame_content: str) -> str:
    """Extracts the frametitle from the frame content."""
    # Try to match frametitle with balanced braces
    # This is a more robust approach that handles nested braces
    frame_title = "Untitled Frame"

    # First, look for \frametitle{ pattern
    title_start = frame_content.find("\\frametitle{")
    if title_start >= 0:
        # Found the start of the title
        title_start += len("\\frametitle{")
        brace_count = 1  # We've already seen one opening brace
        title_end = title_start

        # Find the matching closing brace
        while title_end < len(frame_content) and brace_count > 0:
            if frame_content[title_end] == '{':
                brace_count += 1
            elif frame_content[title_end] == '}':
                brace_count -= 1
            title_end += 1

        if brace_count == 0:  # Found the matching closing brace
            # Extract the title (excluding the closing brace)
            frame_title = frame_content[title_start:title_end-1].strip()

    # If the above method fails, try the simple regex approach as a fallback
    if frame_title == "Untitled Frame":
        match = re.search(r'\\frametitle\{(.*?)\}', frame_content, re.DOTALL)
        if match:
            frame_title = match.group(1).strip()

    # If still no title found, try to extract the first non-empty line as the title
    if frame_title == "Untitled Frame":
        # Clean the content first to remove LaTeX commands
        cleaned_content = clean_latex_content(frame_content)
        lines = cleaned_content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('-') and not line.startswith('Continuation of'):
                # Found a potential title
                frame_title = line
                break

    return frame_title

def clean_latex_content(content: str) -> str:
    """Removes comments and frametitle from LaTeX content."""
    # Remove comments
    content = re.sub(r'%.*?\n', '\n', content)

    # Remove frametitle command and its argument
    content = re.sub(r'\\frametitle\{.*?\}', '', content, flags=re.DOTALL)

    return content

def process_frame_content(frame_content: str) -> Dict[str, Any]:
    """
    Process the content of a LaTeX frame and extract structured information.
    
    Args:
        frame_content: The content of the LaTeX frame
        
    Returns:
        Dictionary containing structured information about the frame:
        - title: The title of the frame
        - text_content: The text content of the frame (without LaTeX commands)
        - math_formulas: List of mathematical formulas found in the frame
        - bullet_points: List of bullet points found in the frame
        - has_figure: Boolean indicating if the frame contains a figure
        - has_table: Boolean indicating if the frame contains a table
    """
    logging.info("Processing frame content")
    
    # Extract the frame title
    title = extract_frame_title(frame_content)
    
    # Clean the content
    cleaned_content = clean_latex_content(frame_content)
    
    # Extract mathematical formulas
    math_formulas = []
    # Look for inline math formulas: $...$
    inline_math = re.findall(r'\$(.*?)\$', cleaned_content, re.DOTALL)
    if inline_math:
        math_formulas.extend(inline_math)
    
    # Look for display math formulas: \begin{equation}...\end{equation}
    equation_math = re.findall(r'\\begin\{equation\}(.*?)\\end\{equation\}', cleaned_content, re.DOTALL)
    if equation_math:
        math_formulas.extend(equation_math)
    
    # Look for display math formulas: \begin{align}...\end{align}
    align_math = re.findall(r'\\begin\{align\}(.*?)\\end\{align\}', cleaned_content, re.DOTALL)
    if align_math:
        math_formulas.extend(align_math)
    
    # Look for display math formulas: \begin{math}...\end{math}
    math_env = re.findall(r'\\begin\{math\}(.*?)\\end\{math\}', cleaned_content, re.DOTALL)
    if math_env:
        math_formulas.extend(math_env)
    
    # Look for display math formulas: \[...\]
    display_math = re.findall(r'\\\[(.*?)\\\]', cleaned_content, re.DOTALL)
    if display_math:
        math_formulas.extend(display_math)
    
    # Extract bullet points
    bullet_points = []
    # Look for itemize environment
    itemize_match = re.search(r'\\begin\{itemize\}(.*?)\\end\{itemize\}', cleaned_content, re.DOTALL)
    if itemize_match:
        itemize_content = itemize_match.group(1)
        # Extract individual items
        items = re.findall(r'\\item\s+(.*?)(?=\\item|\\end\{itemize\}|$)', itemize_content, re.DOTALL)
        bullet_points.extend([item.strip() for item in items])
    
    # Check if the frame contains a figure
    has_figure = '\\begin{figure}' in cleaned_content or '\\includegraphics' in cleaned_content
    
    # Check if the frame contains a table
    has_table = '\\begin{table}' in cleaned_content or '\\begin{tabular}' in cleaned_content
    
    # Remove LaTeX commands to get plain text content
    text_content = cleaned_content
    # Remove math environments
    text_content = re.sub(r'\$(.*?)\$', '', text_content)
    text_content = re.sub(r'\\begin\{equation\}(.*?)\\end\{equation\}', '', text_content, re.DOTALL)
    text_content = re.sub(r'\\begin\{align\}(.*?)\\end\{align\}', '', text_content, re.DOTALL)
    text_content = re.sub(r'\\begin\{math\}(.*?)\\end\{math\}', '', text_content, re.DOTALL)
    text_content = re.sub(r'\\\[(.*?)\\\]', '', text_content, re.DOTALL)
    # Remove itemize environment
    text_content = re.sub(r'\\begin\{itemize\}(.*?)\\end\{itemize\}', '', text_content, re.DOTALL)
    # Remove figure environment
    text_content = re.sub(r'\\begin\{figure\}(.*?)\\end\{figure\}', '', text_content, re.DOTALL)
    # Remove table environment
    text_content = re.sub(r'\\begin\{table\}(.*?)\\end\{table\}', '', text_content, re.DOTALL)
    text_content = re.sub(r'\\begin\{tabular\}(.*?)\\end\{tabular\}', '', text_content, re.DOTALL)
    # Remove other common LaTeX commands
    text_content = re.sub(r'\\[a-zA-Z]+(\{[^{}]*\}|\[[^[\]]*\])*', '', text_content)
    # Clean up whitespace
    text_content = re.sub(r'\s+', ' ', text_content).strip()
    
    return {
        'title': title,
        'text_content': text_content,
        'math_formulas': math_formulas,
        'bullet_points': bullet_points,
        'has_figure': has_figure,
        'has_table': has_table
    }


def parse_pdf_file(pdf_path: str) -> List[Slide]:
    """Parses a PDF file and extracts slides."""
    logging.info(f"Parsing PDF file: {pdf_path}")

    # Extract text from PDF
    pdf_text = extract_text_from_pdf(pdf_path)
    if not pdf_text:
        logging.error(f"Failed to extract text from PDF: {pdf_path}")
        return []

    # Get the number of pages in the PDF
    pdf_page_count = 0
    try:
        result = subprocess.run(['pdfinfo', pdf_path], capture_output=True, text=True, check=True)
        match = re.search(r'Pages:\s+(\d+)', result.stdout)
        if match:
            pdf_page_count = int(match.group(1))
            logging.info(f"PDF has {pdf_page_count} pages")
    except Exception as e:
        logging.error(f"Error getting page count from PDF: {e}")
        return []

    # Split text by page (pdftotext adds form feeds between pages)
    pages = pdf_text.split('\f')

    # Create slides from pages
    slides = []

    # First slide is usually the title page
    if len(pages) > 0:
        title_page_text = pages[0].strip()
        title_lines = [line for line in title_page_text.split('\n') if line.strip()]

        # Try to extract title and author from the first page
        title = title_lines[0] if title_lines else "Presentation Title"
        author = title_lines[1] if len(title_lines) > 1 else ""

        slides.append(Slide(
            frame_number=1,
            title="Title Page",
            content=f"Title: {title}\nAuthor: {author}"
        ))

    # Second slide is usually the outline/TOC
    if len(pages) > 1:
        outline_text = pages[1].strip()

        # Check if this page looks like an outline
        is_outline = False
        outline_keywords = ["outline", "contents", "agenda", "sumário", "índice", "conteúdo"]
        for keyword in outline_keywords:
            if keyword.lower() in outline_text.lower():
                is_outline = True
                break

        if is_outline:
            slides.append(Slide(
                frame_number=2,
                title="Outline",
                content=outline_text
            ))
            start_idx = 2  # Start content slides from page 3
        else:
            # If second page doesn't look like an outline, add a default outline slide
            slides.append(Slide(
                frame_number=2,
                title="Outline",
                content="This slide shows the outline of the presentation."
            ))
            start_idx = 1  # Start content slides from page 2
    else:
        # If there's only one page, add a default outline slide
        slides.append(Slide(
            frame_number=2,
            title="Outline",
            content="This slide shows the outline of the presentation."
        ))
        start_idx = 1  # Start content slides from page 2 (though there aren't any more pages)

    # Process the remaining pages as content slides
    for i in range(start_idx, len(pages)):
        page_text = pages[i].strip()
        if not page_text:
            continue

        # Try to extract a title from the page
        lines = page_text.split('\n')
        title = "Untitled Slide"
        content = page_text

        # Try to find a title in the first few lines
        for j in range(min(3, len(lines))):
            if lines[j].strip() and not lines[j].strip().startswith('-'):
                title = lines[j].strip()
                # Remove the title from the content
                content = '\n'.join(lines[j+1:])
                break

        # Add the slide
        slides.append(Slide(
            frame_number=i+1,
            title=title,
            content=content
        ))

        # Log the extracted content for debugging
        logging.info(f"Slide {i+1}: {title}")
        logging.info(f"Extracted Content:\n{content}")
        logging.info("-" * 80)

    logging.info(f"Successfully parsed {len(slides)} slides from PDF.")
    return slides

def parse_latex_file(file_path: str) -> List[Slide]:
    """Parses a LaTeX Beamer file or PDF file and extracts slides."""
    # Check if the file is a PDF
    if file_path.lower().endswith('.pdf'):
        logging.info(f"Detected PDF file: {file_path}")
        return parse_pdf_file(file_path)

    # Otherwise, treat it as a LaTeX file
    logging.info(f"Parsing LaTeX file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            latex_content = f.read()
    except FileNotFoundError:
        logging.error(f"LaTeX file not found: {file_path}")
        # Check if there's a PDF with the same base name
        pdf_path = os.path.splitext(file_path)[0] + '.pdf'
        if os.path.exists(pdf_path):
            logging.info(f"Found PDF file with same base name: {pdf_path}")
            return parse_pdf_file(pdf_path)
        return []
    except Exception as e:
        logging.error(f"Error reading LaTeX file {file_path}: {e}")
        return []

    # Extract all sections and frames in the order they appear in the file
    elements = extract_sections_and_frames(file_path)
    
    # Filter out only the frames
    frames = [content for elem_type, content, _ in elements if elem_type == "frame"]
    
    # Extract document title and author for use in slides
    title_match = re.search(r'\\title\{(.*?)\}', latex_content, re.DOTALL)
    doc_title = title_match.group(1).strip() if title_match else "Presentation Title"
    author_match = re.search(r'\\author\{(.*?)\}', latex_content, re.DOTALL)
    doc_author = author_match.group(1).strip() if author_match else ""

    # Get the number of pages in the PDF
    # First check in the source directory
    source_dir = os.path.dirname(os.path.abspath(file_path))
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    pdf_path_source = os.path.join(source_dir, base_name + '.pdf')

    # Also check in the output directory
    pdf_path_output = os.path.join('output', 'temp_pdf', base_name + '.pdf')

    pdf_page_count = 0  # Initialize to 0

    # Try to get page count from source directory first
    try:
        if os.path.exists(pdf_path_source):
            logging.info(f"Found PDF in source directory: {pdf_path_source}")
            result = subprocess.run(['pdfinfo', pdf_path_source], capture_output=True, text=True, check=True)
            match = re.search(r'Pages:\s+(\d+)', result.stdout)
            if match:
                pdf_page_count = int(match.group(1))
                logging.info(f"PDF in source directory has {pdf_page_count} pages")
        # If not found in source directory or couldn't get page count, try output directory
        elif os.path.exists(pdf_path_output):
            logging.info(f"Found PDF in output directory: {pdf_path_output}")
            result = subprocess.run(['pdfinfo', pdf_path_output], capture_output=True, text=True, check=True)
            match = re.search(r'Pages:\s+(\d+)', result.stdout)
            if match:
                pdf_page_count = int(match.group(1))
                logging.info(f"PDF in output directory has {pdf_page_count} pages")
        else:
            logging.warning(f"PDF not found in either source directory ({pdf_path_source}) or output directory ({pdf_path_output})")
    except Exception as e:
        logging.warning(f"Could not determine PDF page count: {e}")

    # If we still don't have a page count, try to estimate from the number of frames
    if pdf_page_count == 0:
        # Count the number of frames in the LaTeX file
        frame_count = len(frames)

        # Add 2 for title and outline slides
        estimated_page_count = frame_count + 2

        logging.warning(f"Could not determine PDF page count from file. Estimating {estimated_page_count} pages based on {frame_count} frames plus title and outline slides.")
        pdf_page_count = estimated_page_count

    # Create slides to match the PDF page count
    parsed_slides: List[Slide] = []

    # First slide is always the title page
    parsed_slides.append(Slide(
        frame_number=1,
        title="Title Page",
        content=f"Title: {doc_title}\nAuthor: {doc_author}"
    ))
    
    # Find the outline slide if it exists
    outline_slide_index = -1
    for i, frame_content in enumerate(frames):
        # Check if this frame is an outline/TOC slide
        if '\\tableofcontents' in frame_content or 'Outline' in frame_content or 'Sumário' in frame_content:
            outline_slide_index = i
            break

    # Add a default outline slide if we didn't find one
    if outline_slide_index == -1:
        parsed_slides.append(Slide(
            frame_number=2,
            title="Outline",
            content="This slide shows the outline of the presentation."
        ))
    else:
        # Extract the outline slide content
        outline_content = clean_latex_content(frames[outline_slide_index])
        if not outline_content.strip():
            outline_content = "This slide shows the outline of the presentation."

        # Add the outline slide as slide 2
        parsed_slides.append(Slide(
            frame_number=2,
            title="Outline",
            content=outline_content
        ))

        # Remove the outline slide from frames so we don't process it again
        frames.pop(outline_slide_index)

    # Process the actual content frames and create slides
    start_frame_number = 3  # Start content slides at frame 3 (after title and outline)
    
    # Process each element (section or frame) in the order they appear in the file
    current_section = ""
    frame_index = 0
    
    # Create a directory for section files
    output_dir = os.path.dirname(os.path.abspath(file_path))
    responses_dir = os.path.join(output_dir, 'output', 'chatgpt_responses')
    os.makedirs(responses_dir, exist_ok=True)
    
    for elem_type, content, _ in elements:
        # If it's a section, update the current section and create a section file
        if elem_type == "section":
            current_section = content
            
            # Generate a section slide
            section_slide = Slide(
                frame_number=start_frame_number + frame_index,
                title=f"Section: {current_section}",
                content=f"[Section] {current_section}"
            )
            
            # Add the section slide to our collection
            parsed_slides.append(section_slide)
            
            # Save the section content to a file with the correct format
            section_file_path = os.path.join(responses_dir, f"section_{len(parsed_slides)}_response.txt")
            try:
                with open(section_file_path, 'w', encoding='utf-8') as f:
                    # Make sure to include the opening bracket
                    section_content = f"[Section] {current_section}"
                    f.write(section_content)
                logging.info(f"Saved section file: {section_file_path}")
            except Exception as e:
                logging.error(f"Error saving section file: {e}")
            
            # Increment the frame index
            frame_index += 1
            
            # Log the section slide
            logging.info(f"Added section slide: {current_section}")
        
        # If it's a frame, process it
        elif elem_type == "frame":
            # Skip the title page frame and outline slide (already handled)
            if '\\titlepage' in content or '\\tableofcontents' in content:
                continue
            
            # Calculate the frame number
            frame_number = start_frame_number + frame_index
            if frame_number > pdf_page_count:
                break  # Don't create more slides than PDF pages
            
            # Process the frame content to extract structured information
            processed_content = process_frame_content(content)
            title = processed_content['title']
            
            # Create a more informative content string that includes the structured information
            content_parts = []
            content_parts.append(f"Title: {title}")
            
            # Add the current section if available
            if current_section:
                content_parts.append(f"Section: {current_section}")
                
            content_parts.append(f"Text Content: {processed_content['text_content']}")
            
            if processed_content['math_formulas']:
                content_parts.append("Math Formulas:")
                for i, formula in enumerate(processed_content['math_formulas']):
                    content_parts.append(f"  {i+1}. {formula}")
            
            if processed_content['bullet_points']:
                content_parts.append("Bullet Points:")
                for i, point in enumerate(processed_content['bullet_points']):
                    content_parts.append(f"  {i+1}. {point}")
            
            if processed_content['has_figure']:
                content_parts.append("Contains Figure: Yes")
            
            if processed_content['has_table']:
                content_parts.append("Contains Table: Yes")
            
            # Join all parts with newlines
            structured_content = "\n".join(content_parts)
            
            # Ensure we have content
            if not structured_content.strip():
                logging.warning(f"Frame appears empty after processing. Title: '{title}'")
                structured_content = f"This slide covers {title}."
            
            # Log the extracted content for debugging
            logging.info(f"Slide {frame_number}: {title}")
            logging.info(f"Processed Content:\n{structured_content}")
            logging.info("-" * 80)
            
            # Add the slide to our collection
            parsed_slides.append(Slide(
                frame_number=frame_number,
                title=title,
                content=structured_content
            ))
            
            # Increment the frame index
            frame_index += 1

    # Ensure all slides have sequential frame numbers
    for i, slide in enumerate(parsed_slides):
        slide.frame_number = i + 1

    logging.info(f"Successfully parsed {len(parsed_slides)} slides.")
    return parsed_slides

def extract_sections_and_frames(file_path: str) -> List[Tuple[str, str, int]]:
    """
    Extract all sections and frames from a LaTeX file along with their positions.
    
    Args:
        file_path: Path to the LaTeX file
        
    Returns:
        List of tuples containing (type, content, position_in_file)
        where type is either "section" or "frame"
    """
    logging.info(f"Extracting sections and frames from LaTeX file: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            latex_content = f.read()
    except Exception as e:
        logging.error(f"Error reading LaTeX file {file_path}: {e}")
        return []
    
    # Find all section and frame commands with their positions
    elements = []
    
    # Pattern 1: Standard \section{name}
    section_pattern1 = re.compile(r'\\section\{(.*?)\}', re.DOTALL)
    for match in section_pattern1.finditer(latex_content):
        elements.append(("section", match.group(1).strip(), match.start()))
    
    # Pattern 2: \section[options]{name}
    section_pattern2 = re.compile(r'\\section\[(.*?)\]\{(.*?)\}', re.DOTALL)
    for match in section_pattern2.finditer(latex_content):
        elements.append(("section", match.group(2).strip(), match.start()))
    
    # Pattern 3: \section*{name} (unnumbered sections)
    section_pattern3 = re.compile(r'\\section\*\{(.*?)\}', re.DOTALL)
    for match in section_pattern3.finditer(latex_content):
        elements.append(("section", match.group(1).strip(), match.start()))
    
    # Pattern 4: Look for \begin{frame}{Section: name} pattern
    section_pattern4 = re.compile(r'\\begin\{frame\}\{Section:\s*(.*?)\}', re.DOTALL)
    for match in section_pattern4.finditer(latex_content):
        elements.append(("section", match.group(1).strip(), match.start()))
    
    # Pattern 5: Look for \frametitle{Section: name} pattern
    section_pattern5 = re.compile(r'\\frametitle\{Section:\s*(.*?)\}', re.DOTALL)
    for match in section_pattern5.finditer(latex_content):
        elements.append(("section", match.group(1).strip(), match.start()))
    
    # Pattern 6: Standard \begin{frame}...\end{frame}
    frame_pattern1 = re.compile(r'\\begin\{frame\}(.*?)\\end\{frame\}', re.DOTALL)
    for match in frame_pattern1.finditer(latex_content):
        elements.append(("frame", match.group(1), match.start()))
    
    # Pattern 7: \begin{frame}[options]...\end{frame}
    frame_pattern2 = re.compile(r'\\begin\{frame\}\[(.*?)\](.*?)\\end\{frame\}', re.DOTALL)
    for match in frame_pattern2.finditer(latex_content):
        elements.append(("frame", match.group(2), match.start()))
    
    # Pattern 8: \frame{...} (older LaTeX syntax)
    frame_pattern3 = re.compile(r'(?<!title)\\frame\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', re.DOTALL)
    for match in frame_pattern3.finditer(latex_content):
        elements.append(("frame", match.group(1), match.start()))
    
    # Pattern 9: \begin{frame}{title}...\end{frame}
    frame_pattern4 = re.compile(r'\\begin\{frame\}\{(.*?)\}(.*?)\\end\{frame\}', re.DOTALL)
    for match in frame_pattern4.finditer(latex_content):
        # Skip if it's a section frame (already captured by pattern 4)
        if not match.group(1).startswith("Section:"):
            elements.append(("frame", match.group(2), match.start()))
    
    # Sort elements by their position in the file
    elements.sort(key=lambda x: x[2])
    
    logging.info(f"Found {len(elements)} elements (sections and frames)")
    return elements

def extract_sections_from_latex(file_path: str) -> List[Tuple[str, int]]:
    """
    Extract all section names from a LaTeX file along with their positions.
    
    Args:
        file_path: Path to the LaTeX file
        
    Returns:
        List of tuples containing (section_name, position_in_file)
    """
    logging.info(f"Extracting sections from LaTeX file: {file_path}")
    
    # Get all sections and frames
    elements = extract_sections_and_frames(file_path)
    
    # Filter out only the sections
    sections = [(content, pos) for elem_type, content, pos in elements if elem_type == "section"]
    
    # Extract just the section names
    section_names = [section[0] for section in sections]
    
    # Remove duplicates while preserving order
    unique_sections = []
    for section in section_names:
        if section not in unique_sections:
            unique_sections.append(section)
    
    logging.info(f"Found {len(unique_sections)} unique sections: {unique_sections}")
    return [(section, -1) for section in unique_sections]  # Return with dummy positions

def generate_section_scripts(file_path: str, output_dir: str) -> List[str]:
    """
    Generate script files for each section in a LaTeX file.
    
    Args:
        file_path: Path to the LaTeX file
        output_dir: Directory to save the script files
        
    Returns:
        List of paths to the generated script files
    """
    logging.info(f"Generating section scripts for LaTeX file: {file_path}")
    
    # Extract sections from the LaTeX file
    sections = extract_sections_from_latex(file_path)
    
    # Create output directory if it doesn't exist
    responses_dir = os.path.join(output_dir, 'chatgpt_responses')
    os.makedirs(responses_dir, exist_ok=True)
    
    # If no sections found, return empty list
    if not sections:
        logging.warning("No sections found in LaTeX file.")
        return []
    
    # Generate script files for each section
    script_files = []
    for i, (section_name, _) in enumerate(sections):
        if section_name:
            # Create script content with the required format
            script_content = f"[Section] {section_name}"
            
            # Save to file with a sequential number
            file_name = f"section_{i+1}_response.txt"
            file_path = os.path.join(responses_dir, file_name)
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(script_content)
                logging.info(f"Generated section script for section {i+1}: {section_name}")
                script_files.append(file_path)
            except Exception as e:
                logging.error(f"Error saving section script: {e}")
    
    return script_files

if __name__ == '__main__':
    # Example usage:
    sample_file = '../assets/presentation.tex' # Adjust path if running directly
    parsed_slides = parse_latex_file(sample_file)
    for slide in parsed_slides:
        print(f"--- Slide {slide.frame_number}: {slide.title} ---")
        print(slide.content)
        print("-" * (len(slide.title) + 14))
    
    # Example of extracting sections
    sections = extract_sections_from_latex(sample_file)
    print(f"Found {len(sections)} sections:")
    for i, section in enumerate(sections):
        print(f"{i+1}. {section}")
