import customtkinter as ctk
from core.login import LoginWindow
from core.admin_panel import AdminPanel
from core.teacher_panel import TeacherPanel
from core.formula_extractor import FormulaExtractor


class FormulaExtractorApp:
    def __init__(self):
        self.current_window = None
        self.formula_extractor = FormulaExtractor()
        
        # Obtener dimensiones de la pantalla
        root = ctk.CTk()
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        # Ajustar altura para dejar espacio para la barra de tareas
        self.taskbar_height = 40  # Altura aproximada de la barra de tareas
        self.window_height = self.screen_height - self.taskbar_height
        root.destroy()

    def handle_login_success(self, user_data):
        """Maneja el inicio de sesión exitoso"""
        print(f"Login exitoso para usuario: {user_data.get('username')}")
        
        try:
            # Crear la nueva ventana según el rol
            if user_data.get("role") == "admin":
                print("Creando ventana de administrador...")
                self.current_window = AdminPanel(user_data)
            else:
                print("Creando ventana de profesor...")
                self.current_window = TeacherPanel(user_data, self.formula_extractor)
            
            # Pasar referencia de la aplicación
            if hasattr(self.current_window, 'set_app'):
                self.current_window.set_app(self)
            
            # Configurar ventana
            if hasattr(self.current_window, 'window'):
                window = self.current_window.window
                
                # Configurar tamaño y posición
                x_position = 0
                y_position = 0
                window.geometry(f"{self.screen_width}x{self.window_height}+{x_position}+{y_position}")
                
                # Permitir redimensionar
                window.resizable(True, True)
                
                # Establecer tamaños mínimos        
                window.minsize(600, 600)
                
                # Configurar expansión al maximizar
                window.grid_rowconfigure(0, weight=1)
                window.grid_columnconfigure(0, weight=1)
                
                # Mostrar la ventana
                window.deiconify()
                window.lift()
                window.focus_force()
                
                # Iniciar la ventana
                self.current_window.run()
            else:
                print("Error: No se pudo crear la ventana correctamente")
                
        except Exception as e:
            print(f"Error al crear ventana después del login: {e}")

    def run(self):
        """Inicia la aplicación"""
        # Configurar el tema global de CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Crear y ejecutar la ventana de login
        login_window = LoginWindow(self.handle_login_success)
        
        # Configurar tamaño y posición de la ventana de login
        x_position = 0
        y_position = 0
        login_window.window.geometry(f"{self.screen_width}x{self.window_height}+{x_position}+{y_position}")
        
        # Permitir redimensionar
        login_window.window.resizable(True, True)
        
        # Establecer tamaño mínimo
        login_window.window.minsize(800, 600)
        
        # Iniciar la aplicación
        login_window.run()


def main():
    app = FormulaExtractorApp()
    app.run()


if __name__ == "__main__":
    main()
