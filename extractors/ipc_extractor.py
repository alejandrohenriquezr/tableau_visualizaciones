import io
import pandas as pd
import requests
from extractors.base_extractor import BaseExtractor


class IPCExtractor(BaseExtractor):

  def __init__(self):
    super().__init__(name="IPC_Chile_Oficial")
    self.url = "https://www.ine.gob.cl/docs/default-source/%C3%ADndice-de-precios-al-consumidor/cuadros-estadisticos/base-anual-2023_100/series-de-tiempo/ipc-xls.xlsx"

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

    # 1. Elimina únicamente las primeras 3 filas (títulos del cuadro y fila en blanco)
    # La fila 4 pasa a ser la cabecera del DataFrame.
    df = pd.read_excel(excel_file, sheet_name=0, skiprows=3)
    print(f"📊 Excel cargado en memoria. Columnas detectadas inicialmente: {list(df.columns)}")
    print(f"📉 Filas detectadas inicialmente: {len(df)}")

    # Renombramos la segunda columna a 'Mes' para trabajarla con seguridad
    df.rename(columns={df.columns[1]: "Mes"}, inplace=True)

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
    # 2. Agregar la columna 'nombre_mes' con el texto original del mes
    df['Mes'] = pd.to_numeric(df['Mes'], errors='coerce')
    
    # Crear la columna nombre_mes
    nombre_mes = df['Mes'].map(meses_map)
    año_str = df["Año"].fillna(0).astype(int).astype(str)
    print("✏️ Columna 'nombre_mes' agregada con éxito a partir de la columna 'Mes'.")

    mes_año = nombre_mes + " " + año_str
    mes_index = df.columns.get_loc('Mes')
    df.insert(mes_index + 1, 'nombre_mes', nombre_mes)   
    df.insert(mes_index + 2, 'mes_año', mes_año)  
    


    # 3. Conversión de tipos de datos:
    # Asegurar que todas las columnas excepto 'Glosa' (y 'nombre_mes') sean numéricas
    for col in df.columns:
      if col not in ["Glosa", "nombre_mes", "mes_año"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    print("🔢 Conversión de tipos completada: Todas las series numéricas han sido estandarizadas.")
    print(f"📋 Estructura final del DataFrame lista para exportar. Total filas finales: {len(df)}")
            
    return df
