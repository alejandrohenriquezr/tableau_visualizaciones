import os
import pandas as pd
from extractors.ipc_extractor import IPCExtractor

def save_to_project_folder(df: pd.DataFrame, filename: str):
    """Guarda el archivo CSV procesado directamente en la raíz de tu proyecto local."""
    print(f"📦 Guardando archivo transformado: {filename}...")
    
    # Guarda el archivo directamente en la carpeta donde estás ejecutando el script
    filepath = os.path.join(os.getcwd(), filename)
    df.to_csv(filepath, index=False, encoding='utf-8')
    
    print(f"✅ ¡ÉXITO TOTAL! Archivo guardado físicamente en: {filepath}")

if __name__ == "__main__":
    print("🚀 --- INICIANDO PIPELINE DE DATOS LOCAL ---")
    
    extractor = IPCExtractor()
    try:
        # Ejecuta la extracción de las 19,648 filas del INE
        dataframe_listo = extractor.run()
        
        # Guarda el archivo localmente de forma instantánea
        save_to_project_folder(dataframe_listo, "ine_ipc_chile.csv")
        
    except Exception as e:
        print(f"💥 ERROR CRÍTICO en el pipeline: {str(e)}")
            
    print("🏁 --- PIPELINE FINALIZADO ---")

