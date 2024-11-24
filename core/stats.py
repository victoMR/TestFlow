from typing import Dict, List
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import seaborn as sns

class FormulaStats:
    def __init__(self, collection):
        self.collection = collection

    def get_user_stats(self, user_id: str) -> Dict:
        """Obtiene estadísticas del usuario"""
        try:
            pipeline = [
                {"$match": {"user_id": str(user_id)}},
                {"$group": {
                    "_id": None,
                    "total_formulas": {"$sum": 1},
                    "by_type": {"$push": "$type"},
                    "by_difficulty": {"$push": "$difficulty"},
                    "avg_complexity": {"$avg": {"$strLenCP": {"$ifNull": ["$latex", ""]}}}
                }}
            ]
            
            stats = list(self.collection.aggregate(pipeline))
            
            if not stats:
                return {
                    "total_formulas": 0,
                    "type_distribution": {},
                    "difficulty_distribution": {},
                    "avg_complexity": 0
                }
            
            result = stats[0]
            return {
                "total_formulas": result["total_formulas"],
                "type_distribution": pd.Series(result["by_type"]).value_counts().to_dict(),
                "difficulty_distribution": pd.Series(result["by_difficulty"]).value_counts().to_dict(),
                "avg_complexity": result["avg_complexity"]
            }
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {str(e)}")
            return {
                "total_formulas": 0,
                "type_distribution": {},
                "difficulty_distribution": {},
                "avg_complexity": 0
            }

    def generate_activity_chart(self, user_id: str, save_path: str):
        """Genera un gráfico de actividad del usuario"""
        formulas = list(self.collection.find(
            {"user_id": user_id},
            {"scan_date": 1, "problem_type": 1}
        ))
        
        df = pd.DataFrame(formulas)
        df['scan_date'] = pd.to_datetime(df['scan_date'])
        
        plt.figure(figsize=(12, 6))
        df['scan_date'].dt.date.value_counts().sort_index().plot(kind='line')
        plt.title('Actividad de Escaneo de Fórmulas')
        plt.xlabel('Fecha')
        plt.ylabel('Número de Fórmulas')
        plt.savefig(save_path)
        plt.close()

    def generate_type_distribution_chart(self, user_id: str, save_path: str):
        """Genera un gráfico de distribución por tipo de problema"""
        stats = self.get_user_stats(user_id)
        
        plt.figure(figsize=(10, 6))
        sns.barplot(x=list(stats['type_distribution'].keys()),
                   y=list(stats['type_distribution'].values()))
        plt.xticks(rotation=45)
        plt.title('Distribución por Tipo de Problema')
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close() 