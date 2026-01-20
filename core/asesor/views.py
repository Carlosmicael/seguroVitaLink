from django.shortcuts import render
from core.decorators import role_required
from core.models import Poliza, Estudiante, Profile, Notificaciones, ReporteEvento, Siniestro, ConfiguracionSiniestro

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from core.forms import PolizaForm, SiniestroForm
from django.contrib.auth.decorators import login_required
from core.tasks import ejecutar_recordatorio
from django.utils.timezone import make_aware
from django.utils import timezone
import logging
from datetime import datetime
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
import pusher
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.dateformat import DateFormat
from django.views.decorators.http import require_POST
import os
from datetime import timedelta



logger = logging.getLogger(__name__)






@login_required(login_url='login')
@role_required(['asesor'])
def asesor_dashboard(request):
    return render(request, 'asesor/components/dashboard/dashboard.html')








@login_required(login_url='login')
@role_required(['asesor'])
def siniestros_module_lista(request):
    siniestros = Siniestro.objects.select_related('poliza', 'revisado_por').all()
    
    # Estadísticas
    total = siniestros.count()
    pendientes = siniestros.filter(estado='pendiente').count()
    aprobados = siniestros.filter(estado='aprobado').count()
    rechazados = siniestros.filter(estado='rechazado').count()
    pagados = siniestros.filter(estado='pagado').count()
    enviados = siniestros.filter(enviado=True).count()
    
    for siniestro in siniestros:
        if siniestro.fecha_limite_reporte:
            delta = siniestro.fecha_limite_reporte - timezone.now().date()
            siniestro.dias_restantes = delta.days
        else:
            siniestro.dias_restantes = None
    
    polizas_activas = Poliza.objects.all()
    
    context = {
        'siniestros': siniestros,
        'total': total,
        'pendientes': pendientes,
        'aprobados': aprobados,
        'rechazados': rechazados,
        'pagados': pagados,
        'enviados': enviados,
        'polizas_activas': polizas_activas,
        'tipos_siniestro': Siniestro.TIPO_CHOICES,
    }
    return render(request, 'asesor/components/siniestros/siniestros_module_lista.html', context)












@login_required(login_url='login')
@role_required(['asesor'])
def siniestros_module_detalle(request, id):
    siniestro = get_object_or_404(Siniestro, id=id)
    
    if not siniestro.revisado_por:
        siniestro.revisado_por = request.user
        siniestro.save()
    
    dias_restantes = None
    if siniestro.fecha_limite_reporte:
        delta = siniestro.fecha_limite_reporte - timezone.now().date()
        dias_restantes = delta.days
    
    archivo_url = None
    archivo_tipo = None
    archivo_nombre = None
    
    if siniestro.documento:
        archivo_url = siniestro.documento.url
        archivo_nombre = os.path.basename(siniestro.documento.name)
        extension = os.path.splitext(archivo_nombre)[1].lower()
        
        if extension in ['.pdf']:
            archivo_tipo = 'pdf'
        elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            archivo_tipo = 'imagen'
        elif extension in ['.doc', '.docx']:
            archivo_tipo = 'word'
        elif extension in ['.xls', '.xlsx']:
            archivo_tipo = 'excel'
        else:
            archivo_tipo = 'otro'
    
    estudiantes_info = []
    if siniestro.poliza:
        estudiantes = siniestro.poliza.estudiantes.all()
        for estudiante in estudiantes:
            estudiantes_info.append(f"{estudiante.nombres} {estudiante.apellidos}")
    
    estudiantes_texto = ", ".join(estudiantes_info) if estudiantes_info else 'N/A'

    
    data = {
        'id': siniestro.id,
        'poliza': {'numero': siniestro.poliza.numero_poliza if siniestro.poliza else 'Sin póliza','estudiante': estudiantes_texto,},




        'tipo': siniestro.get_tipo_display() if siniestro.tipo else 'N/A',
        'descripcion': siniestro.descripcion,
        'fecha_evento': siniestro.fecha_evento.strftime('%d/%m/%Y') if siniestro.fecha_evento else 'N/A',
        'estado': siniestro.estado,
        'estado_display': siniestro.get_estado_display(),
        'enviado': siniestro.enviado,
        'fecha_reporte': siniestro.fecha_reporte.strftime('%d/%m/%Y %I:%M %p'),
        'fecha_limite': siniestro.fecha_limite_reporte.strftime('%d/%m/%Y') if siniestro.fecha_limite_reporte else 'N/A',
        'dias_restantes': dias_restantes,
        'nombre_beneficiario': siniestro.nombre_beneficiario,
        'relacion_beneficiario': siniestro.relacion_beneficiario,
        'parentesco': siniestro.parentesco,
        'telefono': siniestro.telefono_contacto,
        'email': siniestro.email_contacto,
        'revisado_por': siniestro.revisado_por.username if siniestro.revisado_por else 'No revisado',
        'comentarios': siniestro.comentarios,
        'archivo_url': archivo_url,
        'archivo_tipo': archivo_tipo,
        'archivo_nombre': archivo_nombre,
    }
    
    return JsonResponse(data)












@login_required(login_url='login')
@role_required(['asesor'])
@require_http_methods(["POST"])
def siniestros_module_crear(request):
    try:
        form = SiniestroForm(request.POST, request.FILES)


        if form.is_valid():
            siniestro = form.save(commit=False)
            
            config = ConfiguracionSiniestro.objects.filter(activo=True).first()
            
            if config:
                dias_max = config.dias_max_reporte
                fecha_actual = timezone.now().date()
                siniestro.fecha_limite_reporte = fecha_actual + timedelta(days=dias_max)
            else:
                fecha_actual = timezone.now().date()
                siniestro.fecha_limite_reporte = fecha_actual + timedelta(days=3)
            
            siniestro.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Siniestro creado exitosamente',
                'siniestro_id': siniestro.id
            })
        else:
            return JsonResponse({'success': False,'errors': form.errors}, status=400)
            
    except Exception as e:
        return JsonResponse({'success': False,'message': str(e)}, status=500)

















@login_required(login_url='login')
@role_required(['asesor'])
@require_http_methods(["POST"])
def siniestros_module_enviar(request, id):
    """Vista para marcar un siniestro como enviado"""
    try:
        siniestro = get_object_or_404(Siniestro, id=id)
        
        # Validar que el siniestro no esté ya enviado
        if siniestro.enviado:
            return JsonResponse({
                'success': False,
                'message': 'Este siniestro ya fue enviado anteriormente'
            }, status=400)
        
        # Marcar como enviado
        siniestro.enviado = True
        siniestro.fecha_actualizacion = timezone.now()
        siniestro.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Siniestro #{siniestro.id} enviado exitosamente a la aseguradora'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required(login_url='login')
@role_required(['asesor'])
def siniestros_module_eliminar(request, id):
    """Vista para eliminar un siniestro"""
    siniestro = get_object_or_404(Siniestro, id=id)
    
    # Eliminar archivo si existe
    if siniestro.documento:
        try:
            if os.path.isfile(siniestro.documento.path):
                os.remove(siniestro.documento.path)
        except Exception as e:
            print(f"Error al eliminar archivo: {e}")
    
    siniestro.delete()
    return redirect('siniestros_module_lista')



































pusher_client = pusher.Pusher(app_id=settings.PUSHER_APP_ID,key=settings.PUSHER_KEY,secret=settings.PUSHER_SECRET,cluster=settings.PUSHER_CLUSTER,ssl=True)



@login_required(login_url='/login')
@role_required(['asesor'])
@csrf_exempt
def pusher_auth(request):
    print("Llegó a pusher_auth!")
    if not request.user.is_authenticated:
        return HttpResponseForbidden()

    channel_name = request.POST.get('channel_name')
    socket_id = request.POST.get('socket_id')
    expected_channel = f"private-user-{request.user.id}"

    if channel_name != expected_channel:
        return HttpResponseForbidden("Canal no autorizado")
    
    auth = pusher_client.authenticate(channel=channel_name,socket_id=socket_id)
    return JsonResponse(auth)




@csrf_exempt
@login_required(login_url='/login')
@role_required(['asesor'])
def trigger_event(request, user_id):
    channel_name = f"private-user-{user_id}"
    pusher_client.trigger(channel_name, 'my-event', {'message': f'Hola, usuario {user_id}! Tienes una nueva notificación.'})
    return JsonResponse({'status': 'Evento enviado correctamente'})







@login_required(login_url='login')
@role_required(['asesor'])
def obtener_notificaciones_usuario(request, user_id):
    profile = Profile.objects.get(user=user_id)
    print(profile)
    mensajes = Notificaciones.objects.filter(not_codcli=profile).order_by('-not_fecha_creacion').values('not_id', 'not_poliza', 'not_fecha_proceso', 'not_estado', 'not_mensaje', 'not_fecha_creacion', 'not_read')
    print(mensajes)
    return JsonResponse(list(mensajes), safe=False)



@login_required(login_url='login')
@role_required(['asesor'])
def marcar_notificaciones_leidas(request, user_id):
    profile = Profile.objects.get(user=user_id)
    Notificaciones.objects.filter(not_codcli=profile, not_read=True).update(not_read=False)
    return JsonResponse({'status': 'ok'})
















from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from core.models import Siniestro, TcasDocumentos
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
@role_required(['asesor'])
def lista_siniestros(request):
    # Traer todos los siniestros sin filtros
    siniestros = Siniestro.objects.all().select_related('poliza').order_by('-fecha_reporte')
    context = {
        'siniestros': siniestros
    }
    return render(request, 'asesor/components/documentos/siniestros_lista.html', context)

@login_required(login_url='login')
@role_required(['asesor'])
def obtener_beneficiarios_por_siniestro(request, siniestro_id):
    siniestro = get_object_or_404(Siniestro, pk=siniestro_id)
    beneficiarios = siniestro.beneficiarios.all().values(
        'id_beneficiario', 'nombre', 'correo', 'telefono', 'numero_cuenta'
    )
    return JsonResponse(list(beneficiarios), safe=False)

@login_required(login_url='login')
@role_required(['asesor'])
def obtener_documentos_por_beneficiario(request, beneficiario_id):
    documentos = TcasDocumentos.objects.filter(beneficiario_id=beneficiario_id).values(
        "doc_cod_doc", "doc_descripcion", "doc_file", "doc_size", "fec_creacion", "fecha_edit", "estado"
    ).order_by('-fec_creacion')
    return JsonResponse(list(documentos), safe=False)
















@login_required(login_url='login')
@role_required(['asesor'])
def lista_reportes(request):
    """Vista principal para listar todos los reportes"""
    reportes = ReporteEvento.objects.all().order_by('-fecha_creacion')
    ultimo_reporte = reportes.first() if reportes.exists() else None
    
    # Estadísticas
    context = {
        'reportes': reportes,
        'ultimo_reporte': ultimo_reporte,
        'total_reportes': reportes.count(),
        'reportes_nuevos': reportes.filter(estado='nuevo').count(),
        'reportes_enviados': reportes.filter(estado='enviado').count(),
        'reportes_evaluados': reportes.filter(evaluado=True).count(),
    }
    
    return render(request, 'asesor/components/reportes/lista_reportes.html', context)








@login_required(login_url='login')
@role_required(['asesor'])
def detalle_reporte(request, id):
    reporte = get_object_or_404(ReporteEvento, id=id)
    
    archivo_url = None
    archivo_tipo = None
    archivo_nombre = None
    
    if reporte.archivo_documento:
        archivo_url = reporte.archivo_documento.url
        archivo_nombre = os.path.basename(reporte.archivo_documento.name)
        extension = os.path.splitext(archivo_nombre)[1].lower()
        
        if extension in ['.pdf']:
            archivo_tipo = 'pdf'
        elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            archivo_tipo = 'imagen'
        elif extension in ['.doc', '.docx']:
            archivo_tipo = 'word'
        elif extension in ['.xls', '.xlsx']:
            archivo_tipo = 'excel'
        else:
            archivo_tipo = 'otro'
    
    return JsonResponse({
        'id': reporte.id,
        'descripcion': reporte.descripcion,
        'beneficiario': reporte.nombre_beneficiario,
        'relacion': reporte.relacion_beneficiario,
        'telefono': reporte.telefono,
        'email': reporte.email,
        'estado': reporte.estado,
        'evaluado': reporte.evaluado,
        'fecha': reporte.fecha_creacion.strftime('%d/%m/%Y %I:%M %p'),
        'archivo_url': archivo_url,
        'archivo_tipo': archivo_tipo,
        'archivo_nombre': archivo_nombre,
    })




@login_required(login_url='login')
@role_required(['asesor'])
@require_POST
def cambiar_estado_reporte(request, id):
    reporte = get_object_or_404(ReporteEvento, id=id)
    nuevo_estado = request.POST.get('estado')
    
    if nuevo_estado in ['nuevo', 'enviado', 'descartado']:
        reporte.estado = nuevo_estado
        
        if nuevo_estado == 'enviado':
            reporte.evaluado = True
        
        reporte.save()
        
        return JsonResponse({
            'success': True,
            'estado': nuevo_estado,
            'evaluado': reporte.evaluado
        })
    
    return JsonResponse({'success': False, 'error': 'Estado no válido'})

@login_required(login_url='login')
@role_required(['asesor'])
def eliminar_reporte(request, id):
    """Vista para eliminar un reporte"""
    reporte = get_object_or_404(ReporteEvento, id=id)
    
    # Eliminar archivo físico si existe
    if reporte.archivo_documento:
        try:
            if os.path.isfile(reporte.archivo_documento.path):
                os.remove(reporte.archivo_documento.path)
        except Exception as e:
            print(f"Error al eliminar archivo: {e}")
    
    reporte.delete()
    return redirect('lista_reportes')