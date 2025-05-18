#!/usr/bin/env python3
import sys
import os
from src.chatgpt_script_generator import clean_chatgpt_response

def test_clean_latex_control_characters():
    """Test that LaTeX control characters are properly removed from ChatGPT responses."""
    
    # Test case with various LaTeX control characters
    test_input = """
    Neste exemplo, vamos explorar como maximizar a área de um retângulo quando o perímetro é fixo. 
    Primeiro, olhemos para a definição do problema. Queremos maximizar a função \( f(x, y) = xy \), que representa a área do retângulo. O objetivo é encontrar os valores de \( x \) e \( y \) que maximizam a área dada uma restrição importante: o perímetro do retângulo. Esta restrição é expressa pela equação \( g(x, y) = 2x + 2y = P \), onde \( P \) é o perímetro fixo do retângulo.
    Para resolver este problema de otimização com restrição, usamos a Função Lagrangiana. A Função Lagrangiana é uma técnica que nos ajuda a encontrar pontos de máximo ou mínimo de uma função sujeita a restrições. 
    A Função Lagrangiana para este problema é definida como \( L(x, y, \lambda) = xy - \lambda(2x + 2y - P) \). Aqui, \( \lambda \) é o multiplicador de Lagrange, uma variável adicional que nos ajuda a incorporar a restrição diretamente na função que estamos maximizando. 
    Ao resolver a Lagrangiana, buscamos os valores de \( x \), \( y \) e \( \lambda \) que maximizam ou minimizam a função sob a restrição dada. Assim, conseguimos encontrar a configuração ideal do retângulo que maximiza a área enquanto mantém o perímetro fixo.
    """
    
    # Clean the response
    cleaned = clean_chatgpt_response(test_input)
    
    # Check for LaTeX control characters
    latex_control_chars = [
        r'\(', r'\)', r'\[', r'\]',  # Math delimiters
        r'\lambda', r'\alpha', r'\beta',  # Greek letters
        r'\frac', r'\sum', r'\int',  # Math operators
        r'\{', r'\}', r'\,', r'\;'  # Special characters
    ]
    
    print("Original text:")
    print(test_input)
    print("\nCleaned text:")
    print(cleaned)
    
    print("\nChecking for LaTeX control characters:")
    all_removed = True
    for char in latex_control_chars:
        if char in cleaned:
            print(f"FAIL: '{char}' still present in cleaned text")
            all_removed = False
    
    if all_removed:
        print("SUCCESS: All LaTeX control characters were removed")
    
    # Check for specific patterns in the example
    patterns_to_check = [
        (r'\( f(x, y) = xy \)', 'f(x, y) = xy'),
        (r'\( g(x, y) = 2x + 2y = P \)', 'g(x, y) = 2x + 2y = P'),
        (r'\( L(x, y, \lambda) = xy - \lambda(2x + 2y - P) \)', 'L(x, y, ) = xy - (2x + 2y - P)'),
        (r'\( x \)', 'x'),
        (r'\( y \)', 'y'),
        (r'\( \lambda \)', '')
    ]
    
    print("\nChecking specific patterns:")
    for original, expected in patterns_to_check:
        if original in test_input:
            replacement = original.replace(original, expected)
            if expected not in cleaned and original in cleaned:
                print(f"FAIL: '{original}' was not properly replaced")
            else:
                print(f"SUCCESS: '{original}' was properly handled")

if __name__ == "__main__":
    test_clean_latex_control_characters()
