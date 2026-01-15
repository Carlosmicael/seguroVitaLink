from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect




def login_view(request):

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            rol = user.profile.rol

            if rol == 'asesor':
                return redirect('asesor_dashboard')

            elif rol == 'solicitante':
                return redirect('solicitante_dashboard')

        return render(request, 'login.html', {'error': 'Credenciales inválidas'})

    return render(request, 'auth/login/login.html')







































































import os
import io
import json
import re
import zipfile
import requests
import traceback
import logging
from datetime import datetime

# Django Core
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse, Http404, HttpResponseNotAllowed
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

# Terceros (Documentos y Drive)
from docx import Document
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Formularios y Modelos locales
from .forms import TcasDocumentosForm
from .models import TcasDocumentos


logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN GOOGLE DRIVE ---
TOKEN_PATH = os.getenv("TOKEN_PATH")
SCOPES = ['https://www.googleapis.com/auth/drive.file']























@login_required(login_url='login')
def documentos_view(request):
    control = False
    titulo = "Documentos"
    subtitulo = "Gestiona los documentos y procesos"
    print("Llegó a documentossssssssddsasafgsghahg!")
    """Vista para mostrar la página de gestión de documentos y procesos"""
    
    if request.method == 'POST':
        print("Llegó a documentos!")
        formDocumentos = TcasDocumentosForm(request.POST)

        if formDocumentos.is_valid():
            print("Llegó a documentos pero de subida!")
            descripcion = formDocumentos.cleaned_data.get("doc_descripcion")
            archivo = request.FILES['archivo']
            documentos = TcasDocumentos.objects.create(doc_descripcion=descripcion,doc_file=archivo,fecha_edit=timezone.now())
            documentos.save()
            return redirect('documentos')
 

        
        return redirect('documentos')

    else:
        formDocumentos = TcasDocumentosForm()
    
    return render(request, 'asesor/components/documentos/documentos.html', {'formDocumentos': formDocumentos, 'control': control, 'titulo': titulo, 'subtitulo': subtitulo})










@login_required(login_url='/login')
def obtener_documentos_por_proceso(request):
    print("Llegó a obtener_documentos_por_proceso!")
    try:
        documentos = TcasDocumentos.objects.all().values("doc_cod_doc", "doc_descripcion", "doc_file", "doc_size","fec_creacion","fecha_edit").order_by('-fec_creacion')
        print("Documentos obtenidos:", documentos)
        return JsonResponse(list(documentos), safe=False)
    except TcasDocumentos.DoesNotExist:
        return JsonResponse({"error": "Documentos no encontrados"}, status=404)





from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from docx import Document
import io, os, zipfile





@login_required(login_url='/login')
def descargar_documento(request, doc_id):
    documento = get_object_or_404(TcasDocumentos, pk=doc_id)

    if not documento.doc_file:
        raise Http404("Documento no encontrado")

    nombre_archivo = documento.doc_file.name.split("/")[-1]
    extension = os.path.splitext(nombre_archivo)[1].lower()

    if extension == ".pdf":
        return FileResponse(
            documento.doc_file.open("rb"),
            as_attachment=True,
            filename=nombre_archivo
        )

    elif extension == ".docx":
        try:
            file_bytes = documento.doc_file.open("rb").read()
            if not zipfile.is_zipfile(io.BytesIO(file_bytes)):
                raise ValueError("Archivo .docx inválido")

            doc = Document(io.BytesIO(file_bytes))
            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            return FileResponse(buffer, as_attachment=True, filename=nombre_archivo)

        except Exception as e:
            print(f"Advertencia DOCX: {e}")
            documento.doc_file.open("rb").seek(0)
            return FileResponse(
                documento.doc_file.open("rb"),
                as_attachment=True,
                filename=nombre_archivo
            )

    elif extension == ".doc":
        return FileResponse(
            documento.doc_file.open("rb"),
            as_attachment=True,
            filename=nombre_archivo
        )

    elif extension in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".svg"]:
        return FileResponse(
            documento.doc_file.open("rb"),
            as_attachment=True,
            filename=nombre_archivo
        )

    else:
        raise Http404("Tipo de archivo no soportado")






@login_required(login_url='/login')
def eliminar_documento(request, doc_id):
    if request.method == "DELETE":
        documento = get_object_or_404(TcasDocumentos, pk=doc_id)
        documento.doc_file.delete(save=False)  
        documento.delete()
        return JsonResponse({"status": "ok"})
    return HttpResponseNotAllowed(["DELETE"])






TOKEN_PATH = os.getenv("TOKEN_PATH")
SCOPES = ['https://www.googleapis.com/auth/drive.file']



def get_drive_service():
    if not os.path.exists(TOKEN_PATH):
        raise RuntimeError(f"Token no encontrado en {TOKEN_PATH}")
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
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
    uploaded = service.files().create(body=metadata,media_body=media,fields='id').execute()

    file_id = uploaded.get('id')

    try:
        service.permissions().create(fileId=file_id,body={'role': 'writer', 'type': 'anyone'}).execute()
    except Exception as e:
        print("No se pudieron cambiar los permisos:", e)

    return {
        'file_id': file_id,
        'view_url': f"https://drive.google.com/file/d/{file_id}/view",
        'edit_url': f"https://docs.google.com/document/d/{file_id}/edit"
    }




@login_required(login_url='/login')
def view_documento(request, doc_id):
    documento = get_object_or_404(TcasDocumentos, pk=doc_id)
    documento.fecha_edit = timezone.now()
    documento.save()
    file_url = documento.doc_file.url
    file_url_local = documento.doc_file.url
    file_path = documento.doc_file.path

    if file_url.endswith(".pdf") or file_url.endswith(".doc") or file_url.endswith(".docx"):
        result = upload_file_to_drive(file_path, os.path.basename(file_path), convert_to_google_doc=True)
        return JsonResponse({'doc_file_url': result['edit_url'],'doc_file': file_url_local})
    
    print("Archivo no es PDF, DOC o DOCX")
    print("File URL:", file_url)
    return JsonResponse({'doc_file_url': f'/imagenesbytes/{doc_id}/'})








import mimetypes
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required(login_url='/login')
def imagenesbytes(request, doc_id):
    documento = get_object_or_404(TcasDocumentos, pk=doc_id)

    file_path = documento.doc_file.path
    file_name = documento.doc_file.name.lower()
    if not file_name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')):
        raise Http404("No es una imagen")
    mime_type, _ = mimetypes.guess_type(file_path)

    return FileResponse(open(file_path, 'rb'), content_type=mime_type or 'image/jpeg')











import traceback
import requests
import json
import re
import os
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required



def extract_drive_id(url):
    patterns = [
        r"/d/([a-zA-Z0-9_-]+)",                      
        r"id=([a-zA-Z0-9_-]+)",                     
        r"/file/d/([a-zA-Z0-9_-]+)"                 
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None




def make_download_url(url):
    if not url:
        return url

    if "docs.google.com/document/d/" in url:
        doc_id = extract_drive_id(url)
        if doc_id:
            return f"https://docs.google.com/document/d/{doc_id}/export?format=pdf"

    if "drive.google.com/file/d/" in url or "drive.google.com/open" in url:
        file_id = extract_drive_id(url)
        if file_id:
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


@csrf_exempt
@login_required(login_url='/login')
def remplazar_documento(request, doc_id):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        url_pdf = data.get("url_pdf")
        file_path = data.get("file_path")

        if not url_pdf or not file_path:
            return JsonResponse({"error": "Faltan parámetros"}, status=400)

        try:
            documento = TcasDocumentos.objects.get(pk=doc_id)
        except TcasDocumentos.DoesNotExist:
            return JsonResponse({"error": f"Documento con id={doc_id} no existe"}, status=404)

        if file_path.startswith("/media/"):
            relative_path = file_path.replace("/media/", "")
            abs_file_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        elif file_path.startswith("http://") or file_path.startswith("https://"):
            idx = file_path.find("/media/")
            if idx != -1:
                relative_path = file_path[idx + len("/media/"):]
                abs_file_path = os.path.join(settings.MEDIA_ROOT, relative_path)
            else:
                return JsonResponse({"error": "file_path no apunta a /media/"}, status=400)
        else:
            abs_file_path = os.path.join(settings.MEDIA_ROOT, file_path.lstrip("/"))

        os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)

        download_url = make_download_url(url_pdf)
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(download_url, headers=headers, stream=True, timeout=60)

        if resp.status_code not in (200, 206):
            return JsonResponse({"error": f"No se pudo descargar el archivo (status {resp.status_code})"}, status=500)

        if os.path.exists(abs_file_path):
            try:
                os.remove(abs_file_path)
            except Exception as e:
                print("Warning: no se pudo eliminar fichero anterior:", e)

        with open(abs_file_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        if os.path.getsize(abs_file_path) == 0:
            return JsonResponse({"error": "El archivo descargado está vacío"}, status=500)

        nombre_archivo = os.path.basename(abs_file_path)
        documento.doc_file = f"documentos/{nombre_archivo}"

        print(documento.doc_file)
        documento.save()

        try:
            eliminar_archivo_drive_interno(url_pdf)
        except Exception as e:
            print("Warning: fallo al eliminar en drive:", e)

        return JsonResponse({
            "message": "Documento reemplazado correctamente",
            "nuevo_archivo": documento.doc_file.url,
        })

    except Exception as e:
        print("ERROR remplazar_documento:", e)
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)




def eliminar_archivo_drive_interno(url_pdf):
    try:
        file_id = url_pdf.split("/d/")[1].split("/")[0]
        service = get_drive_service()
        service.files().delete(fileId=file_id).execute()
        print(f"Archivo {file_id} eliminado de Google Drive.")
    except Exception as e:
        print("Error eliminando archivo de Drive:", e)


@csrf_exempt
@login_required(login_url='/login')
def eliminar_drive(request):
    if request.method == "POST":
        data = json.loads(request.body)
        url_pdf = data.get("url_pdf")
        if not url_pdf:
            return JsonResponse({"error": "Falta url_pdf"}, status=400)

        eliminar_archivo_drive_interno(url_pdf)
        return JsonResponse({"message": "Archivo eliminado de Drive"})
    return JsonResponse({"error": "Método no permitido"}, status=405)













