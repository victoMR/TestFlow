import customtkinter as ctk
import bcrypt
from typing import Optional, Callable
from core.config import APP_CONFIG, UI_CONFIG
from core.database import DatabaseManager
from PIL import Image, ImageTk
import os

class LoginWindow:
    def __init__(self, on_login_success: Callable):
        # Configuración de CustomTkinter
        ctk.set_appearance_mode(APP_CONFIG["THEME"])
        ctk.set_default_color_theme(APP_CONFIG["COLOR_THEME"])
        
        # Inicializar ventana principal
        self.window = ctk.CTk()
        self.window.title("Formula Extractor - Login")
        self.window.geometry("800x600")  # Ventana más grande
        
        # Inicializar base de datos usando el singleton
        self.db_manager = DatabaseManager.get_instance()
        self.users = self.db_manager.get_collection("USERS")
        
        # Callback para login exitoso
        self.on_login_success = on_login_success
        
        # Agregar variables para recordar usuario
        self.remember_var = ctk.BooleanVar(value=False)
        
        # Variables para validación en tiempo real
        self.username_valid = False
        self.password_valid = False
        
        # Obtener dimensiones de la pantalla
        self.window.update_idletasks()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Configurar ventana en pantalla completa
        self.window.geometry(f"{screen_width}x{screen_height}+0+0")
        self.window.resizable(False, False)
        
        # Crear widgets primero
        self._create_widgets()
        
        # Cargar usuario recordado después de crear widgets
        self.load_remembered_user()
        
        # Bind para validación en tiempo real después de crear widgets
        self.username_entry.bind('<KeyRelease>', self._validate_username)
        self.password_entry.bind('<KeyRelease>', self._validate_password)
        
        self._create_admin_if_not_exists()
        
        # Centrar la ventana
        self.center_window()
    
    def _create_widgets(self):
        # Frame principal con grid
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        
        main_frame = ctk.CTkFrame(self.window)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Panel izquierdo para imagen/logo
        left_panel = ctk.CTkFrame(
            main_frame,
            fg_color=UI_CONFIG["COLORS"]["primary"]
        )
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_panel.grid_rowconfigure(1, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)
        
        # Intentar cargar el logo desde múltiples ubicaciones
        logo_paths = [
            os.path.join("assets", "logo.png"),
            os.path.join("..", "assets", "logo.png"),
            os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")
        ]
        
        logo_loaded = False
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    logo_image = Image.open(logo_path)
                    # Hacer el logo responsive
                    logo_size = min(350, int(self.window.winfo_width() * 0.5))
                    logo_image = logo_image.resize((logo_size, logo_size))
                    logo_photo = ImageTk.PhotoImage(logo_image)
                    
                    logo_label = ctk.CTkLabel(
                        left_panel,
                        image=logo_photo,
                        text=""
                    )
                    logo_label.image = logo_photo
                    logo_label.grid(row=0, column=0, pady=20)
                    logo_loaded = True
                    break
                except Exception as e:
                    print(f"Error cargando logo desde {logo_path}: {e}")
        
        if not logo_loaded:
            # Título alternativo con mejor diseño
            title_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
            title_frame.grid(row=0, column=0, pady=50)
            
            ctk.CTkLabel(
                title_frame,
                text="Formula",
                font=("Roboto", 48, "bold"),
                text_color="white"
            ).pack()
            
            ctk.CTkLabel(
                title_frame,
                text="Extractor",
                font=("Roboto", 48, "bold"),
                text_color=UI_CONFIG["COLORS"]["accent"]
            ).pack()
        
        # Texto descriptivo
        desc_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        desc_frame.grid(row=1, column=0, pady=20)
        
        ctk.CTkLabel(
            desc_frame,
            text="Sistema de Extracción y\nGestión de Fórmulas Matemáticas",
            font=("Roboto", 16),
            text_color="white",
            justify="center"
        ).pack()
        
        # Panel derecho para login
        right_panel = ctk.CTkFrame(main_frame)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        
        # Título de login
        ctk.CTkLabel(
            right_panel,
            text="Iniciar Sesión",
            font=("Roboto", 24, "bold")
        ).grid(row=0, column=0, pady=30)
        
        # Frame para el formulario con animación de aparición
        form_frame = ctk.CTkFrame(right_panel)
        form_frame.grid(row=1, column=0, sticky="n", padx=40, pady=20)
        
        # Usuario con validación visual
        username_frame = ctk.CTkFrame(form_frame)
        username_frame.pack(fill="x", pady=10)
        
        self.username_label = ctk.CTkLabel(
            username_frame,
            text="Usuario",
            font=("Roboto", 12)
        )
        self.username_label.pack(anchor="w")
        
        self.username_entry = ctk.CTkEntry(
            username_frame,
            placeholder_text="Ingrese su usuario",
            width=250,
            height=40
        )
        self.username_entry.pack(fill="x", pady=(5, 0))
        
        # Indicador de validación para usuario
        self.username_validation = ctk.CTkLabel(
            username_frame,
            text="",
            text_color=UI_CONFIG["COLORS"]["error"],
            font=("Roboto", 10)
        )
        self.username_validation.pack(anchor="w")
        
        # Contraseña con validación visual
        password_frame = ctk.CTkFrame(form_frame)
        password_frame.pack(fill="x", pady=10)
        
        self.password_label = ctk.CTkLabel(
            password_frame,
            text="Contraseña",
            font=("Roboto", 12)
        )
        self.password_label.pack(anchor="w")
        
        self.password_entry = ctk.CTkEntry(
            password_frame,
            placeholder_text="Ingrese su contraseña",
            show="●",
            width=250,
            height=40
        )
        self.password_entry.pack(fill="x", pady=(5, 0))
        
        # Indicador de validación para contraseña
        self.password_validation = ctk.CTkLabel(
            password_frame,
            text="",
            text_color=UI_CONFIG["COLORS"]["error"],
            font=("Roboto", 10)
        )
        self.password_validation.pack(anchor="w")
        
        # Checkbox para recordar usuario
        self.remember_checkbox = ctk.CTkCheckBox(
            form_frame,
            text="Recordar usuario",
            variable=self.remember_var,
            font=("Roboto", 12)
        )
        self.remember_checkbox.pack(pady=10)
        
        # Botón de login con estado
        self.login_button = ctk.CTkButton(
            form_frame,
            text="Iniciar Sesión",
            command=self._handle_login,
            width=250,
            height=40,
            font=("Roboto", 14),
            state="disabled",  # Inicialmente deshabilitado
            fg_color=UI_CONFIG["COLORS"]["primary"]
        )
        self.login_button.pack(pady=10)
        
        # Mensaje de error con animación
        self.error_label = ctk.CTkLabel(
            form_frame,
            text="",
            text_color=UI_CONFIG["COLORS"]["error"],
            font=("Roboto", 12)
        )
        self.error_label.pack(pady=10)
        
        # Footer
        footer_frame = ctk.CTkFrame(right_panel)
        footer_frame.grid(row=2, column=0, sticky="ew", pady=20, padx=20)
        
        ctk.CTkLabel(
            footer_frame,
            text="© 2024 Formula Extractor\nTodos los derechos reservados",
            font=("Roboto", 10),
            justify="center"
        ).pack()
        
        # Bind para resize
        self.window.bind("<Configure>", self._on_resize)
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_admin_if_not_exists(self):
        """Crea el usuario admin si no existe"""
        if not self.users.find_one({"username": "admin"}):
            password = "admin123"  # Contraseña por defecto
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            admin_user = {
                "username": "admin",
                "password": hashed,
                "role": "admin",
                "name": "Administrador"
            }
            
            self.users.insert_one(admin_user)
            print("Usuario admin creado con éxito")
    
    def _validate_username(self, event=None):
        """Valida el usuario en tiempo real"""
        username = self.username_entry.get()
        
        if len(username) < 3:
            self.username_validation.configure(
                text="El usuario debe tener al menos 3 caracteres",
                text_color=UI_CONFIG["COLORS"]["error"]
            )
            self.username_valid = False
        else:
            self.username_validation.configure(
                text="✓",
                text_color=UI_CONFIG["COLORS"]["success"]
            )
            self.username_valid = True
            
        self._update_login_button()
        
    def _validate_password(self, event=None):
        """Valida la contraseña en tiempo real"""
        password = self.password_entry.get()
        
        if len(password) < 4:
            self.password_validation.configure(
                text="La contraseña debe tener al menos 4 caracteres",
                text_color=UI_CONFIG["COLORS"]["error"]
            )
            self.password_valid = False
        else:
            self.password_validation.configure(
                text="✓",
                text_color=UI_CONFIG["COLORS"]["success"]
            )
            self.password_valid = True
            
        self._update_login_button()
        
    def _update_login_button(self):
        """Actualiza el estado del botón de login"""
        if self.username_valid and self.password_valid:
            self.login_button.configure(
                state="normal",
                fg_color=UI_CONFIG["COLORS"]["primary"]
            )
        else:
            self.login_button.configure(
                state="disabled",
                fg_color=UI_CONFIG["COLORS"]["secondary"]
            )
            
    def _handle_login(self):
        """Maneja el proceso de login con mejor feedback"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        try:
            # Mostrar indicador de carga
            self.login_button.configure(
                text="Iniciando sesión...",
                state="disabled"
            )
            self.window.update()
            
            user = self.users.find_one({"username": username})
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user["password"]):
                # Guardar usuario si está marcada la opción
                if self.remember_var.get():
                    self.save_remembered_user(username)
                
                # Guardar una copia de los datos del usuario y el callback
                user_data = dict(user)  # Hacer una copia del documento
                callback = self.on_login_success
                
                # Programar la destrucción de la ventana y la llamada al callback
                def finish_login():
                    self.window.destroy()
                    if callback:
                        callback(user_data)
                
                # Usar after para dar tiempo a la actualización de la UI
                self.window.after(100, finish_login)
                
            else:
                self.show_error("Usuario o contraseña incorrectos")
                # Restaurar el botón solo si hay error
                self.login_button.configure(
                    text="Iniciar Sesión",
                    state="normal"
                )
                
        except Exception as e:
            self.show_error(f"Error al iniciar sesión: {str(e)}")
            # Restaurar el botón solo si hay error
            self.login_button.configure(
                text="Iniciar Sesión",
                state="normal"
            )
    
    def show_success_animation(self):
        """Muestra una animación de éxito"""
        success_label = ctk.CTkLabel(
            self.window,
            text="✓",
            font=("Roboto", 48),
            text_color=UI_CONFIG["COLORS"]["success"]
        )
        success_label.place(relx=0.5, rely=0.5, anchor="center")
        
        def fade_out():
            success_label.destroy()
            
        self.window.after(800, fade_out)
        
    def show_error(self, message: str):
        """Muestra un error con animación"""
        self.error_label.configure(text=message)
        self.shake_error()
        
    def save_remembered_user(self, username: str):
        """Guarda el usuario recordado"""
        try:
            with open("remembered_user.txt", "w") as f:
                f.write(username)
        except Exception as e:
            print(f"Error guardando usuario recordado: {e}")
            
    def load_remembered_user(self):
        """Carga el usuario recordado"""
        try:
            with open("remembered_user.txt", "r") as f:
                username = f.read().strip()
                if username:
                    self.username_entry.insert(0, username)
                    self.remember_var.set(True)
                    self._validate_username()
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error cargando usuario recordado: {e}")
            
    def finish_login(self, user):
        """Finaliza el proceso de login"""
        try:
            # Guardar referencia al callback
            callback = self.on_login_success
            
            # Destruir ventana de login
            if hasattr(self, 'window') and self.window:
                self.window.destroy()
            
            # Llamar al callback con los datos del usuario
            if callback:
                callback(user)
                
        except Exception as e:
            print(f"Error durante el proceso de login: {e}")
    
    def shake_error(self):
        """Efecto de shake para el mensaje de error"""
        original_x = self.error_label.winfo_x()
        shake_distance = 10
        shake_speed = 50
        
        def _shake(count, direction):
            if count > 0:
                self.error_label.place(x=original_x + (shake_distance * direction))
                direction *= -1
                self.window.after(shake_speed, lambda: _shake(count - 1, direction))
            else:
                self.error_label.place(x=original_x)
        
        _shake(5, 1)
    
    def _on_resize(self, event):
        """Maneja el redimensionamiento de la ventana"""
        if event.widget == self.window:
            # Actualizar tamaños basados en el nuevo tamaño de ventana
            min_width = 800
            min_height = 600
            new_width = max(event.width, min_width)
            new_height = max(event.height, min_height)
            
            if new_width != event.width or new_height != event.height:
                self.window.geometry(f"{new_width}x{new_height}")
    
    def run(self):
        """Inicia la ventana de login"""
        self.window.mainloop() 