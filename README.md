# 📚 FormulaExtractor

<div align="center">
  <img src="assets/image.png" alt="FormulaExtractor Logo" width="200"/>
  
  ![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
  ![License](https://img.shields.io/badge/license-MIT-green)
  ![Version](https://img.shields.io/badge/version-1.0.0-orange)
</div>

## 🌟 Descripción
FormulaExtractor es una aplicación de escritorio innovadora diseñada para revolucionar la forma en que los profesores y educadores manejan fórmulas matemáticas. Permite extraer, gestionar y organizar fórmulas matemáticas desde diversas fuentes, facilitando la creación de una biblioteca personal de recursos matemáticos.

## ✨ Características Principales

### 🔍 Extracción Inteligente
- **Captura de Pantalla**: Extracción rápida usando Win + Shift + S
- **Archivos PDF**: Procesamiento de documentos completos
- **Imágenes**: Soporte para formatos PNG, JPG, JPEG
- **Reconocimiento OCR**: Detección precisa de fórmulas matemáticas

### 📊 Gestión Avanzada
- **Clasificación Automática**: Categorización por tipo de fórmula
- **Organización Inteligente**: 
  - Por tipo (Álgebra, Cálculo, Geometría, etc.)
  - Por dificultad (Fácil, Medio, Difícil)
- **Vista Previa LaTeX**: Renderizado en tiempo real
- **Edición Flexible**: Personalización completa de fórmulas

### 👥 Sistema Multi-Usuario
- **Panel de Profesor**:
  - Biblioteca personal de fórmulas
  - Herramientas de captura y edición
  - Exportación de recursos
- **Panel de Administrador**:
  - Gestión de usuarios
  - Monitoreo del sistema
  - Configuración global

## 🚀 Instalación

### Requisitos del Sistema
- **Python**: 3.9 o superior
- **MongoDB**: 4.4 o superior
- **Sistema Operativo**: Windows 10/11, Linux, macOS
- **RAM**: Mínimo 4GB (Recomendado 8GB)
- **Espacio en Disco**: 500MB mínimo

### Guía de Instalación Rápida

1. **Clonar Repositorio**:
```bash
git clone https://github.com/tuusuario/FormulaExtractor.git
cd FormulaExtractor
```

2. **Configurar Entorno Virtual** (Recomendado):
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

3. **Instalar Dependencias**:
```bash
pip install -r requirements.txt
```

4. **Configurar Variables de Entorno**:
Crear archivo `.env`:
```env
MONGO_URI=tu_uri_de_mongodb
SECRET_KEY=tu_clave_secreta
DEBUG=True
```

5. **Iniciar Aplicación**:
```bash
python core/app.py
```

### 🎯 Crear Ejecutable
```bash
# Windows
build.bat

# Linux/macOS
python build.py
```

## 📖 Guía de Uso

### 🔑 Inicio de Sesión
1. Ejecutar la aplicación
2. Ingresar credenciales
3. Seleccionar rol (Profesor/Administrador)

### 📸 Captura de Fórmulas
1. Presionar Win + Shift + S
2. Seleccionar área con la fórmula
3. La fórmula se procesará automáticamente
4. Verificar y editar si es necesario

### 📚 Gestión de Biblioteca
1. Acceder a "Mis Fórmulas"
2. Usar filtros para organizar
3. Editar o eliminar según necesidad
4. Exportar en diferentes formatos

## 🛠️ Tecnologías Utilizadas

- **Frontend**:
  - CustomTkinter
  - Matplotlib
  - Pillow

- **Backend**:
  - PyMongo
  - OpenCV
  - Pix2Tex

- **Base de Datos**:
  - MongoDB

## 📂 Estructura del Proyecto
```
FormulaExtractor/
├── assets/                 # Recursos estáticos
│   ├── icon.ico
│   └── image.png
├── core/                   # Código fuente
│   ├── __init__.py
│   ├── app.py             # Punto de entrada
│   ├── admin_panel.py     # Panel administrativo
│   ├── teacher_panel.py   # Panel de profesor
│   ├── formula_extractor.py
│   └── formula_viewer.py
├── docs/                   # Documentación
├── tests/                  # Pruebas unitarias
├── .env                    # Variables de entorno
├── .gitignore
├── build.py               # Script de construcción
├── build.bat              # Script de construcción Windows
├── LICENSE
├── README.md
└── requirements.txt
```

## 🤝 Contribuir
1. Fork el proyecto
2. Crear rama (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add: AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia
Este proyecto está bajo la Licencia MIT - ver [LICENSE](LICENSE) para más detalles.

## 👥 Autores
- **Nombre Apellido** - *Trabajo Inicial* - [GitHub](https://github.com/username)

## 🙏 Agradecimientos
- Universidad X por el apoyo
- Biblioteca Y por los recursos
- Comunidad Z por el feedback

## 📞 Contacto
- **Email**: 2024378001@uteq.edu.mx
- **Twitter**: [@username](https://twitter.com/username)
- **LinkedIn**: [Perfil](https://linkedin.com/in/username)

---
<div align="center">
  Hecho con ❤️ por MindFlex IT 
  
  [⬆ Volver arriba](#formulaextractor)
</div>