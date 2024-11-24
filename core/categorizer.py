from typing import Dict, List
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import numpy as np
import joblib
import os


class FormulaCategorizer:
    def __init__(self):
        self.patterns = {
            "Ecuación Cuadrática": [
                r"ax²\s*[+\-]\s*bx\s*[+\-]\s*c\s*=\s*0",  # Forma general
                r"x²",  # Término cuadrático
                r"[-+]?\d*x²\s*[-+]\s*\d*x\s*[-+]\s*\d+\s*=\s*0",  # Forma específica
                r"\\frac{-b\s*\\pm\s*\\sqrt{b²\s*-\s*4ac}}{2a}",  # Fórmula general
                r"[-+]?\d*[a-zA-Z]²",  # Cualquier término al cuadrado
            ],
            "Álgebra Básica": [
                r"^\d+[\+\-\*/]\d+$",  # Operaciones básicas
                r"^\\frac{\d+}{\d+}$",  # Fracciones simples
                r"[a-zA-Z]\s*[+\-*/]\s*[a-zA-Z]",  # Operaciones con variables
            ],
            "Cálculo": [
                r"\\int",  # Integrales
                r"\\frac{d}{dx}",  # Derivadas
                r"\\lim_{[^}]*}",  # Límites
                r"\\sum_{[^}]*}",  # Sumas
                r"\\prod_{[^}]*}",  # Productos
            ],
            "Trigonometría": [
                r"\\sin|\\cos|\\tan|\\csc|\\sec|\\cot",  # Funciones trigonométricas
                r"\\theta|\\alpha|\\beta",  # Ángulos comunes
                r"\\pi",  # Pi
            ],
            "Geometría": [
                r"\\triangle|\\square|\\circle",  # Figuras geométricas
                r"\\angle",  # Ángulos
                r"\\parallel|\\perp",  # Relaciones geométricas
                r"área|perímetro|volumen",  # Medidas geométricas
            ],
            "Logaritmos": [
                r"\\log|\\ln",  # Logaritmos
                r"\\log_[^{]*{[^}]*}",  # Logaritmos con base específica
            ],
            "Estadística": [
                r"\\bar{[^}]*}",  # Media
                r"\\sigma",  # Desviación estándar
                r"P\([^)]*\)",  # Probabilidad
                r"\\binom",  # Combinaciones
            ],
            "Probabilidad": [
                r"P\([^)]*\)",  # Probabilidad
                r"\\binom",  # Combinaciones
                r"\\frac{P[^}]*}{P[^}]*}",  # Probabilidad condicional
            ],
            "Ecuaciónes Cuadráticas": [
                r"x²\s*[+\-]\s*\d*x\s*[+\-]\s*\d+\s*=\s*0",  # Ecuaciones cuadráticas estándar
                r"ax²\s*[+\-]\s*bx\s*[+\-]\s*c\s*=\s*0",  # Ecuaciones cuadráticas generales
                r"\\frac{-b\s*\\pm\s*\\sqrt{b²\s*-\s*4ac}}{2a}",  # Fórmula general
            ],

        }

        # Patrones específicos para dificultad
        self.difficulty_patterns = {
            "Fácil": [
                r"^\d+[\+\-\*/]\d+$",  # Operaciones básicas
                r"^\\frac{\d+}{\d+}$",  # Fracciones simples
                r"^\\sqrt{\d+}$",  # Raíces simples
                r"^[a-zA-Z]\s*[+\-]\s*\d+$",  # Ecuaciones lineales simples
            ],
            "Moderado": [
                r"x²\s*[+\-]\s*\d*x\s*[+\-]\s*\d+\s*=\s*0",  # Ecuaciones cuadráticas estándar
                r"\\frac{[^}]{1,20}}{[^}]{1,20}}",  # Fracciones moderadas
                r"\\sin|\\cos|\\tan",  # Trigonometría básica
                r"\\log",  # Logaritmos básicos
            ],
            "Difícil": [
                r"\\int.*dx",  # Integrales
                r"\\lim_{[^}]*}",  # Límites
                r"\\sum_{[^}]*}",  # Series
                r"\\frac{d}{dx}",  # Derivadas
                r"\\sqrt{[^}]{20,}}",  # Raíces complejas
                r"\\frac{[^}]{20,}}{[^}]{20,}}",  # Fracciones complejas
            ],
        }

        # Inicializar clasificadores ML
        self._initialize_models()

    def _initialize_models(self):
        """Inicializa o carga los modelos pre-entrenados"""
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(2, 4), max_features=1000
        )

        self.type_classifier = MultinomialNB()
        self.difficulty_classifier = MultinomialNB()

        # Entrenar con ejemplos iniciales
        self._train_initial_models()

    def _train_initial_models(self):
        """Entrena los modelos con ejemplos específicos para cada categoría"""
        type_examples = {
            "Ecuación Cuadrática": [
                "x² + 5x + 6 = 0",
                "2x² - 7x + 3 = 0",
                "ax² + bx + c = 0",
                "\\frac{-b \\pm \\sqrt{b² - 4ac}}{2a}",
                "x² = 25",
                "3x² + 2 = 14",
            ],
            "Álgebra Básica": [
                "x + y = 10",
                "2x - 3 = 7",
                "\\frac{x}{y} + 2",
                "a + b = c",
            ],
            "Trigonometría": [
                "\\sin(x)",
                "\\cos(x)",
                "\\tan(x)",
            ],
            "Geometría": [
                "\\triangle ABC",
                "\\square ABCD",
                "\\circle O",
            ],
            "Logaritmos": [
                "\\log(x)",
                "\\log_{10}(x)",
            ],
            "Estadística": [
                "\\bar{x}",
                "\\sigma",
                "P(A \\cap B)",
            ],
            "Probabilidad": [
                "P(A \\cup B)",
                "P(A \\cap B)",
            ],
            "Integrales": [
                "\\int",
                "\\int_{a}^{b}",
            ],
            "Sumatorias": [
                "\\sum",
                "\\sum_{a}^{b}",
            ],
            "Derivadas": [
                "\\frac{d}{dx}",
                "\\frac{d^2}{dx^2}",
            ]
        }

        # Preparar datos de entrenamiento
        X_type = []
        y_type = []
        for type_name, examples in type_examples.items():
            X_type.extend(examples)
            y_type.extend([type_name] * len(examples))

        # Entrenar clasificador de tipos
        X_type_vec = self.vectorizer.fit_transform(X_type)
        self.type_classifier.fit(X_type_vec, y_type)

    def classify_type(self, latex: str) -> str:
        """Clasifica el tipo de problema usando patrones y ML"""
        # Primero verificar patrones específicos
        for type_name, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, latex, re.IGNORECASE):
                    return type_name

        # Si no hay coincidencia por patrones, usar ML
        try:
            X = self.vectorizer.transform([latex])
            return self.type_classifier.predict([latex])[0]
        except:
            return "Otro"

    def classify_difficulty(self, latex: str) -> str:
        """Clasifica la dificultad basada en patrones y características"""
        # Verificar patrones de dificultad
        for difficulty, patterns in self.difficulty_patterns.items():
            for pattern in patterns:
                if re.search(pattern, latex):
                    return difficulty

        # Si no hay coincidencia, calcular basado en complejidad
        complexity = self._calculate_complexity(latex)

        if complexity < 30:
            return "Fácil"
        elif complexity < 100:
            return "Moderado"
        else:
            return "Difícil"

    def _calculate_complexity(self, latex: str) -> float:
        """Calcula la complejidad de la fórmula"""
        score = len(latex)  # Longitud base

        # Factores de complejidad
        complexity_factors = {
            r"x²": 5,  # Términos cuadráticos
            r"\\sqrt": 3,  # Raíces
            r"\\frac": 5,  # Fracciones
            r"\\int": 10,  # Integrales
            r"\\sum": 8,  # Sumas
            r"\\prod": 8,  # Productos
            r"\\lim": 7,  # Límites
            r"\\log": 4,  # Logaritmos
            r"\\sin|\\cos|\\tan": 4,  # Trigonometría
            r"{": 2,  # Agrupaciones
            r"_": 1,  # Subíndices
            r"^": 1,  # Superíndices
        }

        for pattern, weight in complexity_factors.items():
            score += len(re.findall(pattern, latex)) * weight

        return score
