import customtkinter as ctk
from typing import Dict, List, Tuple, Optional
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageGrab
from datetime import datetime
from core.exporters import FormulaExporter
from core.stats import FormulaStats
from core.config import UI_CONFIG, APP_CONFIG
import numpy as np
from core.database import DatabaseManager
from core.formula_extractor import FormulaExtractor
from bson.objectid import ObjectId
import logging
import os

class TeacherPanel:
    def __init__(self, user_data: Dict, formula_extractor: FormulaExtractor):
        self.window = ctk.CTk()
        self.window.title("Panel de Profesor")
        self.window.geometry(APP_CONFIG["WINDOW_SIZE"])
        
        self.user_data = user_data
        self.formula_extractor = formula_extractor
        self.db_manager = DatabaseManager.get_instance()
        
        # Cargar imágenes
        self.load_images()
        
        # Obtener colección de fórmulas
        try:
            self.formulas = self.db_manager.get_collection("FORMULAS")
            self.total_formulas = self.formulas.count_documents({"user_id": str(self.user_data["_id"])})
        except Exception as e:
            print(f"Error al obtener colecciones: {e}")
            messagebox.showerror(
                "Error de Base de Datos",
                "No se pudieron cargar las fórmulas. Por favor, contacte al administrador."
            )
        
        self._create_widgets()

    def load_images(self):
        """Carga las imágenes necesarias para la interfaz"""
        try:
            # Asegurarse de que el directorio assets existe
            assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
            if not os.path.exists(assets_dir):
                os.makedirs(assets_dir)

            # Cargar imagen de bienvenida
            welcome_path = os.path.join(assets_dir, "image.png")
            if os.path.exists(welcome_path):
                self.welcome_image = Image.open(welcome_path)
                self.welcome_image = self.welcome_image.resize((400, 400))
                self.welcome_photo = ImageTk.PhotoImage(self.welcome_image)
            else:
                self.welcome_photo = None
                print("Imagen de bienvenida no encontrada")

        except Exception as e:
            print(f"Error cargando imágenes: {e}")
            self.welcome_photo = None

    def _create_widgets(self):
        """Crea la interfaz principal del panel de profesor"""
        self.window.configure(fg_color=UI_CONFIG["COLORS"]["background"])
        
        # Frame superior con información del usuario
        self._create_top_frame()
        
        # Panel principal dividido en dos secciones
        main_container = ctk.CTkFrame(self.window, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Panel izquierdo para acciones
        self._create_left_panel(main_container)
        
        # Panel derecho para visualización
        self._create_right_panel(main_container)

    def _create_top_frame(self):
        """Crea el frame superior con información del usuario"""
        top_frame = ctk.CTkFrame(self.window, fg_color=UI_CONFIG["COLORS"]["primary"])
        top_frame.pack(fill="x", padx=10, pady=5)

        # Frame para información del usuario
        user_info = ctk.CTkFrame(top_frame, fg_color="transparent")
        user_info.pack(side="left", padx=10)

        # Icono de usuario
        ctk.CTkLabel(
            user_info,
            text="👤",
            font=("Roboto", 24)
        ).pack(side="left", padx=5)

        # Información del usuario
        user_text = ctk.CTkFrame(user_info, fg_color="transparent")
        user_text.pack(side="left", padx=5)

        ctk.CTkLabel(
            user_text,
            text=self.user_data['name'],
            font=("Roboto", 16, "bold")
        ).pack(anchor="w")

        ctk.CTkLabel(
            user_text,
            text=self.user_data['email'],
            font=("Roboto", 12),
            text_color="gray"
        ).pack(anchor="w")

        # Frame para estadísticas rápidas
        stats_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        stats_frame.pack(side="left", expand=True, padx=20)

        ctk.CTkLabel(
            stats_frame,
            text=f"📚 Total Fórmulas: {self.total_formulas}",
            font=("Roboto", 14)
        ).pack(side="left", padx=10)

        # Botón de cerrar sesión
        logout_btn = ctk.CTkButton(
            top_frame,
            text="Cerrar Sesión",
            command=self.logout,
            fg_color=UI_CONFIG["COLORS"]["error"],
            hover_color="#C62828",
            width=120,
            height=35
        )
        logout_btn.pack(side="right", padx=10)

    def logout(self):
        """Maneja el cierre de sesión cierra la ventana y mandar al login"""
        try:
            # Cerrar ventana actual
            self.window.destroy()

            # Mostrar ventana de login
            from core.app import FormulaExtractorApp
            app = FormulaExtractorApp()
            app.run()
        except Exception as e:
            print(f"Error al cerrar sesión: {e}")

    def capture_screen(self):
        """Captura una parte de la pantalla"""
        self.window.iconify()  # Minimizar ventana
        
        instruction_window = self._create_instruction_window()
        
        def on_capture():
            try:
                captured_image = ImageGrab.grabclipboard()
                if captured_image is None:
                    messagebox.showerror(
                        "Error",
                        "No se encontró ninguna captura en el portapapeles.\n"
                        "Por favor, realice una captura usando Win + Shift + S"
                    )
                    return
                
                instruction_window.destroy()
                
                # Procesar imagen con FormulaExtractor
                image_array = np.array(captured_image)
                formulas = self.formula_extractor.process_image(image_array)
                
                if formulas:
                    # Mostrar fórmulas detectadas
                    self.formula_extractor.show_formulas(
                        formulas,
                        on_save_callback=self.save_formulas
                    )
                else:
                    messagebox.showinfo(
                        "Información",
                        "No se detectaron fórmulas en la imagen capturada."
                    )
                    
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Error al procesar la captura: {str(e)}"
                )
            finally:
                self.window.deiconify()

        # Botón para procesar captura
        ctk.CTkButton(
            instruction_window,
            text="Procesar Captura",
            command=on_capture,
            fg_color=UI_CONFIG["COLORS"]["primary"],
            hover_color=UI_CONFIG["COLORS"]["button_hover"],
            height=40
        ).pack(pady=10)

        instruction_window.protocol(
            "WM_DELETE_WINDOW",
            lambda: [instruction_window.destroy(), self.window.deiconify()]
        )

    def _create_instruction_window(self):
        """Crea una ventana con instrucciones para capturar pantalla"""
        window = ctk.CTkToplevel(self.window)
        window.title("Captura de Pantalla")
        window.geometry("500x300")
        window.configure(fg_color=UI_CONFIG["COLORS"]["background"])

        # Frame principal
        main_frame = ctk.CTkFrame(window, fg_color=UI_CONFIG["COLORS"]["surface"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        ctk.CTkLabel(
            main_frame,
            text="📸 Captura de Pantalla",
            font=("Roboto", 20, "bold")
        ).pack(pady=10)

        # Instrucciones
        instructions = [
            "1. Presione Win + Shift + S",
            "2. Seleccione el área con la fórmula",
            "3. Espere a que se copie al portapapeles",
            "4. Presione 'Procesar Captura'"
        ]

        for instruction in instructions:
            ctk.CTkLabel(
                main_frame,
                text=instruction,
                font=("Roboto", 14)
            ).pack(pady=5)

        return window

    def run(self):
        """Inicia la ventana del panel"""
        self.window.mainloop()

    def _create_left_panel(self, parent):
        """Crea el panel izquierdo con las acciones principales"""
        left_panel = ctk.CTkFrame(parent, fg_color=UI_CONFIG["COLORS"]["surface"], width=300)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Título del panel
        ctk.CTkLabel(
            left_panel,
            text="Acciones",
            font=("Roboto", 20, "bold")
        ).pack(pady=20)
        
        # Sección de Captura
        capture_section = ctk.CTkFrame(left_panel, fg_color=UI_CONFIG["COLORS"]["background"])
        capture_section.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            capture_section,
            text="📸 Captura",
            font=("Roboto", 16, "bold"),
            text_color=UI_CONFIG["COLORS"]["accent"]
        ).pack(pady=10)
        
        ctk.CTkButton(
            capture_section,
            text="Cargar PDF",
            command=self.load_pdf,
            fg_color=UI_CONFIG["COLORS"]["primary"],
            hover_color=UI_CONFIG["COLORS"]["button_hover"],
            height=40
        ).pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            capture_section,
            text="Capturar Pantalla",
            command=self.capture_screen,
            fg_color=UI_CONFIG["COLORS"]["primary"],
            hover_color=UI_CONFIG["COLORS"]["button_hover"],
            height=40
        ).pack(fill="x", padx=10, pady=5)
        
        # Sección de Gestión
        management_section = ctk.CTkFrame(left_panel, fg_color=UI_CONFIG["COLORS"]["background"])
        management_section.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            management_section,
            text="📚 Gestión",
            font=("Roboto", 16, "bold"),
            text_color=UI_CONFIG["COLORS"]["accent"]
        ).pack(pady=10)
        
        ctk.CTkButton(
            management_section,
            text="Mis Fórmulas",
            command=self.show_my_formulas,
            fg_color=UI_CONFIG["COLORS"]["secondary"],
            hover_color=UI_CONFIG["COLORS"]["button_hover"],
            height=40
        ).pack(fill="x", padx=10, pady=5)
        
        # Sección de Herramientas
        tools_section = ctk.CTkFrame(left_panel, fg_color=UI_CONFIG["COLORS"]["background"])
        tools_section.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            tools_section,
            text="🛠️ Herramientas",
            font=("Roboto", 16, "bold"),
            text_color=UI_CONFIG["COLORS"]["accent"]
        ).pack(pady=10)
        
        ctk.CTkButton(
            tools_section,
            text="Exportar",
            command=self.show_export_options,
            fg_color=UI_CONFIG["COLORS"]["secondary"],
            hover_color=UI_CONFIG["COLORS"]["button_hover"],
            height=40
        ).pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            tools_section,
            text="Estadísticas",
            command=self.show_statistics,
            fg_color=UI_CONFIG["COLORS"]["secondary"],
            hover_color=UI_CONFIG["COLORS"]["button_hover"],
            height=40
        ).pack(fill="x", padx=10, pady=5)

    def _create_right_panel(self, parent):
        """Crea el panel derecho para visualización"""
        right_panel = ctk.CTkFrame(parent, fg_color=UI_CONFIG["COLORS"]["surface"])
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Área de trabajo
        workspace_label = ctk.CTkLabel(
            right_panel,
            text="Área de Trabajo",
            font=("Roboto", 20, "bold")
        )
        workspace_label.pack(pady=20)
        
        # Panel de bienvenida
        welcome_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        welcome_frame.pack(fill="both", expand=True)
        
        # Mostrar imagen de bienvenida si existe
        if hasattr(self, 'welcome_photo') and self.welcome_photo:
            ctk.CTkLabel(
                welcome_frame,
                image=self.welcome_photo,
                text=""
            ).pack(pady=20)
        
        # Mensaje de bienvenida
        ctk.CTkLabel(
            welcome_frame,
            text=f"¡Bienvenido, {self.user_data['name']}!",
            font=("Roboto", 24, "bold"),
            text_color=UI_CONFIG["COLORS"]["accent"]
        ).pack(pady=20)
        
        # Instrucciones
        instructions = [
            "1. Capture fórmulas usando Win + Shift + S",
            "2. Cargue PDFs con fórmulas matemáticas",
            "3. Gestione su biblioteca de fórmulas",
            "4. Exporte y analice sus fórmulas"
        ]
        
        for instruction in instructions:
            ctk.CTkLabel(
                welcome_frame,
                text=instruction,
                font=("Roboto", 14),
                text_color="gray"
            ).pack(pady=5)

    def load_pdf(self):
        """Carga y procesa un archivo PDF"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar PDF",
            filetypes=[("PDF files", "*.pdf")]
        )
        
        if file_path:
            try:
                formulas = self.formula_extractor.process_pdf(file_path)
                if formulas:
                    self.formula_extractor.show_formulas(
                        formulas,
                        on_save_callback=self.save_formulas
                    )
                else:
                    messagebox.showinfo(
                        "Información",
                        "No se detectaron fórmulas en el PDF."
                    )
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Error al procesar el PDF: {str(e)}"
                )

    def save_formulas(self, formulas: List[dict]):
        """Guarda las fórmulas en la base de datos"""
        try:
            for formula in formulas:
                formula_doc = {
                    "latex": formula["latex"],
                    "type": formula["type"],
                    "difficulty": formula["difficulty"],
                    "user_id": str(self.user_data["_id"]),
                    "timestamp": datetime.now()
                }
                self.formulas.insert_one(formula_doc)
            
            # Actualizar contador de fórmulas
            self.total_formulas = self.formulas.count_documents(
                {"user_id": str(self.user_data["_id"])}
            )
            
            messagebox.showinfo(
                "Éxito",
                f"Se guardaron {len(formulas)} fórmulas correctamente"
            )
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al guardar las fórmulas: {str(e)}"
            )

    def show_my_formulas(self):
        """Muestra las fórmulas guardadas del profesor"""
        try:
            # Obtener fórmulas del usuario
            formulas = list(self.formulas.find({"user_id": str(self.user_data["_id"])}))
            
            if not formulas:
                messagebox.showinfo(
                    "Información",
                    "No tiene fórmulas guardadas aún"
                )
                return
            
            # Crear ventana
            formulas_window = ctk.CTkToplevel(self.window)
            formulas_window.title("Mis Fórmulas")
            formulas_window.geometry("1400x800")
            formulas_window.configure(fg_color="#1a1a1a")
            
            # Frame principal con grid
            main_frame = ctk.CTkFrame(formulas_window, fg_color="#2B2B2B")
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Header con información
            header = ctk.CTkFrame(main_frame, fg_color="transparent", height=60)
            header.pack(fill="x", pady=(0, 20))
            
            # Título e información
            title_frame = ctk.CTkFrame(header, fg_color="transparent")
            title_frame.pack(side="left")
            
            ctk.CTkLabel(
                title_frame,
                text="📚 Mis Fórmulas",
                font=("Roboto", 24, "bold")
            ).pack(side="left", padx=10)
            
            ctk.CTkLabel(
                title_frame,
                text=f"Total: {len(formulas)}",
                font=("Roboto", 14),
                text_color="gray"
            ).pack(side="left", padx=10)
            
            # Panel de búsqueda y filtros
            search_frame = ctk.CTkFrame(main_frame, fg_color="#404040")
            search_frame.pack(fill="x", pady=(0, 10))
            
            # Buscador
            search_box = ctk.CTkFrame(search_frame, fg_color="transparent")
            search_box.pack(side="left", fill="x", expand=True, padx=10, pady=10)
            
            search_entry = ctk.CTkEntry(
                search_box,
                placeholder_text="🔍 Buscar fórmula...",
                width=300,
                height=40,
                font=("Roboto", 14)
            )
            search_entry.pack(side="left", padx=5)
            
            # Filtros
            filters_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
            filters_frame.pack(side="right", padx=10)
            
            type_filter = ctk.CTkOptionMenu(
                filters_frame,
                values=["Todos", "Álgebra", "Cálculo", "Geometría", "Trigonometría"],
                width=150,
                font=("Roboto", 12)
            )
            type_filter.pack(side="left", padx=5)
            
            difficulty_filter = ctk.CTkOptionMenu(
                filters_frame,
                values=["Todos", "Fácil", "Medio", "Difícil"],
                width=150,
                font=("Roboto", 12)
            )
            difficulty_filter.pack(side="left", padx=5)
            
            # Frame para las fórmulas con grid
            formulas_container = ctk.CTkFrame(main_frame, fg_color="transparent")
            formulas_container.pack(fill="both", expand=True)
            
            # ScrollableFrame para las fórmulas
            formulas_frame = ctk.CTkScrollableFrame(
                formulas_container,
                fg_color="transparent",
                label_text="Fórmulas",
                label_font=("Roboto", 14, "bold")
            )
            formulas_frame.pack(fill="both", expand=True)
            
            def update_formulas(*args):
                try:
                    # Limpiar frame actual
                    for widget in formulas_frame.winfo_children():
                        widget.destroy()
                    
                    # Obtener términos de búsqueda
                    search_term = search_entry.get().lower()
                    type_term = type_filter.get()
                    difficulty_term = difficulty_filter.get()
                    
                    # Construir query
                    query = {"user_id": str(self.user_data["_id"])}
                    
                    if type_term != "Todos":
                        query["type"] = type_term
                    if difficulty_term != "Todos":
                        query["difficulty"] = difficulty_term
                    
                    if search_term:
                        query["$or"] = [
                            {"latex": {"$regex": search_term, "$options": "i"}},
                            {"type": {"$regex": search_term, "$options": "i"}},
                        ]
                    
                    # Obtener fórmulas filtradas
                    filtered_formulas = list(self.formulas.find(query).sort("scan_date", -1))
                    
                    if not filtered_formulas:
                        ctk.CTkLabel(
                            formulas_frame,
                            text="No se encontraron fórmulas",
                            font=("Roboto", 14),
                            text_color="gray"
                        ).pack(pady=20)
                        return
                    
                    # Mostrar fórmulas en grid
                    for formula in filtered_formulas:
                        try:
                            card = self._create_formula_card(formulas_frame, formula)
                            if card:  # Solo agregar si la tarjeta se creó correctamente
                                card.pack(fill="x", pady=5, padx=10)
                        except Exception as e:
                            print(f"Error creando tarjeta para fórmula: {e}")
                            continue
                        
                except Exception as e:
                    print(f"Error en update_formulas: {e}")
                    messagebox.showerror("Error", "Error actualizando la lista de fórmulas")
            
            # Vincular búsqueda y filtros
            search_entry.bind('<KeyRelease>', update_formulas)
            type_filter.configure(command=update_formulas)
            difficulty_filter.configure(command=update_formulas)
            
            # Cargar fórmulas iniciales
            update_formulas()
            
            # Centrar ventana
            formulas_window.update_idletasks()
            width = formulas_window.winfo_width()
            height = formulas_window.winfo_height()
            x = (formulas_window.winfo_screenwidth() // 2) - (width // 2)
            y = (formulas_window.winfo_screenheight() // 2) - (height // 2)
            formulas_window.geometry(f'+{x}+{y}')
            
        except Exception as e:
            print(f"Error detallado: {e}")
            messagebox.showerror(
                "Error",
                f"Error al mostrar fórmulas: {str(e)}"
            )

    def _create_formula_card(self, parent, formula: dict) -> Optional[ctk.CTkFrame]:
        """Crea una tarjeta para mostrar una fórmula"""
        try:
            if not formula or not isinstance(formula, dict):
                print(f"Fórmula inválida: {formula}")
                return None
            
            # Verificar que la fórmula tenga los campos necesarios
            required_fields = ['latex', 'type', 'difficulty']
            if not all(field in formula for field in required_fields):
                print(f"Fórmula incompleta, campos faltantes: {formula}")
                return None
            
            card = ctk.CTkFrame(parent, fg_color="#404040")
            
            # Grid para mejor organización
            grid = ctk.CTkFrame(card, fg_color="transparent")
            grid.pack(fill="x", padx=10, pady=10)
            
            # LaTeX con vista previa
            latex_frame = ctk.CTkFrame(grid, fg_color="#2B2B2B")
            latex_frame.pack(fill="x", pady=(0,10))
            
            # Renderizar fórmula
            try:
                rendered_formula = self.formula_extractor.viewer._render_latex(formula.get('latex', ''))
                if rendered_formula:
                    preview_img = ctk.CTkImage(
                        light_image=rendered_formula,
                        dark_image=rendered_formula,
                        size=rendered_formula.size
                    )
                    
                    ctk.CTkLabel(
                        latex_frame,
                        image=preview_img,
                        text=""
                    ).pack(pady=5)
            except Exception as e:
                print(f"Error renderizando fórmula: {e}")
                ctk.CTkLabel(
                    latex_frame,
                    text=formula.get('latex', ''),
                    font=("Roboto", 14),
                    wraplength=800
                ).pack(pady=5, padx=10)
            
            # Metadatos
            meta_frame = ctk.CTkFrame(grid, fg_color="transparent")
            meta_frame.pack(fill="x")
            
            # Tipo con color
            type_label = ctk.CTkLabel(
                meta_frame,
                text=formula.get('type', 'No clasificado'),
                font=("Roboto", 12),
                fg_color="#1E88E5",
                corner_radius=5,
                padx=10
            )
            type_label.pack(side="left", padx=5)
            
            # Dificultad con color
            difficulty_colors = {
                "Fácil": "#4CAF50",
                "Medio": "#FF9800",
                "Difícil": "#F44336"
            }
            
            diff_label = ctk.CTkLabel(
                meta_frame,
                text=formula.get('difficulty', 'No definida'),
                font=("Roboto", 12),
                fg_color=difficulty_colors.get(formula.get('difficulty', ''), "#757575"),
                corner_radius=5,
                padx=10
            )
            diff_label.pack(side="left", padx=5)
            
            # Fecha - Manejo mejorado
            date_str = "No disponible"
            try:
                # Intentar obtener la fecha de diferentes campos
                date_obj = None
                if 'timestamp' in formula and isinstance(formula['timestamp'], datetime):
                    date_obj = formula['timestamp']
                elif 'scan_date' in formula:
                    if isinstance(formula['scan_date'], datetime):
                        date_obj = formula['scan_date']
                    elif isinstance(formula['scan_date'], str):
                        date_obj = datetime.strptime(formula['scan_date'], "%Y-%m-%d %H:%M:%S")
                elif 'last_modified' in formula and isinstance(formula['last_modified'], datetime):
                    date_obj = formula['last_modified']
                
                if date_obj:
                    date_str = date_obj.strftime("%Y-%m-%d")
            except Exception as e:
                print(f"Error procesando fecha: {e}")
            
            ctk.CTkLabel(
                meta_frame,
                text=f"📅 {date_str}",
                font=("Roboto", 12),
                text_color="gray"
            ).pack(side="left", padx=10)
            
            # Botones de acción
            actions = ctk.CTkFrame(grid, fg_color="transparent")
            actions.pack(fill="x", pady=(10,0))
            
            # Botón editar
            ctk.CTkButton(
                actions,
                text="✏️ Editar",
                command=lambda: self._edit_formula(formula),
                width=100,
                fg_color="#2196F3",
                hover_color="#1976D2"
            ).pack(side="left", padx=2)
            
            # Botón eliminar
            ctk.CTkButton(
                actions,
                text="🗑️ Eliminar",
                command=lambda: self._delete_formula(formula, card),
                width=100,
                fg_color="#F44336",
                hover_color="#D32F2F"
            ).pack(side="left", padx=2)
            
            return card
            
        except Exception as e:
            print(f"Error creando tarjeta: {e}")
            print(f"Detalles de la fórmula: {formula}")
            return None

    def _edit_formula(self, formula: dict):
        """Edita una fórmula existente"""
        try:
            # Crear ventana de edición
            edit_window = ctk.CTkToplevel(self.window)
            edit_window.title("Editar Fórmula")
            edit_window.geometry("800x600")
            edit_window.configure(fg_color="#1a1a1a")
            
            # Frame principal
            main_frame = ctk.CTkFrame(edit_window, fg_color="#2B2B2B")
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Vista previa de la fórmula
            preview_frame = ctk.CTkFrame(main_frame, fg_color="#404040")
            preview_frame.pack(fill="x", pady=10)
            
            # Renderizar fórmula
            try:
                rendered = self.formula_extractor.viewer._render_latex(formula.get('latex', ''))
                if rendered:
                    preview_img = ctk.CTkImage(
                        light_image=rendered,
                        dark_image=rendered,
                        size=rendered.size
                    )
                    
                    ctk.CTkLabel(
                        preview_frame,
                        image=preview_img,
                        text=""
                    ).pack(pady=10)
            except Exception as e:
                print(f"Error renderizando fórmula: {e}")
            
            # Campo LaTeX
            latex_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            latex_frame.pack(fill="x", pady=10)
            
            ctk.CTkLabel(
                latex_frame,
                text="LaTeX:",
                font=("Roboto", 14, "bold")
            ).pack(anchor="w")
            
            latex_entry = ctk.CTkEntry(
                latex_frame,
                height=40,
                font=("Roboto", 14)
            )
            latex_entry.insert(0, formula.get('latex', ''))
            latex_entry.pack(fill="x", pady=5)
            
            # Opciones
            options_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            options_frame.pack(fill="x", pady=10)
            
            # Tipo
            type_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
            type_frame.pack(side="left", fill="x", expand=True)
            
            ctk.CTkLabel(
                type_frame,
                text="Tipo:",
                font=("Roboto", 12)
            ).pack(anchor="w")
            
            type_menu = ctk.CTkOptionMenu(
                type_frame,
                values=["Álgebra", "Cálculo", "Geometría", "Trigonometría"],
                width=150
            )
            type_menu.set(formula.get('type', 'Álgebra'))
            type_menu.pack(fill="x", pady=5)
            
            # Dificultad
            diff_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
            diff_frame.pack(side="right", fill="x", expand=True, padx=10)
            
            ctk.CTkLabel(
                diff_frame,
                text="Dificultad:",
                font=("Roboto", 12)
            ).pack(anchor="w")
            
            diff_menu = ctk.CTkOptionMenu(
                diff_frame,
                values=["Fácil", "Medio", "Difícil"],
                width=150
            )
            diff_menu.set(formula.get('difficulty', 'Medio'))
            diff_menu.pack(fill="x", pady=5)
            
            # Botones de acción
            buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            buttons_frame.pack(fill="x", pady=20)
            
            def update_preview():
                try:
                    new_latex = latex_entry.get()
                    rendered = self.formula_extractor.viewer._render_latex(new_latex)
                    if rendered:
                        preview_img = ctk.CTkImage(
                            light_image=rendered,
                            dark_image=rendered,
                            size=rendered.size
                        )
                        
                        for widget in preview_frame.winfo_children():
                            widget.destroy()
                        
                        ctk.CTkLabel(
                            preview_frame,
                            image=preview_img,
                            text=""
                        ).pack(pady=10)
                except Exception as e:
                    messagebox.showerror("Error", f"Error actualizando vista previa: {e}")
            
            def save_changes():
                try:
                    # Actualizar en la base de datos
                    self.formulas.update_one(
                        {"_id": formula["_id"]},
                        {
                            "$set": {
                                "latex": latex_entry.get(),
                                "type": type_menu.get(),
                                "difficulty": diff_menu.get(),
                                "last_modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                        }
                    )
                    
                    messagebox.showinfo("Éxito", "Fórmula actualizada correctamente")
                    edit_window.destroy()
                    
                    # Actualizar la vista
                    self.show_my_formulas()
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Error guardando cambios: {e}")
            
            # Botón actualizar vista previa
            ctk.CTkButton(
                buttons_frame,
                text="↻ Actualizar Vista Previa",
                command=update_preview,
                fg_color="#4CAF50",
                hover_color="#388E3C",
                width=150
            ).pack(side="left", padx=5)
            
            # Botón guardar
            ctk.CTkButton(
                buttons_frame,
                text="💾 Guardar",
                command=save_changes,
                fg_color="#2196F3",
                hover_color="#1976D2",
                width=100
            ).pack(side="left", padx=5)
            
            # Botón cancelar
            ctk.CTkButton(
                buttons_frame,
                text="❌ Cancelar",
                command=edit_window.destroy,
                fg_color="#F44336",
                hover_color="#D32F2F",
                width=100
            ).pack(side="right", padx=5)
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al editar fórmula: {str(e)}"
            )

    def _delete_formula(self, formula: dict, card: ctk.CTkFrame):
        """Elimina una fórmula"""
        try:
            if messagebox.askyesno(
                "Confirmar eliminación",
                "¿Está seguro que desea eliminar esta fórmula?"
            ):
                # Eliminar de la base de datos
                result = self.formulas.delete_one({"_id": formula["_id"]})
                
                if result.deleted_count > 0:
                    # Actualizar contador
                    self.total_formulas = self.formulas.count_documents(
                        {"user_id": str(self.user_data["_id"])}
                    )
                    
                    # Eliminar tarjeta
                    card.destroy()
                    
                    messagebox.showinfo(
                        "Éxito",
                        "Fórmula eliminada correctamente"
                    )
                    
                    # Actualizar la vista si no quedan fórmulas
                    if self.total_formulas == 0:
                        self.show_my_formulas()
                else:
                    messagebox.showerror(
                        "Error",
                        "No se pudo eliminar la fórmula"
                    )
                
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al eliminar fórmula: {str(e)}"
            )

    def show_export_options(self):
        """Muestra las opciones de exportación"""
        try:
            # Obtener fórmulas del usuario
            formulas = list(self.formulas.find({"user_id": str(self.user_data["_id"])}))
            
            if not formulas:
                messagebox.showinfo(
                    "Información",
                    "No hay fórmulas para exportar"
                )
                return
            
            # Crear ventana de exportación
            export_window = ctk.CTkToplevel(self.window)
            export_window.title("Exportar Fórmulas")
            export_window.geometry("400x300")
            export_window.configure(fg_color=UI_CONFIG["COLORS"]["background"])
            
            # Frame principal
            main_frame = ctk.CTkFrame(export_window, fg_color=UI_CONFIG["COLORS"]["surface"])
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Título
            ctk.CTkLabel(
                main_frame,
                text="📊 Exportar Fórmulas",
                font=("Roboto", 18, "bold")
            ).pack(pady=10)
            
            # Información
            ctk.CTkLabel(
                main_frame,
                text=f"Se exportarán {len(formulas)} fórmulas",
                font=("Roboto", 12)
            ).pack(pady=5)
            
            # Opciones de exportación
            formats = [
                ("LaTeX", "tex", "📝"),
                ("HTML", "html", "🌐"),
                ("Excel", "xlsx", "📊")
            ]
            
            for format_name, extension, icon in formats:
                ctk.CTkButton(
                    main_frame,
                    text=f"{icon} Exportar a {format_name}",
                    command=lambda ext=extension: self.export_formulas(formulas, ext),
                    height=35
                ).pack(fill="x", padx=10, pady=5)
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al mostrar opciones de exportación: {str(e)}"
            )

    def export_formulas(self, formulas: List[dict], format_type: str):
        """Exporta las fórmulas al formato especificado"""
        try:
            file_types = {
                "tex": ("Archivo LaTeX", "*.tex"),
                "html": ("Página web", "*.html"),
                "xlsx": ("Archivo Excel", "*.xlsx")
            }
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=f".{format_type}",
                filetypes=[file_types[format_type]]
            )
            
            if file_path:
                exporter = FormulaExporter()
                if format_type == "tex":
                    exporter.to_latex(formulas, file_path)
                elif format_type == "html":
                    exporter.to_html(formulas, file_path)
                else:
                    exporter.to_excel(formulas, file_path)
                
                messagebox.showinfo(
                    "Éxito",
                    "Fórmulas exportadas correctamente"
                )
                
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al exportar: {str(e)}"
            )

    def show_statistics(self):
        """Muestra estadísticas de las fórmulas"""
        try:
            stats = FormulaStats(self.formulas)
            user_stats = stats.get_user_stats(str(self.user_data["_id"]))
            
            # Crear ventana de estadísticas
            stats_window = ctk.CTkToplevel(self.window)
            stats_window.title("Estadísticas")
            stats_window.geometry("800x600")
            stats_window.configure(fg_color=UI_CONFIG["COLORS"]["background"])
            
            # Frame principal
            main_frame = ctk.CTkFrame(stats_window, fg_color=UI_CONFIG["COLORS"]["surface"])
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Título
            ctk.CTkLabel(
                main_frame,
                text="📊 Estadísticas de Fórmulas",
                font=("Roboto", 24, "bold")
            ).pack(pady=20)
            
            # Resumen
            summary_frame = ctk.CTkFrame(main_frame)
            summary_frame.pack(fill="x", pady=10)
            
            # Calcular dificultad promedio
            difficulty_map = {
                "Fácil": 1,
                "Medio": 2,
                "Difícil": 3
            }
            
            total_difficulty = 0
            difficulty_count = 0
            
            for formula in self.formulas.find({"user_id": str(self.user_data["_id"])}):
                if "difficulty" in formula:
                    difficulty_value = difficulty_map.get(formula["difficulty"], 0)
                    if difficulty_value > 0:
                        total_difficulty += difficulty_value
                        difficulty_count += 1
            
            avg_difficulty = "No disponible"
            if difficulty_count > 0:
                avg_value = total_difficulty / difficulty_count
                if avg_value < 1.67:
                    avg_difficulty = "Fácil"
                elif avg_value < 2.34:
                    avg_difficulty = "Medio"
                else:
                    avg_difficulty = "Difícil"
            
            stats_data = [
                ("Total de Fórmulas", user_stats["total_formulas"], "📚"),
                ("Tipos Diferentes", len(user_stats["type_distribution"]), "📑"),
                ("Dificultad Promedio", avg_difficulty, "📈")
            ]
            
            for title, value, icon in stats_data:
                stat_card = ctk.CTkFrame(summary_frame)
                stat_card.pack(side="left", expand=True, padx=5, fill="x")
                
                ctk.CTkLabel(
                    stat_card,
                    text=icon,
                    font=("Roboto", 36)
                ).pack(pady=5)
                
                ctk.CTkLabel(
                    stat_card,
                    text=title,
                    font=("Roboto", 14)
                ).pack()
                
                ctk.CTkLabel(
                    stat_card,
                    text=str(value),
                    font=("Roboto", 24, "bold")
                ).pack(pady=5)
            
            # Mostrar distribuciones
            self._show_distribution(
                main_frame,
                "Distribución por Tipo",
                user_stats["type_distribution"]
            )
            
            # Mostrar distribución de dificultad
            difficulty_distribution = {}
            for formula in self.formulas.find({"user_id": str(self.user_data["_id"])}):
                difficulty = formula.get("difficulty", "No definida")
                difficulty_distribution[difficulty] = difficulty_distribution.get(difficulty, 0) + 1
            
            self._show_distribution(
                main_frame,
                "Distribución por Dificultad",
                difficulty_distribution
            )
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al mostrar estadísticas: {str(e)}"
            )

    def _show_distribution(self, parent, title: str, distribution: dict):
        """Muestra una distribución en forma de barras"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=10, padx=20)
        
        ctk.CTkLabel(
            frame,
            text=title,
            font=("Roboto", 16, "bold")
        ).pack(pady=10)
        
        total = sum(distribution.values())
        
        for category, count in distribution.items():
            percentage = (count / total) * 100 if total > 0 else 0
            
            bar_frame = ctk.CTkFrame(frame)
            bar_frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(
                bar_frame,
                text=category,
                width=100
            ).pack(side="left", padx=5)
            
            progress = ctk.CTkProgressBar(bar_frame)
            progress.pack(side="left", fill="x", expand=True, padx=5)
            progress.set(percentage / 100)
            
            ctk.CTkLabel(
                bar_frame,
                text=f"{percentage:.1f}%"
            ).pack(side="right", padx=5)

if __name__ == "__main__":
    # Datos de ejemplo para pruebas
    test_user = {
        "name": "Profesor Test",
        "email": "test@example.com",
        "_id": "test_id"
    }
    
    formula_extractor = FormulaExtractor()
    panel = TeacherPanel(test_user, formula_extractor)
    panel.run()
