from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os

# RUTAS (ajústalas si cambian)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CREDENTIALS_PATH = os.path.join(BASE_DIR, "data", "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "data", "token.json")

SCOPES = ['https://www.googleapis.com/auth/drive.file']


def main():
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Renovando token...")
            creds.refresh(Request())
        else:
            print("🔐 Abriendo navegador para autorizar...")
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH,
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

        print("✅ Token generado correctamente en:")
        print(TOKEN_PATH)
    else:
        print("✅ El token ya es válido, no fue necesario regenerar.")

    # Prueba rápida de conexión
    service = build('drive', 'v3', credentials=creds)
    about = service.about().get(fields="user").execute()
    print("👤 Cuenta conectada:", about["user"]["emailAddress"])


if __name__ == "__main__":
    main()
