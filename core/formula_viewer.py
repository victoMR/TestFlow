import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw
from typing import List, Dict
import logging
import re
import tkinter.messagebox as messagebox
import io
import os
import tempfile
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Usar backend no interactivo

class FormulaViewer:
    """Clase para mostrar y editar fórmulas detectadas"""
    
    def __init__(self):
        # Desactivar logging de pix2tex
        logging.getLogger('pix2tex').setLevel(logging.ERROR)
        
        # Variables de estado
        self.current_formula = None
        self.current_entry = None
        self.formulas = []
        
        # Configuración para renderizado
        self.temp_dir = tempfile.mkdtemp()
        
        # Configurar matplotlib para renderizado
        plt.rcParams.update({
            'text.usetex': False,  # No usar LaTeX externo
            'mathtext.default': 'regular',
            'font.family': 'DejaVu Sans',
            'figure.facecolor': '#2B2B2B',
            'text.color': 'white',
            'axes.facecolor': '#2B2B2B'
        })
        
    def _render_latex(self, latex: str) -> Image.Image:
        """Renderiza una expresión LaTeX usando matplotlib"""
        try:
            # Limpiar la fórmula
            latex = self._prepare_latex_for_matplotlib(latex)
            
            # Crear figura
            fig = plt.figure(figsize=(6, 1))
            fig.patch.set_alpha(0.0)
            
            # Renderizar fórmula
            plt.text(0.5, 0.5, f'${latex}$',
                    horizontalalignment='center',
                    verticalalignment='center',
                    fontsize=14,
                    color='white')
            
            # Configurar ejes
            plt.axis('off')
            
            # Guardar en buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', 
                       bbox_inches='tight',
                       transparent=True,
                       dpi=150,
                       pad_inches=0.1)
            plt.close(fig)
            
            # Convertir a imagen PIL
            buf.seek(0)
            image = Image.open(buf)
            
            return image
            
        except Exception as e:
            print(f"Error renderizando LaTeX: {e}")
            return self._create_error_image(str(e))
    
    def _prepare_latex_for_matplotlib(self, latex: str) -> str:
        """Prepara el LaTeX para ser renderizado por matplotlib"""
        # Reemplazar comandos LaTeX que matplotlib no soporta
        replacements = {
            r'\frac': r'\dfrac',  # Usar fracciones displaystyle
            r'\mathbf': r'\mathbf',
            r'\text': r'\mathrm',
            r'\left': '',
            r'\right': '',
            r'\\': r'\\'
        }
        
        for old, new in replacements.items():
            latex = latex.replace(old, new)
        
        # Limpiar espacios extras
        latex = re.sub(r'\s+', ' ', latex)
        
        return latex
    
    def _create_error_image(self, error_msg: str) -> Image.Image:
        """Crea una imagen de error"""
        # Crear una imagen roja con mensaje de error
        img = Image.new('RGB', (400, 50), '#2B2B2B')
        from PIL import ImageDraw
        
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), f"Error: {error_msg}", fill='red')
        
        return img

    def _create_formula_card(self, parent, formula: dict, index: int):
        """Crea una tarjeta para una fórmula con vista previa renderizada"""
        card = ctk.CTkFrame(parent, fg_color="#404040")
        card.pack(fill="x", pady=5, padx=5)
        
        # Header con número y tipo
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)
        
        # Número de fórmula con estilo
        formula_num = ctk.CTkLabel(
            header,
            text=f"Fórmula #{index}",
            font=("Roboto", 14, "bold"),
            fg_color="#2B2B2B",
            corner_radius=5,
            width=100
        )
        formula_num.pack(side="left")
        
        # Tipo de fórmula
        formula_type = ctk.CTkLabel(
            header,
            text=formula.get("type", "No clasificada"),
            font=("Roboto", 12),
            fg_color="#1E88E5",
            corner_radius=5,
            padx=10
        )
        formula_type.pack(side="right")
        
        # Panel de visualización
        preview_frame = ctk.CTkFrame(card, fg_color="#2B2B2B")
        preview_frame.pack(fill="x", padx=10, pady=5)
        
        # LaTeX original
        latex_label = ctk.CTkLabel(
            preview_frame,
            text="LaTeX:",
            font=("Roboto", 12, "bold")
        )
        latex_label.pack(anchor="w", padx=5)
        
        latex_text = ctk.CTkTextbox(
            preview_frame,
            height=40,
            font=("Courier", 12),
            fg_color="#404040"
        )
        latex_text.pack(fill="x", padx=5, pady=2)
        latex_text.insert("1.0", formula.get("latex", ""))
        latex_text.configure(state="disabled")
        
        # Vista previa renderizada
        preview_label = ctk.CTkLabel(
            preview_frame,
            text="Vista previa:",
            font=("Roboto", 12, "bold")
        )
        preview_label.pack(anchor="w", padx=5, pady=(10,0))
        
        try:
            # Intentar renderizar la fórmula
            rendered = self._render_latex(formula.get("latex", ""))
            if rendered:
                preview_img = ctk.CTkImage(
                    light_image=rendered,
                    dark_image=rendered,
                    size=rendered.size
                )
                
                img_label = ctk.CTkLabel(
                    preview_frame,
                    image=preview_img,
                    text=""
                )
                img_label.pack(pady=5)
                img_label.image = preview_img  # Mantener referencia
            else:
                ctk.CTkLabel(
                    preview_frame,
                    text="Error al renderizar fórmula",
                    text_color="red"
                ).pack(pady=5)
                
        except Exception as e:
            print(f"Error mostrando vista previa: {e}")
            ctk.CTkLabel(
                preview_frame,
                text="Error al renderizar fórmula",
                text_color="red"
            ).pack(pady=5)
        
        # Panel de edición
        edit_frame = ctk.CTkFrame(card, fg_color="transparent")
        edit_frame.pack(fill="x", padx=10, pady=5)
        
        # Campo editable de LaTeX
        latex_entry = ctk.CTkEntry(
            edit_frame,
            placeholder_text="LaTeX",
            height=35,
            font=("Roboto", 14)
        )
        latex_entry.insert(0, formula.get("latex", ""))
        latex_entry.pack(fill="x", pady=2)
        
        # Establecer como entry actual cuando recibe el foco
        latex_entry.bind("<FocusIn>", lambda e: setattr(self, 'current_entry', latex_entry))
        
        # Opciones de clasificación
        options_frame = ctk.CTkFrame(edit_frame, fg_color="transparent")
        options_frame.pack(fill="x", pady=2)
        
        # Tipo
        type_menu = ctk.CTkOptionMenu(
            options_frame,
            values=["Álgebra", "Cálculo", "Geometría", "Trigonometría", "Estadística"],
            width=150
        )
        type_menu.set(formula.get("type", "Álgebra"))
        type_menu.pack(side="left", padx=2)
        
        # Dificultad
        diff_menu = ctk.CTkOptionMenu(
            options_frame,
            values=["Fácil", "Medio", "Difícil"],
            width=150
        )
        diff_menu.set(formula.get("difficulty", "Medio"))
        diff_menu.pack(side="left", padx=2)

        # Poner el resultado de la formula con un txtBox
        result_label = ctk.CTkLabel(
            preview_frame,
            text="Resultado:",
            font=("Roboto", 12, "bold")
        )

        result_label.pack(anchor="w", padx=5, pady=(10,0))

        result_text = ctk.CTkTextbox(
            preview_frame,
            height=40,
            font=("Courier", 12),
            fg_color="#404040"
        )

        result_text.pack(fill="x", padx=5, pady=2)

        
        # Botones de acción
        actions_frame = ctk.CTkFrame(edit_frame, fg_color="transparent")
        actions_frame.pack(fill="x", pady=5)
        
        # Botón para actualizar vista previa
        update_btn = ctk.CTkButton(
            actions_frame,
            text="↻ Actualizar Vista Previa",
            command=lambda: self._update_preview(latex_entry.get(), preview_frame),
            fg_color="#4CAF50",
            hover_color="#388E3C",
            width=150
        )
        update_btn.pack(side="left", padx=2)
        
        # Botón para copiar LaTeX
        copy_btn = ctk.CTkButton(
            actions_frame,
            text="📋 Copiar LaTeX",
            command=lambda: self._copy_latex(latex_entry.get()),
            fg_color="#2196F3",
            hover_color="#1976D2",
            width=120
        )
        copy_btn.pack(side="left", padx=2)
        
        # Guardar referencias
        formula["entry"] = latex_entry
        formula["type_menu"] = type_menu
        formula["diff_menu"] = diff_menu
        formula["result_text"] = result_text
        
        return card

    def _update_preview(self, latex: str, preview_frame):
        """Actualiza la vista previa de una fórmula"""
        try:
            # Limpiar vista previa anterior
            for widget in preview_frame.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and not widget.cget("text"):
                    widget.destroy()
            
            # Renderizar nueva vista previa
            rendered = self._render_latex(latex)
            if rendered:
                preview_img = ctk.CTkImage(
                    light_image=rendered,
                    dark_image=rendered,
                    size=rendered.size
                )
                
                img_label = ctk.CTkLabel(
                    preview_frame,
                    image=preview_img,
                    text=""
                )
                img_label.pack(pady=5)
                img_label.image = preview_img
                
                messagebox.showinfo(
                    "Éxito",
                    "Vista previa actualizada correctamente"
                )
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo renderizar la fórmula"
                )
                
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error actualizando vista previa: {str(e)}"
            )

    def _copy_latex(self, latex: str):
        """Copia el LaTeX al portapapeles"""
        try:
            self.window.clipboard_clear()
            self.window.clipboard_append(latex)
            messagebox.showinfo(
                "Éxito",
                "LaTeX copiado al portapapeles"
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error copiando LaTeX: {str(e)}"
            )

    def __del__(self):
        """Limpia archivos temporales al destruir la instancia"""
        try:
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error limpiando archivos temporales: {e}")
        
    def _create_header(self, parent):
        """Crea el header con información y controles"""
        header = ctk.CTkFrame(parent, fg_color="#2B2B2B", height=80)
        header.pack(fill="x", pady=(0, 20))
        
        # Panel izquierdo con título e información
        info_panel = ctk.CTkFrame(header, fg_color="transparent")
        info_panel.pack(side="left", padx=20, pady=10)
        
        # Título con icono
        ctk.CTkLabel(
            info_panel,
            text="📚",
            font=("Roboto", 32)
        ).pack(side="left", padx=(0, 10))
        
        title_frame = ctk.CTkFrame(info_panel, fg_color="transparent")
        title_frame.pack(side="left")
        
        ctk.CTkLabel(
            title_frame,
            text=f"Fórmulas Detectadas ({len(self.formulas)})",
            font=("Roboto", 24, "bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_frame,
            text="Edite y verifique las fórmulas antes de guardar",
            font=("Roboto", 12),
            text_color="gray"
        ).pack(anchor="w")
        
        # Panel derecho con controles
        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.pack(side="right", padx=20)
        
        # Botón de ayuda
        help_btn = ctk.CTkButton(
            controls,
            text="❓ Ayuda",
            width=100,
            command=self._show_help
        )
        help_btn.pack(side="right", padx=5)
        
        return header

    def _create_calculator_panel(self, parent):
        """Crea el panel de la calculadora matemática"""
        calculator = ctk.CTkFrame(parent, width=300, fg_color="#2B2B2B")
        calculator.pack(side="right", fill="y", padx=10)
        
        # Título
        ctk.CTkLabel(
            calculator,
            text="🔢 Calculadora LaTeX",
            font=("Roboto", 16, "bold")
        ).pack(pady=10)
        
        # Secciones de la calculadora
        sections = {
            "Operadores Básicos": ["+", "-", "\\times", "\\div", "=", "\\pm", "\\neq"],
            "Subíndices y Superíndices": ["_", "^", "_{}", "^{}", "_{}^{}"],
            "Fracciones": ["\\frac{}{}", "\\dfrac{}{}", "\\tfrac{}{}"],
            "Raíces": ["\\sqrt{}", "\\sqrt[n]{}", "\\sqrt[3]{}"],
            "Letras Griegas": ["\\alpha", "\\beta", "\\gamma", "\\theta", "\\pi", "\\sigma"],
            "Funciones": ["\\sin", "\\cos", "\\tan", "\\log", "\\ln", "\\lim"],
            "Símbolos": ["\\infty", "\\partial", "\\sum", "\\int", "\\prod", "\\rightarrow"],
            "Paréntesis": ["()", "[]", "\\{\\}", "\\left(\\right)", "\\left[\\right]"]
        }
        
        # Crear frame scrollable para las secciones
        sections_frame = ctk.CTkScrollableFrame(calculator, fg_color="transparent")
        sections_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Crear cada sección
        for section_name, symbols in sections.items():
            section_frame = ctk.CTkFrame(sections_frame, fg_color="#404040")
            section_frame.pack(fill="x", pady=5, padx=2)
            
            # Título de la sección
            ctk.CTkLabel(
                section_frame,
                text=section_name,
                font=("Roboto", 12, "bold")
            ).pack(anchor="w", padx=5, pady=2)
            
            # Grid de botones
            buttons_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            buttons_frame.pack(fill="x", padx=5, pady=2)
            
            for i, symbol in enumerate(symbols):
                btn = ctk.CTkButton(
                    buttons_frame,
                    text=symbol,
                    width=60,
                    height=30,
                    command=lambda s=symbol: self._insert_symbol(s),
                    fg_color="#2B2B2B",
                    hover_color="#1a1a1a"
                )
                btn.grid(row=i//4, column=i%4, padx=2, pady=2, sticky="nsew")
                
                # Tooltip
                self._create_tooltip(btn, f"Insertar {symbol}")
            
            # Configurar grid
            for i in range(4):
                buttons_frame.grid_columnconfigure(i, weight=1)
        
        # Panel de vista previa
        preview_frame = ctk.CTkFrame(calculator, fg_color="#404040", height=100)
        preview_frame.pack(fill="x", padx=5, pady=5)
        
        self.preview_label = ctk.CTkLabel(
            preview_frame,
            text="Vista previa de la fórmula",
            height=80
        )
        self.preview_label.pack(fill="both", expand=True)
        
        return calculator

    def _insert_symbol(self, symbol: str):
        """Inserta un símbolo en el entry activo"""
        if self.current_entry:
            pos = self.current_entry.index("insert")
            current_text = self.current_entry.get()
            new_text = current_text[:pos] + symbol + current_text[pos:]
            self.current_entry.delete(0, "end")
            self.current_entry.insert(0, new_text)
            self.current_entry.icursor(pos + len(symbol))
            self.current_entry.focus()
            
            # Actualizar vista previa
            if hasattr(self, 'preview_label'):
                rendered = self._render_latex(new_text)
                if rendered:
                    preview_img = ctk.CTkImage(
                        light_image=rendered,
                        dark_image=rendered,
                        size=rendered.size
                    )
                    self.preview_label.configure(image=preview_img)
                    self.preview_label.image = preview_img

    def _show_help(self):
        """Muestra una ventana de ayuda"""
        help_window = ctk.CTkToplevel(self.window)
        help_window.title("Ayuda")
        help_window.geometry("600x400")
        help_window.configure(fg_color="#1a1a1a")
        
        # Frame principal
        main_frame = ctk.CTkFrame(help_window, fg_color="#2B2B2B")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(
            main_frame,
            text="❓ Ayuda - Uso del Editor de Fórmulas",
            font=("Roboto", 18, "bold")
        ).pack(pady=10)
        
        # Contenido de ayuda
        help_text = """
        🔍 Guía de Uso:
        
        1. Vista Previa:
           - Las fórmulas detectadas se muestran con su representación LaTeX
           - Puede ver la vista previa renderizada de cada fórmula
        
        2. Editor:
           - Modifique el código LaTeX directamente si es necesario
           - Use los botones de actualización para ver los cambios
           - Seleccione el tipo y dificultad de cada fórmula
        
        3. Acciones:
           - Actualizar Vista Previa: Renderiza los cambios en LaTeX
           - Copiar LaTeX: Copia el código al portapapeles
           - Guardar Todo: Guarda todas las fórmulas editadas
        
        4. Consejos:
           - Verifique que las fórmulas estén correctamente detectadas
           - Puede editar el LaTeX manualmente si es necesario
           - No olvide guardar los cambios antes de cerrar
        """
        
        help_label = ctk.CTkLabel(
            main_frame,
            text=help_text,
            font=("Roboto", 14),
            justify="left",
            wraplength=500
        )
        help_label.pack(padx=20, pady=20)
        
        # Botón de cerrar
        ctk.CTkButton(
            main_frame,
            text="Cerrar",
            command=help_window.destroy,
            width=100,
            height=35,
            fg_color="#F44336",
            hover_color="#D32F2F"
        ).pack(pady=10)
        
        # Centrar la ventana
        help_window.update_idletasks()
        width = help_window.winfo_width()
        height = help_window.winfo_height()
        x = (help_window.winfo_screenwidth() // 2) - (width // 2)
        y = (help_window.winfo_screenheight() // 2) - (height // 2)
        help_window.geometry(f'+{x}+{y}')

    def _create_editor_panel(self, parent, formulas: List[dict]):
        """Crea el panel de edición de fórmulas"""
        editor = ctk.CTkScrollableFrame(
            parent,
            width=600,
            label_text="Editor",
            fg_color="#2B2B2B"
        )
        editor.pack(side="left", fill="both", expand=True, padx=10)
        
        for i, formula in enumerate(formulas, 1):
            self._create_formula_card(editor, formula, i)

    def _create_action_buttons(self, parent, formulas: List[dict], on_save_callback=None):
        """Crea los botones de acción"""
        actions = ctk.CTkFrame(parent, fg_color="#2B2B2B")
        actions.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkButton(
            actions,
            text="💾 Guardar Todo",
            command=lambda: self._save_formulas(formulas, on_save_callback),
            font=("Roboto", 14),
            height=40,
            fg_color="#4CAF50",
            hover_color="#388E3C"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            actions,
            text="❌ Cancelar",
            command=parent.destroy,
            font=("Roboto", 14),
            height=40,
            fg_color="#F44336",
            hover_color="#D32F2F"
        ).pack(side="right", padx=5)

    def _save_formulas(self, formulas: List[dict], callback=None):
        """Guarda las fórmulas editadas"""
        for formula in formulas:
            formula["latex"] = formula["entry"].get()
            formula["type"] = formula["type_menu"].get()
            formula["difficulty"] = formula["diff_menu"].get()
            formula["result"] = formula["result_text"].get("1.0", "end-1c") # Obtiene el texto del txtBox el 1.0 es la fila 1 columna 0 y end-1c es el final menos el salto de linea
        
        if callback:
            callback(formulas)

    def _create_thumbnails_panel(self, parent):
        """Crea el panel de miniaturas de las fórmulas"""
        thumbnails = ctk.CTkScrollableFrame(
            parent,
            width=200,
            label_text="Vista Previa",
            fg_color="#2B2B2B"
        )
        thumbnails.pack(side="left", fill="y", padx=(0, 10))

        # Guardar referencia al panel de miniaturas
        self.thumbnails_panel = thumbnails
        
        # Etiqueta cuando no hay miniaturas
        self.no_thumbnails_label = ctk.CTkLabel(
            thumbnails,
            text="No hay miniaturas\ndisponibles",
            font=("Roboto", 12),
            text_color="gray"
        )
        self.no_thumbnails_label.pack(pady=20)

        return thumbnails

    def _add_thumbnail(self, parent, formula: dict, index: int):
        """Agrega una miniatura de fórmula al panel"""
        # Ocultar etiqueta de no miniaturas si existe
        if hasattr(self, 'no_thumbnails_label'):
            self.no_thumbnails_label.pack_forget()

        # Crear frame para la miniatura
        thumb_frame = ctk.CTkFrame(parent, fg_color="#404040")
        thumb_frame.pack(fill="x", pady=2, padx=5)

        # Número de fórmula
        ctk.CTkLabel(
            thumb_frame,
            text=f"#{index}",
            font=("Roboto", 12, "bold"),
            width=30,
            height=30,
            fg_color="#2B2B2B",
            corner_radius=15
        ).pack(pady=5)

        # Miniatura de la fórmula
        if "image" in formula:
            try:
                # Crear una versión en miniatura de la imagen
                thumbnail_size = (180, 60)  # Tamaño fijo para miniaturas
                thumbnail = formula["image"]._light_image.copy()  # Acceder a la imagen PIL subyacente
                thumbnail.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                
                # Convertir a CTkImage
                ctk_thumb = ctk.CTkImage(
                    light_image=thumbnail,
                    dark_image=thumbnail,
                    size=thumbnail.size
                )
                
                # Mostrar miniatura
                thumb_label = ctk.CTkLabel(
                    thumb_frame,
                    image=ctk_thumb,
                    text=""
                )
                thumb_label.pack(pady=5)
                
                # Guardar referencia para evitar que se elimine por el recolector de basura
                thumb_label.image = ctk_thumb
                
            except Exception as e:
                print(f"Error creando miniatura: {e}")
                # Si hay error, mostrar un placeholder
                ctk.CTkLabel(
                    thumb_frame,
                    text="[Vista previa\nno disponible]",
                    font=("Roboto", 10),
                    text_color="gray"
                ).pack(pady=5)

        # Tipo y dificultad
        info_frame = ctk.CTkFrame(thumb_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=5, pady=2)

        ctk.CTkLabel(
            info_frame,
            text=formula.get("type", "Sin tipo"),
            font=("Roboto", 10),
            fg_color="#2B2B2B",
            corner_radius=5,
            padx=5
        ).pack(side="left", padx=2)

        ctk_label = ctk.CTkLabel(
            info_frame,
            text=formula.get("difficulty", "Sin dificultad"),
            font=("Roboto", 10),
            fg_color="#2B2B2B",
            corner_radius=5,
            padx=5
        )
        ctk_label.pack(side="right", padx=2)

        # Hacer la miniatura clickeable
        thumb_frame.bind("<Button-1>", lambda e: self._on_thumbnail_click(formula))
        
        return thumb_frame

    def _on_thumbnail_click(self, formula: dict):
        """Maneja el clic en una miniatura"""
        # Aquí puedes agregar la lógica para cuando se hace clic en una miniatura
        # Por ejemplo, resaltar la fórmula correspondiente en el panel de edición
        if hasattr(self, 'current_formula'):
            self.current_formula = formula
            # Actualizar la interfaz según sea necesario 

    def show_formulas(self, formulas: List[dict], on_save_callback=None):
        """Muestra las fórmulas detectadas"""
        if not formulas:
            print("No hay fórmulas para mostrar")
            messagebox.showinfo(
                "Información",
                "No se detectaron fórmulas en la imagen."
            )
            return
        
        print(f"Mostrando {len(formulas)} fórmulas")
        self.formulas = formulas
        
        # Crear ventana principal
        self.window = ctk.CTkToplevel()
        self.window.title("Fórmulas Detectadas")
        self.window.geometry("1400x900")
        self.window.configure(fg_color="#1a1a1a")
        
        # Header con información
        self._create_header(self.window)
        
        # Panel principal con 3 columnas
        main_panel = ctk.CTkFrame(self.window)
        main_panel.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Crear paneles
        thumbnails = self._create_thumbnails_panel(main_panel)
        editor = self._create_editor_panel(main_panel, formulas)
        calculator = self._create_calculator_panel(main_panel)
        
        # Botones de acción
        self._create_action_buttons(self.window, formulas, on_save_callback)
        
        # Centrar la ventana
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'+{x}+{y}')
        
        return self.window 

    def _create_tooltip(self, widget, text: str):
        """Crea un tooltip para un widget"""
        def enter(event):
            try:
                # Crear tooltip
                tooltip = ctk.CTkToplevel()
                tooltip.wm_overrideredirect(True)
                
                # Obtener posición del mouse
                x = widget.winfo_rootx() + widget.winfo_width()
                y = widget.winfo_rooty() + widget.winfo_height()
                
                # Ajustar posición del tooltip
                tooltip.wm_geometry(f"+{x+10}+{y+10}")
                tooltip.configure(fg_color="#2B2B2B")
                
                # Crear label con el texto
                label = ctk.CTkLabel(
                    tooltip,
                    text=text,
                    font=("Roboto", 12),
                    text_color="white",
                    fg_color="#2B2B2B",
                    corner_radius=6,
                    padx=10,
                    pady=5
                )
                label.pack()
                
                # Guardar referencia al tooltip
                widget.tooltip = tooltip
                widget.tooltip_label = label
                
            except Exception as e:
                print(f"Error creando tooltip: {e}")
        
        def leave(event):
            try:
                if hasattr(widget, 'tooltip'):
                    widget.tooltip.destroy()
                    del widget.tooltip
                    if hasattr(widget, 'tooltip_label'):
                        del widget.tooltip_label
            except Exception as e:
                print(f"Error eliminando tooltip: {e}")
        
        # Vincular eventos
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave) 