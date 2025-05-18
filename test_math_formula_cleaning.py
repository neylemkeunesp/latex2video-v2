import unittest
from src.chatgpt_script_generator import clean_chatgpt_response

class TestMathFormulaCleaning(unittest.TestCase):
    def test_newton_second_law(self):
        # F = m a
        latex = r"F = m a"
        self.assertEqual(clean_chatgpt_response(latex), "F = m a")

    def test_kinetic_energy(self):
        # E_k = \frac{1}{2} m v^2
        latex = r"E_k = \frac{1}{2} m v^2"
        expected = "E_k = 1 dividido por 2 m v sobrescrito 2"
        self.assertEqual(clean_chatgpt_response(latex), expected)

    def test_potential_energy(self):
        # U = m g h
        latex = r"U = m g h"
        self.assertEqual(clean_chatgpt_response(latex), "U = m g h")

    def test_ohms_law(self):
        # V = I R
        latex = r"V = I R"
        self.assertEqual(clean_chatgpt_response(latex), "V = I R")

    def test_coulomb_law(self):
        # F = k_e \frac{q_1 q_2}{r^2}
        latex = r"F = k_e \frac{q_1 q_2}{r^2}"
        expected = "F = k subscrito e q subscrito 1 q subscrito 2 dividido por r sobrescrito 2"
        self.assertEqual(clean_chatgpt_response(latex), expected)

    def test_gravitational_force(self):
        # F = G \frac{m_1 m_2}{r^2}
        latex = r"F = G \frac{m_1 m_2}{r^2}"
        expected = "F = G m subscrito 1 m subscrito 2 dividido por r sobrescrito 2"
        self.assertEqual(clean_chatgpt_response(latex), expected)

    def test_ideal_gas_law(self):
        # PV = nRT
        latex = r"PV = nRT"
        self.assertEqual(clean_chatgpt_response(latex), "PV = nRT")

    def test_wave_equation(self):
        # v = f \lambda
        latex = r"v = f \lambda"
        expected = "v = f lambda"
        self.assertEqual(clean_chatgpt_response(latex), expected)

    def test_schrodinger(self):
        # -\frac{\hbar^2}{2m} \nabla^2 \psi + V\psi = E\psi
        latex = r"-\frac{\hbar^2}{2m} \nabla^2 \psi + V\psi = E\psi"
        expected = "-hbar sobrescrito 2 dividido por 2m gradiente sobrescrito 2 psi + Vpsi = Epsi"
        self.assertEqual(clean_chatgpt_response(latex), expected)

    def test_matrix(self):
        # \begin{bmatrix} a & b \\ c & d \end{bmatrix}
        latex = r"\begin{bmatrix} a & b \\ c & d \end{bmatrix}"
        expected = "início da matriz a e b; c e d fim da matriz"
        self.assertEqual(clean_chatgpt_response(latex), expected)

    def test_summation(self):
        # \sum_{i=1}^{n} i
        latex = r"\sum_{i=1}^{n} i"
        expected = " somatório  subscrito i=1 sobrescrito n i"
        self.assertEqual(clean_chatgpt_response(latex), expected)

    def test_integral(self):
        # \int_{a}^{b} f(x) dx
        latex = r"\int_{a}^{b} f(x) dx"
        expected = " integral  subscrito a sobrescrito b f(x) dx"
        self.assertEqual(clean_chatgpt_response(latex), expected)

    def test_rotacional(self):
        # \nabla \times \vec{A}
        latex = r"\nabla \times \vec{A}"
        expected = " rotacional  vec{A}"
        self.assertEqual(clean_chatgpt_response(latex), expected)

    def test_divergente(self):
        # \nabla \cdot \vec{A}
        latex = r"\nabla \cdot \vec{A}"
        expected = " divergente  vec{A}"
        self.assertEqual(clean_chatgpt_response(latex), expected)

    def test_gradiente(self):
        # \nabla f
        latex = r"\nabla f"
        expected = " gradiente  f"
        self.assertEqual(clean_chatgpt_response(latex), expected)

    def test_produtorio(self):
        # \prod_{i=1}^{n} i
        latex = r"\prod_{i=1}^{n} i"
        expected = " produtório  subscrito i=1 sobrescrito n i"
        self.assertEqual(clean_chatgpt_response(latex), expected)

    def test_union_intersection(self):
        # A \cup B, A \cap B
        latex = r"A \cup B, A \cap B"
        expected = "A união B, A interseção B"
        self.assertEqual(clean_chatgpt_response(latex), expected)

    def test_cubic_root(self):
        # \sqrt[3]{x}
        latex = r"\sqrt[3]{x}"
        expected = "raiz cúbica de x"
        self.assertEqual(clean_chatgpt_response(latex), expected)

if __name__ == "__main__":
    unittest.main()
