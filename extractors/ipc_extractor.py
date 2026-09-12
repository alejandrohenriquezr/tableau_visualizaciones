import io
import pandas as pd
import requests
from extractors.base_extractor import BaseExtractor


class IPCExtractor(BaseExtractor):

  def __init__(self):
    super().__init__(name="IPC_Chile_Oficial")
    self.url = "https://ine.gob.cl"

  def fetch_raw_data(self) -> dict:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(self.url, headers=headers, timeout=40)
    response.raise_for_status()
    return {"excel_bytes": response.content}

  def transform(self, raw_data: dict) -> pd.DataFrame:
    excel_file = io.BytesIO(raw_data["excel_bytes"])

    # 1. Elimina únicamente las primeras 3 filas (títulos del cuadro y fila en blanco)
    # La fila 4 pasa a ser la cabecera del DataFrame.
    df = pd.read_excel(excel_file, sheet_name=0, skiprows=3)

    # Renombramos la segunda columna a 'Mes' para trabajarla con seguridad
    df.rename(columns={df.columns[1]: "Mes"}, inplace=True)

    # 2. Agregar la columna 'nombre_mes' con el texto original del mes
    df["nombre_mes"] = df["Mes"].astype(str).str.strip()

    # 3. Conversión de tipos de datos:
    # Asegurar que todas las columnas excepto 'Glosa' (y 'nombre_mes') sean numéricas
    for col in df.columns:
      if col not in ["Glosa", "nombre_mes"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df
