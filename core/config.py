from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# MongoDB configuración
MONGODB_CONFIG = {
    "URI": os.getenv("MONGODB_URI", "mongodb://localhost:27017/"),
    "DB_NAME": os.getenv("MONGODB_DB", "math_problems"),
    "COLLECTIONS": {"FORMULAS": "formulas", "USERS": "users"},
    "OPTIONS": {
        "serverSelectionTimeoutMS": 5000,
        "connectTimeoutMS": 5000,
        "retryWrites": True,
        "w": "majority",
    },
}

# Configuración de la aplicación
APP_CONFIG = {"THEME": "dark", "COLOR_THEME": "blue", "WINDOW_SIZE": "600x600"}

# Configuración de procesamiento de imágenes
IMAGE_CONFIG = {
    "MIN_WIDTH": 800,
    "ZOOM_FACTOR": 2,
    "ENHANCEMENT": {"contrast": 2.0, "sharpness": 1.8, "brightness": 1.1},
}

# Configuración de detección de fórmulas
FORMULA_CONFIG = {"MIN_TEXT_DENSITY": 0.05, "PADDING": 10, "MERGE_DISTANCE": 20}

# Configuración de logging
LOG_CONFIG = {
    "LEVEL": "INFO",
    "FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "FILE": "app.log",
}

# Configuración de debug
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Configuración de colores y UI
UI_CONFIG = {
    "COLORS": {
        # Colores principales
        "primary": "#1f538d",  # Azul principal
        "secondary": "#14213d",  # Azul oscuro
        "accent": "#fca311",  # Naranja/Dorado para acentos
        "background": "#1a1a1a",  # Fondo oscuro
        "surface": "#2B2B2B",  # Superficie de componentes
        # Estados y feedback
        "success": "#2a9d8f",  # Verde para éxito
        "error": "#e63946",  # Rojo para errores
        "warning": "#f4a261",  # Naranja para advertencias
        "info": "#457b9d",  # Azul claro para información
        # Texto
        "text": "#ffffff",  # Texto principal (blanco)
        "text_secondary": "#b0b0b0",  # Texto secundario (gris claro)
        "text_disabled": "#666666",  # Texto deshabilitado (gris oscuro)
        # Dificultad
        "difficulty_easy": "#4CAF50",  # Verde
        "difficulty_medium": "#FF9800",  # Naranja
        "difficulty_hard": "#F44336",  # Rojo
        # Bordes y divisores
        "border": "#404040",  # Bordes de componentes
        "divider": "#333333",  # Líneas divisorias
        # Estados de botones
        "button_hover": "#2a6fc1",  # Color al pasar el mouse
        "button_pressed": "#153a6a",  # Color al presionar
        "button_disabled": "#666666",  # Color deshabilitado
    },
    # Configuración de fuentes
    "FONTS": {
        "family": "Roboto",
        "sizes": {"small": 10, "regular": 12, "large": 14, "title": 24, "subtitle": 18},
    },
    # Configuración de espaciado
    "SPACING": {"xs": 5, "small": 10, "medium": 20, "large": 30, "xl": 40},
    # Configuración de bordes
    "BORDER_RADIUS": {"small": 4, "medium": 8, "large": 12},
    # Configuración de sombras
    "SHADOWS": {
        "small": "0 2px 4px rgba(0,0,0,0.1)",
        "medium": "0 4px 8px rgba(0,0,0,0.2)",
        "large": "0 8px 16px rgba(0,0,0,0.3)",
    },
    # Configuración de animaciones
    "ANIMATIONS": {"duration_short": 200, "duration_medium": 300, "duration_long": 500},
}
