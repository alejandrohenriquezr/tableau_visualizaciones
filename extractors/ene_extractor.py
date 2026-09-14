import io
import pandas as pd
import requests
from extractors.base_extractor import BaseExtractor

class ENEExtractor(BaseExtractor):
    def __init__(self):
        super().__init__(name="ENE_Chile_Oficial")
        self.url = "https://www.ine.gob.cl/docs/default-source/ocupacion-y-desocupacion/cuadros-estadisticos/series-vigentes/indicadores_principales.xlsx"

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

        # Leer saltando las primeras 5 filas. La fila 6 (índice 5 original) tendrá los nombres principales,
        # y la fila 7 (índice 6 original) tendrá "nota" / "en miles" / "tasa (%)".
        # Usamos header=[0, 1] para capturar ambas filas como MultiIndex.
        df = pd.read_excel(excel_file, sheet_name="AS", skiprows=5, header=[0, 1])
        
        print(f"📊 Excel cargado en memoria.")
        
        # Crear los nuevos nombres de columnas
        new_columns = []
        for col in df.columns:
            # col es una tupla, e.g., ('Año', 'Unnamed: 0_level_1') o ('Población en edad de trabajar (Total)', 'nota')
            main_col = str(col[0]).strip()
            sub_col = str(col[1]).strip()
            
            # Limpiar nombres de columnas Unnamed
            if "Unnamed" in main_col:
                main_col = ""
            if "Unnamed" in sub_col:
                sub_col = ""
            
            # Combinar ambos niveles
            if main_col and sub_col:
                # Arreglar el caso en que el main_col está vacío por celdas combinadas (pandas le pone Unnamed a veces, pero con MultiIndex suele repetir o dejar vacío)
                # En pandas, las celdas combinadas en MultiIndex suelen llenarse hacia la derecha si no se desactiva, pero a veces no.
                pass
        
        # En la práctica, dado que las celdas están combinadas, read_excel puede hacer que main_col se repita para ambas subcolumnas.
        # Vamos a implementarlo uniendo con un " - "
        for col in df.columns:
            main_col = str(col[0]).strip()
            sub_col = str(col[1]).strip()
            
            if "Unnamed" in main_col:
                main_col = ""
            if "Unnamed" in sub_col:
                sub_col = ""
                
            if main_col and sub_col:
                new_col_name = f"{main_col} - {sub_col}"
            elif main_col:
                new_col_name = main_col
            elif sub_col:
                new_col_name = sub_col
            else:
                new_col_name = "Columna_Vacia"
                
            new_columns.append(new_col_name)
            
        df.columns = new_columns
        
        # Asegurar que Año sea numérico, convirtiendo notas al final en NaN
        df["Año"] = pd.to_numeric(df["Año"], errors='coerce')
        
        # Remover cualquier fila donde Año o Trimestre sean nulos
        df = df.dropna(subset=['Año', 'Trimestre'])
        
        # Convertir de vuelta a entero para evitar el formato 2010.0
        df["Año"] = df["Año"].astype(int)
        
        # Mapeo del mes central del trimestre
        mes_central_map = {
            "Ene - Mar": "Feb",
            "Feb - Abr": "Mar",
            "Mar - May": "Abr",
            "Abr - Jun": "May",
            "May - Jul": "Jun",
            "Jun - Ago": "Jul",
            "Jul - Sep": "Ago",
            "Ago - Oct": "Sep",
            "Sep - Nov": "Oct",
            "Oct - Dic": "Nov",
            "Nov - Ene": "Dic",
            "Dic - Feb": "Ene"
        }
        
        # Crear Trim_año y mes_año
        # Primero aseguramos que Año se formatee sin decimales si viene como float
        año_str = df["Año"].fillna(0).astype(int).astype(str)
        # Limpiamos Trimestre de espacios extra en los bordes
        trimestre_str = df["Trimestre"].astype(str).str.strip()
        
        trim_año = año_str + "_" + trimestre_str
        mes_central = trimestre_str.map(mes_central_map)
        mes_año = mes_central + "_" + año_str
        
        # Insertamos después de Trimestre (índice 1)
        df.insert(2, "Trim_año", trim_año)
        df.insert(3, "mes_año", mes_año)
        
        print(f"📋 Estructura final del DataFrame lista para exportar. Total filas finales: {len(df)}")
        return df

if __name__ == "__main__":
    extractor = ENEExtractor()
    df = extractor.run()
    print(df.head(5).to_string())
