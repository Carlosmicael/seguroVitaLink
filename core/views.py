from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, FormView, ListView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from datetime import timedelta
from core.forms import ActivacionPolizaForm, BeneficiarioLoginForm, GestionSolicitudForm
from core.models import Siniestro, Poliza, Estudiante
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ReporteEvento
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.views.generic import FormView
from .forms import ActivacionPolizaForm
from .models import ReporteEvento





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
from .models import Profile
from core.tasks import ejecutar_recordatorio
from .models import Notificaciones
from django.utils import timezone





logger = logging.getLogger(__name__)




def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                login(request, user)
                
                if hasattr(user, 'profile'):
                    rol = user.profile.rol
                    
                    if rol == 'administrador':
                        return redirect('administrador_dashboard')
                    elif rol == 'asesor':
                        return redirect('asesor_dashboard')
                    elif rol == 'solicitante':
                        return redirect('solicitante_dashboard')
                    elif rol == 'beneficiario':
                        return redirect('beneficiario_dashboard')
                    else:
                        logout(request)
                        return render(request, 'auth/login/login.html', {
                            'error': 'Rol de usuario no válido'
                        })
                else:
                    logout(request)
                    return render(request, 'auth/login/login.html', {'error': 'Usuario no tiene perfil configurado'})
                    
            except Exception as e:
                logout(request)
                return render(request, 'auth/login/login.html', {'error': 'Error al procesar el inicio de sesión'})
        
        return render(request, 'auth/login/login.html', {'error': 'Credenciales inválidas'})

    return render(request, 'auth/login/login.html')






def reportar_evento(request):
    print("Entrando al reportar_evento")
    form_class = ActivacionPolizaForm
    success_url = reverse_lazy('inicio')
    if request.method == 'POST':

        try:
            descripcion = request.POST.get('descripcion')
            nombre_beneficiario = request.POST.get('nombre_beneficiario')
            relacion_beneficiario = request.POST.get('relacion_beneficiario')
            telefono = request.POST.get('telefono')
            email = request.POST.get('email')
            archivo_documento = request.FILES.get('archivo_documento')
            nombre_estudiante_fallecido = request.POST.get('nombre_estudiante_fallecido')
            cedula_estudiante_fallecido = request.POST.get('cedula_estudiante_fallecido')
            motivo_muerte = request.POST.get('motivo_muerte')

            reporte = ReporteEvento.objects.create(
                descripcion=descripcion,
                nombre_beneficiario=nombre_beneficiario,
                relacion_beneficiario=relacion_beneficiario,
                telefono=telefono,
                email=email,
                estado='nuevo',
                evaluado=False,
                archivo_documento=archivo_documento,
                nombre_estudiante_fallecido=nombre_estudiante_fallecido,
                cedula_estudiante_fallecido=cedula_estudiante_fallecido,
                motivo_muerte=motivo_muerte
            )
            reporte.save()

            print("Reporte guardado correctamente")

            fecha_hora_str = timezone.now() + timedelta(minutes=1)
            print(f"Programando tarea para: {fecha_hora_str}")
            task = ejecutar_recordatorio.apply_async(eta=fecha_hora_str)

            profileFilter = Profile.objects.filter(rol='asesor')   
            profile = profileFilter.first()

            recordatorio = Notificaciones.objects.create(
                not_codcli=profile,
                not_poliza = Poliza.objects.filter(estado="activa").first(),
                not_fecha_proceso=fecha_hora_str, 
                not_fecha_creacion=timezone.now(),
                not_mensaje=f"Recordatorio de reporte se ha mandado un reporte de evento para {reporte.id}",
                not_read=False,
                not_estado=False,
                not_celery_task_id=task.id,
            )

            recordatorio.save()

            messages.success(request, "Reporte enviado correctamente.")
            return redirect('inicio')

        except Exception as e:
            print(f"Error al enviar el reporte: {str(e)}")
            messages.error(request, f"Error al enviar el reporte: {str(e)}")
            return redirect('inicio')

    return render(request, 'siniestros/formulario_activacion.html', {'form': form_class, 'success_url': success_url})









































class SiniestrosInicioView(TemplateView):

    print("SiniestrosInicioView")

    template_name = 'siniestros/siniestro_report.html' 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print("SiniestrosInicioView - get_context_data")
        context['titulo'] = 'Gestión de Siniestros - VitaLink'
        return context













class FormularioActivacionView(FormView):
    """Vista para el formulario de reporte de evento (fallecimiento)"""
    template_name = 'siniestros/formulario_activacion.html'
    form_class = ActivacionPolizaForm
    success_url = reverse_lazy('siniestros:inicio')
    
    def form_valid(self, form):
        """Procesar el formulario válido"""
        try:
            # Crear el reporte con todos los datos
            reporte = ReporteEvento(
                # Datos originales
                descripcion=form.cleaned_data['descripcion'],
                nombre_beneficiario=form.cleaned_data['nombre_beneficiario'],
                relacion_beneficiario=form.cleaned_data['relacion_beneficiario'],
                telefono=form.cleaned_data['telefono'],
                email=form.cleaned_data['email'],
                archivo_documento=form.cleaned_data.get('archivo_documento'),
                
                nombre_estudiante_fallecido=form.cleaned_data['nombre_estudiante_fallecido'],
                cedula_estudiante_fallecido=form.cleaned_data['cedula_estudiante_fallecido'],
                motivo_muerte=form.cleaned_data['motivo_muerte'],
                
                # Estado inicial
                estado='nuevo',
                evaluado=False
            )
            reporte.save()
            
            messages.success(
                self.request,
                f'✓ Reporte #{reporte.id} registrado exitosamente. '
                f'El equipo de VitalLink se contactará con los beneficiarios utilizando los datos proporcionados. '
                f'Recibirá una confirmación en {reporte.email}.'
            )
            
        except Exception as e:
            messages.error(
                self.request,
                f'❌ Error al procesar el reporte: {str(e)}. Por favor, intenta nuevamente.'
            )
            return self.form_invalid(form)
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Procesar formulario inválido"""
        # Mostrar errores específicos
        for field, errors in form.errors.items():
            for error in errors:
                field_name = form.fields[field].label if field in form.fields else field
                messages.error(self.request, f'{field_name}: {error}')
        
        # Error general si no hay archivo
        if not form.cleaned_data.get('archivo_documento'):
            messages.error(
                self.request,
                'El certificado de defunción es obligatorio. Por favor, adjunta el documento.'
            )
        
        return super().form_invalid(form)






def is_staff_user(user):
    """Verificar si el usuario es staff"""
    return user.is_authenticated and user.is_staff


class AdminSolicitudesListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Vista para listar todas las solicitudes (siniestros) para el administrador"""
    model = Siniestro
    template_name = 'siniestros/admin_lista_solicitudes.html'
    context_object_name = 'solicitudes'
    paginate_by = 20
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def get_queryset(self):
        return Siniestro.objects.all().select_related('poliza', 'poliza__estudiante').order_by('-fecha_reporte')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ahora = timezone.now()
        
        # Calcular días restantes para cada solicitud
        solicitudes_con_plazo = []
        for solicitud in context['solicitudes']:
            fecha_vencimiento = solicitud.fecha_reporte + timedelta(days=4)
            dias_restantes = (fecha_vencimiento - ahora).days
            horas_restantes = (fecha_vencimiento - ahora).total_seconds() / 3600
            
            solicitudes_con_plazo.append({
                'solicitud': solicitud,
                'fecha_vencimiento': fecha_vencimiento,
                'dias_restantes': dias_restantes,
                'horas_restantes': horas_restantes,
                'vencido': dias_restantes < 0,
                'por_vencer': 0 <= dias_restantes <= 1
            })
        
        context['solicitudes_con_plazo'] = solicitudes_con_plazo
        return context


class AdminSolicitudDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Vista para ver el detalle de una solicitud"""
    model = Siniestro
    template_name = 'siniestros/admin_detalle_solicitud.html'
    context_object_name = 'solicitud'
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        solicitud = context['solicitud']
        ahora = timezone.now()
        fecha_vencimiento = solicitud.fecha_reporte + timedelta(days=4)
        dias_restantes = (fecha_vencimiento - ahora).days
        horas_restantes = (fecha_vencimiento - ahora).total_seconds() / 3600
        
        context['fecha_vencimiento'] = fecha_vencimiento
        context['dias_restantes'] = dias_restantes
        context['horas_restantes'] = horas_restantes
        context['vencido'] = dias_restantes < 0
        context['por_vencer'] = 0 <= dias_restantes <= 1
        context['form'] = GestionSolicitudForm(instance=solicitud)
        return context





class AdminGestionSolicitudView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Vista para gestionar una solicitud (asignar tipo, estudiante, etc.)"""
    model = Siniestro
    form_class = GestionSolicitudForm
    template_name = 'siniestros/admin_gestionar_solicitud.html'
    context_object_name = 'solicitud'
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('siniestros:admin_detalle_solicitud', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Obtener el estudiante seleccionado
        estudiante = form.cleaned_data['estudiante']
        
        # Obtener o crear la póliza del estudiante (OneToOneField)
        poliza, created = Poliza.objects.get_or_create(
            estudiante=estudiante,
            defaults={
                'numero': f'POL-{estudiante.codigo_estudiante}-{estudiante.id}',
                'estado': 'activa'
            }
        )
        
        # Guardar primero los campos del ModelForm
        siniestro = form.save(commit=False)
        
        # Asignar la póliza al siniestro
        siniestro.poliza = poliza
        siniestro.revisado_por = self.request.user
        siniestro.save()
        
        messages.success(self.request, f'Solicitud #{siniestro.id} actualizada correctamente.')
        return redirect(self.get_success_url())




































































































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
        return JsonResponse({'doc_file_url': file_url, 'doc_file': file_url})
    
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













