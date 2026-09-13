import io
import pandas as pd
import requests
from extractors.base_extractor import BaseExtractor


class IPCExtractor(BaseExtractor):

  def __init__(self):
    super().__init__(name="IPC_Chile_Oficial")
    self.url = "https://ine.gob.cl"

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

    # 2. Agregar la columna 'nombre_mes' con el texto original del mes
    df["nombre_mes"] = df["Mes"].astype(str).str.strip()
    print("✏️ Columna 'nombre_mes' agregada con éxito a partir de la columna 'Mes'.")

    # 3. Conversión de tipos de datos:
    # Asegurar que todas las columnas excepto 'Glosa' (y 'nombre_mes') sean numéricas
    for col in df.columns:
      if col not in ["Glosa", "nombre_mes"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    print("🔢 Conversión de tipos completada: Todas las series numéricas han sido estandarizadas.")
    print(f"📋 Estructura final del DataFrame lista para exportar. Total filas finales: {len(df)}")
            
    return df
