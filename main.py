import os
import json
import io
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Importar extractores activos
from extractors.ipc_extractor import IPCExtractor
# Cuando crees más, solo los importas aquí:
# from extractors.ene_extractor import ENEExtractor 

DRIVE_FOLDER_ID = os.environ.get("GD_FOLDER_ID")

def upload_to_drive(df: pd.DataFrame, filename: str):
    """Sube o reemplaza el archivo CSV en la carpeta de Google Drive."""
    scopes = ['https://googleapis.com']
    
    creds_dict = json.loads(os.environ.get("GOOGLE_CREDENTIALS"))
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    service = build('drive', 'v3', credentials=creds)
    
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_bytes = io.BytesIO(csv_buffer.getvalue().encode('utf-8'))
    
    query = f"name = '{filename}' and '{DRIVE_FOLDER_ID}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])
    
    media = MediaIoBaseUpload(csv_bytes, mimetype='text/csv', resumable=True)
    
    if files:
        file_id = files[0]['id'] # Corrección: obtener el primer elemento de la lista
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f" Archivo {filename} actualizado exitosamente.")
    else:
        file_metadata = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
        new_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        file_id = new_file.get('id')
        print(f" Archivo {filename} creado exitosamente con ID: {file_id}")
        
        # --- NUEVO BLOQUE: OTORGAR PERMISOS ---
        # Esto hace que el archivo herede o permita que cualquier usuario con acceso a la carpeta lo lea
        permission_metadata = {
            'type': 'anyone',
            'role': 'reader'
        }
        service.permissions().create(fileId=file_id, body=permission_metadata).execute()
        print(f" Permisos de lectura globales aplicados al archivo.")
