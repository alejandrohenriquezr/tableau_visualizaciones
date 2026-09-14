import os
import pandas as pd
from extractors.ipc_extractor import IPCExtractor
from extractors.ene_extractor import ENEExtractor
from extractors.ir_extractor import IRExtractor

def save_to_project_folder(df: pd.DataFrame, filename: str):
    """Guarda el archivo CSV procesado directamente en la raíz de tu proyecto local."""
    print(f"📦 Guardando archivo transformado: {filename}...")
    
    # Guarda el archivo directamente en la carpeta donde estás ejecutando el script
    filepath = os.path.join(os.getcwd(), filename)
    df.to_csv(filepath, index=False, encoding='utf-8')
    
    print(f"✅ ¡ÉXITO TOTAL! Archivo guardado físicamente en: {filepath}")

if __name__ == "__main__":
    print("🚀 --- INICIANDO PIPELINE DE DATOS LOCAL ---")
    
    # --- 1. Extractor de IPC ---
    ipc_extractor = IPCExtractor()
    try:
        df_ipc = ipc_extractor.run()
        save_to_project_folder(df_ipc, "ine_ipc_chile.csv")
    except Exception as e:
        print(f"💥 ERROR CRÍTICO en IPC: {str(e)}")

    print("\n----------------------------------------\n")
    
    # --- 2. Extractor de ENE ---
    ene_extractor = ENEExtractor()
    try:
        df_ene = ene_extractor.run()
        save_to_project_folder(df_ene, "ine_ene_chile.csv")
    except Exception as e:
        print(f"💥 ERROR CRÍTICO en ENE: {str(e)}")

    print("\n----------------------------------------\n")
    
    # --- 3. Extractor de IR ---
    ir_extractor = IRExtractor()
    try:
        df_ir = ir_extractor.run()
        save_to_project_folder(df_ir, "ine_ir_chile.csv")
    except Exception as e:
        print(f"💥 ERROR CRÍTICO en IR: {str(e)}")
            
    print("🏁 --- PIPELINE FINALIZADO ---")

