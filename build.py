import PyInstaller.__main__
import os
import sys

def build_exe():
    # Obtener el directorio actual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Definir los paths
    app_path = os.path.join(current_dir, 'core', 'app.py')
    icon_path = os.path.join(current_dir, 'assets', 'icon.ico')  # Si tienes un icono
    assets_dir = os.path.join(current_dir, 'assets')
    
    # Configurar argumentos para PyInstaller
    args = [
        app_path,  # Script principal
        '--name=FormulaExtractor',  # Nombre del ejecutable
        '--onedir',  # Crear un directorio con el ejecutable y dependencias
        '--windowed',  # Sin consola
        '--noconsole',  # Sin consola (Windows)
        f'--add-data={assets_dir}{os.pathsep}assets',  # Incluir assets
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=customtkinter',
        '--hidden-import=pix2tex',
        '--hidden-import=pix2tex.cli', # Para que LatexOCR funcione
        '--hidden-import=matplotlib',
        '--hidden-import=numpy',
        '--hidden-import=cv2',
        '--hidden-import=pymongo',
        '--hidden-import=bcrypt',
        '--clean',  # Limpiar cache
        '--noconfirm',  # No confirmar sobrescritura
    ]
    
    # Agregar icono si existe
    if os.path.exists(icon_path):
        args.append(f'--icon={icon_path}')
    
    # Ejecutar PyInstaller
    PyInstaller.__main__.run(args)

if __name__ == "__main__":
    build_exe() 