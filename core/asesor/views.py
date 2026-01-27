from django.shortcuts import render, redirect
from core.decorators import role_required
from core.models import Poliza, Estudiante, Profile, Notificaciones, ReporteEvento, Siniestro, ConfiguracionSiniestro,Factura,Pago,Beneficiario,DocumentosAseguradora

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from django.views.decorators.http import require_http_methods
from core.forms import PolizaForm, FacturaForm, PagoForm
from django.contrib.auth.decorators import login_required
from core.tasks import ejecutar_recordatorio
from django.utils.timezone import make_aware
from django.utils import timezone
import logging
from datetime import datetime
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
import pusher
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.dateformat import DateFormat
from django.views.decorators.http import require_POST
import os
from datetime import timedelta
from django.db.models import Count, Sum, F, Q
from django.db import transaction
from django.contrib import messages
from decimal import Decimal
from datetime import timedelta, date


logger = logging.getLogger(__name__)






MONTH_LABELS = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
]


def _shift_month(year, month, delta):
    total = year * 12 + (month - 1) + delta
    return total // 12, total % 12 + 1


def _month_sequence(count=6):
    today = timezone.now().date()
    months = []
    for offset in range(-count + 1, 1):
        year, month = _shift_month(today.year, today.month, offset)
        months.append((year, month))
    return months


def _month_label(year, month):
    return f"{MONTH_LABELS[month - 1]} {year}"


def _series_for(qs, date_field, months):
    start_year, start_month = months[0]
    end_year, end_month = _shift_month(months[-1][0], months[-1][1], 1)
    tz = timezone.get_current_timezone()
    start = timezone.datetime(start_year, start_month, 1, tzinfo=tz)
    end = timezone.datetime(end_year, end_month, 1, tzinfo=tz)

    month_map = {}
    date_values = qs.filter(**{f"{date_field}__gte": start, f"{date_field}__lt": end}).values_list(
        date_field, flat=True
    )
    for value in date_values:
        if value is None:
            continue
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        key = (value.year, value.month)
        month_map[key] = month_map.get(key, 0) + 1

    return [month_map.get((year, month), 0) for year, month in months]


def _current_month_range():
    now = timezone.now()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_year, end_month = _shift_month(start.year, start.month, 1)
    end = start.replace(year=end_year, month=end_month)
    return start, end


def _build_dashboard_metrics():
    polizas_activas = Poliza.objects.filter(estado='activa').count()
    siniestros_en_proceso = Siniestro.objects.filter(
        estado__in=['pendiente', 'aprobado']
    ).count()
    #Modficación de la lógica para facturas pendientes - Ronal
    #Hace que cuente las facturas que no han sido pagadas completamente
    facturas_pendientes = (
        Factura.objects.annotate(total_pagado=Sum('pagos__monto_pagado'))
        .filter(Q(total_pagado__lt=F('monto')) | Q(total_pagado__isnull=True))
        .count()
    )

    start, end = _current_month_range()
    start_date = start.date()
    end_date = end.date()
    total_pagado_mes = (
        Pago.objects.filter(
            fecha_pago__gte=start_date,
            fecha_pago__lt=end_date,
        )
        .aggregate(total=Sum('monto_pagado'))
        .get('total')
    )
    if total_pagado_mes is None:
        total_pagado_mes = Decimal('0.00')

    months = _month_sequence(6)
    labels = [_month_label(year, month) for year, month in months]
    polizas_series = _series_for(Poliza.objects.all(), "fecha_creacion", months)
    siniestros_series = _series_for(Siniestro.objects.all(), "fecha_reporte", months)

    return {
        "polizas_activas": polizas_activas,
        "siniestros_en_proceso": siniestros_en_proceso,
        "facturas_pendientes": facturas_pendientes,
        "total_pagado_mes": total_pagado_mes,
        "labels": labels,
        "polizas_series": polizas_series,
        "siniestros_series": siniestros_series,
    }


@login_required(login_url='login')
@role_required(['asesor'])
def asesor_dashboard(request):
    dashboard_data = _build_dashboard_metrics()
    return render(
        request,
        'asesor/components/dashboard/dashboard.html',
        {"dashboard_data": dashboard_data},
    )


@login_required(login_url='login')
@role_required(['asesor'])
def asesor_dashboard_metrics(request):
    return JsonResponse(_build_dashboard_metrics())








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
        
        data = request.POST
        
        if not all([data.get('poliza'), data.get('tipo'), data.get('descripcion'), data.get('fecha_evento')]):
            return JsonResponse({'success': False,'message': 'Faltan campos requeridos'}, status=400)
        
        try:
            poliza = Poliza.objects.get(id=int(data['poliza']))
        except:
            return JsonResponse({'success': False,'message': 'Póliza no válida'}, status=400)
        
        siniestro = Siniestro(
            poliza=poliza,
            tipo=data['tipo'],
            descripcion=data['descripcion'],
            fecha_evento=data['fecha_evento'],
            nombre_beneficiario=data.get('nombre_beneficiario', ''),
            relacion_beneficiario=data.get('relacion_beneficiario', ''),
            parentesco=data.get('parentesco', ''),
            telefono_contacto=data.get('telefono_contacto', ''),
            email_contacto=data.get('email_contacto', ''),
            estado='pendiente',
            enviado=False,
        )
        
        if 'documento' in request.FILES:
            siniestro.documento = request.FILES['documento']
        
        config = ConfiguracionSiniestro.objects.filter(activo=True).first()
        fecha_actual = timezone.now().date()
        
        if config:
            siniestro.fecha_limite_reporte = fecha_actual + timedelta(days=config.dias_max_reporte)
        else:
            siniestro.fecha_limite_reporte = fecha_actual + timedelta(days=3)
        

        siniestro.save()

        # ============================================
        # CREAR RECORDATORIOS
        # ============================================
        
        profile = Profile.objects.get(user=request.user)
        
        hora_actual = timezone.now().time()
        fecha_limite = siniestro.fecha_limite_reporte
        
        dias_recordatorios = [1, 2] 
        
        for dias_antes in dias_recordatorios:
            fecha_recordatorio = fecha_limite - timedelta(days=dias_antes)
            fecha_hora_recordatorio = timezone.make_aware(datetime.combine(fecha_recordatorio, hora_actual))
            mensaje = (
                f"Recordatorio: Reporte de siniestro #{siniestro.id} "
                f"({siniestro.get_tipo_display()}) vence el "
                f"{fecha_limite.strftime('%d/%m/%Y')}. "
                f"¡Falta{'n' if dias_antes > 1 else ''} {dias_antes} día{'s' if dias_antes > 1 else ''}!"
            )
            
            task = ejecutar_recordatorio.apply_async(eta=fecha_hora_recordatorio)
                
            recordatorio = Notificaciones.objects.create(
                not_codcli=profile,
                not_poliza=poliza,
                not_fecha_proceso=fecha_hora_recordatorio,
                not_fecha_creacion=timezone.now(),
                not_mensaje=mensaje,
                not_read=False,
                not_estado=False,
                not_celery_task_id=task.id,
            )

            recordatorio.save()

        return JsonResponse({
            'success': True,
            'message': f'Siniestro creado exitosamente. Se programaron recordatorios.',
            'siniestro_id': siniestro.id,
            'fecha_limite': siniestro.fecha_limite_reporte.strftime('%d/%m/%Y'),
            'recordatorios_creados': len(dias_recordatorios)
        })

        
        
            
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'success': False,'message': f'Error: {str(e)}'}, status=500)
















@login_required(login_url='login')
@role_required(['asesor'])
@require_http_methods(["POST"])
def siniestros_module_enviar(request, id):
    try:
        siniestro = get_object_or_404(Siniestro, id=id)
        
        if siniestro.enviado:
            return JsonResponse({'success': False,'message': 'Este siniestro ya fue enviado anteriormente'}, status=400)
        
        if siniestro.fecha_limite_reporte:
            dias_restantes = (siniestro.fecha_limite_reporte - timezone.now().date()).days
            
            if dias_restantes < 0:
                return JsonResponse({'success': False,'message': f'No se puede enviar el siniestro porque está vencido. La fecha límite era: {siniestro.fecha_limite_reporte.strftime("%d/%m/%Y")}'}, status=400)
            
            if dias_restantes <= 3:
                print(f"ADVERTENCIA: Siniestro #{id} se está enviando con solo {dias_restantes} días restantes")
        
        siniestro.enviado = True
        siniestro.fecha_actualizacion = timezone.now()
        siniestro.save()
        
        return JsonResponse({'success': True,'message': f'Siniestro #{siniestro.id} enviado exitosamente a la aseguradora'})
        
    except Exception as e:
        return JsonResponse({'success': False,'message': str(e)}, status=500)







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



















import random
import string
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.db import transaction
from core.models import Beneficiario, Siniestro, Profile
from core.forms import BeneficiarioForm
from core.tasks import enviar_recordatorio

def generar_username(nombre):
    base = nombre.lower().replace(' ', '')[:8]
    numeros = ''.join(random.choices(string.digits, k=4))
    fecha = datetime.now().strftime('%m%d')
    username = f"{base}{fecha}{numeros}"
    
    while User.objects.filter(username=username).exists():
        numeros = ''.join(random.choices(string.digits, k=6))
        username = f"{base}{numeros}"
    
    return username





def generar_password():
    caracteres = string.ascii_letters + string.digits + '@#$%&*'
    password = ''.join(random.choices(caracteres, k=12))
    return password

@login_required(login_url='login')
@role_required(['asesor'])
def beneficiarios_module_lista(request):
    beneficiarios = Beneficiario.objects.select_related('siniestro', 'siniestro__poliza','profile', 'profile__user').all()

    total = beneficiarios.count()
    activos = beneficiarios.filter(profile__isnull=False).count()
    pendientes = beneficiarios.filter(profile__isnull=True).count()
    siniestros_aprobados = Siniestro.objects.filter(estado='aprobado')
    
    form = BeneficiarioForm()
    
    context = {'beneficiarios': beneficiarios,'total': total,'activos': activos,'pendientes': pendientes,'siniestros_aprobados': siniestros_aprobados,'form': form}
    
    return render(request, 'asesor/components/beneficiarios/beneficiarios_module_lista.html', context)















@login_required(login_url='login')
@role_required(['asesor'])
def beneficiarios_module_detalle(request, id):

    beneficiario = get_object_or_404(Beneficiario, id_beneficiario=id)
    
    data = {
        'id': beneficiario.id_beneficiario,
        'nombre': beneficiario.nombre,
        'correo': beneficiario.correo,
        'numero_cuenta': beneficiario.numero_cuenta or 'N/A',
        'telefono': beneficiario.telefono or 'N/A',
        'fecha_creacion': beneficiario.fecha_creacion.strftime('%d/%m/%Y %I:%M %p'),
        'siniestro': {
            'id': beneficiario.siniestro.id,
            'tipo': beneficiario.siniestro.get_tipo_display(),
            'poliza': beneficiario.siniestro.poliza.numero_poliza if beneficiario.siniestro.poliza else 'N/A',
            'estado': beneficiario.siniestro.get_estado_display(),
        },
        'tiene_cuenta': beneficiario.profile is not None,
        'username': beneficiario.profile.user.username if beneficiario.profile else None,
    }
    
    return JsonResponse(data)






@login_required(login_url='login')
@role_required(['asesor'])
@require_http_methods(["POST"])
def beneficiarios_module_crear(request):

    try:
        form = BeneficiarioForm(request.POST)
        
        if form.is_valid():

            siniestro = form.cleaned_data['siniestro']
            
            if siniestro.estado != 'aprobado':
                return JsonResponse({'success': False,'message': f'El siniestro #{siniestro.id} no ha sido aprobado o esta caducado. Estado actual: {siniestro.get_estado_display()}'}, status=400)
            

            with transaction.atomic():

                username = generar_username(form.cleaned_data['nombre'])
                password = generar_password()
                
                user = User.objects.create_user(username=username,email=form.cleaned_data['correo'],password=password)
                
                profile = Profile.objects.create(user=user,rol='beneficiario')
                
                beneficiario = form.save(commit=False)
                beneficiario.profile = profile
                beneficiario.save()
                

                mensaje = f"""
                Bienvenido al sistema VitaLink.
                
                Se ha creado una cuenta para usted como beneficiario del siniestro #{siniestro.id}.
                
                Sus credenciales de acceso son:
                Usuario: {username}
                Contraseña: {password}
                
                Por favor, guarde estas credenciales en un lugar seguro y cámbielas al iniciar sesión por primera vez.
                
                Puede acceder al sistema en: {request.build_absolute_uri('/')}
                """
                
                fecha_actual = datetime.now().strftime('%d/%m/%Y')


                tipo_siniestro = siniestro.tipo 
                aseguradora_siniestro = siniestro.poliza.aseguradora if siniestro.poliza else None
                documentos_req = DocumentosAseguradora.objects.filter(siniestro_tipo=tipo_siniestro,activo=True,aseguradora=aseguradora_siniestro).order_by('dias_max_entrega')

                lista_fechas_limite = []
                fecha_hoy = date.today()

                for doc in documentos_req:
                    fecha_vencimiento = fecha_hoy + timedelta(days=doc.dias_max_entrega)
                    lista_fechas_limite.append(fecha_vencimiento.strftime('%Y-%m-%d'))

                beneficiario.fechas_limite = lista_fechas_limite
                beneficiario.save()


                print("aqui envia el mensaje al correo electronico")
                
                try:
                    enviar_recordatorio(user, mensaje, fecha_actual)
                except Exception as e:
                    print(f"Error al enviar correo: {e}")
                
                


            return JsonResponse({'success': True,'message': f'Beneficiario creado exitosamente. Se han enviado las credenciales a {form.cleaned_data["correo"]}','beneficiario_id': beneficiario.id_beneficiario})
        else:
            return JsonResponse({'success': False,'errors': form.errors}, status=400)
            
    except Exception as e:
        return JsonResponse({'success': False,'message': f'Error al crear el beneficiario: {str(e)}'}, status=500)













































pusher_client = pusher.Pusher(app_id=settings.PUSHER_APP_ID,key=settings.PUSHER_KEY,secret=settings.PUSHER_SECRET,cluster=settings.PUSHER_CLUSTER,ssl=True)



@login_required(login_url='/login')
@role_required(['asesor'])
@csrf_exempt
def pusher_auth(request):
    print("Llegó a pusher_auth asesorrrr!")
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
    siniestros = Siniestro.objects.all().select_related('poliza').order_by('-fecha_reporte')
    context = {'siniestros': siniestros}
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






## Gestión de Liquidaciones - RONAL ----


@login_required(login_url='/login')
@role_required(['asesor'])
def siniestros_pendientes_pago(request):
    siniestros = (
        Siniestro.objects.filter(estado='aprobado')
        .select_related('poliza')
        .prefetch_related('beneficiarios', 'beneficiarios__factura', 'beneficiarios__factura__pagos')
        .order_by('-fecha_reporte')
    )

    siniestros_data = []
    for siniestro in siniestros:
        beneficiarios = []
        for beneficiario in siniestro.beneficiarios.all():
            factura = getattr(beneficiario, 'factura', None)
            total_pagado = (
                factura.pagos.aggregate(total=Sum('monto_pagado')).get('total') or Decimal('0.00')
                if factura
                else Decimal('0.00')
            )
            restante = (factura.monto - total_pagado) if factura else None
            beneficiarios.append(
                {
                    'beneficiario': beneficiario,
                    'factura': factura,
                    'total_pagado': total_pagado,
                    'restante': restante,
                    'pagada': factura is not None and total_pagado >= factura.monto,
                }
            )

        if not beneficiarios:
            continue

        siniestros_data.append(
            {
                'siniestro': siniestro,
                'beneficiarios': beneficiarios,
            }
        )

    return render(
        request,
        'asesor/components/liquidaciones/siniestros_pendientes.html',
        {'siniestros_data': siniestros_data},
    )


def _siniestro_liquidado(siniestro):
    beneficiarios = list(siniestro.beneficiarios.all())
    if not beneficiarios:
        return False
    for beneficiario in beneficiarios:
        factura = getattr(beneficiario, 'factura', None)
        if factura is None:
            return False
        total_pagado = factura.pagos.aggregate(total=Sum('monto_pagado')).get('total') or Decimal('0.00')
        if total_pagado < factura.monto:
            return False
    return True


def registrar_liquidacion(request, beneficiario_id):
    beneficiario = get_object_or_404(Beneficiario, pk=beneficiario_id)
    siniestro = beneficiario.siniestro
    factura = getattr(beneficiario, 'factura', None)
    pagos = factura.pagos.order_by('-fecha_pago') if factura else Pago.objects.none()

    total_pagado = (
        factura.pagos.aggregate(total=Sum('monto_pagado')).get('total') or Decimal('0.00')
        if factura
        else Decimal('0.00')
    )
    restante = (factura.monto - total_pagado) if factura else None

    if request.method == 'POST':
        if factura is None:
            factura_form = FacturaForm(request.POST, prefix='factura')
            pago_form = PagoForm(prefix='pago')
            if factura_form.is_valid():
                nueva_factura = factura_form.save(commit=False)
                nueva_factura.siniestro = siniestro
                nueva_factura.beneficiario = beneficiario
                nueva_factura.save()
                messages.success(request, 'Factura registrada correctamente.')
                return redirect('registrar_liquidacion', beneficiario_id=beneficiario.id_beneficiario)
        else:
            pago_form = PagoForm(request.POST, prefix='pago')
            factura_form = FacturaForm(prefix='factura', instance=factura)
            # Modificación de la lógica para validar el pago
            if pago_form.is_valid():
                monto_pagado = pago_form.cleaned_data['monto_pagado']
                if restante is not None and restante <= Decimal('0.00'):
                    pago_form.add_error('monto_pagado', 'La factura ya esta completamente pagada.')
                elif restante is not None and monto_pagado > restante:
                    pago_form.add_error('monto_pagado', 'El monto supera el saldo pendiente.')
                else:
                    with transaction.atomic():
                        pago = pago_form.save(commit=False)
                        pago.factura = factura
                        pago.siniestro = siniestro
                        pago.save()

                        if _siniestro_liquidado(siniestro):
                            siniestro.estado = 'pagado'
                            siniestro.save(update_fields=['estado'])

                    messages.success(request, 'Pago registrado correctamente.')
                    return redirect('registrar_liquidacion', beneficiario_id=beneficiario.id_beneficiario)
    else:
        factura_form = FacturaForm(prefix='factura') if factura is None else FacturaForm(prefix='factura', instance=factura)
        pago_form = PagoForm(prefix='pago')

    return render(
        request,
        'asesor/components/liquidaciones/registrar_liquidacion.html',
        {
            'siniestro': siniestro,
            'beneficiario': beneficiario,
            'factura': factura,
            'pagos': pagos,
            'total_pagado': total_pagado,
            'restante': restante,
            'factura_form': factura_form,
            'pago_form': pago_form,
        },
    )


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _factura_estado(monto_factura, total_pagado):
    if total_pagado <= Decimal('0.00'):
        return 'pendiente'
    if total_pagado < monto_factura:
        return 'parcial'
    return 'pagada'


@login_required(login_url='/login')
@role_required(['asesor'])
def factura_detalle(request, factura_id):
    factura = get_object_or_404(Factura.objects.select_related('beneficiario', 'siniestro'), pk=factura_id)
    pagos = factura.pagos.order_by('-fecha_pago')
    total_pagado = pagos.aggregate(total=Sum('monto_pagado')).get('total') or Decimal('0.00')
    restante = factura.monto - total_pagado
    estado = _factura_estado(factura.monto, total_pagado)
    return render(
        request,
        'asesor/components/reportes/factura_detalle.html',
        {
            'factura': factura,
            'pagos': pagos,
            'total_pagado': total_pagado,
            'restante': restante,
            'estado': estado,
        },
    )







@login_required(login_url='/login')
@role_required(['asesor'])
def reportes_liquidacion(request):
    start_date = _parse_date(request.GET.get('fecha_inicio'))
    end_date = _parse_date(request.GET.get('fecha_fin'))
    beneficiario_id = request.GET.get('beneficiario') or ''
    estado_filtro = request.GET.get('estado') or ''
    export = request.GET.get('export')

    facturas_qs = Factura.objects.select_related('beneficiario', 'siniestro', 'siniestro__poliza').prefetch_related('pagos', 'siniestro__poliza__estudiantes').order_by('-fecha')
    
    if beneficiario_id:
        facturas_qs = facturas_qs.filter(beneficiario_id=beneficiario_id)

    facturas_filtradas = []
    for factura in facturas_qs:
        pagos_qs = factura.pagos.all()
        if start_date:
            pagos_qs = pagos_qs.filter(fecha_pago__gte=start_date)
        if end_date:
            pagos_qs = pagos_qs.filter(fecha_pago__lte=end_date)

        total_pagado_filtrado = pagos_qs.aggregate(total=Sum('monto_pagado')).get('total') or Decimal('0.00')
        total_pagado_total = factura.pagos.aggregate(total=Sum('monto_pagado')).get('total') or Decimal('0.00')
        estado = _factura_estado(factura.monto, total_pagado_total)

        if start_date or end_date:
            if total_pagado_filtrado == Decimal('0.00'):
                continue

        if estado_filtro and estado != estado_filtro:
            continue

        saldo_pendiente = factura.monto - total_pagado_total
        
        estudiante = None
        if factura.siniestro and factura.siniestro.poliza:
            estudiantes = factura.siniestro.poliza.estudiantes.all()
            estudiante = estudiantes.first() if estudiantes.exists() else None
        
        facturas_filtradas.append(
            {
                'factura': factura,
                'beneficiario': factura.beneficiario,
                'siniestro': factura.siniestro,
                'estudiante': estudiante,  
                'total_pagado': total_pagado_filtrado,
                'saldo_pendiente': saldo_pendiente,
                'estado': estado,
            }
        )

    total_facturado = sum((item['factura'].monto for item in facturas_filtradas), Decimal('0.00'))
    total_pagado = sum((item['total_pagado'] for item in facturas_filtradas), Decimal('0.00'))
    saldo_pendiente = total_facturado - total_pagado

    if export == 'xlsx':
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Liquidaciones"
        ws.append([
            "Siniestro",
            "Beneficiario",
            "Estudiante",
            "Carrera",
            "Nivel",
            "Factura",
            "Monto facturado",
            "Total pagado",
            "Saldo pendiente",
            "Estado",
        ])
        
        for item in facturas_filtradas:
            estudiante = item['estudiante']
            estudiante_nombre = f"{estudiante.nombres} {estudiante.apellidos}" if estudiante else "-"
            ws.append([
                item['siniestro'].id if item['siniestro'] else "",
                item['beneficiario'].nombre if item['beneficiario'] else "",
                estudiante_nombre,
                estudiante.carrera if estudiante else "",
                estudiante.nivel if estudiante else "",
                item['factura'].numero_factura,
                float(item['factura'].monto),
                float(item['total_pagado']),
                float(item['saldo_pendiente']),
                item['estado'],
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="reporte_liquidaciones.xlsx"'
        wb.save(response)
        return response

    siniestros_groups = {}
    for item in facturas_filtradas:
        siniestro_id = item['siniestro'].id if item['siniestro'] else None
        siniestros_groups.setdefault(siniestro_id, {'siniestro': item['siniestro'], 'items': []})
        siniestros_groups[siniestro_id]['items'].append(item)

    siniestros_ordenados = [siniestros_groups[key] for key in sorted(siniestros_groups.keys(), reverse=True)]

    beneficiarios = Factura.objects.values_list('beneficiario_id', 'beneficiario__nombre').distinct().order_by('beneficiario__nombre')

    return render(
        request,
        'asesor/components/reportes/liquidaciones_reportes.html',
        {
            'total_facturado': total_facturado,
            'total_pagado': total_pagado,
            'saldo_pendiente': saldo_pendiente,
            'siniestros_ordenados': siniestros_ordenados,
            'beneficiarios': beneficiarios,
            'filtros': {
                'fecha_inicio': start_date.isoformat() if start_date else '',
                'fecha_fin': end_date.isoformat() if end_date else '',
                'beneficiario': beneficiario_id,
                'estado': estado_filtro,
            },
        },
    )

























from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from core.decorators import role_required
from core.models import Beneficiario 
import json
import pusher
from django.conf import settings
from django.utils import timezone

# Cliente Pusher
pusher_client = pusher.Pusher(
    app_id=settings.PUSHER_APP_ID,
    key=settings.PUSHER_KEY,
    secret=settings.PUSHER_SECRET,
    cluster=settings.PUSHER_CLUSTER,
    ssl=True
)


@login_required(login_url='/login')
@role_required(['asesor'])
@csrf_exempt
def enviar_mensaje_asesor(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            beneficiario_id = data.get('beneficiario_id')
            print("Message:", message)
            print("Beneficiario ID:", beneficiario_id)
            
            if len(message) == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'El mensaje no puede estar vacío'
                }, status=400)
            
            if len(message) > 200:
                return JsonResponse({
                    'status': 'error',
                    'message': 'El mensaje no puede superar los 200 caracteres'
                }, status=400)
            
            if not beneficiario_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'ID de beneficiario requerido'
                }, status=400)

            try:
                beneficiario = Beneficiario.objects.get(id_beneficiario=beneficiario_id)
            except Beneficiario.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Beneficiario no encontrado'
                }, status=404)

            if not beneficiario.profile:
                return JsonResponse({
                    'status': 'error',
                    'message': 'El beneficiario no tiene perfil asociado'
                }, status=400)

            beneficiario_user = beneficiario.profile.user
            beneficiario_user_id = beneficiario_user.id


            print("Beneficiario User ID:", beneficiario_user_id)
            channel_name = f"private-user-{beneficiario_user_id}"

            print("Channel Name:", channel_name)
            
            pusher_client.trigger(channel_name, 'chat-message', {'message': message,'timestamp': str(timezone.now())})
            
            return JsonResponse({
                'status': 'success',
                'message': 'Mensaje enviado correctamente'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Formato de datos inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error al enviar mensaje: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)





    # En core/asesor/views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from core.decorators import role_required
from core.models import Beneficiario

@login_required
@role_required(['asesor'])
def get_beneficiarios_para_chat(request):
    """Obtener beneficiarios para mostrar en el chat del asesor"""
    try:
        # Obtener todos los beneficiarios
        beneficiarios = Beneficiario.objects.all()
        
        beneficiarios_list = []
        for benef in beneficiarios:
            beneficiarios_list.append({
                'id': benef.id_beneficiario,  # ID del beneficiario
                'nombre': benef.nombre,
                'email': benef.correo,
                'telefono': benef.telefono or '',
                'tiene_perfil': benef.profile is not None
            })
        
        return JsonResponse({
            'status': 'success',
            'beneficiarios': beneficiarios_list,
            'count': len(beneficiarios_list)
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error al obtener beneficiarios: {str(e)}'
        }, status=500)