#!/usr/bin/env python3
import unittest
import sys
import os
import re

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.narration_generator import latex_math_to_speakable_text_pt, MATH_SPEAK_MAP_PT

class TestNarrationGenerator(unittest.TestCase):
    """Test cases for the narration generator module."""
    
    def test_latex_delimiters_removal(self):
        """Test that LaTeX delimiters are properly removed."""
        test_cases = [
            # Test case format: (input, expected_output)
            ("$x + y$", "x mais ipsilon"),
            ("$$\\frac{a}{b}$$", "a fração com numerador a e denominador b"),
            ("\\(\\alpha + \\beta\\)", "alfa mais beta"),
            ("\\[x^2 + y^2\\]", "x elevado a 2 mais ipsilon elevado a 2"),
            ("f(x y) = x^2 + y^2", "f de x e ipsilon igual a x elevado a 2 mais ipsilon elevado a 2"),
        ]
        
        for latex, expected in test_cases:
            result = latex_math_to_speakable_text_pt(latex)
            self.assertNotIn("$", result, f"Dollar sign found in: {result}")
            self.assertNotIn("\\(", result, f"\\( found in: {result}")
            self.assertNotIn("\\)", result, f"\\) found in: {result}")
            self.assertNotIn("\\[", result, f"\\[ found in: {result}")
            self.assertNotIn("\\]", result, f"\\] found in: {result}")
            self.assertEqual(result, expected, f"Expected '{expected}', got '{result}'")
    
    def test_greek_letters_conversion(self):
        """Test that Greek letters are properly converted to Portuguese pronunciation."""
        # Test a sample of Greek letters
        test_cases = [
            ("$\\alpha$", "alfa"),
            ("$\\beta$", "beta"),
            ("$\\gamma$", "gama"),
            ("$\\delta$", "delta"),
            ("$\\Gamma$", "Gama"),
            ("$\\Delta$", "Delta"),
            ("$\\Omega$", "Ômega"),
            ("$\\omega$", "ômega"),
            ("$\\theta$", "teta"),
            ("$\\phi$", "fi"),
        ]
        
        for latex, expected in test_cases:
            result = latex_math_to_speakable_text_pt(latex)
            self.assertEqual(result, expected, f"Expected '{expected}', got '{result}'")
    
    def test_math_operators_conversion(self):
        """Test that mathematical operators are properly converted."""
        test_cases = [
            ("$x + y$", "x mais ipsilon"),
            ("$x - y$", "x menos ipsilon"),
            ("$x * y$", "x vezes ipsilon"),
            ("$x / y$", "x dividido por ipsilon"),
            ("$x = y$", "x igual a ipsilon"),
            ("$x > y$", "x maior que ipsilon"),
            ("$x < y$", "x menor que ipsilon"),
            ("$x \\leq y$", "x menor ou igual a ipsilon"),
            ("$x \\geq y$", "x maior ou igual a ipsilon"),
            ("$x \\neq y$", "x diferente de ipsilon"),
            ("$x \\approx y$", "x aproximadamente igual a ipsilon"),
        ]
        
        for latex, expected in test_cases:
            result = latex_math_to_speakable_text_pt(latex)
            self.assertEqual(result, expected, f"Expected '{expected}', got '{result}'")
    
    def test_complex_math_expressions(self):
        """Test that complex mathematical expressions are properly converted."""
        test_cases = [
            ("$\\frac{x}{y}$", "a fração com numerador x e denominador ipsilon"),
            ("$x^2$", "x elevado a 2"),
            ("$x_i$", "x índice i"),
            ("$f(x y)$", "f de x e ipsilon"),
            ("$\\sum_{i=1}^{n} x_i$", "o somatório índice i igual a 1 elevado a n x índice i"),
            ("$\\prod_{i=1}^{n} x_i$", "o produtório índice i igual a 1 elevado a n x índice i"),
            ("$\\int_{a}^{b} f(x) dx$", "a integral índice a elevado a b f de x dx"),
            ("$\\nabla f$", "nabla f"),
            ("$\\nabla \\cdot \\vec{F}$", "nabla vezes vec F"),
            ("$\\nabla \\times \\vec{F}$", "nabla vezes vec F"),
        ]
        
        for latex, expected in test_cases:
            result = latex_math_to_speakable_text_pt(latex)
            print(f"Input: {latex}")
            print(f"Result: {result}")
            print(f"Expected: {expected}")
            print("---")
        
        for latex, expected in test_cases:
            result = latex_math_to_speakable_text_pt(latex)
            self.assertEqual(result, expected, f"Expected '{expected}', got '{result}'")
    
    def test_no_spurious_characters(self):
        """Test that no spurious LaTeX characters remain in the output."""
        # List of LaTeX commands and delimiters that should not appear in the output
        spurious_patterns = [
            r'\$',              # Dollar sign
            r'\\[\(\)\[\]]',    # \(, \), \[, \]
            r'\\begin\{.*?\}',  # \begin{...}
            r'\\end\{.*?\}',    # \end{...}
            r'\\[a-zA-Z]+',     # Any LaTeX command
            r'&',               # Alignment character
            r'\\\\',            # Line break in align environment
            r'_(?!\w)',         # Underscore not followed by a word character
            r'\^(?!\w)',        # Caret not followed by a word character
            r'\{',              # Opening curly brace
            r'\}',              # Closing curly brace
        ]
        
        # Test with a variety of complex LaTeX expressions
        test_inputs = [
            "$\\int_{0}^{\\infty} e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}$",
            "$$\\sum_{n=1}^{\\infty} \\frac{1}{n^2} = \\frac{\\pi^2}{6}$$",
            "\\begin{align} E &= mc^2 \\\\ F &= ma \\end{align}",
            "$\\nabla \\times \\vec{E} = -\\frac{\\partial \\vec{B}}{\\partial t}$",
            "$\\nabla \\cdot \\vec{E} = \\frac{\\rho}{\\epsilon_0}$",
            "$\\prod_{i=1}^{n} (x_i + y_i) = \\sum_{k=0}^{n} \\sum_{1 \\leq i_1 < i_2 < \\ldots < i_k \\leq n} \\prod_{j=1}^{k} x_{i_j} \\prod_{l \\in \\{1, 2, \\ldots, n\\} \\setminus \\{i_1, i_2, \\ldots, i_k\\}} y_l$",
        ]
        
        for latex in test_inputs:
            result = latex_math_to_speakable_text_pt(latex)
            print(f"Input: {latex}")
            print(f"Result: {result}")
            for pattern in spurious_patterns:
                matches = re.findall(pattern, result)
                if len(matches) > 0:
                    print(f"Spurious pattern '{pattern}' found in result: {matches}")
                self.assertEqual(len(matches), 0, f"Spurious pattern '{pattern}' found in result: {matches}")
    
    def test_y_to_ipsilon_conversion(self):
        """Test that 'y' is properly converted to 'ipsilon'."""
        test_cases = [
            ("$y$", "ipsilon"),
            ("$x + y$", "x mais ipsilon"),
            ("$f(x, y)$", "f de x e ipsilon"),
            ("$y^2$", "ipsilon elevado a 2"),
            ("$y_i$", "ipsilon índice i"),
            ("$\\frac{x}{y}$", "a fração com numerador x e denominador ipsilon"),
        ]
        
        for latex, expected in test_cases:
            result = latex_math_to_speakable_text_pt(latex)
            self.assertEqual(result, expected, f"Expected '{expected}', got '{result}'")
            # Ensure 'y' is not present as a standalone word
            self.assertNotRegex(result, r'\by\b', f"Standalone 'y' found in: {result}")
    
    def test_all_math_symbols_have_translations(self):
        """Test that all math symbols in MATH_SPEAK_MAP_PT have valid translations."""
        for latex, spoken in MATH_SPEAK_MAP_PT.items():
            # Ensure the spoken form doesn't contain LaTeX commands
            self.assertNotRegex(spoken, r'\\[a-zA-Z]+', f"LaTeX command found in spoken form: {spoken}")
            # Ensure the spoken form is not empty
            self.assertTrue(spoken, f"Empty spoken form for LaTeX command: {latex}")

if __name__ == '__main__':
    unittest.main()
