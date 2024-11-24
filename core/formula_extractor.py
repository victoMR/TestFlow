import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageOps
from pix2tex.cli import LatexOCR
import re
from datetime import datetime
from typing import List, Tuple, Optional
from core.categorizer import FormulaCategorizer
from core.formula_viewer import FormulaViewer
import logging
import customtkinter as ctk

class FormulaExtractor:
    def __init__(self):
        # Configuración mejorada
        self.model = LatexOCR()
        self.categorizer = FormulaCategorizer()
        self.viewer = FormulaViewer()
        
        # Parámetros optimizados para detección
        self.min_formula_area = 100  # Área mínima aumentada
        self.padding = 15  # Padding aumentado
        
        # Patrones matemáticos comunes para validación
        self.math_patterns = {
            'ecuaciones': r'=',
            'fracciones': r'\\frac',
            'potencias': r'\^',
            'raices': r'\\sqrt',
            'integrales': r'\\int',
            'sumatorias': r'\\sum',
            'limites': r'\\lim',
            'derivadas': r'\\frac{d}{d[x-z]}',
            'matrices': r'\\begin{matrix}',
            'vectores': r'\\vec'
        }
        
        # Desactivar logs innecesarios
        for logger in ['pix2tex', 'PIL', 'transformers']:
            logging.getLogger(logger).setLevel(logging.CRITICAL)

    def process_image(self, image: np.ndarray) -> List[dict]:
        """Procesa una imagen con redimensionamiento inteligente y optimización"""
        try:
            print("\n=== Iniciando procesamiento de imagen ===")
            
            # 1. Convertir a PIL y pre-procesar
            pil_image = Image.fromarray(image)
            print(f"Dimensiones originales: {pil_image.size}")
            
            # 2. Redimensionamiento inteligente
            processed_image = self._smart_resize(pil_image)
            print(f"Dimensiones después de resize: {processed_image.size}")
            
            # 3. Mejorar calidad
            enhanced_image = self._enhance_image_quality(processed_image)
            
            print("Intentando detección de fórmulas...")
            # 4. Intentar OCR directo primero (más rápido)
            try:
                latex = self.model(enhanced_image)
                print(f"LaTeX detectado: {latex}")
                
                if latex:
                    formulas = self.clean_latex(latex)
                    print(f"Fórmulas después de limpieza: {formulas}")
                    
                    if formulas:
                        valid_formulas = []
                        for formula in formulas:
                            if self._is_valid_mathematical_expression(formula):
                                formula_dict = {
                                    "latex": formula,
                                    "type": self.classify_problem_type(formula),
                                    "difficulty": self.classify_difficulty(formula),
                                    "confidence": self._calculate_confidence(formula, enhanced_image),
                                    "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                valid_formulas.append(formula_dict)
                                print(f"Fórmula válida encontrada: {formula}")
                            else:
                                print(f"Fórmula descartada por validación: {formula}")
                        
                        print(f"Total de fórmulas válidas: {len(valid_formulas)}")
                        if valid_formulas:
                            return valid_formulas
                        
            except Exception as e:
                print(f"Error en OCR directo: {e}")

            # 5. Si falla, intentar con segmentación
            print("Intentando segmentación...")
            segmented_formulas = self._process_with_segmentation(enhanced_image)
            if segmented_formulas:
                print(f"Fórmulas encontradas por segmentación: {len(segmented_formulas)}")
                return segmented_formulas
            
            print("No se detectaron fórmulas válidas")
            return []
                
        except Exception as e:
            logging.error(f"Error en process_image: {str(e)}")
            return []

    def _smart_resize(self, image: Image.Image) -> Image.Image:
        """Redimensiona la imagen de manera inteligente para optimizar la detección"""
        try:
            # Obtener dimensiones originales
            width, height = image.size
            
            # Definir rangos óptimos
            MIN_SIZE = 800
            MAX_SIZE = 2000
            TARGET_DPI = 300
            
            # Calcular ratio actual
            current_ratio = width / height
            
            # Determinar si la imagen es muy pequeña o muy grande
            min_dim = min(width, height)
            max_dim = max(width, height)
            
            if min_dim < MIN_SIZE:
                # Imagen muy pequeña, aumentar tamaño
                scale_factor = MIN_SIZE / min_dim
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                
                print(f"Redimensionando imagen pequeña: {width}x{height} -> {new_width}x{new_height}")
                
                return image.resize(
                    (new_width, new_height),
                    Image.Resampling.LANCZOS
                )
                
            elif max_dim > MAX_SIZE:
                # Imagen muy grande, reducir tamaño
                scale_factor = MAX_SIZE / max_dim
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                
                print(f"Redimensionando imagen grande: {width}x{height} -> {new_width}x{new_height}")
                
                return image.resize(
                    (new_width, new_height),
                    Image.Resampling.LANCZOS
                )
                
            return image
            
        except Exception as e:
            logging.error(f"Error en smart_resize: {str(e)}")
            return image

    def _enhance_image_quality(self, image: Image.Image) -> Image.Image:
        """Mejora la calidad de la imagen para mejor detección"""
        try:
            # 1. Convertir a escala de grises si es necesario
            if image.mode != 'L':
                image = image.convert('L')
            
            # 2. Mejorar contraste
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # 3. Mejorar nitidez
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)
            
            # 4. Binarización adaptativa
            img_array = np.array(image)
            binary = cv2.adaptiveThreshold(
                img_array,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2
            )
            
            # 5. Reducción de ruido
            denoised = cv2.fastNlMeansDenoising(binary)
            
            return Image.fromarray(denoised)
            
        except Exception as e:
            logging.error(f"Error en enhance_image_quality: {str(e)}")
            return image

    def _process_with_segmentation(self, image: Image.Image) -> List[dict]:
        """Procesa la imagen usando segmentación cuando el OCR directo falla"""
        try:
            # Convertir a array numpy
            img_array = np.array(image)
            
            # Detectar regiones de texto
            mser = cv2.MSER_create(
                _min_area=100,
                _max_area=5000
            )
            
            regions, _ = mser.detectRegions(img_array)
            
            # Fusionar regiones cercanas
            merged_regions = self._merge_regions(regions)
            
            formulas = []
            for x, y, w, h in merged_regions:
                # Extraer y procesar región
                region = image.crop((x, y, x+w, y+h))
                region = self._enhance_image_quality(region)
                
                try:
                    latex = self.model(region)
                    if latex and self._is_valid_mathematical_expression(latex):
                        formulas.append({
                            "latex": latex,
                            "type": self.classify_problem_type(latex),
                            "difficulty": self.classify_difficulty(latex),
                            "confidence": self._calculate_confidence(latex, region),
                            "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                except Exception as e:
                    print(f"Error procesando región: {e}")
                    continue
            
            print(f"Fórmulas detectadas por segmentación: {len(formulas)}")
            return formulas
            
        except Exception as e:
            logging.error(f"Error en process_with_segmentation: {str(e)}")
            return []

    def _merge_regions(self, regions) -> List[Tuple[int, int, int, int]]:
        """Fusiona regiones cercanas para mejor detección"""
        try:
            if not regions:
                return []
            
            # Convertir regiones a formato (x,y,w,h)
            boxes = []
            for region in regions:
                x = min(region[:, 0])
                y = min(region[:, 1])
                w = max(region[:, 0]) - x
                h = max(region[:, 1]) - y
                boxes.append([x, y, w, h])
            
            # Ordenar por posición
            boxes.sort(key=lambda b: (b[1], b[0]))
            
            # Fusionar cajas cercanas
            merged = []
            current = boxes[0]
            
            for box in boxes[1:]:
                if self._should_merge(current, box):
                    # Fusionar
                    x = min(current[0], box[0])
                    y = min(current[1], box[1])
                    w = max(current[0] + current[2], box[0] + box[2]) - x
                    h = max(current[1] + current[3], box[1] + box[3]) - y
                    current = [x, y, w, h]
                else:
                    merged.append(current)
                    current = box
            
            merged.append(current)
            return merged
            
        except Exception as e:
            logging.error(f"Error en merge_regions: {str(e)}")
            return []

    def _should_merge(self, box1, box2, distance_threshold=20):
        """Determina si dos cajas deben fusionarse"""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # Calcular centros
        c1_y = y1 + h1/2
        c2_y = y2 + h2/2
        
        # Verificar si están en la misma línea
        if abs(c1_y - c2_y) > h1/2:
            return False
        
        # Verificar distancia horizontal
        right1 = x1 + w1
        left2 = x2
        
        return left2 - right1 < distance_threshold

    def _is_valid_mathematical_expression(self, latex: str) -> bool:
        """Verifica si el LaTeX representa una expresión matemática válida"""
        try:
            print(f"\nValidando expresión: {latex}")
            
            # Verificar longitud mínima
            if len(latex) < 3:
                print("Rechazada: longitud muy corta")
                return False
            
            # Verificar patrones matemáticos básicos
            basic_patterns = [
                r'[xyz]_{\d+}',    # Variables con subíndices
                r'[xyz]\d',        # Variables con números
                r'[+\-*/=]',       # Operadores básicos
                r'\d+',            # Números
            ]
            
            has_math_content = any(
                re.search(pattern, latex) 
                for pattern in basic_patterns
            )
            
            if not has_math_content:
                has_math_content = any(
                    re.search(pattern, latex) 
                    for pattern in self.math_patterns.values()
                )
            
            if not has_math_content:
                print("Rechazada: no contiene elementos matemáticos")
                return False
            
            # Verificar balance de símbolos de manera más flexible
            symbols_to_check = [
                ('{', '}'),
                ('(', ')'),
                ('[', ']'),
            ]
            
            # Contar símbolos ignorando los que están escapados
            for start, end in symbols_to_check:
                start_count = len(re.findall(r'(?<!\\)\{', latex)) if start == '{' else latex.count(start)
                end_count = len(re.findall(r'(?<!\\)\}', latex)) if end == '}' else latex.count(end)
                
                if abs(start_count - end_count) > 0:  # Debe estar perfectamente balanceado
                    print(f"Advertencia: símbolos {start}{end} desbalanceados pero permitiendo")
                    # No retornamos False aquí para ser más permisivos
            
            # Verificar que tenga al menos un componente matemático válido
            if any([
                '=' in latex,           # Ecuación
                '_' in latex,           # Subíndice
                '^' in latex,           # Exponente
                '/4' in latex,          # División
                re.search(r'\d', latex) # Números
            ]):
                print("Expresión válida")
                return True
            
            print("Rechazada: no es una expresión matemática válida")
            return False
            
        except Exception as e:
            logging.error(f"Error validando expresión: {str(e)}")
            return False

    def _detect_by_segmentation(self, image: Image.Image) -> List[dict]:
        """Detecta fórmulas usando segmentación de imagen"""
        try:
            # Convertir a array numpy
            img_array = np.array(image)
            
            # Aplicar umbralización adaptativa
            binary = cv2.adaptiveThreshold(
                img_array, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                11, 2
            )
            
            # Encontrar componentes conectados
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
                binary, connectivity=8
            )
            
            formulas = []
            for i in range(1, num_labels):  # Ignorar fondo (label 0)
                x = stats[i, cv2.CC_STAT_LEFT]
                y = stats[i, cv2.CC_STAT_TOP]
                w = stats[i, cv2.CC_STAT_WIDTH]
                h = stats[i, cv2.CC_STAT_HEIGHT]
                area = stats[i, cv2.CC_STAT_AREA]
                
                # Filtrar por tamaño
                if area < self.min_formula_area:
                    continue
                
                # Extraer región con padding
                region = self._extract_region_with_padding(image, x, y, w, h)
                
                # Intentar OCR en la región
                latex = self.model(region)
                if latex and self._is_valid_mathematical_expression(latex):
                    formulas.append({
                        "latex": latex,
                        "type": self.classify_problem_type(latex),
                        "difficulty": self.classify_difficulty(latex),
                        "confidence": self._calculate_confidence(latex, region),
                        "agrega_en_fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            return formulas
            
        except Exception as e:
            logging.error(f"Error en segmentación: {str(e)}")
            return []

    def _extract_region_with_padding(self, image: Image.Image, x: int, y: int, w: int, h: int) -> Image.Image:
        """Extrae una región con padding inteligente"""
        try:
            # Calcular padding adaptativo
            pad_x = int(w * 0.2)
            pad_y = int(h * 0.2)
            
            # Asegurar que no nos salimos de la imagen
            x1 = max(0, x - pad_x)
            y1 = max(0, y - pad_y)
            x2 = min(image.size[0], x + w + pad_x)
            y2 = min(image.size[1], y + h + pad_y)
            
            # Extraer región
            region = image.crop((x1, y1, x2, y2))
            
            # Redimensionar si es muy pequeña
            min_size = 200
            if min(region.size) < min_size:
                ratio = min_size / min(region.size)
                new_size = tuple(int(dim * ratio) for dim in region.size)
                region = region.resize(new_size, Image.Resampling.LANCZOS)
            
            return region
            
        except Exception as e:
            logging.error(f"Error extrayendo región: {str(e)}")
            return image

    def _validate_formula(self, formula: dict) -> bool:
        """Valida una fórmula detectada"""
        try:
            latex = formula.get('latex', '')
            
            # Verificar LaTeX válido
            if not self._is_valid_mathematical_expression(latex):
                return False
            
            # Verificar confianza mínima
            if formula.get('confidence', 0) < 0.5:
                return False
            
            # Verificar longitud y complejidad
            if len(latex) < 3 or len(latex) > 500:
                return False
            
            # Verificar presencia de elementos matemáticos
            required_elements = [
                r'\d',           # Números
                r'[a-zA-Z]',    # Variables
                r'[+\-*/=]|\\[a-zA-Z]+' # Operadores o comandos LaTeX
            ]
            
            has_required = all(
                re.search(pattern, latex) 
                for pattern in required_elements
            )
            
            return has_required
            
        except Exception as e:
            logging.error(f"Error validando fórmula: {str(e)}")
            return False

    def show_formulas(self, formulas: List[dict], on_save_callback=None):
        """Muestra las fórmulas detectadas usando FormulaViewer"""
        return self.viewer.show_formulas(formulas, on_save_callback)

    def process_formula_region(self, region_image: np.ndarray) -> Tuple[str, Image.Image]:
        """Procesa una región y retorna el LaTeX y la imagen mejorada"""
        try:
            # Convertir a RGB
            if len(region_image.shape) == 2:
                region_image = cv2.cvtColor(region_image, cv2.COLOR_GRAY2RGB)
            elif len(region_image.shape) == 3:
                if region_image.shape[2] == 3:
                    region_image = cv2.cvtColor(region_image, cv2.COLOR_BGR2RGB)
                elif region_image.shape[2] == 4:
                    region_image = cv2.cvtColor(region_image, cv2.COLOR_BGRA2RGB)

            # Convertir a PIL y redimensionar
            pil_image = Image.fromarray(region_image)
            
            # Agrandar MUCHO más la imagen para mejor reconocimiento
            target_height = 400  # Altura objetivo mucho más grande
            ratio = target_height / pil_image.size[1]
            new_size = (int(pil_image.size[0] * ratio), target_height)
            pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Mejorar calidad con parámetros más agresivos
            enhancers = [
                (ImageEnhance.Contrast, 2.5),     # Más contraste
                (ImageEnhance.Sharpness, 2.0),    # Más nitidez
                (ImageEnhance.Brightness, 1.3),    # Más brillo
            ]

            enhanced = pil_image
            for enhancer_class, factor in enhancers:
                enhancer = enhancer_class(enhanced)
                enhanced = enhancer.enhance(factor)
            
            # Asegurar fondo blanco y texto negro
            enhanced = self._ensure_black_text(enhanced)
            
            # Extraer LaTeX con manejo de errores
            try:
                latex = self.model(enhanced)
                latex = self.clean_latex(latex)
                
                # Si no se detectó fórmula, intentar con la imagen original
                if not latex:
                    latex = self.model(pil_image)
                    latex = self.clean_latex(latex)
            except Exception as e:
                print(f"Error en OCR: {e}")
                latex = ""
            
            return latex, enhanced

        except Exception as e:
            print(f"Error en process_formula_region: {str(e)}")
            raise

    def process_pdf(self, pdf_path: str) -> List[dict]:
        """Procesa un PDF y extrae las fórmulas"""
        import fitz  # Importar aquí para no cargar si no se usa
        
        formulas = []
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap()
            
            # Convertir a numpy array
            img_array = np.frombuffer(pix.samples, dtype=np.uint8)
            img_array = img_array.reshape(pix.height, pix.width, pix.n)
            
            # Procesar página
            page_formulas = self.process_image(img_array)
            for formula in page_formulas:
                formula['page'] = page_num + 1
                formulas.append(formula)
        
        return formulas

    def detect_formula_regions(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detecta regiones que contienen fórmulas con mejor precisión"""
        try:
            # Preprocesamiento mejorado
            processed = self._preprocess_for_detection(image)
            
            # Detectar usando múltiples métodos
            regions = []
            
            # 1. Detección por umbralización adaptativa
            binary = cv2.adaptiveThreshold(
                processed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # 2. Detección por gradientes
            sobelx = cv2.Sobel(processed, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(processed, cv2.CV_64F, 0, 1, ksize=3)
            gradient = np.sqrt(sobelx**2 + sobely**2)
            gradient = np.uint8(gradient * 255 / np.max(gradient))
            
            # 3. Combinar resultados
            combined = cv2.bitwise_or(binary, gradient)
            
            # 4. Operaciones morfológicas para conectar componentes
            kernel_connect = cv2.getStructuringElement(cv2.MORPH_RECT, (5,2))
            connected = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel_connect)
            
            # 5. Encontrar contornos
            contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Parámetros adaptables según el tamaño de la imagen
            height, width = image.shape[:2]
            min_area = (width * height) * 0.0005  # 0.05% del área total
            max_area = (width * height) * 0.3     # 30% del área total
            
            # Procesar cada contorno
            for contour in contours:
                area = cv2.contourArea(contour)
                if min_area < area < max_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    # Verificar contenido de la región
                    if self._is_valid_formula_region(connected[y:y+h, x:x+w]):
                        regions.append((x, y, w, h))
            
            # Agrupar regiones cercanas usando DBSCAN
            if regions:
                regions = self._cluster_regions(regions, width, height)
            
            # Expandir regiones con padding
            final_regions = []
            for x, y, w, h in regions:
                padded = self._add_region_padding(x, y, w, h, width, height)
                final_regions.append(padded)
            
            # Debug: guardar imagen con regiones detectadas
            debug = image.copy()
            for x, y, w, h in final_regions:
                cv2.rectangle(debug, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.imwrite('debug_formulas.png', debug)
            
            return final_regions
            
        except Exception as e:
            print(f"Error en detección de regiones: {str(e)}")
            return []

    def _is_valid_formula_region(self, region: np.ndarray) -> bool:
        """Verifica si una región probablemente contiene una fórmula"""
        try:
            # Calcular características de la región
            height, width = region.shape
            area = width * height
            pixel_density = np.count_nonzero(region) / area
            
            # Calcular distribución vertical y horizontal
            vertical_proj = np.sum(region, axis=1) / width
            horizontal_proj = np.sum(region, axis=0) / height
            
            # Criterios de validación
            min_density = 0.05
            max_density = 0.6
            min_variation = 0.1
            
            # Verificar densidad de píxeles
            if not (min_density < pixel_density < max_density):
                return False
            
            # Verificar variación en proyecciones
            v_variation = np.std(vertical_proj)
            h_variation = np.std(horizontal_proj)
            
            if v_variation < min_variation or h_variation < min_variation:
                return False
            
            # Verificar proporción
            aspect_ratio = width / height
            if not (0.2 < aspect_ratio < 10):
                return False
            
            return True
            
        except Exception as e:
            print(f"Error en validación de región: {e}")
            return False

    def _cluster_regions(self, regions: List[Tuple[int, int, int, int]], 
                        image_width: int, image_height: int) -> List[Tuple[int, int, int, int]]:
        """Agrupa regiones cercanas usando DBSCAN"""
        try:
            from sklearn.cluster import DBSCAN
            
            if not regions:
                return []
            
            # Extraer centros y características de las regiones
            centers = []
            for x, y, w, h in regions:
                cx = x + w/2
                cy = y + h/2
                centers.append([cx/image_width, cy/image_height])  # Normalizar coordenadas
            
            # Configurar DBSCAN
            eps = 0.05  # 5% de la dimensión de la imagen
            min_samples = 1  # Permitir clusters pequeños
            
            # Aplicar clustering
            clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(centers)
            
            # Procesar cada cluster
            merged_regions = []
            for label in set(clustering.labels_):
                if label == -1:  # Ruido
                    continue
                    
                # Obtener regiones del cluster
                cluster_regions = [regions[i] for i in range(len(regions)) 
                                 if clustering.labels_[i] == label]
                
                # Fusionar regiones del cluster
                if cluster_regions:
                    x_min = min(r[0] for r in cluster_regions)
                    y_min = min(r[1] for r in cluster_regions)
                    x_max = max(r[0] + r[2] for r in cluster_regions)
                    y_max = max(r[1] + r[3] for r in cluster_regions)
                    
                    merged_regions.append((x_min, y_min, x_max - x_min, y_max - y_min))
            
            return merged_regions
            
        except Exception as e:
            print(f"Error en clustering: {e}")
            return regions

    def _add_region_padding(self, x: int, y: int, w: int, h: int, 
                           image_width: int, image_height: int) -> Tuple[int, int, int, int]:
        """Añade padding a una región detectada"""
        try:
            # Calcular padding adaptativo
            pad_x = int(w * 0.15)  # 15% del ancho
            pad_y = int(h * 0.15)  # 15% del alto
            
            # Aplicar padding con límites
            new_x = max(0, x - pad_x)
            new_y = max(0, y - pad_y)
            new_w = min(image_width - new_x, w + 2*pad_x)
            new_h = min(image_height - new_y, h + 2*pad_y)
            
            return (new_x, new_y, new_w, new_h)
            
        except Exception as e:
            print(f"Error añadiendo padding: {e}")
            return (x, y, w, h)

    def merge_nearby_regions(self, regions: List[Tuple[int, int, int, int]], 
                           h_threshold: int = 70,  # Distancia horizontal
                           v_threshold: int = 40) -> List[Tuple[int, int, int, int]]:  # Distancia vertical
        """Une regiones que están cerca con criterios flexibles"""
        if not regions:
            return []

        def should_merge(r1, r2):
            """Determina si dos regiones deberían unirse"""
            x1, y1, w1, h1 = r1
            x2, y2, w2, h2 = r2
            
            # Calcular centros
            c1_y = y1 + h1/2
            c2_y = y2 + h2/2
            
            # Distancia vertical entre centros
            vertical_distance = abs(c2_y - c1_y)
            
            # Calcular superposición horizontal
            left = max(x1, x2)
            right = min(x1 + w1, x2 + w2)
            horizontal_overlap = right - left if right > left else -1
            
            if horizontal_overlap > 0:
                return True
            
            # Calcular distancia horizontal
            if x1 < x2:
                horizontal_distance = x2 - (x1 + w1)
            else:
                horizontal_distance = x1 - (x2 + w2)
            
            # Criterios más flexibles para unión
            same_line = vertical_distance < v_threshold
            close_enough = horizontal_distance < h_threshold
            
            # Considerar también el tamaño relativo
            similar_height = abs(h1 - h2) < max(h1, h2) * 0.5
            
            return same_line and (close_enough or similar_height)

        # Ordenar regiones
        regions = sorted(regions, key=lambda r: (r[1], r[0]))
        merged = []
        
        if not regions:
            return merged
            
        current = list(regions[0])
        
        for next_region in regions[1:]:
            if should_merge(current, next_region):
                # Expandir región actual
                x = min(current[0], next_region[0])
                y = min(current[1], next_region[1])
                max_x = max(current[0] + current[2], next_region[0] + next_region[2])
                max_y = max(current[1] + current[3], next_region[1] + next_region[3])
                current = [x, y, max_x - x, max_y - y]
            else:
                merged.append(tuple(current))
                current = list(next_region)
        
        merged.append(tuple(current))
        return merged

    def enhance_formula_image(self, image: Image.Image) -> Image.Image:
        """Mejora la calidad de la imagen de la fórmula"""
        try:
            # Asegurar tamaño mínimo adecuado para OCR
            min_height = 200
            if image.size[1] < min_height:
                ratio = min_height / image.size[1]
                new_size = (int(image.size[0] * ratio), min_height)
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Aplicar mejoras más agresivas
            enhancers = [
                (ImageEnhance.Contrast, 2.0),     # Más contraste
                (ImageEnhance.Sharpness, 1.8),    # Más nitidez
                (ImageEnhance.Brightness, 1.2),    # Ajuste de brillo
            ]

            enhanced = image
            for enhancer_class, factor in enhancers:
                enhancer = enhancer_class(enhanced)
                enhanced = enhancer.enhance(factor)

            return enhanced

        except Exception as e:
            print(f"Error en enhance_formula_image: {str(e)}")
            return image

    def clean_latex(self, latex: str) -> List[str]:
        """Limpia y separa las fórmulas LaTeX en una lista"""
        try:
            print(f"\nLimpiando LaTeX: {latex}")
            if not latex or len(latex.strip()) < 2:
                return []

            # Limpiar caracteres problemáticos
            cleaned = latex.strip()
            
            # Si es un array, procesar especialmente
            if '\\begin{array}' in cleaned:
                # Extraer contenido del array
                content = cleaned.replace('\\begin{array}{r l}', '')
                content = content.replace('\\begin{array}{l}', '')
                content = content.replace('\\end{array}', '')
                
                # Separar por \\
                raw_formulas = [f.strip() for f in content.split('\\\\')]
                
                formulas = []
                for formula in raw_formulas:
                    if not formula:
                        continue
                    
                    # Limpiar cada fórmula
                    formula = formula.strip()
                    
                    # Limpiar estructura de la fórmula
                    formula = self._clean_formula_structure(formula)
                    
                    if formula:
                        formulas.append(formula)
                        print(f"Fórmula limpia: {formula}")
            else:
                # Para fórmulas individuales
                formulas = [self._clean_formula_structure(cleaned)]

            return [f for f in formulas if f]  # Filtrar fórmulas vacías
            
        except Exception as e:
            print(f"Error limpiando LaTeX: {e}")
            return []

    def _clean_formula_structure(self, formula: str) -> str:
        """Limpia la estructura de una fórmula LaTeX"""
        try:
            # Eliminar espacios extras
            formula = formula.strip()
            
            # Reemplazar &{} por = y limpiar &
            formula = formula.replace('&{}', '=')
            formula = formula.replace('&', '=')
            
            # Limpiar llaves extras y estructura
            formula = re.sub(r'=\{\}=', '=', formula)  # Eliminar ={}}=
            formula = re.sub(r'\{\{+', '{', formula)   # Reducir múltiples { a uno
            formula = re.sub(r'\}\}+', '}', formula)   # Reducir múltiples } a uno
            formula = re.sub(r'(?<!=)\{\}(?!=)', '', formula)  # Eliminar {} vacías
            
            # Limpiar estructura específica del problema
            formula = re.sub(r'=\}=', '=', formula)    # Eliminar =}=
            formula = re.sub(r'=\{=', '=', formula)    # Eliminar ={=
            
            # Asegurar que los subíndices estén bien formados
            formula = re.sub(r'([xyz])_(\d+)\}(?!\w)', r'\1_{\2}', formula)
            
            # Limpiar espacios extras
            formula = re.sub(r'\s+', ' ', formula)
            
            # Limpiar estructura final
            formula = re.sub(r'^\{|\}$', '', formula)  # Eliminar llaves al inicio y final
            formula = re.sub(r'(?<==)\s+|\s+(?==)', '', formula)  # Eliminar espacios alrededor del =
            
            # Verificar y corregir balance de llaves
            open_count = formula.count('{')
            close_count = formula.count('}')
            
            if open_count > close_count:
                formula += '}' * (open_count - close_count)
            elif close_count > open_count:
                formula = '{' * (close_count - open_count) + formula
            
            print(f"Estructura limpia: {formula}")
            return formula
            
        except Exception as e:
            print(f"Error limpiando estructura: {e}")
            return formula

    def is_valid_latex(self, latex: str) -> bool:
        """Verifica si la expresión LaTeX es válida y tiene sentido matemático"""
        try:
            # Verificar que no esté vacío
            if not latex or len(latex.strip()) < 2:
                return False

            # Verificar balance de llaves
            if latex.count('{') != latex.count('}'):
                return False

            # Verificar caracteres inválidos
            invalid_chars = ['\\\\', '&&', '\\]', '\\[']
            if any(char in latex for char in invalid_chars):
                return False

            # Verificar que contenga al menos un carácter matemático
            math_chars = [
                'x', 'y', 'z', '+', '-', '=', '^', '\\frac', '\\sqrt',
                '\\alpha', '\\beta', '\\pi', '\\sum', '\\int',
                '\\infty', '\\partial', '\\nabla', '\\Delta',
                '\\sin', '\\cos', '\\tan', '\\log', '\\ln'
            ]
            if not any(char in latex for char in math_chars):
                return False

            # Verificar patrones inválidos
            invalid_patterns = [
                r'[^\\]\$',  # Símbolos $ sin escapar
                r'\\[^a-zA-Z{}]',  # Comandos LaTeX inválidos
                r'\{\}',  # Llaves vacías
                r'\\begin\{[^}]*\}\\end',  # Entornos vacíos
                r'\\[a-zA-Z]+\{\}',  # Comandos con argumentos vacíos
            ]
            
            for pattern in invalid_patterns:
                if re.search(pattern, latex):
                    return False

            # Verificar estructura básica
            if not self._check_latex_structure(latex):
                return False

            return True

        except Exception as e:
            print(f"Error validando LaTeX: {e}")
            return False

    def _check_latex_structure(self, latex: str) -> bool:
        """Verifica la estructura básica de la expresión LaTeX"""
        try:
            # Pila para verificar balance de llaves
            stack = []
            
            for i, char in enumerate(latex):
                if char == '{':
                    stack.append(i)
                elif char == '}':
                    if not stack:  # Llave de cierre sin apertura
                        return False
                    stack.pop()
            
            if stack:  # Quedaron llaves sin cerrar
                return False

            # Verificar comandos LaTeX válidos
            commands = re.findall(r'\\[a-zA-Z]+', latex)
            valid_commands = {
                '\\frac', '\\sqrt', '\\sum', '\\int', '\\alpha', '\\beta',
                '\\pi', '\\theta', '\\infty', '\\partial', '\\nabla',
                '\\Delta', '\\sin', '\\cos', '\\tan', '\\log', '\\ln',
                '\\lim', '\\rightarrow', '\\leftarrow', '\\leq', '\\geq',
                '\\neq', '\\approx', '\\cdot', '\\times', '\\div'
            }

            for cmd in commands:
                if cmd not in valid_commands:
                    # Permitir algunos comandos desconocidos pero con estructura válida
                    if not re.match(r'\\[a-zA-Z]{2,}', cmd):
                        return False

            # Verificar subíndices y superíndices
            subscripts = re.findall(r'_\{[^}]*\}', latex)
            superscripts = re.findall(r'\^\{[^}]*\}', latex)
            
            for script in subscripts + superscripts:
                if not script[2:-1].strip():  # Contenido vacío
                    return False

            return True

        except Exception as e:
            print(f"Error verificando estructura LaTeX: {e}")
            return False

    def classify_problem_type(self, latex: str) -> str:
        """Clasifica el tipo de problema basado en el LaTeX"""
        try:
            # Usar el categorizador para clasificar
            return self.categorizer.classify_type(latex)
        except Exception as e:
            print(f"Error clasificando tipo: {e}")
            return "No clasificado"

    def classify_difficulty(self, latex: str) -> str:
        """Clasifica la dificultad basado en el LaTeX"""
        try:
            # Usar el categorizador para clasificar dificultad
            return self.categorizer.classify_difficulty(latex)
        except Exception as e:
            print(f"Error clasificando dificultad: {e}")
            return "No definida"

    def _preprocess_for_detection(self, image: np.ndarray) -> np.ndarray:
        """Preprocesamiento mejorado para detección de fórmulas"""
        try:
            # Convertir a escala de grises si es necesario
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Aplicar múltiples técnicas de mejora
            # 1. Mejora de contraste adaptativo
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            contrast = clahe.apply(gray)
            
            # 2. Reducción de ruido
            denoised = cv2.fastNlMeansDenoising(contrast)
            
            # 3. Normalización de brillo
            normalized = cv2.normalize(denoised, None, 0, 255, cv2.NORM_MINMAX)
            
            # 4. Umbralización adaptativa
            binary = cv2.adaptiveThreshold(
                normalized,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                11,
                2
            )
            
            # 5. Operaciones morfológicas para conectar componentes
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
            morphology = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return morphology
        
        except Exception as e:
            print(f"Error en preprocesamiento: {e}")
            return image

    def _detect_with_contours(self, binary_image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detección basada en contornos con parámetros optimizados"""
        regions = []
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        height, width = binary_image.shape[:2]
        min_area = width * height * 0.001  # Área mínima adaptativa
        max_area = width * height * 0.5    # Área máxima adaptativa
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area < area < max_area:
                x, y, w, h = cv2.boundingRect(contour)
                regions.append((x, y, w, h))
        
        return regions

    def _detect_connected_components(self, binary_image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detección usando análisis de componentes conectados"""
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_image)
        
        regions = []
        for i in range(1, num_labels):  # Ignorar el fondo (label 0)
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]
            area = stats[i, cv2.CC_STAT_AREA]
            
            if area > 100:  # Filtro de área mínima
                regions.append((x, y, w, h))
        
        return regions

    def _enhance_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """Preprocesamiento específico para OCR"""
        try:
            # 1. Asegurar tamaño mínimo
            min_height = 400  # Altura mínima aumentada
            if image.size[1] < min_height:
                ratio = min_height / image.size[1]
                new_size = (int(image.size[0] * ratio), min_height)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # 2. Convertir a escala de grises
            if image.mode != 'L':
                image = image.convert('L')
            
            # 3. Mejorar contraste local
            enhanced_array = np.array(image)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced_array = clahe.apply(enhanced_array)
            
            # 4. Reducción de ruido
            enhanced_array = cv2.fastNlMeansDenoising(enhanced_array)
            
            # 5. Binarización adaptativa
            binary = cv2.adaptiveThreshold(
                enhanced_array,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2
            )
            
            return Image.fromarray(binary)
            
        except Exception as e:
            print(f"Error en mejora para OCR: {e}")
            return image

    def _calculate_confidence(self, latex: str, image: Image.Image) -> float:
        """Calcula un puntaje de confianza para la fórmula detectada"""
        try:
            confidence = 1.0
            
            # 1. Verificar complejidad del LaTeX
            if len(latex) < 5:
                confidence *= 0.5
            elif len(latex) > 100:
                confidence *= 0.8
            
            # 2. Verificar presencia de símbolos matemáticos
            math_symbols = ['\\frac', '\\sqrt', '^', '_', '+', '-', '=', '\\int', '\\sum']
            symbol_count = sum(1 for symbol in math_symbols if symbol in latex)
            confidence *= min(1.0, symbol_count * 0.2)
            
            # 3. Verificar calidad de imagen
            img_array = np.array(image)
            if len(img_array.shape) == 2:
                contrast = np.std(img_array)
                confidence *= min(1.0, contrast / 50.0)
            
            # 4. Verificar estructura LaTeX
            if latex.count('{') == latex.count('}'):
                confidence *= 1.2
            
            return min(1.0, confidence)
            
        except Exception as e:
            print(f"Error calculando confianza: {e}")
            return 0.5

    def _merge_all_regions(self, regions: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """Combina y filtra todas las regiones detectadas por diferentes métodos"""
        try:
            if not regions:
                return []

            # Eliminar duplicados
            unique_regions = list(set(regions))
            
            # Ordenar regiones por posición (arriba a abajo, izquierda a derecha)
            sorted_regions = sorted(unique_regions, key=lambda r: (r[1], r[0]))
            
            merged = []
            current = list(sorted_regions[0])
            
            # Parámetros para fusión
            h_overlap_threshold = 0.3  # 30% de superposición horizontal
            v_overlap_threshold = 0.3  # 30% de superposición vertical
            distance_threshold = 20    # Distancia máxima entre regiones
            
            for next_region in sorted_regions[1:]:
                if self._should_merge_regions(current, next_region,
                                            h_overlap_threshold,
                                            v_overlap_threshold,
                                            distance_threshold):
                    # Fusionar regiones
                    x = min(current[0], next_region[0])
                    y = min(current[1], next_region[1])
                    max_x = max(current[0] + current[2], next_region[0] + next_region[2])
                    max_y = max(current[1] + current[3], next_region[1] + next_region[3])
                    current = [x, y, max_x - x, max_y - y]
                else:
                    # Agregar región actual y comenzar nueva
                    merged.append(tuple(current))
                    current = list(next_region)
            
            # Agregar última región
            merged.append(tuple(current))
            
            # Filtrar regiones por tamaño y proporción
            filtered = self._filter_merged_regions(merged)
            
            return filtered
            
        except Exception as e:
            print(f"Error en merge_all_regions: {e}")
            return regions

    def _should_merge_regions(self, r1: Tuple[int, int, int, int], 
                             r2: Tuple[int, int, int, int],
                             h_threshold: float,
                             v_threshold: float,
                             distance_threshold: int) -> bool:
        """Determina si dos regiones deben fusionarse basado en superposición y distancia"""
        try:
            x1, y1, w1, h1 = r1
            x2, y2, w2, h2 = r2
            
            # Calcular superposición
            x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
            y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
            
            # Calcular porcentajes de superposición
            h_overlap_ratio = x_overlap / min(w1, w2) if min(w1, w2) > 0 else 0
            v_overlap_ratio = y_overlap / min(h1, h2) if min(h1, h2) > 0 else 0
            
            # Calcular distancia entre centros
            c1_x, c1_y = x1 + w1/2, y1 + h1/2
            c2_x, c2_y = x2 + w2/2, y2 + h2/2
            distance = ((c2_x - c1_x)**2 + (c2_y - c1_y)**2)**0.5
            
            # Verificar si hay suficiente superposición o están lo suficientemente cerca
            return (h_overlap_ratio > h_threshold or 
                    v_overlap_ratio > v_threshold or 
                    distance < distance_threshold)
                
        except Exception as e:
            print(f"Error en should_merge_regions: {e}")
            return False

    def _filter_merged_regions(self, regions: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """Filtra las regiones fusionadas por tamaño y proporción"""
        try:
            filtered = []
            
            for x, y, w, h in regions:
                # Calcular métricas
                area = w * h
                aspect_ratio = w / h if h > 0 else 0
                
                # Criterios de filtrado más permisivos
                is_valid_size = 100 < area < 1000000  # Rango de área más amplio
                is_valid_ratio = 0.1 < aspect_ratio < 10  # Rango de proporción más amplio
                
                if is_valid_size and is_valid_ratio:
                    filtered.append((x, y, w, h))
            
            return filtered
            
        except Exception as e:
            print(f"Error en filter_merged_regions: {e}")
            return regions

    def _extract_padded_region(self, image: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
        """Extrae una región con padding adicional"""
        try:
            height, width = image.shape[:2]
            
            # Aumentar padding para capturar más contexto
            pad_x = int(w * 0.2)  # Reducido de 0.3
            pad_y = int(h * 0.2)  # Reducido de 0.3
            
            # Calcular coordenadas con padding
            x1 = max(0, x - pad_x)
            y1 = max(0, y - pad_y)
            x2 = min(width, x + w + pad_x)
            y2 = min(height, y + h + pad_y)
            
            # Extraer región
            region = image[y1:y2, x1:x2].copy()
            
            # Agrandar la región extraída pero no tanto
            scale_factor = 2  # Reducido de 4
            enlarged = cv2.resize(
                region, 
                None, 
                fx=scale_factor, 
                fy=scale_factor, 
                interpolation=cv2.INTER_CUBIC
            )
            
            return enlarged
            
        except Exception as e:
            print(f"Error en extract_padded_region: {e}")
            return image[y:y+h, x:x+w].copy()

    def _create_formula_image(self, image: Image.Image) -> ctk.CTkImage:
        """Crea una imagen CTk a partir de una imagen PIL"""
        try:
            return ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=image.size
            )
        except Exception as e:
            print(f"Error creando CTkImage: {e}")
            return None

    def _ensure_black_text(self, image: Image.Image) -> Image.Image:
        """Asegura que el texto sea negro sobre fondo blanco"""
        try:
            # Convertir a array numpy
            img_array = np.array(image)
            
            # Calcular brillo promedio
            if len(img_array.shape) == 3:
                brightness = np.mean(img_array, axis=2)
            else:
                brightness = img_array
            
            # Determinar si el texto es claro u oscuro
            is_dark_text = np.mean(brightness) > 128
            
            if is_dark_text:
                # Invertir colores si el texto es claro
                if len(img_array.shape) == 3:
                    img_array = 255 - img_array
                else:
                    img_array = 255 - img_array
                
            return Image.fromarray(img_array)
            
        except Exception as e:
            print(f"Error en ensure_black_text: {e}")
            return image

    def _detect_by_projection(self, image: np.ndarray, direction: str) -> List[Tuple[int, int, int, int]]:
        """Detecta regiones usando proyección horizontal o vertical"""
        try:
            height, width = image.shape[:2]
            regions = []
            
            # Calcular proyección
            if direction == 'horizontal':
                projection = np.sum(image, axis=1)
                threshold = np.mean(projection) * 0.5
                
                # Encontrar regiones continuas
                start_y = None
                for y in range(height):
                    if projection[y] > threshold:
                        if start_y is None:
                            start_y = y
                    elif start_y is not None:
                        h = y - start_y
                        if h > 10:  # Altura mínima
                            regions.append((0, start_y, width, h))
                        start_y = None
                    
            else:  # vertical
                projection = np.sum(image, axis=0)
                threshold = np.mean(projection) * 0.5
                
                # Encontrar regiones continuas
                start_x = None
                for x in range(width):
                    if projection[x] > threshold:
                        if start_x is None:
                            start_x = x
                    elif start_x is not None:
                        w = x - start_x
                        if w > 10:  # Ancho mínimo
                            regions.append((start_x, 0, w, height))
                        start_x = None
            
            return regions
            
        except Exception as e:
            print(f"Error en detección por proyección: {e}")
            return []

    def _enhance_image_quality(self, image: Image.Image) -> Image.Image:
        """Mejora agresiva de la calidad de imagen"""
        try:
            # 1. Convertir a escala de grises si es color
            if image.mode == 'RGB':
                image = image.convert('L')
            
            # 2. Aplicar mejoras más agresivas
            enhancers = [
                (ImageEnhance.Contrast, 2.5),     # Más contraste
                (ImageEnhance.Sharpness, 2.0),    # Más nitidez
                (ImageEnhance.Brightness, 1.3),    # Más brillo
            ]
            
            enhanced = image
            for enhancer_class, factor in enhancers:
                enhancer = enhancer_class(enhanced)
                enhanced = enhancer.enhance(factor)
            
            # 3. Binarización adaptativa
            enhanced_array = np.array(enhanced)
            binary = cv2.adaptiveThreshold(
                enhanced_array,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2
            )
            
            # 4. Operaciones morfológicas
            kernel = np.ones((2,2), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return Image.fromarray(binary)
            
        except Exception as e:
            print(f"Error en mejora de calidad: {e}")
            return image

    def _try_multiple_ocr(self, image: Image.Image) -> str:
        """Intenta OCR con diferentes configuraciones y tamaños"""
        try:
            # Asegurar tamaño mínimo inicial
            min_size = 200
            if image.size[0] < min_size or image.size[1] < min_size:
                ratio = min_size / min(image.size)
                new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            attempts = [
                # Intento 1: Imagen original mejorada
                lambda img: self.model(self._enhance_for_ocr(img)),
                
                # Intento 2: Imagen más grande
                lambda img: self.model(img.resize(
                    (img.size[0]*2, img.size[1]*2), 
                    Image.Resampling.LANCZOS
                )),
                
                # Intento 3: Imagen con más contraste
                lambda img: self.model(ImageEnhance.Contrast(img).enhance(2.5)),
                
                # Intento 4: Imagen en blanco y negro
                lambda img: self.model(img.convert('L')),
                
                # Intento 5: Imagen muy grande
                lambda img: self.model(img.resize(
                    (img.size[0]*4, img.size[1]*4), 
                    Image.Resampling.LANCZOS
                ))
            ]
            
            for i, attempt_func in enumerate(attempts, 1):
                try:
                    print(f"Intento OCR #{i}")
                    latex = attempt_func(image)
                    if latex:
                        cleaned = self.clean_latex(latex)
                        if cleaned and self.is_valid_latex(cleaned):
                            return cleaned
                except Exception as e:
                    print(f"Error en intento OCR #{i}: {e}")
                    continue
            
            # Si ningún intento funcionó, intentar con la imagen original
            return self.clean_latex(self.model(image))
            
        except Exception as e:
            print(f"Error en múltiples OCR: {e}")
            return None
