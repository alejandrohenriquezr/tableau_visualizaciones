import os
import json
import io
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Importamos tu extractor oficial corregido del IPC
from extractors.ipc_extractor import IPCExtractor

DRIVE_FOLDER_ID = os.environ.get("GD_FOLDER_ID")

def upload_to_drive(df: pd.DataFrame, filename: str):
    """Sube o reemplaza el archivo CSV en la carpeta de Google Drive usando credenciales firmadas."""
    print(f"☁️ Iniciando conexión con Google Drive para subir el archivo: {filename}...")
    
    # Definimos los ámbitos obligatorios para la lectura y escritura de archivos
    scopes = ['https://www.googleapis.com/auth/drive']
    
    if not os.environ.get("GOOGLE_CREDENTIALS"):
        raise ValueError("❌ ERROR: La variable de entorno GOOGLE_CREDENTIALS está vacía.")
    if not DRIVE_FOLDER_ID:
        raise ValueError("❌ ERROR: La variable de entorno GD_FOLDER_ID no está configurada.")
        
    creds_dict = json.loads(os.environ.get("GOOGLE_CREDENTIALS"))
    
    # --- CONFIGURACIÓN DE AUTENTICACIÓN CORRECTA ---
    # Usamos la clase nativa de credenciales con los ámbitos cargados explícitamente
    creds = service_account.Credentials.from_service_account_info(creds_dict).with_scopes(scopes)
    
    # Construimos el servicio cliente de la API de Google Drive
    service = build('drive', 'v3', credentials=creds)
    
    # Convertir el DataFrame (las 19,648 filas) a buffer de memoria en texto CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_bytes = io.BytesIO(csv_buffer.getvalue().encode('utf-8'))
    
    # Consultar si el archivo ya existe dentro de la carpeta asignada
    query = f"name = '{filename}' and '{DRIVE_FOLDER_ID}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])
    
    media = MediaIoBaseUpload(csv_bytes, mimetype='text/csv', resumable=True)
    
    if files:
        # Si el archivo existe, tomamos el ID del primer elemento encontrado de la lista y lo actualizamos
        file_id = files[0]['id']
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"🔄 ¡ÉXITO! El archivo {filename} ya existía y fue actualizado en Drive (ID: {file_id}).")
    else:
        # Si el archivo no existe, lo creamos de cero dentro de la carpeta contenedora
        file_metadata = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
        new_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        file_id = new_file.get('id')
        print(f"🆕 ¡ÉXITO! Archivo nuevo {filename} creado correctamente en Google Drive (ID: {file_id}).")
        
        # Le aplicamos permisos de lectura globales para asegurar que Tableau pueda consumirlo
        permission_metadata = {'type': 'anyone', 'role': 'reader'}
        service.permissions().create(fileId=file_id, body=permission_metadata).execute()
        print("🔓 Permisos públicos de lectura concedidos al archivo de forma exitosa.")

if __name__ == "__main__":
    print("🚀 --- INICIANDO PIPELINE DE DATOS ---")
    
    pipeline_jobs = [
        {"extractor": IPCExtractor(), "filename": "ine_ipc_chile.csv"}
    ]
    
    print(f"📋 Total de tareas encontradas en el plan: {len(pipeline_jobs)}")
    
    for job in pipeline_jobs:
        try:
            dataframe_listo = job["extractor"].run()
            upload_to_drive(dataframe_listo, job["filename"])
        except Exception as e:
            print(f"💥 ERROR CRÍTICO procesando la tarea [{job['filename']}]: {str(e)}")
            
    print("🏁 --- PIPELINE FINALIZADO ---")
