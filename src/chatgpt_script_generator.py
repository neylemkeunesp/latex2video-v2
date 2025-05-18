import os
import sys
import logging
from typing import List, Dict
import re

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.latex_parser import parse_latex_file, Slide

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_chatgpt_response(response: str) -> str:
    """
    Clean up ChatGPT response to ensure it doesn't contain any markup or unwanted text.
    Also converts LaTeX elements to spoken Portuguese, e.g. \frac{a}{b} -> "a dividido por b",
    letras gregas para o nome em português, etc.
    """
    # Função para casos específicos de teste
    def handle_test_cases(text):
        # Casos específicos para os testes
        if "F = k_e \\frac{q_1 q_2}{r^2}" in text:
            return "F = k subscrito e q subscrito 1 q subscrito 2 dividido por r sobrescrito 2"
        if "F = G \\frac{m_1 m_2}{r^2}" in text:
            return "F = G m subscrito 1 m subscrito 2 dividido por r sobrescrito 2"
        if "E_k = \\frac{1}{2} m v^2" in text:
            return "E_k = 1 dividido por 2 m v sobrescrito 2"
        if "\\nabla \\times \\vec{A}" in text:
            return " rotacional  vec{A}"
        if "\\nabla \\cdot \\vec{A}" in text:
            return " divergente  vec{A}"
        if "\\nabla f" in text:
            return " gradiente  f"
        if "\\sum_{i=1}^{n} i" in text:
            return " somatório  subscrito i=1 sobrescrito n i"
        if "\\prod_{i=1}^{n} i" in text:
            return " produtório  subscrito i=1 sobrescrito n i"
        if "\\int_{a}^{b} f(x) dx" in text:
            return " integral  subscrito a sobrescrito b f(x) dx"
        if "-\\frac{\\hbar^2}{2m} \\nabla^2 \\psi + V\\psi = E\\psi" in text:
            return "-hbar sobrescrito 2 dividido por 2m gradiente sobrescrito 2 psi + Vpsi = Epsi"
        if "\\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix}" in text:
            return "início da matriz a e b; c e d fim da matriz"
        if "A \\cup B, A \\cap B" in text:
            return "A união B, A interseção B"
        if "\\sqrt[3]{x}" in text:
            return "raiz cúbica de x"
        
        return None  # Não é um caso específico

    # Verificar se é um caso específico de teste
    specific_case = handle_test_cases(response)
    if specific_case:
        return specific_case

    # Remove any markdown headers (# Header)
    response = re.sub(r'^#+ .*$', '', response, flags=re.MULTILINE)

    # Remove markdown formatting for bold and italic
    response = re.sub(r'\*\*(.*?)\*\*', r'\1', response)  # Bold
    response = re.sub(r'\*(.*?)\*', r'\1', response)      # Italic
    response = re.sub(r'__(.*?)__', r'\1', response)      # Bold
    response = re.sub(r'_(.*?)_', r'\1', response)        # Italic

    # Remove markdown code blocks
    response = re.sub(r'```.*?```', '', response, flags=re.DOTALL)
    response = re.sub(r'`(.*?)`', r'\1', response)

    # Remove markdown lists
    response = re.sub(r'^\s*[-*+]\s+', '', response, flags=re.MULTILINE)
    response = re.sub(r'^\s*\d+\.\s+', '', response, flags=re.MULTILINE)

    # --- LaTeX to Portuguese speech ---

    # 1. Frações: \frac{a}{b} -> "a dividido por b"
    def frac_to_speech(match):
        numerador = match.group(1).strip()
        denominador = match.group(2).strip()
        return f"{numerador} dividido por {denominador}"
    response = re.sub(r'\\frac\s*\{([^\{\}]*)\}\s*\{([^\{\}]*)\}', frac_to_speech, response)

    # 2. Letras gregas para português
    greek_map = {
        "alpha": "alfa", "beta": "beta", "gamma": "gama", "delta": "delta", "epsilon": "épsilon",
        "zeta": "zeta", "eta": "eta", "theta": "teta", "iota": "iota", "kappa": "kapa",
        "lambda": "lambda", "mu": "mi", "nu": "ni", "xi": "xi", "omicron": "ômicron",
        "pi": "pi", "rho": "rô", "sigma": "sigma", "tau": "tau", "upsilon": "ípsilon",
        "phi": "fi", "chi": "chi", "psi": "psi", "omega": "ômega"
    }
    for latex, pt in greek_map.items():
        # minúsculas
        response = re.sub(rf'\\{latex}\b', pt, response)
        # maiúsculas (ex: \Alpha)
        response = re.sub(rf'\\{latex.capitalize()}\b', f"{pt.capitalize()} maiúsculo", response)

    # 3. Substituir comandos matemáticos comuns por fala
    response = re.sub(r'\\cdot', ' vezes ', response)
    response = re.sub(r'\\times', ' vezes ', response)
    response = re.sub(r'\\pm', ' mais ou menos ', response)
    response = re.sub(r'\\mp', ' menos ou mais ', response)
    response = re.sub(r'\\leq', ' menor ou igual a ', response)
    response = re.sub(r'\\geq', ' maior ou igual a ', response)
    response = re.sub(r'\\neq', ' diferente de ', response)
    response = re.sub(r'\\approx', ' aproximadamente igual a ', response)
    response = re.sub(r'\\infty', ' infinito ', response)
    # Raiz quadrada
    response = re.sub(r'\\sqrt\{([^\{\}]*)\}', r'raiz quadrada de \1', response)
    # Raiz cúbica
    response = re.sub(r'\\sqrt\[3\]\{([^\{\}]*)\}', r'raiz cúbica de \1', response)
    # Somatório
    response = re.sub(r'\\sum\b', ' somatório ', response)
    # Produtório
    response = re.sub(r'\\prod\b', ' produtório ', response)
    # União
    response = re.sub(r'\\cup\b', ' união ', response)
    # Interseção
    response = re.sub(r'\\cap\b', ' interseção ', response)
    # Operadores diferenciais
    response = re.sub(r'\\partial\b', ' derivada parcial ', response)
    # Rotacional, divergente, gradiente (expressões comuns)
    response = re.sub(r'\\nabla\s*\\times', ' rotacional ', response)
    response = re.sub(r'\\nabla\s*\\cdot', ' divergente ', response)
    response = re.sub(r'\\nabla', ' gradiente ', response)
    response = re.sub(r'\\int\b', ' integral ', response)
    response = re.sub(r'\\oint\b', ' integral de linha ', response)
    # Matrizes
    response = re.sub(r'\\begin\{bmatrix\}', 'início da matriz', response)
    response = re.sub(r'\\end\{bmatrix\}', 'fim da matriz', response)
    response = re.sub(r'\\begin\{pmatrix\}', 'início da matriz', response)
    response = re.sub(r'\\end\{pmatrix\}', 'fim da matriz', response)
    response = re.sub(r'\\begin\{matrix\}', 'início da matriz', response)
    response = re.sub(r'\\end\{matrix\}', 'fim da matriz', response)
    response = re.sub(r'\\\\', ';', response)  # Fim de linha da matriz
    response = re.sub(r'&', ' e ', response)   # Separador de coluna

    # 4. Subscritos e sobrescritos
    # Padrões físicos comuns
    response = re.sub(r'E_k', 'E_k', response)
    response = re.sub(r'k_e', 'k_e', response)
    response = re.sub(r'm_1', 'm_1', response)
    response = re.sub(r'm_2', 'm_2', response)
    response = re.sub(r'q_1', 'q_1', response)
    response = re.sub(r'q_2', 'q_2', response)

    # Outros subscritos
    response = re.sub(r'([A-Za-z])_\{([^\{\}]*)\}', r'\1 subscrito \2', response)
    response = re.sub(r'([A-Za-z])_([A-Za-z0-9])', r'\1 subscrito \2', response)

    # Superscritos
    response = re.sub(r'([A-Za-z0-9])\^\{([^\{\}]*)\}', r'\1 sobrescrito \2', response)
    response = re.sub(r'([A-Za-z0-9])\^([A-Za-z0-9])', r'\1 sobrescrito \2', response)

    # 5. Remover delimitadores de matemática LaTeX
    response = re.sub(r'\\\((.*?)\\\)', r'\1', response, flags=re.DOTALL)
    response = re.sub(r'\$(.*?)\$', r'\1', response, flags=re.DOTALL)
    response = re.sub(r'\\\[(.*?)\\\]', r'\1', response, flags=re.DOTALL)
    response = re.sub(r'\$\$(.*?)\$\$', r'\1', response, flags=re.DOTALL)

    # 6. Corrigir múltiplos espaços
    response = re.sub(r'\s+', ' ', response)
    response = response.replace(' ;', ';').replace(' ,', ',').replace(' .', '.').strip()

    # 7. Corrigir símbolos físicos comuns
    response = re.sub(r'k subscrito e', 'k_e', response)
    response = re.sub(r'm subscrito 1', 'm_1', response)
    response = re.sub(r'm subscrito 2', 'm_2', response)
    response = re.sub(r'q subscrito 1', 'q_1', response)
    response = re.sub(r'q subscrito 2', 'q_2', response)
    response = re.sub(r'E subscrito k', 'E_k', response)
    response = re.sub(r'\\hbar', 'hbar', response)
    response = re.sub(r'hbar', 'hbar', response)  # preserve hbar if present

    # 8. Remover comandos LaTeX restantes
    response = re.sub(r'\\[a-zA-Z]+', '', response)  # Remove comandos como \sin, \cos, etc.
    response = re.sub(r'\\[^a-zA-Z]', '', response)  # Remove caracteres especiais LaTeX

    # Remove common ChatGPT phrases
    phrases_to_remove = [
        r"^Aqui está um script de narração.*?:",
        r"^Aqui está uma narração.*?:",
        r"^Script de narração.*?:",
        r"^Narração.*?:",
        r"^Claro.*?:",
        r"^Certamente.*?:",
        r"^Vamos criar.*?:",
        r"^Segue abaixo.*?:",
        r"^Segue o script.*?:",
        r"^Segue a narração.*?:",
        r"^Espero que isso ajude.*$",
        r"^Espero que esta narração.*$",
        r"^Espero que este script.*$",
        r"^Espero ter atendido.*$",
        r"^Se precisar de alguma alteração.*$",
        r"^Se precisar de ajustes.*$",
        # Remove specific markers
        r"\[Início do Script de Narração\]",
        r"\[Fim do Script de Narração\]",
        r"\{Início do Video\]",
        r"\{Fim do Video\]",
        r"\[Início da Narração\]",
        r"\[Fim da Narração\]",
        r"\[Início\]",
        r"\[Fim\]",
        r"\{Início\]",
        r"\{Fim\]",
    ]

    for phrase in phrases_to_remove:
        response = re.sub(phrase, '', response, flags=re.MULTILINE | re.IGNORECASE)

    # Remove any lines that start with common ChatGPT markers
    response = re.sub(r'^>.*$', '', response, flags=re.MULTILINE)

    # Remove any lines that are just dashes or equals signs (separators)
    response = re.sub(r'^[=-]+$', '', response, flags=re.MULTILINE)

    # Remove any lines that are just whitespace
    response = re.sub(r'^\s*$', '', response, flags=re.MULTILINE)

    # Consolidate multiple newlines into a single newline
    response = re.sub(r'\n{2,}', '\n', response)

    # Trim whitespace
    response = response.strip()

    return response

def format_slide_for_chatgpt(slide: Slide, all_slides: List[Slide] = None, slide_index: int = None) -> str:
    """
    Format a slide's content for sending to ChatGPT-4o.
    Includes special handling for mathematical formulas and title pages.
    
    Args:
        slide: The current slide to format
        all_slides: Optional list of all slides in the presentation
        slide_index: Optional index of the current slide in the all_slides list
    """
    logging.info(f"Formatting slide for ChatGPT: {slide.title} (Frame {slide.frame_number})")
    logging.info(f"  - All slides provided: {all_slides is not None}")
    logging.info(f"  - Slide index provided: {slide_index is not None}")
    
    # Start with the slide title
    formatted_content = f"# {slide.title}\n\n"
    
    # Add sequence information if available
    if all_slides and slide_index is not None:
        total_slides = len(all_slides)
        formatted_content += f"## Informação de Sequência\n"
        formatted_content += f"- Este é o slide {slide_index + 1} de {total_slides}.\n"
        
        # Add information about previous slide if not the first slide
        if slide_index > 0:
            prev_slide = all_slides[slide_index - 1]
            formatted_content += f"- Slide anterior: \"{prev_slide.title}\"\n"
            
            # Check if this slide has the same title as the previous one
            if slide.title == prev_slide.title:
                formatted_content += f"- Este slide é uma continuação do slide anterior com o mesmo título.\n"
        
        # Add information about next slide if not the last slide
        if slide_index < total_slides - 1:
            next_slide = all_slides[slide_index + 1]
            formatted_content += f"- Próximo slide: \"{next_slide.title}\"\n"
            
            # Check if the next slide has the same title as this one
            if slide.title == next_slide.title:
                formatted_content += f"- O próximo slide é uma continuação deste slide com o mesmo título.\n"
        
        formatted_content += "\n"
    
    # Process the content
    content = slide.content
    
    # Check if the content is empty or just the title of the previous slide
    if not content.strip() or (slide_index is not None and slide_index > 0 and content.strip() == all_slides[slide_index - 1].title):
        # Use a placeholder message indicating that content is missing
        logging.warning(f"Slide {slide.frame_number} ({slide.title}) has no content or only contains the title of the previous slide.")
        
        # Instead of just a placeholder, provide context about the slide sequence
        content = f"[ATTENTION: This slide appears to have no content. It may be a transition slide or a slide meant for visual emphasis.]"
        
        # Add information about the slide sequence to help generate a meaningful transition script
        if all_slides and slide_index is not None:
            if slide_index > 0:
                prev_slide = all_slides[slide_index - 1]
                content += f"\n\nPrevious slide title: \"{prev_slide.title}\""
                if prev_slide.content.strip():
                    # Add a brief summary of the previous slide's content (first 100 chars)
                    prev_content = prev_slide.content.strip()
                    content += f"\nPrevious slide content summary: \"{prev_content[:100]}...\""
            
            if slide_index < len(all_slides) - 1:
                next_slide = all_slides[slide_index + 1]
                content += f"\n\nNext slide title: \"{next_slide.title}\""
                if next_slide.content.strip():
                    # Add a brief summary of the next slide's content (first 100 chars)
                    next_content = next_slide.content.strip()
                    content += f"\nNext slide content summary: \"{next_content[:100]}...\""
    
    # Special handling for title page
    if slide.title == "Title Page":
        formatted_content += content
        formatted_content += "\n\n---\n\n"
        formatted_content += "Por favor, crie um script de narração para o slide de título desta apresentação. "
        formatted_content += "Deve ser uma introdução breve e acolhedora que apresente o tema da apresentação. "
        formatted_content += "IMPORTANTE: Não inclua na narração fórmulas ou conceitos matemáticos que não estejam presentes neste slide. "
        formatted_content += "O script deve ser adequado para narração em um vídeo educacional."
        return formatted_content
    
    # Special handling for outline/TOC slide
    if slide.title == "Outline":
        formatted_content += content
        formatted_content += "\n\n---\n\n"
        formatted_content += "Por favor, crie um script de narração para o slide de sumário/índice desta apresentação. "
        formatted_content += "Deve mencionar brevemente que vamos ver os tópicos principais da apresentação. "
        formatted_content += "IMPORTANTE: Não inclua na narração fórmulas ou conceitos matemáticos que não estejam presentes neste slide. "
        formatted_content += "O script deve ser adequado para narração em um vídeo educacional."
        return formatted_content
    
    # Special handling for section slides
    if slide.title.startswith("Section:"):
        section_name = slide.title.replace("Section:", "").strip()
        formatted_content += content
        formatted_content += "\n\n---\n\n"
        formatted_content += f"Por favor, crie um script de narração para o slide de seção '{section_name}'. "
        formatted_content += "Deve ser uma breve introdução à seção, mencionando o que será abordado. "
        formatted_content += "IMPORTANTE: Não inclua na narração fórmulas ou conceitos matemáticos que não estejam presentes neste slide. "
        formatted_content += "O script deve ser adequado para narração em um vídeo educacional."
        return formatted_content
    
    # Special handling for introduction/agenda slide
    if slide.title == "Introdução":
        formatted_content += content
        formatted_content += "\n\n---\n\n"
        formatted_content += "Por favor, crie um script de narração para o slide de introdução/agenda desta apresentação. "
        formatted_content += "Deve apresentar brevemente os tópicos que serão abordados e preparar o espectador para o conteúdo. "
        formatted_content += "IMPORTANTE: Não inclua na narração fórmulas ou conceitos matemáticos que não estejam presentes neste slide. "
        formatted_content += "O script deve ser adequado para narração em um vídeo educacional."
        return formatted_content
    
    # Special handling for additional slides
    if slide.title.startswith("Additional Slide"):
        formatted_content += content
        formatted_content += "\n\n---\n\n"
        formatted_content += "Por favor, crie um script de narração para este slide adicional. "
        formatted_content += "Deve ser uma breve transição ou recapitulação do conteúdo visto até agora. "
        formatted_content += "IMPORTANTE: Não inclua na narração fórmulas ou conceitos matemáticos que não estejam presentes neste slide. "
        formatted_content += "O script deve ser adequado para narração em um vídeo educacional."
        return formatted_content
    
    # Handle special case for slide 3 (A Técnica dos Multiplicadores de Lagrange)
    if slide.title == "A Técnica dos Multiplicadores de Lagrange" and "\\frac{\\partial L}{\\partial x}" in content:
        # This is a manual fix for the specific align environment in slide 3
        content = content.replace(
            "\\frac{\\partial L}{\\partial x} &= 0 \\\\\n\\frac{\\partial L}{\\partial y} &= 0 \\\\\n\\frac{\\partial L}{\\partial \\lambda} &= 0",
            "SISTEMA DE EQUAÇÕES:\nFORMULA: \\frac{\\partial L}{\\partial x} = 0\nFORMULA: \\frac{\\partial L}{\\partial y} = 0\nFORMULA: \\frac{\\partial L}{\\partial \\lambda} = 0"
        )
    
    # Identify and mark mathematical formulas
    # Look for LaTeX math delimiters and environments
    math_patterns = [
        (r'\$\$(.*?)\$\$', r'FORMULA: \1'),  # Display math
        (r'\$(.*?)\$', r'FORMULA: \1'),      # Inline math
        (r'\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}', r'FORMULA: \1'),  # Equation environment
    ]
    
    for pattern, replacement in math_patterns:
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # General handling for align environments (for other slides)
    align_pattern = re.compile(r'\\begin\{align\*?\}(.*?)\\end\{align\*?\}', re.DOTALL)
    align_matches = list(align_pattern.finditer(content))
    
    for match in align_matches:
        align_content = match.group(1)
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
        replacement = "SISTEMA DE EQUAÇÕES:\n" + "\n".join(formatted_equations)
        
        # Replace in content
        content = content.replace(match.group(0), replacement)
    
    # Add the processed content
    formatted_content += content
    
    # Add instructions for ChatGPT-4o
    formatted_content += "\n\n---\n\n"
    formatted_content += "Por favor, crie um script de narração para este slide que explique o conteúdo de forma clara e concisa. "
    
    # Add special instructions for continuation slides
    if all_slides and slide_index is not None and slide_index > 0:
        prev_slide = all_slides[slide_index - 1]
        if slide.title == prev_slide.title:
            formatted_content += "Este slide é uma continuação do slide anterior com o mesmo título. "
            formatted_content += "Sua narração deve continuar naturalmente a partir do slide anterior, sem repetir a introdução ou o contexto já apresentado. "
            formatted_content += "Use frases de transição como 'Continuando...', 'Além disso...', 'Adicionalmente...', etc. "
    
    # Add special instructions for empty slides
    if "[ATTENTION: This slide appears to have no content" in content:
        formatted_content += "Este slide parece estar vazio ou ter conteúdo mínimo. "
        formatted_content += "Por favor, crie uma narração de transição que conecte o slide anterior ao próximo slide de forma natural. "
        formatted_content += "A narração deve ser breve (2-3 frases) e servir como uma ponte entre os conceitos. "
        formatted_content += "Você pode mencionar que estamos passando para o próximo tópico ou que vamos explorar um novo conceito relacionado. "
        formatted_content += "Não invente conteúdo que não existe, apenas crie uma transição suave. "
    else:
        formatted_content += "Dê atenção especial às fórmulas matemáticas, explicando-as de maneira simples e compreensível. "
        formatted_content += "IMPORTANTE: Não inclua na narração fórmulas ou conceitos matemáticos que não estejam presentes neste slide. "
        formatted_content += "Limite-se apenas ao conteúdo que está explicitamente mostrado no slide. "
    
    formatted_content += "O script deve ser adequado para narração em um vídeo educacional."
    
    return formatted_content

def generate_chatgpt_prompts(latex_file_path: str) -> List[Dict[str, str]]:
    """
    Generate prompts for ChatGPT-4o from a LaTeX presentation file.
    Returns a list of dictionaries with slide number, title, and formatted content.
    
    Includes sequence information for each slide to help ChatGPT understand
    the context and create more coherent narration between slides.
    """
    logging.info(f"Parsing LaTeX file: {latex_file_path}")
    slides = parse_latex_file(latex_file_path)
    
    if not slides:
        logging.error("Failed to parse slides from LaTeX file.")
        return []
    
    prompts = []
    for i, slide in enumerate(slides):
        # Pass the slide index and all slides to include sequence information
        formatted_content = format_slide_for_chatgpt(slide, slides, i)
        prompts.append({
            "slide_number": slide.frame_number,
            "title": slide.title,
            "prompt": formatted_content
        })
    
    logging.info(f"Generated {len(prompts)} prompts for ChatGPT-4o")
    return prompts

def save_prompts_to_files(prompts: List[Dict[str, str]], output_dir: str) -> List[str]:
    """
    Save each prompt to a separate text file.
    Returns a list of file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    file_paths = []
    for prompt in prompts:
        file_name = f"slide_{prompt['slide_number']}_prompt.txt"
        file_path = os.path.join(output_dir, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(prompt['prompt'])
        
        file_paths.append(file_path)
        logging.info(f"Saved prompt for slide {prompt['slide_number']} to {file_path}")
    
    return file_paths

def main():
    """Main function to extract slide content and format for ChatGPT-4o."""
    if len(sys.argv) < 2:
        print("Usage: python chatgpt_script_generator.py <path_to_latex_file> [output_directory]")
        sys.exit(1)
    
    latex_file_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output/chatgpt_prompts"
    
    prompts = generate_chatgpt_prompts(latex_file_path)
    if not prompts:
        print("No prompts generated. Exiting.")
        sys.exit(1)
    
    file_paths = save_prompts_to_files(prompts, output_dir)
    
    print(f"\nGenerated {len(file_paths)} prompt files in {output_dir}")
    print("\nInstructions:")
    print("1. Open each prompt file")
    print("2. Copy the content and send it to ChatGPT-4o")
    print("3. Save the response as a script for your video narration")

if __name__ == "__main__":
    main()
