import requests
import io
import pandas as pd
from extractors.base_extractor import BaseExtractor

class IPCExtractor(BaseExtractor):
    def __init__(self):
        super().__init__(name="IPC_Chile_Oficial")
        # Tu URL oficial del archivo de series de tiempo base 2023=100 del INE
        self.url = "https://www.ine.gob.cl/docs/default-source/%C3%ADndice-de-precios-al-consumidor/cuadros-estadisticos/base-anual-2023_100/series-de-tiempo/ipc-xls.xlsx"

    def fetch_raw_data(self) -> dict:
        """Descarga el Excel completo directamente desde el servidor del INE."""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(self.url, headers=headers, timeout=40)
        response.raise_for_status()
        
        # Guardamos el archivo binario en memoria usando un diccionario para pasarlo al transformador
        return {"excel_bytes": response.content}

    def transform(self, raw_data: dict) -> pd.DataFrame:
        """Procesa y limpia las hojas de la planilla Excel para Tableau."""
        excel_file = io.BytesIO(raw_data["excel_bytes"])
        
        # El INE suele estructurar este archivo con la hoja 'Índices' o la primera hoja con las series
        # Cargamos el Excel omitiendo las filas de encabezados institucionales estéticos (generalmente las primeras 3)
        df_raw = pd.read_excel(excel_file, sheet_name=0, skiprows=3)
        
        # --- Limpieza de estructura estándar de series del INE ---
        # 1. Eliminar filas completamente vacías o notas al pie de página
        df_raw = df_raw.dropna(subset=[df_raw.columns[0], df_raw.columns[1]], how='all')
        
        # 2. Renombrar columnas clave (por ejemplo, Año / Producto / Glosa)
        df_raw.rename(columns={df_raw.columns[0]: 'Año', df_raw.columns[1]: 'Mes'}, inplace=True)
        
        # Si el Excel del INE viene en formato tradicional (Filas = Años, Columnas = Meses),
        # lo transformamos a formato vertical óptimo para Tableau. 
        # Si ya viene vertical, simplemente estandarizamos los nombres:
        df_final = df_raw.copy()
        
        # Aseguramos tipos de datos limpios
        if 'Año' in df_final.columns and 'Mes' in df_final.columns:
            # Creamos una columna de fecha real para que Tableau la entienda nativamente
            # Manejo básico de meses en español del INE
            meses_map = {
                'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
                'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
                'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6,
                'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12
            }
            if df_final['Mes'].dtype == 'object':
                df_final['Mes_Num'] = df_final['Mes'].str.strip().map(meses_map)
                # Rellenar años hacia abajo si el Excel viene combinado
                df_final['Año'] = df_final['Año'].ffill()
                df_final = df_final.dropna(subset=['Mes_Num'])
                
                # Construimos la fecha
                df_final['Fecha'] = pd.to_datetime(df_final['Año'].astype(int).astype(str) + '-' + df_final['Mes_Num'].astype(int).astype(str) + '-01').dt.date
                
                # Dejar solo las columnas deseadas (Fecha e Índice General)
                # El Índice General suele ser la tercera columna
                df_final['Valor_IPC'] = df_final[df_final.columns[2]].astype(float)
                df_final = df_final[['Fecha', 'Valor_IPC']]
        
        return df_final
