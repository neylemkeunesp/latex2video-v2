import re
import os
import logging
import subprocess
from typing import List, Dict, Any, Optional

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
    """Represents a single slide with its content and type."""
    def __init__(self, frame_number: int, title: str, content: str, slide_type: str = "frame"):
        self.frame_number = frame_number
        self.title = title
        self.content = content
        self.slide_type = slide_type  # 'frame' or 'section'

    def __repr__(self):
        return f"Slide(type='{self.slide_type}', frame_number={self.frame_number}, title='{self.title}', content_len={len(self.content)})"

def extract_frame_title(frame_content: str) -> str:
    """Extracts the frametitle from the frame content, or recognizes special frames like Outline/Table of Contents/Title Page."""
    # Special handling for frames that are just \tableofcontents or \titlepage
    content_no_space = frame_content.replace(" ", "").replace("\n", "")
    if "\\tableofcontents" in content_no_space:
        return "Outline"
    if "\\titlepage" in content_no_space:
        return "Title Page"

    # Try to match frametitle with balanced braces
    frame_title = "Untitled Frame"

    # First, look for \frametitle{ pattern
    title_start = frame_content.find("\\frametitle{")
    if title_start >= 0:
        title_start += len("\\frametitle{")
        brace_count = 1
        title_end = title_start
        while title_end < len(frame_content) and brace_count > 0:
            if frame_content[title_end] == '{':
                brace_count += 1
            elif frame_content[title_end] == '}':
                brace_count -= 1
            title_end += 1
        if brace_count == 0:
            frame_title = frame_content[title_start:title_end-1].strip()

    # Fallback: simple regex
    if frame_title == "Untitled Frame":
        match = re.search(r'\\frametitle\{(.*?)\}', frame_content, re.DOTALL)
        if match:
            frame_title = match.group(1).strip()

    # Fallback: first non-empty line
    if frame_title == "Untitled Frame":
        cleaned_content = clean_latex_content(frame_content)
        lines = cleaned_content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('-') and not line.startswith('Continuation of'):
                frame_title = line
                break

    # Clean up the title - remove any 'e{' prefix that might have been added
    frame_title = re.sub(r'^e\{', '', frame_title)
    
    # Remove any remaining LaTeX commands from the title
    frame_title = re.sub(r'\\[a-zA-Z@]+(\*|\[[^\]]*\])?\{(.*?)\}', r'\2', frame_title)
    
    # Remove any remaining braces
    frame_title = re.sub(r'[\{\}]', '', frame_title)

    return frame_title

def clean_latex_content(content: str) -> str:
    """Removes comments and frametitle from LaTeX content, while preserving mathematical formulas."""
    # Remove comments
    content = re.sub(r'%.*?\n', '\n', content)

    # Remove frametitle command and its argument
    content = re.sub(r'\\frametitle\{.*?\}', '', content, flags=re.DOTALL)

    # Handle itemize, enumerate (basic)
    content = re.sub(r'\\begin\{(itemize|enumerate)\}', '', content)
    content = re.sub(r'\\end\{(itemize|enumerate)\}', '', content)
    # Replace \item and any following whitespace with a newline, hyphen, and space.
    # This helps ensure items are on new lines and standardizes spacing after \item.
    content = re.sub(r'\\item\s*', '\n- ', content)

    # Preserve mathematical content by temporarily replacing it
    math_placeholders = {}
    
    # Extract and preserve display math ($$...$$)
    display_math_pattern = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
    for i, match in enumerate(display_math_pattern.finditer(content)):
        placeholder = f"DISPLAY_MATH_{i}"
        math_placeholders[placeholder] = f"FORMULA: {match.group(1).strip()}"
        content = content.replace(match.group(0), placeholder)
    
    # Extract and preserve inline math ($...$)
    inline_math_pattern = re.compile(r'\$(.*?)\$')
    for i, match in enumerate(inline_math_pattern.finditer(content)):
        placeholder = f"INLINE_MATH_{i}"
        math_placeholders[placeholder] = f"FORMULA: {match.group(1).strip()}"
        content = content.replace(match.group(0), placeholder)
    
    # Extract and preserve equation environments
    equation_pattern = re.compile(r'\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}', re.DOTALL)
    for i, match in enumerate(equation_pattern.finditer(content)):
        placeholder = f"EQUATION_{i}"
        math_placeholders[placeholder] = f"FORMULA: {match.group(1).strip()}"
        content = content.replace(match.group(0), placeholder)
    
    # Extract and preserve align environments
    align_pattern = re.compile(r'\\begin\{align\*?\}(.*?)\\end\{align\*?\}', re.DOTALL)
    for i, match in enumerate(align_pattern.finditer(content)):
        placeholder = f"ALIGN_{i}"
        align_content = match.group(1).strip()
        # Split by newline or \\ to get individual equations
        equations = re.split(r'\\\\|\n', align_content)
        equations = [eq.strip() for eq in equations if eq.strip()]
        
        # Format each equation
        formatted_equations = []
        for eq in equations:
            # Remove alignment markers
            eq = re.sub(r'&', '', eq)
            formatted_equations.append(f"FORMULA: {eq}")
        
        # Join with newlines
        math_placeholders[placeholder] = "SISTEMA DE EQUAÇÕES:\n" + "\n".join(formatted_equations)
        content = content.replace(match.group(0), placeholder)
    
    # Handle center environments (for images) before removing LaTeX commands
    content = re.sub(r'\\begin\{center\}(.*?)\\end\{center\}', r'\1', content, flags=re.DOTALL)
    
    # Handle includegraphics before removing LaTeX commands
    content = re.sub(r'\\includegraphics(\[.*?\])?\{(.*?)\}', r'[IMAGEM: \2]', content)
    
    # Remove other common LaTeX commands (simplistic) but preserve the content
    # This regex tries to match commands like \textbf{text} or \command[opt]{arg} or \command*
    # It's not perfect and might be too greedy or not greedy enough for some cases.
    content = re.sub(r'\\([a-zA-Z@]+)(\*|\[[^\]]*\])?\{(.*?)\}', r'\3', content)
    
    # Remove commands without arguments
    content = re.sub(r'\\[a-zA-Z@]+(\*|\[[^\]]*\])?(?!\{)', '', content)
    
    # Remove leftover empty braces that might result from command stripping
    content = re.sub(r'\{\s*\}', '', content) # Handles {} or { }

    # Normalize newlines and clean up:
    # 1. Split into lines.
    # 2. Strip whitespace from each line.
    # 3. Filter out any lines that became empty after stripping.
    # 4. Join them back with a single newline.
    lines = [line.strip() for line in content.splitlines()]
    content = '\n'.join([line for line in lines if line]) # Keep only non-empty lines

    # Final strip to remove any leading/trailing newlines created by the process
    content = content.strip()

    # Remove leading braces and whitespace at the start of the content (fixes stray '{' at start)
    content = re.sub(r'^[{]+', '', content).lstrip()
    
    # Restore mathematical content
    for placeholder, math_content in math_placeholders.items():
        content = content.replace(placeholder, math_content)

    return content


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
    """Parses a LaTeX Beamer file or PDF file and extracts slides, including \section as slides."""
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

    # --- NEW: Find all \section and frame occurrences with their positions ---
    # Pattern for \section{...}
    section_pattern = re.compile(r'\\section\{(.*?)\}', re.DOTALL)
    # Patterns for frames
    frame_patterns = [
        re.compile(r'\\begin\{frame\}(.*?)\\end\{frame\}', re.DOTALL),
        re.compile(r'\\begin\{frame\}\[(.*?)\](.*?)\\end\{frame\}', re.DOTALL),
        re.compile(r'(?<!title)\\frame\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', re.DOTALL),
        re.compile(r'\\begin\{frame\}\{(.*?)\}(.*?)\\end\{frame\}', re.DOTALL),
    ]

    # Find all \section occurrences
    section_matches_raw = [(m.start(), m.group(1).strip()) for m in section_pattern.finditer(latex_content)]

    # Find all frame occurrences. Store them with details.
    # Each item: {'start': int, 'end': int, 'direct_title': Optional[str], 'full_block_content': str}
    # 'full_block_content' is everything between \begin{frame} and \end{frame} or \frame{...}
    
    frames_detailed = []
    processed_ranges = set() # To avoid processing same content block twice if matched by multiple regexes

    # Pattern for \begin{frame}[options]{TITLE} body \end{frame} or \begin{frame}{TITLE} body \end{frame}
    # Group 1: Optional frame options like [fragile] - can be None
    # Group 2: Direct title given in braces (e.g., {My Actual Title}) - captures "My Actual Title"
    # Group 3: The actual body content of the frame
    pat_begin_frame_with_title = re.compile(r'\\begin\{frame\}\s*(\[.*?\])?\s*\{(.*?)\}(.*?)\\end\{frame\}', re.DOTALL)
    for m in pat_begin_frame_with_title.finditer(latex_content):
        if m.start() in processed_ranges: continue
        frames_detailed.append({
            'start': m.start(), 'end': m.end(),
            'direct_title': m.group(2).strip(), # Title is from {TITLE}
            'full_block_content': m.group(3).strip() # Body is the rest
        })
        processed_ranges.add(m.start())

    # Pattern for \begin{frame}[options] body \end{frame} or \begin{frame} body \end{frame} (no direct title in {} after \begin{frame})
    # Group 1: Optional frame options like [fragile] - can be None
    # Group 2: The entire body content of the frame (may contain \frametitle)
    pat_begin_frame_no_title = re.compile(r'\\begin\{frame\}\s*(\[.*?\])?(.*?)(\\end\{frame\})', re.DOTALL)
    for m in pat_begin_frame_no_title.finditer(latex_content):
        if m.start() in processed_ranges: continue
        frames_detailed.append({
            'start': m.start(), 'end': m.end(),
            'direct_title': None,
            'full_block_content': m.group(2).strip() # Entire content, \frametitle to be extracted later
        })
        processed_ranges.add(m.start())

    # Pattern for simple \frame{body} (everything inside braces is the body)
    # We need to handle nested braces properly to capture the entire frame content
    pat_simple_frame = re.compile(r'(?<!\\frametitle)(?<!\\begin\{frame\})\\frame\{', re.DOTALL)
    for m in pat_simple_frame.finditer(latex_content):
        if m.start() in processed_ranges:
            continue
        
        # Find the matching closing brace, accounting for nested braces
        start_pos = m.end()  # Position after \frame{
        brace_count = 1
        end_pos = start_pos
        
        while end_pos < len(latex_content) and brace_count > 0:
            if latex_content[end_pos] == '{':
                brace_count += 1
            elif latex_content[end_pos] == '}':
                brace_count -= 1
            end_pos += 1
        
        if brace_count == 0:  # Found matching closing brace
            # Get the full content of the frame
            frame_content = latex_content[start_pos:end_pos-1].strip()
            
            # Check if this is a frame with math content
            if '$$' in frame_content:
                # This is a frame with math content, make sure we capture it properly
                logging.info(f"Found frame with math content at position {m.start()}")
            
            frames_detailed.append({
                'start': m.start(), 'end': end_pos,
                'direct_title': None, 
                'full_block_content': frame_content
            })
            processed_ranges.add(m.start())
        
    # Additional pattern for \frame{\frametitle{title} content} format
    # We need to handle nested braces properly
    pat_frame_with_frametitle = re.compile(r'\\frame\{\\frametitle\{', re.DOTALL)
    for m in pat_frame_with_frametitle.finditer(latex_content):
        if m.start() in processed_ranges:
            continue
        
        # Find the matching closing brace for the title
        title_start = m.end()  # Position after \frame{\frametitle{
        brace_count = 1
        title_end = title_start
        
        while title_end < len(latex_content) and brace_count > 0:
            if latex_content[title_end] == '{':
                brace_count += 1
            elif latex_content[title_end] == '}':
                brace_count -= 1
            title_end += 1
        
        if brace_count == 0:  # Found matching closing brace for title
            title = latex_content[title_start:title_end-1].strip()
            
            # Now find the matching closing brace for the frame
            content_start = title_end
            brace_count = 1  # We're already inside one level of braces
            content_end = content_start
            
            while content_end < len(latex_content) and brace_count > 0:
                if latex_content[content_end] == '{':
                    brace_count += 1
                elif latex_content[content_end] == '}':
                    brace_count -= 1
                content_end += 1
            
            if brace_count == 0:  # Found matching closing brace for frame
                content = latex_content[content_start:content_end-1].strip()
                
                frames_detailed.append({
                    'start': m.start(), 'end': content_end,
                    'direct_title': title,  # Title is from \frametitle{title}
                    'full_block_content': content  # Content is everything after \frametitle{title}
                })
                processed_ranges.add(m.start())
        
    # Combine sections and frames, then sort by start position
    all_slide_elements = []
    for start_pos, title_text in section_matches_raw:
        all_slide_elements.append({'type': 'section', 'start': start_pos, 'title': title_text})
    for frame_data in frames_detailed:
        # Add 'type' to frame_data for consistent structure with sections
        frame_data['type'] = 'frame'
        all_slide_elements.append(frame_data)
    
    all_slide_elements.sort(key=lambda x: x['start'])

    # Extract document title and author for use in slides
    title_match = re.search(r'\\title\{(.*?)\}', latex_content, re.DOTALL)
    doc_title = title_match.group(1).strip() if title_match else "Presentation Title"
    author_match = re.search(r'\\author\{(.*?)\}', latex_content, re.DOTALL)
    doc_author = author_match.group(1).strip() if author_match else ""

    # Get the number of pages in the PDF
    source_dir = os.path.dirname(os.path.abspath(file_path))
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    pdf_path_source = os.path.join(source_dir, base_name + '.pdf')
    pdf_path_output = os.path.join('output', 'temp_pdf', base_name + '.pdf')
    pdf_page_count = 0  # Initialize to 0

    try:
        if os.path.exists(pdf_path_source):
            logging.info(f"Found PDF in source directory: {pdf_path_source}")
            result = subprocess.run(['pdfinfo', pdf_path_source], capture_output=True, text=True, check=True)
            match = re.search(r'Pages:\s+(\d+)', result.stdout)
            if match:
                pdf_page_count = int(match.group(1))
                logging.info(f"PDF in source directory has {pdf_page_count} pages")
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

    # If we still don't have a page count, estimate from number of slides
    if pdf_page_count == 0:
        # Use all_slide_elements as this is before filtering for title/toc pages
        estimated_page_count = len(all_slide_elements) + 2 # +2 for manually added title/outline
        logging.warning(f"Could not determine PDF page count from file. Estimating {estimated_page_count} pages based on {len(all_slide_elements)} raw elements plus title and outline.")
        pdf_page_count = estimated_page_count

    # --- Build slides ---
    parsed_slides: List[Slide] = []

    # Filtrar slides duplicados de capa e sumário
    def is_title_or_outline(title: str) -> bool:
        if not title:
            return False
        t = title.strip().lower()
        if t in ["title page", "outline"]:
            return True
        if doc_title and t == doc_title.strip().lower():
            return True
        return False

    # Filter out unwanted slides (e.g., \titlepage frames if we add title manually)
    # and prepare final list of elements to become slides.
    final_slide_elements = []
    for element in all_slide_elements:
        if element['type'] == 'section':
            section_title = element['title']
            if is_title_or_outline(section_title):
                logging.info(f"Filtering out section with title: '{section_title}' (is_title_or_outline)")
                continue
            final_slide_elements.append(element)
        
        elif element['type'] == 'frame':
            direct_title = element.get('direct_title')
            full_block_content = element.get('full_block_content', '')

            current_frame_title = direct_title
            if current_frame_title:
                # If the direct_title starts with a brace, fallback to extract_frame_title for robust extraction
                if current_frame_title.strip().startswith("{"):
                    current_frame_title = extract_frame_title(full_block_content)
            else:
                current_frame_title = extract_frame_title(full_block_content)

            # Always strip all leading/trailing braces and whitespace from the title
            current_frame_title = re.sub(r'^[{]+', '', current_frame_title)
            current_frame_title = re.sub(r'[}]+$', '', current_frame_title)
            current_frame_title = current_frame_title.strip()
            # Normalize common outline/title page cases
            if "outline" in current_frame_title.lower():
                current_frame_title = "Outline"
            if "title page" in current_frame_title.lower() or "titlepage" in current_frame_title.lower():
                current_frame_title = "Title Page"

            # Cleaned content for filtering and slide body
            slide_body_cleaned = clean_latex_content(full_block_content)

            # Filter out frames that are empty after cleaning, unless they are Outline or Title Page
            if not slide_body_cleaned.strip() and current_frame_title not in ["Outline", "Title Page"]:
                logging.info(f"Filtering out empty frame at pos {element['start']} with title '{current_frame_title}'")
                continue

            # Avoid duplicate Outline/Title Page slides
            if current_frame_title in ["Outline", "Title Page"]:
                # Only add if not already present in final_slide_elements
                if any(e.get('final_title') == current_frame_title for e in final_slide_elements):
                    continue

            element['final_title'] = current_frame_title
            element['final_body'] = slide_body_cleaned
            final_slide_elements.append(element)

    # --- Consolidation of consecutive frames with the same title has been removed to ensure each frame is a separate slide ---
    # (No consolidation: final_slide_elements is used as-is)

    # Decide if we need to add manual "Title Page" and "Outline" slides
    has_title_page = any(
        el['type'] == 'frame' and (
            (el.get('final_title', '').strip().lower() == 'title page') or
            (el.get('final_title', '').strip().lower() == doc_title.strip().lower()) or
            (re.sub(r'\\frametitle\{.*?\}', '', el.get('full_block_content', ''), flags=re.DOTALL).strip().lower() == '\\titlepage')
        )
        for el in final_slide_elements
    )
    has_outline = any(
        el['type'] == 'frame' and (
            (el.get('final_title', '').strip().lower() == 'outline') or
            (re.sub(r'\\frametitle\{.*?\}', '', el.get('full_block_content', ''), flags=re.DOTALL).strip().lower() == '\\tableofcontents')
        )
        for el in final_slide_elements
    )

    parsed_slides = []
    frame_number = 1

    # Reorder slides so Title Page is always first, Outline second (if present)
    # Find and remove Title Page and Outline from final_slide_elements if present
    title_page_idx = next((i for i, el in enumerate(final_slide_elements)
                           if el.get('final_title', '').strip().lower() == 'title page'), None)
    outline_idx = next((i for i, el in enumerate(final_slide_elements)
                        if el.get('final_title', '').strip().lower() == 'outline'), None)

    title_page_el = final_slide_elements.pop(title_page_idx) if title_page_idx is not None else None
    # If we removed title_page, outline_idx may have shifted
    if outline_idx is not None:
        if title_page_idx is not None and outline_idx > title_page_idx:
            outline_idx -= 1
        outline_el = final_slide_elements.pop(outline_idx) if outline_idx is not None else None
    else:
        outline_el = None

    # Add Title Page first (manual or from LaTeX)
    if title_page_el:
        # Always include the presentation title and author in the Title Page content
        title_page_content = f"Título da Apresentação: {doc_title}"
        if doc_author:
            title_page_content += f"\nAutor: {doc_author}"
        parsed_slides.append(Slide(
            frame_number=frame_number,
            title=title_page_el['final_title'],
            content=title_page_content,
            slide_type="frame"
        ))
        frame_number += 1
    elif not has_title_page:
        title_page_content = f"Título da Apresentação: {doc_title}"
        if doc_author:
            title_page_content += f"\nAutor: {doc_author}"
        parsed_slides.append(Slide(
            frame_number=frame_number,
            title="Title Page",
            content=title_page_content,
            slide_type="frame"
        ))
        frame_number += 1

    # Add Outline second (manual or from LaTeX)
    if outline_el:
        parsed_slides.append(Slide(
            frame_number=frame_number,
            title=outline_el['final_title'],
            content=outline_el['final_body'],
            slide_type="frame"
        ))
        frame_number += 1
    elif not has_outline:
        parsed_slides.append(Slide(
            frame_number=frame_number,
            title="Outline",
            content="This slide shows the outline of the presentation.",
            slide_type="frame"
        ))
        frame_number += 1

    # Add all remaining slides (section and frame), in order of appearance
    for element in final_slide_elements:
        slide_type = element['type']
        if slide_type == 'section':
            section_title = element['title'].strip()
            parsed_slides.append(Slide(
                frame_number=frame_number,
                title=section_title,
                content=section_title,
                slide_type="section"
            ))
        elif slide_type == 'frame':
            frame_title_to_use = element['final_title']
            frame_body_to_use = element['final_body']
            parsed_slides.append(Slide(
                frame_number=frame_number,
                title=frame_title_to_use,
                content=frame_body_to_use,
                slide_type="frame"
            ))
        frame_number += 1

    logging.info(f"Successfully parsed {len(parsed_slides)} slides from LaTeX content (including sections as slides). PDF page count was {pdf_page_count} for reference.")
    return parsed_slides

if __name__ == '__main__':
    # Example usage:
    sample_file = '../assets/presentation.tex' # Adjust path if running directly
    parsed_slides = parse_latex_file(sample_file)
    for slide in parsed_slides:
        print(f"--- Slide {slide.frame_number}: {slide.title} ---")
        print(slide.content)
        print("-" * (len(slide.title) + 14))
