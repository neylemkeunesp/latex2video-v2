#!/usr/bin/env python3
import os
import sys
import yaml
from src.latex_parser import parse_latex_file
from src.narration_generator import generate_all_narrations

def validate_narrations(slides, narrations):
    """Validate that all narrations are appropriate for their slides."""
    all_valid = True
    issues = []
    
    if len(slides) != len(narrations):
        issues.append(f"ERROR: Mismatch between slides ({len(slides)}) and narrations ({len(narrations)})")
        all_valid = False
    
    for i, (slide, narration) in enumerate(zip(slides, narrations)):
        # Check if narration is empty
        if not narration.strip():
            issues.append(f"ERROR: Slide {i+1} ({slide.title}) has empty narration")
            all_valid = False
        
        # Check if narration is too short (less than 10 characters)
        elif len(narration) < 10:
            issues.append(f"WARNING: Slide {i+1} ({slide.title}) has very short narration: '{narration}'")
            all_valid = False
        
        # Check for special slides
        if slide.title in ["Title Page", "Titulo"]:
            if "Bem-vindos" not in narration and slide.title not in narration:
                issues.append(f"WARNING: Title slide {i+1} may have inappropriate narration: '{narration}'")
                all_valid = False
        
        if slide.title in ["Outline", "Agenda"]:
            if "tópicos" not in narration and "apresentação" not in narration:
                issues.append(f"WARNING: Agenda slide {i+1} may have inappropriate narration: '{narration}'")
                all_valid = False
    
    return all_valid, issues

def main():
    # Load config
    try:
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        config = {}

    # Parse LaTeX file
    latex_file = 'assets/presentation.tex'
    slides = parse_latex_file(latex_file)
    if not slides:
        print("Failed to parse slides from LaTeX file.")
        return
    
    print(f"Successfully parsed {len(slides)} slides.")
    
    # Print slide titles to check for "Titulo" and "Agenda" slides
    print("\nSlide Titles:")
    for i, slide in enumerate(slides):
        print(f"Slide {i+1}: {slide.title}")
    
    # Generate narrations
    narrations = generate_all_narrations(slides, config)
    if not narrations:
        print("Failed to generate narration scripts.")
        return
    
    print(f"\nSuccessfully generated {len(narrations)} narration scripts.")
    
    # Validate narrations
    valid, issues = validate_narrations(slides, narrations)
    if not valid:
        print("\n⚠️ VALIDATION ISSUES DETECTED:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nPlease fix these issues before starting the recording.")
    else:
        print("\n✅ All narrations validated successfully! Ready for recording.")
    
    # Print narrations to verify our fix
    print("\nNarrations:")
    for i, narration in enumerate(narrations):
        print(f"--- Narration for Slide {i+1} ({slides[i].title}) ---")
        print(narration)
        print("-" * 50)

if __name__ == "__main__":
    main()
