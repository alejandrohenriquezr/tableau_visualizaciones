import io
import pandas as pd
import requests
from extractors.base_extractor import BaseExtractor

class IRExtractor(BaseExtractor):
    def __init__(self):
        super().__init__(name="IR_Chile_Oficial")
        self.url = "https://www.ine.gob.cl/docs/default-source/sueldos-y-salarios/cuadros-estadisticos/ir-icl-base-anual-2023-100/series-empalmadas/tabulado_ir_real_empalmado.xlsx"

    def fetch_raw_data(self) -> dict:
        print(f"📡 Intentando conectar con el servidor del INE Chile...")
        print(f"🔗 URL: {self.url}")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(self.url, headers=headers, timeout=40)
        response.raise_for_status()
        print(f"✅ Archivo Excel leído exitosamente desde el INE. Tamaño recibido: {len(response.content)} bytes.")
        return {"excel_bytes": response.content}

    def transform(self, raw_data: dict) -> pd.DataFrame:
        print("⚙️ Iniciando proceso de transformación y limpieza de datos...")
        excel_file = io.BytesIO(raw_data["excel_bytes"])

        df = pd.read_excel(excel_file, sheet_name="General")
        
        print(f"📊 Excel cargado en memoria.")
        
        # Mapeo de meses
        meses_map = {
            1: "Enero",
            2: "Febrero",
            3: "Marzo",
            4: "Abril",
            5: "Mayo",
            6: "Junio",
            7: "Julio",
            8: "Agosto",
            9: "Septiembre",
            10: "Octubre",
            11: "Noviembre",
            12: "Diciembre"
        }
        
        # Limpiar filas donde 'mes' o 'año' sean nulos (por precaución)
        df = df.dropna(subset=['año', 'mes'])
        
        # Convertir 'mes' a numérico por si viene como string
        df['mes'] = pd.to_numeric(df['mes'], errors='coerce')
        
        # Crear la columna nombre_mes
        nombre_mes = df['mes'].map(meses_map)
        
        # Encontrar el índice de la columna 'mes' e insertar 'nombre_mes' justo después
        mes_index = df.columns.get_loc('mes')
        df.insert(mes_index + 1, 'nombre_mes', nombre_mes)
        
        print(f"📋 Estructura final del DataFrame lista para exportar. Total filas finales: {len(df)}")
        return df

if __name__ == "__main__":
    extractor = IRExtractor()
    df = extractor.run()
    print(df.head(5).to_string())
