from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from core.config import MONGODB_CONFIG
import logging
from typing import Optional

class DatabaseManager:
    """
    Clase para gestionar la conexión y operaciones con MongoDB usando el patrón Singleton.
    Esto asegura que solo exista una instancia de la conexión a la base de datos.
    """
    
    # Variable de clase para almacenar la única instancia
    _instance: Optional['DatabaseManager'] = None
    
    def __new__(cls) -> 'DatabaseManager':
        """Implementación del Singleton usando __new__"""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializa la conexión a MongoDB solo una vez"""
        # Evitar reinicialización si ya está inicializado
        if getattr(self, '_initialized', False):
            return
            
        try:
            # Configurar logging
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)
            
            # Inicializar la conexión
            self.client = MongoClient(MONGODB_CONFIG["URI"])
            self.db = self.client[MONGODB_CONFIG["DB_NAME"]]
            
            # Verificar conexión
            self.is_connected()
            self.logger.info("Conexión exitosa a MongoDB")
            
            # Marcar como inicializado
            self._initialized = True
            
        except Exception as e:
            self.logger.error(f"Error al conectar a MongoDB: {str(e)}")
            raise
    
    def is_connected(self) -> bool:
        """Verifica si la conexión a MongoDB está activa"""
        try:
            # Ejecutar comando de administrador para verificar conexión
            self.client.admin.command('ping')
            return True
        except ConnectionFailure:
            self.logger.error("No se pudo conectar a MongoDB")
            return False
    
    def collection_exists(self, collection_name: str) -> bool:
        """Verifica si una colección existe en la base de datos"""
        try:
            return collection_name in self.db.list_collection_names()
        except Exception as e:
            self.logger.error(f"Error al verificar colección {collection_name}: {str(e)}")
            return False
    
    def get_collection(self, collection_name: str):
        """Obtiene una colección específica de la base de datos"""
        try:
            # Verificar si la colección existe
            if not self.collection_exists(collection_name):
                # Crear la colección si no existe
                self.db.create_collection(collection_name)
                self.logger.info(f"Colección {collection_name} creada")
            return self.db[collection_name]
        except Exception as e:
            self.logger.error(f"Error al obtener la colección {collection_name}: {str(e)}")
            raise
    
    def close_connection(self):
        """Cierra la conexión a MongoDB"""
        try:
            if hasattr(self, 'client'):
                self.client.close()
                self.logger.info("Conexión a MongoDB cerrada correctamente")
        except Exception as e:
            self.logger.error(f"Error al cerrar la conexión: {str(e)}")
    
    @classmethod
    def get_instance(cls) -> 'DatabaseManager':
        """Método estático para obtener la instancia del Singleton"""
        if cls._instance is None:
            cls._instance = DatabaseManager()
        return cls._instance
    
    def __del__(self):
        """Destructor que asegura el cierre de la conexión"""
        self.close_connection() 