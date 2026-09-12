import requests
import pandas as pd
from extractors.base_extractor import BaseExtractor

class IPCExtractor(BaseExtractor):
    def __init__(self):
        super().__init__(name="IPC_Chile")
        # Ejemplo con endpoint de consulta de series temporales
        self.url = "https://mindicador.cl" 

    def fetch_raw_data(self) -> dict:
        response = requests.get(self.url, timeout=30)
        response.raise_for_status()
        return response.json()

    def transform(self, raw_data: dict) -> pd.DataFrame:
        # Extrae la serie histórica del JSON
        records = raw_data.get('serie', [])
        df = pd.DataFrame(records)
        
        # Formateo óptimo para Tableau
        df['fecha'] = pd.to_datetime(df['fecha']).dt.date
        df['valor'] = df['valor'].astype(float)
        df['indicador'] = 'IPC'
        
        # Ordenar cronológicamente
        df = df.sort_values('fecha').reset_index(drop=True)
        return df
