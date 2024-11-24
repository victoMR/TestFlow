import json
import csv
from datetime import datetime
from typing import List, Dict
import pandas as pd
import latex2mathml.converter

class FormulaExporter:
    @staticmethod
    def to_latex(formulas: List[Dict], filepath: str):
        """Exporta las fórmulas a un archivo LaTeX"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\\documentclass{article}\n")
            f.write("\\usepackage{amsmath}\n")
            f.write("\\begin{document}\n\n")
            
            for formula in formulas:
                f.write(f"\\subsection*{{Fórmula - {formula['scan_date']}}}\n")
                f.write("\\begin{equation*}\n")
                f.write(formula['latex_formula'])
                f.write("\n\\end{equation*}\n")
                f.write(f"Tipo: {formula['problem_type']}\n")
                f.write(f"Dificultad: {formula['difficulty']}\n\n")
            
            f.write("\\end{document}")

    @staticmethod
    def to_html(formulas: List[Dict], filepath: str):
        """Exporta las fórmulas a un archivo HTML con MathML"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Fórmulas Matemáticas</title>
                <style>
                    .formula-card {
                        border: 1px solid #ccc;
                        margin: 10px;
                        padding: 15px;
                        border-radius: 5px;
                    }
                </style>
            </head>
            <body>
            """)
            
            for formula in formulas:
                mathml = latex2mathml.converter.convert(formula['latex_formula'])
                f.write(f"""
                <div class="formula-card">
                    <h3>Fórmula - {formula['scan_date']}</h3>
                    {mathml}
                    <p>Tipo: {formula['problem_type']}</p>
                    <p>Dificultad: {formula['difficulty']}</p>
                </div>
                """)
            
            f.write("</body></html>")

    @staticmethod
    def to_excel(formulas: List[Dict], filepath: str):
        """Exporta las fórmulas a un archivo Excel"""
        df = pd.DataFrame(formulas)
        df.to_excel(filepath, index=False) 