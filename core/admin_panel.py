import customtkinter as ctk
from typing import Dict
from core.config import MONGODB_CONFIG, APP_CONFIG, UI_CONFIG
from core.database import DatabaseManager
import bcrypt
from datetime import datetime, timedelta
from tkinter import messagebox
from core.login import LoginWindow
from bson import ObjectId
import logging

class AdminPanel:
    def __init__(self, user_data: Dict):
        self.window = ctk.CTk()
        self.window.title("Panel de Administración")
        self.window.geometry(APP_CONFIG["WINDOW_SIZE"])
        
        self.user_data = user_data
        
        # Inicializar conexión a la base de datos
        print("\n=== DEBUG: Verificando conexión a MongoDB ===")
        try:
            # Inicializar DatabaseManager
            self.db_manager = DatabaseManager.get_instance()
            
            # Verificar que la conexión sea exitosa
            if not self.db_manager.is_connected():
                raise Exception("No se pudo establecer la conexión con MongoDB")
            
            # Obtener referencias a las colecciones
            self.users = self.db_manager.get_collection("USERS")
            self.formulas = self.db_manager.get_collection("FORMULAS")
            
            # Verificar si las colecciones existen
            if not self.db_manager.collection_exists("USERS") or not self.db_manager.collection_exists("FORMULAS"):
                raise Exception("No se pudieron obtener las colecciones")
            
            # Insertar algunas fórmulas de ejemplo si la colección está vacía
            if self.formulas.count_documents({}) == 0:
                example_formulas = [
                    {
                        "latex": "E = mc^2",
                        "type": "Física",
                        "difficulty": "Moderado",
                        "description": "Ecuación de Einstein de la relatividad",
                        "user_id": str(self.user_data.get("_id", "")),
                        "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    {
                        "latex": "a^2 + b^2 = c^2",
                        "type": "Geometría",
                        "difficulty": "Fácil",
                        "description": "Teorema de Pitágoras",
                        "user_id": str(self.user_data.get("_id", "")),
                        "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    {
                        "latex": "\\frac{d}{dx}(x^n) = nx^{n-1}",
                        "type": "Cálculo",
                        "difficulty": "Moderado",
                        "description": "Regla de la potencia en derivación",
                        "user_id": str(self.user_data.get("_id", "")),
                        "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                ]
                
                self.formulas.insert_many(example_formulas)
                print(f"Se insertaron {len(example_formulas)} fórmulas de ejemplo")
            
            print(f"Total de fórmulas en DB: {self.formulas.count_documents({})}")
            
        except Exception as e:
            print(f"Error al configurar la base de datos: {e}")
            messagebox.showerror(
                "Error de Conexión",
                "No se pudo establecer la conexión con la base de datos. "
                "Por favor, verifica que MongoDB esté ejecutándose."
            )
            self.window.destroy()
            return
        
        print("=== Fin DEBUG ===\n")
        
        self.app = None  # Referencia a la aplicación principal
        
        # Configurar tema oscuro
        self.window.configure(fg_color="#1a1a1a")
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Configurar estilo de la tabla
        self.table_styles = {
            "header_bg": "#2B2B2B",
            "row_bg": "#404040",
            "alternate_row_bg": "#363636",
            "hover_bg": "#505050"
        }
        
        self._create_widgets()
        
    def set_app(self, app):
        """Establece la referencia a la aplicación principal"""
        self.app = app
        
    def _create_widgets(self):
        # Frame superior para información y cerrar sesión
        top_frame = ctk.CTkFrame(self.window, fg_color="#2B2B2B")
        top_frame.pack(fill="x", padx=20, pady=(10, 0))
        
        # Información del usuario actual
        user_info = ctk.CTkLabel(
            top_frame,
            text=f"Admin: {self.user_data['name']}",
            font=("Roboto", 12, "bold"),
            text_color="white"
        )
        user_info.pack(side="left", padx=10)
        
        # Botón de cerrar sesión
        logout_btn = ctk.CTkButton(
            top_frame,
            text="Cerrar Sesión",
            command=self._logout,
            fg_color=UI_CONFIG["COLORS"]["error"],
            width=100
        )
        logout_btn.pack(side="right", padx=10)
        
        # Crear tabs con estilo mejorado
        self.tabview = ctk.CTkTabview(
            self.window,
            fg_color="#2B2B2B"
        )
        self.tabview.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Tabs
        self.users_tab = self.tabview.add("Gestión de Usuarios")
        self.formulas_tab = self.tabview.add("Gestión de Fórmulas")
        self.stats_tab = self.tabview.add("Estadísticas")
        
        # Configurar color de fondo para cada tab
        for tab in [self.users_tab, self.formulas_tab, self.stats_tab]:
            tab.configure(fg_color="#1a1a1a")
        
        self._create_users_tab()
        self._create_formulas_tab()
        self._create_stats_tab()
    
    def _logout(self):
        """Maneja el cierre de sesión"""
        if messagebox.askyesno("Cerrar Sesión", "¿Está seguro que desea cerrar sesión?"):
            try:
                # Guardar una referencia al app
                app = self.app
                
                # Destruir la ventana actual
                if hasattr(self, 'window') and self.window:
                    self.window.destroy()
                
                # Crear nueva instancia de login después de destruir la ventana actual
                if app:
                    login_window = LoginWindow(app.handle_login_success)
                    login_window.run()
                    
            except Exception as e:
                print(f"Error durante el cierre de sesión: {e}")
    
    def run(self):
        """Inicia la ventana del panel de administración"""
        try:
            if hasattr(self, 'window') and self.window:
                self.window.mainloop()
        except Exception as e:
            print(f"Error al ejecutar el panel de administración: {e}")

    def _create_users_tab(self):
        """Crea la pestaña de gestión de usuarios"""
        # Frame para búsqueda
        search_frame = ctk.CTkFrame(self.users_tab, fg_color="#2B2B2B")
        search_frame.pack(fill="x", padx=20, pady=10)
        
        self.search_user = ctk.CTkEntry(
            search_frame,
            placeholder_text="Buscar usuario...",
            fg_color="#404040",
            text_color="white"
        )
        self.search_user.pack(side="left", padx=5, fill="x", expand=True)
        
        ctk.CTkButton(
            search_frame,
            text="🔍 Buscar",
            command=self._search_users,
            fg_color=UI_CONFIG["COLORS"]["primary"],
            width=100
        ).pack(side="left", padx=5)
        
        # Frame para nuevo usuario
        new_user_frame = ctk.CTkFrame(self.users_tab, fg_color="#2B2B2B")
        new_user_frame.pack(fill="x", padx=20, pady=10)
        
        # Campos para nuevo usuario
        self.user_entries = {}
        fields = [
            ("username", "Usuario"),
            ("password", "Contraseña"),
            ("name", "Nombre completo"),
            ("email", "Correo electrónico")
        ]
        
        for field, placeholder in fields:
            entry = ctk.CTkEntry(
                new_user_frame,
                placeholder_text=placeholder,
                fg_color="#404040",
                text_color="white",
                width=200
            )
            entry.pack(side="left", padx=5)
            self.user_entries[field] = entry
        
        ctk.CTkButton(
            new_user_frame,
            text="➕ Agregar Profesor",
            command=self._add_user,
            fg_color=UI_CONFIG["COLORS"]["success"],
            width=150
        ).pack(side="left", padx=5)
        
        # Lista de usuarios
        self.users_frame = ctk.CTkScrollableFrame(self.users_tab, fg_color="#1a1a1a")
        self.users_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self._update_users_list()

    def _create_formulas_tab(self):
        """Crea la pestaña de gestión de fórmulas"""
        # Código de depuración
        print("\n=== DEBUG: Verificando fórmulas ===")
        formulas_list = list(self.formulas.find())
        print(f"Total de fórmulas encontradas: {len(formulas_list)}")
        for formula in formulas_list:
            print(f"Fórmula: {formula}")
        print("=== Fin DEBUG ===\n")
        
        # Frame para búsqueda y filtros
        top_frame = ctk.CTkFrame(self.formulas_tab, fg_color="#2B2B2B")
        top_frame.pack(fill="x", padx=20, pady=10)
        
        # Buscador de fórmulas
        self.formula_search = ctk.CTkEntry(
            top_frame,
            placeholder_text="Buscar fórmula...",
            fg_color="#404040",
            text_color="white"
        )
        self.formula_search.pack(side="left", padx=5, fill="x", expand=True)
        
        ctk.CTkButton(
            top_frame,
            text="🔍 Buscar",
            command=self._search_formulas,
            fg_color=UI_CONFIG["COLORS"]["primary"],
            width=100
        ).pack(side="left", padx=5)
        
        # Frame para agregar nueva fórmula
        new_formula_frame = ctk.CTkFrame(self.formulas_tab, fg_color="#2B2B2B")
        new_formula_frame.pack(fill="x", padx=20, pady=10)
        
        # Campos para nueva fórmula
        self.formula_entries = {}
        fields = [
            ("latex", "LaTeX de la fórmula"),
            ("type", "Tipo (Álgebra/Cálculo)"),
            ("difficulty", "Dificultad"),
            ("description", "Descripción")
        ]
        
        for field, placeholder in fields:
            if field in ["type", "difficulty"]:
                if field == "type":
                    values = ["Álgebra", "Cálculo", "Trigonometría", "Geometría"]
                else:
                    values = ["Fácil", "Moderado", "Difícil"]
                
                entry = ctk.CTkOptionMenu(
                    new_formula_frame,
                    values=values,
                    fg_color="#404040",
                    width=200
                )
            else:
                entry = ctk.CTkEntry(
                    new_formula_frame,
                    placeholder_text=placeholder,
                    fg_color="#404040",
                    text_color="white",
                    width=200
                )
            entry.pack(side="left", padx=5)
            self.formula_entries[field] = entry
        
        ctk.CTkButton(
            new_formula_frame,
            text="➕ Agregar Fórmula",
            command=self._add_formula,
            fg_color=UI_CONFIG["COLORS"]["success"],
            width=150
        ).pack(side="left", padx=5)

        # Lista de fórmulas (Agregamos esto que faltaba)
        self.formulas_frame = ctk.CTkScrollableFrame(
            self.formulas_tab,
            fg_color="#1a1a1a"
        )
        self.formulas_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Actualizar lista inicial de fórmulas
        self._update_formulas_list()

    def _create_stats_tab(self):
        """Crea la pestaña de estadísticas"""
        stats_frame = ctk.CTkFrame(self.stats_tab, fg_color="#2B2B2B")
        stats_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Estadísticas generales
        total_users = self.users.count_documents({"role": "teacher"})
        total_formulas = self.formulas.count_documents({})
        
        stats = [
            ("👥 Total de Profesores", total_users),
            ("📚 Total de Fórmulas", total_formulas),
            ("📊 Fórmulas esta semana", self._get_formulas_this_week())
        ]
        
        for label, value in stats:
            frame = ctk.CTkFrame(stats_frame, fg_color="#2B2B2B")
            frame.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(
                frame,
                text=label,
                font=("Roboto", 16),
                text_color="white"
            ).pack()
            
            ctk.CTkLabel(
                frame,
                text=str(value),
                font=("Roboto", 24, "bold"),
                text_color=UI_CONFIG["COLORS"]["accent"]
            ).pack()

    def _get_formulas_this_week(self):
        """Obtiene el número de fórmulas agregadas esta semana"""
        week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = week_start - timedelta(days=week_start.weekday())
        
        return self.formulas.count_documents({
            "scan_date": {"$gte": week_start.strftime("%Y-%m-%d %H:%M:%S")}
        })

    def _search_users(self):
        """Busca usuarios según el término ingresado"""
        search_term = self.search_user.get()
        if search_term:
            users = self.users.find({
                "$or": [
                    {"username": {"$regex": search_term, "$options": "i"}},
                    {"name": {"$regex": search_term, "$options": "i"}},
                    {"email": {"$regex": search_term, "$options": "i"}}
                ],
                "role": "teacher"
            })
        else:
            users = self.users.find({"role": "teacher"})
        
        self._update_users_list(users)

    def _update_users_list(self, users=None):
        """Actualiza la lista de usuarios"""
        # Limpiar lista actual
        for widget in self.users_frame.winfo_children():
            widget.destroy()
        
        if users is None:
            users = self.users.find({"role": "teacher"})
        
        # Crear encabezados
        headers = ["Usuario", "Nombre", "Email", "Acciones"]
        header_frame = ctk.CTkFrame(self.users_frame, fg_color="#2B2B2B")
        header_frame.pack(fill="x", padx=5, pady=5)
        
        for header in headers:
            ctk.CTkLabel(
                header_frame,
                text=header,
                font=("Roboto", 12, "bold"),
                text_color="white"
            ).pack(side="left", expand=True, padx=5)
        
        # Listar usuarios
        for user in users:
            self._create_user_row(user)

    def _create_user_row(self, user):
        """Crea una fila para un usuario"""
        user_frame = ctk.CTkFrame(self.users_frame, fg_color="#404040")
        user_frame.pack(fill="x", padx=5, pady=2)
        
        # Información del usuario
        ctk.CTkLabel(
            user_frame,
            text=user["username"],
            text_color="white",
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            user_frame,
            text=user["name"],
            text_color="white",
            width=200
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            user_frame,
            text=user.get("email", ""),
            text_color="white",
            width=200
        ).pack(side="left", padx=5)
        
        # Botones de acción
        actions_frame = ctk.CTkFrame(user_frame, fg_color="#404040")
        actions_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkButton(
            actions_frame,
            text="✏️ Editar",
            command=lambda u=user: self._edit_user(u),
            fg_color="#2B2B2B",
            width=80
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            actions_frame,
            text="🗑️ Eliminar",
            command=lambda u=user: self._delete_user(u),
            fg_color=UI_CONFIG["COLORS"]["error"],
            width=80
        ).pack(side="left", padx=2)

    def _add_user(self):
        """Agrega un nuevo usuario profesor"""
        try:
            # Obtener valores de los campos
            username = self.user_entries["username"].get()
            password = self.user_entries["password"].get()
            name = self.user_entries["name"].get()
            email = self.user_entries["email"].get()
            
            # Validar campos requeridos
            if not all([username, password, name]):
                messagebox.showerror(
                    "Error",
                    "Los campos Usuario, Contraseña y Nombre son obligatorios"
                )
                return
            
            # Verificar si el usuario ya existe
            if self.users.find_one({"username": username}):
                messagebox.showerror(
                    "Error",
                    "El nombre de usuario ya existe"
                )
                return
            
            # Crear nuevo usuario
            new_user = {
                "username": username,
                "password": bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()),
                "name": name,
                "email": email,
                "role": "teacher",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Insertar en la base de datos
            self.users.insert_one(new_user)
            
            # Limpiar campos
            for entry in self.user_entries.values():
                entry.delete(0, 'end')
            
            # Actualizar lista
            self._update_users_list()
            
            messagebox.showinfo(
                "Éxito",
                f"Usuario {username} creado exitosamente"
            )
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al crear usuario: {str(e)}"
            )

    def _edit_user(self, user):
        """Abre ventana para editar usuario"""
        edit_window = self._create_toplevel_window(f"Editar Usuario - {user['username']}", "400x500")
        edit_window.configure(fg_color="#1a1a1a")
        
        # Frame principal
        main_frame = ctk.CTkFrame(edit_window, fg_color="#2B2B2B")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Campos editables
        fields = {
            "name": "Nombre completo",
            "email": "Correo electrónico",
            "password": "Nueva contraseña (opcional)"
        }
        
        entries = {}
        for field, label in fields.items():
            frame = ctk.CTkFrame(main_frame, fg_color="#2B2B2B")
            frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(
                frame,
                text=label,
                text_color="white"
            ).pack(anchor="w")
            
            entry = ctk.CTkEntry(
                frame,
                width=300,
                fg_color="#404040",
                text_color="white"
            )
            entry.pack(fill="x", pady=2)
            
            if field != "password":
                entry.insert(0, user.get(field, ""))
            
            entries[field] = entry
        
        def save_changes():
            try:
                updates = {
                    "name": entries["name"].get(),
                    "email": entries["email"].get()
                }
                
                # Actualizar contraseña solo si se proporciona una nueva
                new_password = entries["password"].get()
                if new_password:
                    updates["password"] = bcrypt.hashpw(
                        new_password.encode('utf-8'),
                        bcrypt.gensalt()
                    )
                
                self.users.update_one(
                    {"_id": user["_id"]},
                    {"$set": updates}
                )
                
                self._update_users_list()
                messagebox.showinfo("Éxito", "Usuario actualizado correctamente")
                edit_window.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar usuario: {str(e)}")
        
        # Botones
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="#2B2B2B")
        buttons_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(
            buttons_frame,
            text="💾 Guardar",
            command=save_changes,
            fg_color=UI_CONFIG["COLORS"]["success"],
            hover_color="#2E7D32"
        ).pack(side="left", padx=5, expand=True)
        
        ctk.CTkButton(
            buttons_frame,
            text="❌ Cancelar",
            command=edit_window.destroy,
            fg_color=UI_CONFIG["COLORS"]["error"],
            hover_color="#C62828"
        ).pack(side="left", padx=5, expand=True)

    def _delete_user(self, user):
        """Elimina un usuario después de confirmación"""
        if messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Está seguro de eliminar al usuario {user['username']}?\n"
            "Esta acción no se puede deshacer."
        ):
            try:
                self.users.delete_one({"_id": user["_id"]})
                self._update_users_list()
                messagebox.showinfo("Éxito", "Usuario eliminado correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar usuario: {str(e)}")

    def _create_toplevel_window(self, title: str, size: str = "400x300") -> ctk.CTkToplevel:
        """Crea una ventana secundaria con configuración estándar"""
        window = ctk.CTkToplevel(self.window)
        window.title(title)
        window.geometry(size)
        window.transient(self.window)
        window.grab_set()
        
        # Centrar la ventana
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'+{x}+{y}')
        
        return window
    
    def _apply_formula_filters(self):
        """Aplica los filtros seleccionados a la lista de fórmulas"""
        # Limpiar lista actual
        for widget in self.formulas_frame.winfo_children():
            widget.destroy()
        
        # Construir query
        query = {}
        
        # Filtro por usuario
        selected_user = self.formula_filters["Usuario"].get()
        if selected_user != "Todos":
            user = self.users.find_one({"name": selected_user})
            if user:
                query["user_id"] = str(user["_id"])
        
        # Filtro por tipo
        tipo = self.formula_filters["Tipo"].get()
        if tipo != "Todos":
            query["type"] = tipo
        
        # Filtro por dificultad
        dificultad = self.formula_filters["Dificultad"].get()
        if dificultad != "Todos":
            query["difficulty"] = dificultad
        
        # Filtro por fecha
        fecha = self.formula_filters["Fecha"].get()
        if fecha:
            try:
                fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
                query["scan_date"] = {
                    "$gte": fecha_dt.strftime("%Y-%m-%d 00:00:00"),
                    "$lte": fecha_dt.strftime("%Y-%m-%d 23:59:59")
                }
            except ValueError:
                pass
        
        # Obtener fórmulas filtradas
        formulas = self.formulas.find(query).sort("scan_date", -1)
        
        # Mostrar resultados
        for formula in formulas:
            self._create_formula_row(formula)

    def _update_formulas_list(self, formulas=None):
        """Actualiza la lista de fórmulas"""
        print("\n=== DEBUG: Actualizando lista de fórmulas ===")
        
        # Limpiar lista actual
        for widget in self.formulas_frame.winfo_children():
            widget.destroy()
        
        # Obtener todas las fórmulas si no se proporcionan
        if formulas is None:
            formulas = self.formulas.find().sort("scan_date", -1)
        
        formulas_list = list(formulas)  # Convertir cursor a lista
        print(f"Fórmulas a mostrar: {len(formulas_list)}")
        
        # Crear encabezados
        headers = ["Fórmula", "Tipo", "Dificultad", "Fecha", "Acciones"]
        header_frame = ctk.CTkFrame(self.formulas_frame, fg_color="#2B2B2B")
        header_frame.pack(fill="x", padx=5, pady=5)
        
        for header in headers:
            ctk.CTkLabel(
                header_frame,
                text=header,
                font=("Roboto", 12, "bold"),
                text_color="white"
            ).pack(side="left", expand=True, padx=5)
        
        # Listar fórmulas
        for formula in formulas_list:
            try:
                print(f"Creando fila para fórmula: {formula.get('latex', '')}")
                self._create_formula_row(formula)
            except Exception as e:
                print(f"Error al crear fila para fórmula: {e}")
        
        print("=== Fin DEBUG ===\n")

    def _create_formula_row(self, formula):
        """Crea una fila para mostrar una fórmula"""
        try:
            formula_frame = ctk.CTkFrame(self.formulas_frame, fg_color="#404040")
            formula_frame.pack(fill="x", padx=5, pady=2)
            
            # Contenedor principal con Grid
            grid_frame = ctk.CTkFrame(formula_frame, fg_color="#404040")
            grid_frame.pack(fill="x", expand=True, padx=5, pady=5)
            grid_frame.grid_columnconfigure((0,1,2,3,4), weight=1)  # Distribuir columnas uniformemente
            
            # LaTeX de la fórmula (columna 0)
            latex_label = ctk.CTkLabel(
                grid_frame,
                text=formula.get('latex', ''),
                text_color="white",
                wraplength=200,
                justify="left",
                anchor="w"
            )
            latex_label.grid(row=0, column=0, padx=5, sticky="w")
            
            # Tipo (columna 1)
            type_label = ctk.CTkLabel(
                grid_frame,
                text=formula.get('type', 'No especificado'),
                text_color="white",
                width=100,
                anchor="center"
            )
            type_label.grid(row=0, column=1, padx=5)
            
            # Dificultad con color (columna 2)
            difficulty = formula.get('difficulty', 'No especificada')
            difficulty_colors = {
                "Fácil": "#4CAF50",
                "Moderado": "#FF9800",
                "Difícil": "#F44336"
            }
            
            difficulty_label = ctk.CTkLabel(
                grid_frame,
                text=difficulty,
                text_color=difficulty_colors.get(difficulty, "white"),
                width=100,
                anchor="center"
            )
            difficulty_label.grid(row=0, column=2, padx=5)
            
            # Fecha (columna 3)
            date_str = formula.get('scan_date', '')
            if date_str:
                try:
                    # Intentar formatear la fecha si existe
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                except:
                    formatted_date = date_str.split()[0] if ' ' in date_str else date_str
            else:
                formatted_date = 'No disponible'
                
            date_label = ctk.CTkLabel(
                grid_frame,
                text=formatted_date,
                text_color="white",
                width=100,
                anchor="center"
            )
            date_label.grid(row=0, column=3, padx=5)
            
            # Botones de acción (columna 4)
            actions_frame = ctk.CTkFrame(grid_frame, fg_color="#404040")
            actions_frame.grid(row=0, column=4, padx=5)
            
            # Botones con tooltips
            buttons_config = [
                ("👁️", "Ver detalles", lambda f=formula: self._show_formula_details(f), "#2B2B2B"),
                ("✏️", "Editar", lambda f=formula: self._edit_formula(f), "#2B2B2B"),
                ("🗑️", "Eliminar", lambda f=formula: self._delete_formula(f, formula_frame), UI_CONFIG["COLORS"]["error"])
            ]
            
            for i, (text, tooltip, command, color) in enumerate(buttons_config):
                btn = ctk.CTkButton(
                    actions_frame,
                    text=text,
                    command=command,
                    fg_color=color,
                    width=30,
                    height=30,
                    cursor="hand2"
                )
                btn.pack(side="left", padx=2)
                
                # Crear tooltip
                self._create_tooltip(btn, tooltip)

        except Exception as e:
            logging.error(f"Error al crear fila para fórmula {formula.get('latex', '')}: {str(e)}")
            print(f"Error detallado al crear fila para fórmula: {str(e)}")

    def _create_tooltip(self, widget, text):
        """Crea un tooltip para un widget"""
        def enter(event):
            tooltip = ctk.CTkToplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ctk.CTkLabel(
                tooltip,
                text=text,
                fg_color="#2B2B2B",
                corner_radius=6,
                padx=5,
                pady=2
            )
            label.pack()
            
            widget.tooltip = tooltip
            
        def leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def _show_formula_details(self, formula):
        """Muestra los detalles de una fórmula"""
        details_window = self._create_toplevel_window(
            "Detalles de Fórmula",
            "600x400"
        )
        details_window.configure(fg_color="#1a1a1a")
        
        # Frame principal
        main_frame = ctk.CTkFrame(details_window, fg_color="#2B2B2B")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # LaTeX
        latex_frame = ctk.CTkFrame(main_frame, fg_color="#2B2B2B")
        latex_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            latex_frame,
            text="LaTeX:",
            font=("Roboto", 14, "bold"),
            text_color="white"
        ).pack(anchor="w")
        
        latex_text = ctk.CTkTextbox(
            latex_frame,
            height=100,
            font=("Roboto", 12),
            fg_color="#404040",
            text_color="white"
        )
        latex_text.pack(fill="x", pady=5)
        latex_text.insert("1.0", formula.get('latex', ''))
        latex_text.configure(state="disabled")
        
        # Información adicional
        info_frame = ctk.CTkFrame(main_frame, fg_color="#2B2B2B")
        info_frame.pack(fill="x", pady=10)
        
        # Tipo y dificultad
        ctk.CTkLabel(
            info_frame,
            text=f"Tipo: {formula.get('type', 'No especificado')}",
            font=("Roboto", 12),
            text_color="white"
        ).pack(anchor="w", pady=2)
        
        ctk.CTkLabel(
            info_frame,
            text=f"Dificultad: {formula.get('difficulty', 'No especificada')}",
            font=("Roboto", 12),
            text_color="white"
        ).pack(anchor="w", pady=2)
        
        # Descripción
        if formula.get('description'):
            desc_frame = ctk.CTkFrame(main_frame, fg_color="#2B2B2B")
            desc_frame.pack(fill="x", pady=10)
            
            ctk.CTkLabel(
                desc_frame,
                text="Descripción:",
                font=("Roboto", 14, "bold"),
                text_color="white"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                desc_frame,
                text=formula.get('description', ''),
                font=("Roboto", 12),
                text_color="white",
                wraplength=500
            ).pack(anchor="w", pady=5)
        
        # Fecha
        ctk.CTkLabel(
            info_frame,
            text=f"Fecha: {formula.get('scan_date', 'No disponible')}",
            font=("Roboto", 12),
            text_color="white"
        ).pack(anchor="w", pady=2)
        
        # Botón cerrar
        ctk.CTkButton(
            main_frame,
            text="Cerrar",
            command=details_window.destroy,
            fg_color=UI_CONFIG["COLORS"]["primary"]
        ).pack(pady=20)

    def _delete_formula(self, formula, frame):
        """Elimina una fórmula"""
        if messagebox.askyesno(
            "Confirmar eliminación",
            "¿Está seguro de eliminar esta fórmula?"
        ):
            try:
                # Convertir el _id a ObjectId si es necesario
                formula_id = formula["_id"]
                if isinstance(formula_id, str):
                    formula_id = ObjectId(formula_id)
                
                self.formulas.delete_one({"_id": formula_id})
                frame.destroy()
                messagebox.showinfo("Éxito", "Fórmula eliminada correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar la fórmula: {str(e)}")

    def _search_users(self):
        """Busca usuarios según el término ingresado"""
        search_term = self.search_user.get()
        if search_term:
            users = self.users.find({
                "$or": [
                    {"username": {"$regex": search_term, "$options": "i"}},
                    {"name": {"$regex": search_term, "$options": "i"}},
                    {"email": {"$regex": search_term, "$options": "i"}}
                ],
                "role": "teacher"
            })
        else:
            users = self.users.find({"role": "teacher"})

        self._update_users_list(users)

    def _update_users_list(self, users=None):
        """Actualiza la lista de usuarios"""
        # Limpiar lista actual
        for widget in self.users_frame.winfo_children():
            widget.destroy()

        if users is None:
            users = self.users.find({"role": "teacher"})

        # Crear encabezados
        headers = ["Usuario", "Nombre", "Email", "Acciones"]
        header_frame = ctk.CTkFrame(self.users_frame, fg_color="#2B2B2B")
        header_frame.pack(fill="x", padx=5, pady=5)

        for header in headers:
            ctk.CTkLabel(
                header_frame,
                text=header,
                font=("Roboto", 12, "bold"),
                text_color="white"
            ).pack(side="left", expand=True, padx=5)

        # Listar usuarios
        for user in users:
            self._create_user_row(user)

    def _create_user_row(self, user):
        """Crea una fila para un usuario"""
        user_frame = ctk.CTkFrame(self.users_frame, fg_color="#404040")
        user_frame.pack(fill="x", padx=5, pady=2)

        # Información del usuario
        ctk.CTkLabel(
            user_frame,
            text=user["username"],
            text_color="white",
            width=150
        ).pack(side="left", padx=5)

        ctk.CTkLabel(
            user_frame,
            text=user["name"],
            text_color="white",
            width=200
        ).pack(side="left", padx=5)

        ctk.CTkLabel(
            user_frame,
            text=user.get("email", ""),
            text_color="white",
            width=200
        ).pack(side="left", padx=5)

        # Botones de acción
        actions_frame = ctk.CTkFrame(user_frame, fg_color="#404040")
        actions_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            actions_frame,
            text="✏️ Editar",
            command=lambda u=user: self._edit_user(u),
            fg_color="#2B2B2B",
            width=80
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            actions_frame,
            text="🗑️ Eliminar",
            command=lambda u=user: self._delete_user(u),
            fg_color=UI_CONFIG["COLORS"]["error"],
            width=80
        ).pack(side="left", padx=2)

    def _add_formula(self):
        """Agrega una nueva fórmula a la base de datos"""
        try:
            # Obtener valores de los campos
            latex = self.formula_entries["latex"].get()
            formula_type = self.formula_entries["type"].get()
            difficulty = self.formula_entries["difficulty"].get()
            description = self.formula_entries["description"].get()
            
            # Validar campos requeridos
            if not latex:
                messagebox.showerror(
                    "Error",
                    "El campo LaTeX es obligatorio"
                )
                return
            
            # Crear nueva fórmula
            new_formula = {
                "latex": latex,
                "type": formula_type,
                "difficulty": difficulty,
                "description": description,
                "user_id": str(self.user_data.get("_id", "")),  # Asegurarse de que existe _id
                "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Insertar en la base de datos
            result = self.formulas.insert_one(new_formula)
            
            if result.inserted_id:
                # Limpiar campos
                for entry in self.formula_entries.values():
                    if isinstance(entry, ctk.CTkEntry):
                        entry.delete(0, 'end')
                    elif isinstance(entry, ctk.CTkOptionMenu):
                        entry.set(entry._values[0])  # Resetear al primer valor
                
                # Actualizar lista
                self._update_formulas_list()
                
                messagebox.showinfo(
                    "Éxito",
                    "Fórmula agregada exitosamente"
                )
            else:
                raise Exception("No se pudo insertar la fórmula")
                
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al agregar fórmula: {str(e)}"
            )

    def _search_formulas(self):
        """Busca fórmulas según el término ingresado"""
        search_term = self.formula_search.get()
        if search_term:
            formulas = self.formulas.find({
                "$or": [
                    {"latex": {"$regex": search_term, "$options": "i"}},
                    {"type": {"$regex": search_term, "$options": "i"}},
                    {"description": {"$regex": search_term, "$options": "i"}}
                ]
            })
        else:
            formulas = self.formulas.find()
        
        self._update_formulas_list(formulas)

    def _edit_formula(self, formula):
        """Abre ventana para editar fórmula"""
        edit_window = self._create_toplevel_window("Editar Fórmula", "500x400")
        edit_window.configure(fg_color="#1a1a1a")
        
        # Frame principal
        main_frame = ctk.CTkFrame(edit_window, fg_color="#2B2B2B")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Campos editables
        entries = {}
        fields = {
            "latex": "LaTeX",
            "type": "Tipo",
            "difficulty": "Dificultad",
            "description": "Descripción"
        }
        
        for field, label in fields.items():
            frame = ctk.CTkFrame(main_frame, fg_color="#2B2B2B")
            frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(
                frame,
                text=label,
                text_color="white"
            ).pack(anchor="w")
            
            if field in ["type", "difficulty"]:
                if field == "type":
                    values = ["Álgebra", "Cálculo", "Trigonometría", "Geometría"]
                else:
                    values = ["Fácil", "Moderado", "Difícil"]
                
                entry = ctk.CTkOptionMenu(
                    frame,
                    values=values,
                    fg_color="#404040"
                )
                entry.set(formula.get(field, values[0]))
            else:
                entry = ctk.CTkEntry(
                    frame,
                    width=400,
                    fg_color="#404040",
                    text_color="white"
                )
                entry.insert(0, formula.get(field, ""))
            
            entry.pack(fill="x", pady=2)
            entries[field] = entry
        
        def save_changes():
            try:
                updates = {
                    "latex": entries["latex"].get(),
                    "type": entries["type"].get(),
                    "difficulty": entries["difficulty"].get(),
                    "description": entries["description"].get()
                }
                
                # Convertir el _id a ObjectId si es necesario
                formula_id = formula["_id"]
                if isinstance(formula_id, str):
                    formula_id = ObjectId(formula_id)
                
                result = self.formulas.update_one(
                    {"_id": formula_id},
                    {"$set": updates}
                )
                
                if result.modified_count > 0:
                    self._update_formulas_list()
                    messagebox.showinfo("Éxito", "Fórmula actualizada correctamente")
                    edit_window.destroy()
                else:
                    raise Exception("No se pudo actualizar la fórmula")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar fórmula: {str(e)}")
        
        # Botones
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="#2B2B2B")
        buttons_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(
            buttons_frame,
            text="💾 Guardar",
            command=save_changes,
            fg_color=UI_CONFIG["COLORS"]["success"]
        ).pack(side="left", padx=5, expand=True)
        
        ctk.CTkButton(
            buttons_frame,
            text="❌ Cancelar",
            command=edit_window.destroy,
            fg_color=UI_CONFIG["COLORS"]["error"]
        ).pack(side="left", padx=5, expand=True)


if __name__ == "__main__":
    admin = AdminPanel({"name": "Admin"})
    admin.run()
