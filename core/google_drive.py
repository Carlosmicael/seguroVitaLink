# apps/abogado_app/google_drive.py
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# BASE_DIR apunta a la raíz del proyecto Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# rutas relativas seguras
DATA_DIR = os.path.join(BASE_DIR, 'data')
CREDENTIALS_PATH = os.path.join(DATA_DIR, 'credentials.json')
TOKEN_PATH = os.path.join(DATA_DIR, 'token.json')

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    if not os.path.exists(TOKEN_PATH):
        raise RuntimeError(f"❌ Token no encontrado en {TOKEN_PATH}")

    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # guarda token renovado
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)





def upload_file_to_drive(file_path, file_name, folder_id=None, convert_to_google_doc=False):
    service = get_drive_service()

    metadata = {'name': file_name}
    if folder_id:
        metadata['parents'] = [folder_id]

    if convert_to_google_doc:
        metadata['mimeType'] = 'application/vnd.google-apps.document'

    media = MediaFileUpload(file_path, resumable=True)
    uploaded = service.files().create(
        body=metadata,
        media_body=media,
        fields='id'
    ).execute()

    file_id = uploaded.get('id')

    # hacerlo público
    try:
        service.permissions().create(
            fileId=file_id,
            body={'role': 'reader', 'type': 'anyone'}
        ).execute()
    except Exception as e:
        print("⚠️ No se pudieron cambiar los permisos:", e)

    return {
        'file_id': file_id,
        'view_url': f"https://drive.google.com/file/d/{file_id}/view",
        'edit_url': f"https://docs.google.com/document/d/{file_id}/edit"
    }