import os
import pandas as pd
from extractors.ipc_extractor import IPCExtractor

def save_locally(df: pd.DataFrame, filename: str):
    """Guarda el archivo CSV directamente en el repositorio local para GitHub Pages."""
    print(f"📦 Guardando archivo transformado en el entorno local: {filename}...")
    
    # Creamos una carpeta pública si no existe
    os.makedirs("public", exist_ok=True)
    filepath = os.path.join("public", filename)
    
    # Exportamos las 19,648 filas limpias
    df.to_csv(filepath, index=False, encoding='utf-8')
    print(f"✅ ¡ÉXITO! Archivo guardado correctamente en: {filepath}")

if __name__ == "__main__":
    print("🚀 --- INICIANDO PIPELINE DE DATOS NATIVO ---")
    
    extractor = IPCExtractor()
    try:
        # Se ejecuta tu limpieza impecable del IPC del INE
        dataframe_listo = extractor.run()
        
        # Guardado local rápido y sin APIs externas de Google
        save_locally(dataframe_listo, "ine_ipc_chile.csv")
        
    except Exception as e:
        print(f"💥 ERROR CRÍTICO en el pipeline: {str(e)}")
            
    print("🏁 --- PIPELINE FINALIZADO ---")
