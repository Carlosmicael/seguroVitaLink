from core.decorators import role_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta, datetime
from core.models import (Poliza, Estudiante, Aseguradora, Siniestro, DocumentosAseguradora, ConfiguracionSiniestro, ReglasPoliza, Notificaciones, Profile)
from django.views.decorators.http import require_http_methods
from datetime import date, datetime, timedelta
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
import pusher
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json
from core.tasks import ejecutar_recordatorio
from django.utils.timezone import make_aware
from django.utils import timezone


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from core.decorators import role_required
from core.models import Aseguradora, PoliticaAseguradora
from core.forms import AseguradoraForm, PoliticaAseguradoraForm


@login_required(login_url='login')
@role_required(['administrador'])
def administrador_dashboard(request):
    context = {
        'total_polizas': Poliza.objects.count(),
        'polizas_activas': Poliza.objects.filter(estado='activa').count(),
        'total_siniestros': Siniestro.objects.count(),
        'siniestros_pendientes': Siniestro.objects.filter(estado='pendiente').count(),
        'total_estudiantes': Estudiante.objects.filter(estado='activo').count(),
    }
    return render(request, 'administrador/components/dashboard/dashboard.html', context)






# ==================== PÓLIZAS ====================
@login_required(login_url='login')
@role_required(['administrador'])
def lista_polizas(request):
    """Lista todas las pólizas con filtros"""
    polizas = Poliza.objects.prefetch_related('estudiantes').select_related('aseguradora', 'regla_poliza').all()
    estudiantes = Estudiante.objects.filter(estado='activo')
    aseguradoras = Aseguradora.objects.all()
    reglas_polizas = ReglasPoliza.objects.filter(activo=True).select_related('aseguradora')
    
    # Estadísticas
    total = polizas.count()
    activas = polizas.filter(estado='activa').count()
    pendientes = polizas.filter(estado='pendiente').count()
    vencidas = polizas.filter(estado='vencida').count()
    
    # Calcular días para vencimiento de cada póliza
    dias_vencimiento = {}
    for poliza in polizas:
        if poliza.fecha_vencimiento:
            hoy = timezone.localdate()  
            fecha_venc = poliza.fecha_vencimiento.date()
            dias_vencimiento[poliza.numero_poliza] = (fecha_venc - hoy).days
        else:
            dias_vencimiento[poliza.numero_poliza] = 0


    print("dias_vencimiento", dias_vencimiento)
    context = {
        'polizas': polizas,
        'estudiantes': estudiantes,
        'aseguradoras': aseguradoras,
        'reglas_polizas': reglas_polizas,
        'total': total,
        'activas': activas,
        'pendientes': pendientes,
        'vencidas': vencidas,
        'dias_vencimiento': json.dumps(dias_vencimiento),
    }
    return render(request, 'administrador/components/polizas/lista_polizas.html', context)



def aseguradoras_list(request):
    aseguradoras = Aseguradora.objects.all().order_by('-fecha_creacion')
    return render(
        request,
        'administrador/components/aseguradoras/lista_aseguradoras.html',
        {'aseguradoras': aseguradoras},
    )


@login_required(login_url='login')
@role_required(['administrador'])
@require_http_methods(["POST"])
def crear_poliza(request):
    try:
        estudiantes_ids = request.POST.getlist('estudiantes') 
        numero_poliza = request.POST.get('numero_poliza')
        estado = request.POST.get('estado')
        tipo_cobertura = request.POST.get('tipo_cobertura')
        fecha_inicio = request.POST.get('fecha_inicio')
        prima_neta = request.POST.get('prima_neta')
        aseguradora_id = request.POST.get('aseguradora')
        regla_poliza_id = request.POST.get('regla_poliza')
        
        if not all([estudiantes_ids, numero_poliza, estado, tipo_cobertura, fecha_inicio, prima_neta, regla_poliza_id]):
            return JsonResponse({'success': False,'message': 'Todos los campos obligatorios deben ser completados'}, status=400)
        
        # Obtener regla de póliza
        regla_poliza = get_object_or_404(ReglasPoliza, pk=regla_poliza_id, activo=True)
        




        # VALIDACIÓN 1: Número de estudiantes
        num_estudiantes = len(estudiantes_ids)
        if regla_poliza.max_estudiantes and num_estudiantes > regla_poliza.max_estudiantes:
            return JsonResponse({
                'success': False,
                'message': f'Ha excedido el número máximo de estudiantes permitidos ({regla_poliza.max_estudiantes}). Seleccionó {num_estudiantes} estudiantes.'
            }, status=400)
        
        # VALIDACIÓN 2: Prima neta dentro de rango
        prima_neta_decimal = float(prima_neta)
        if prima_neta_decimal < float(regla_poliza.monto_minimo):
            return JsonResponse({
                'success': False,
                'message': f'La prima neta no puede ser menor a ${regla_poliza.monto_minimo}. Según la regla seleccionada.'
            }, status=400)
        
        if regla_poliza.monto_maximo and prima_neta_decimal > float(regla_poliza.monto_maximo):
            return JsonResponse({
                'success': False,
                'message': f'La prima neta no puede ser mayor a ${regla_poliza.monto_maximo}. Según la regla seleccionada.'
            }, status=400)
        
        aseguradora = None
        if aseguradora_id:
            aseguradora = get_object_or_404(Aseguradora, pk=aseguradora_id)
        
        if isinstance(fecha_inicio, str):
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        
        fecha_fin, fecha_vencimiento = regla_poliza.calcular_fecha_vencimiento(fecha_inicio)


        poliza = Poliza.objects.create(
            aseguradora=aseguradora,
            regla_poliza=regla_poliza,
            numero_poliza=numero_poliza,
            numero=numero_poliza,
            estado=estado,
            tipo_cobertura=tipo_cobertura,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            fecha_vencimiento=fecha_vencimiento,
            prima_neta=prima_neta_decimal
        )
        
        estudiantes = Estudiante.objects.filter(id__in=estudiantes_ids)
        poliza.estudiantes.set(estudiantes)

        print("Fecha fin:",poliza.fecha_fin.strftime("%d/%m/%Y %I:%M %p"))


        fecha_hora_naive = datetime.fromisoformat(fecha_fin.isoformat())
        fecha_hora_aware = timezone.make_aware(fecha_hora_naive)
        print(f"Programando tarea para: {fecha_hora_aware}")
        task = ejecutar_recordatorio.apply_async(eta=fecha_hora_aware)
        profile = Profile.objects.get(user=request.user)

        recordatorio = Notificaciones.objects.create(
            not_codcli=profile,
            not_poliza=poliza,  
            not_fecha_proceso=fecha_hora_aware, 
            not_fecha_creacion=timezone.now(),
            not_mensaje=f"Recordatorio de vencimiento de póliza para {poliza.numero_poliza} su estado actual es {poliza.estado}",
            not_read=False,
            not_estado=False,
            not_celery_task_id=task.id,
        )

        recordatorio.save()
        
        return JsonResponse({'success': True,'message': 'Póliza creada exitosamente','poliza_id': poliza.id})
        
    except ReglasPoliza.DoesNotExist:
        return JsonResponse({'success': False,'message': 'La regla de póliza seleccionada no existe o no está activa'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False,'message': f'Error al crear póliza: {str(e)}'}, status=500)





















pusher_client = pusher.Pusher(app_id=settings.PUSHER_APP_ID,key=settings.PUSHER_KEY,secret=settings.PUSHER_SECRET,cluster=settings.PUSHER_CLUSTER,ssl=True)



@login_required(login_url='/login')
@role_required(['administrador'])
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
@role_required(['administrador'])
def trigger_event(request, user_id):
    channel_name = f"private-user-{user_id}"
    pusher_client.trigger(channel_name, 'my-event', {'message': f'Hola, usuario {user_id}! Tienes una nueva notificación.'})
    return JsonResponse({'status': 'Evento enviado correctamente'})





@login_required(login_url='login')
@role_required(['administrador'])
def obtener_notificaciones_usuario(request, user_id):
    profile = Profile.objects.get(user=user_id)
    mensajes = Notificaciones.objects.filter(not_codcli=profile).order_by('-not_fecha_creacion').values('not_id', 'not_poliza', 'not_fecha_proceso', 'not_estado', 'not_mensaje', 'not_fecha_creacion', 'not_read')
    return JsonResponse(list(mensajes), safe=False)



@login_required(login_url='login')
@role_required(['administrador'])
def marcar_notificaciones_leidas(request, user_id):
    profile = Profile.objects.get(user=user_id)
    Notificaciones.objects.filter(not_codcli=profile, not_read=True).update(not_read=False)
    return JsonResponse({'status': 'ok'})



















@login_required(login_url='login')
@role_required(['administrador'])
def generar_numero_poliza(request):
    numero = Poliza.generar_numero_poliza()
    return JsonResponse({'numero_poliza': numero})




@login_required(login_url='login')
@role_required(['administrador'])
def obtener_regla_poliza(request, id_regla):
    
    try:
        regla = get_object_or_404(ReglasPoliza, pk=id_regla, activo=True)
        
        data = {
            'success': True,
            'regla': {
                'id': regla.id_regla,
                'nombre': regla.nombre_regla,
                'descripcion': regla.descripcion,
                'dias_vigencia': regla.dias_vigencia,
                'horas_vigencia': regla.horas_vigencia,
                'minutos_vigencia': regla.minutos_vigencia,
                'dias_gracia': regla.dias_gracia,
                'horas_gracia': regla.horas_gracia,
                'minutos_gracia': regla.minutos_gracia,
                'max_estudiantes': regla.max_estudiantes,
                'monto_minimo': float(regla.monto_minimo),
                'monto_maximo': float(regla.monto_maximo) if regla.monto_maximo else None,
            }
        }
        
        return JsonResponse(data)
    except ReglasPoliza.DoesNotExist:
        return JsonResponse({'success': False,'message': 'Regla de póliza no encontrada'}, status=404)







@login_required(login_url='login')
@role_required(['administrador'])
def detalle_poliza(request, numero_poliza):
    try:
        poliza = get_object_or_404(Poliza.objects.prefetch_related('estudiantes'), numero_poliza=numero_poliza)
        
        estudiantes_lista = []
        for est in poliza.estudiantes.all():
            estudiantes_lista.append({
                'id': est.id,
                'nombre': f"{est.nombres} {est.apellidos}",
                'email': est.email,
                'cedula': est.cedula
            })
        
        data = {
            'success': True,
            'poliza': {
                'id': poliza.id,
                'numero_poliza': poliza.numero_poliza,
                'estudiantes': estudiantes_lista,
                'estado': poliza.estado,
                'tipo_cobertura': poliza.get_tipo_cobertura_display(),
                'prima_neta': float(poliza.prima_neta),
                'duracion': poliza.duracion_meses,
                'fecha_inicio': poliza.fecha_inicio.strftime('%Y-%m-%d'),
                'fecha_fin': poliza.fecha_fin.strftime('%Y-%m-%dT%H:%M'),
                'fecha_vencimiento': poliza.fecha_vencimiento.strftime('%Y-%m-%dT%H:%M') if poliza.fecha_vencimiento else None,
            }
        }        
        return JsonResponse({'success': True,'poliza': data['poliza']})
        
    except Poliza.DoesNotExist:
        return JsonResponse({'success': False,'message': 'Póliza no encontrada'}, status=404)






























# ==================== SINIESTROS ====================

@login_required(login_url='login')
@role_required(['administrador'])
def lista_siniestros(request):
    """Lista todos los siniestros"""
    siniestros = (Siniestro.objects.select_related('poliza').prefetch_related('poliza__estudiantes').all())
    
    # Estadísticas
    total = siniestros.count()
    pendientes = siniestros.filter(estado='pendiente').count()
    aprobados = siniestros.filter(estado='aprobado').count()
    rechazados = siniestros.filter(estado='rechazado').count()
    pagados = siniestros.filter(estado='pagado').count()
    
    # Obtener configuración actual
    config = ConfiguracionSiniestro.objects.filter(activo=True).first()
    
    context = {
        'siniestros': siniestros,
        'total': total,
        'pendientes': pendientes,
        'aprobados': aprobados,
        'rechazados': rechazados,
        'pagados': pagados,
        'config_actual': config,
    }
    return render(request, 'administrador/components/siniestros/lista_siniestros.html', context)





@login_required(login_url='login')
@role_required(['administrador'])
def configuracion_siniestros(request):
    """Vista de configuración de siniestros"""
    config = ConfiguracionSiniestro.objects.filter(activo=True).first()
    aseguradoras = Aseguradora.objects.all()
    tipos_siniestro = Siniestro.TIPO_CHOICES
    
    if not config:
        config = ConfiguracionSiniestro.objects.create(dias_max_reporte=3,dias_max_documentacion=7,activo=True)
    
    context = {'config': config,'aseguradoras': aseguradoras,'tipos_siniestro': tipos_siniestro}
    return render(request, 'administrador/components/siniestros/configuracion_siniestros.html', context)





@login_required(login_url='login')
@role_required(['administrador'])
def guardar_config_siniestro(request):
    """Guarda la configuración de siniestros"""
    if request.method == 'POST':
        try:
            dias_max_reporte = request.POST.get('dias_max_reporte')
            dias_max_documentacion = request.POST.get('dias_max_documentacion')
            aseguradora_id = request.POST.get('aseguradora')
            tipo_siniestro = request.POST.get('tipo_siniestro') or None
            
            if not dias_max_reporte:
                return JsonResponse({
                    'success': False,
                    'message': 'El campo de días máximos es obligatorio'
                }, status=400)
            
            # Desactivar configuraciones anteriores
            ConfiguracionSiniestro.objects.filter(activo=True).update(activo=False)
            
            # Crear nueva configuración
            aseguradora = None
            if aseguradora_id:
                aseguradora = get_object_or_404(Aseguradora, pk=aseguradora_id)
            
            config = ConfiguracionSiniestro.objects.create(
                aseguradora=aseguradora,
                dias_max_reporte=int(dias_max_reporte),
                dias_max_documentacion=int(dias_max_documentacion) if dias_max_documentacion else 7,
                activo=True,
                tipo_siniestro=tipo_siniestro
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Configuración guardada exitosamente',
                'config_id': config.id_config
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al guardar configuración: {str(e)}'
            }, status=500)
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)


















# ==================== DOCUMENTOS ====================

@login_required(login_url='login')
@role_required(['administrador'])
def lista_documentos(request):
    documentos = DocumentosAseguradora.objects.select_related('aseguradora').all()
    aseguradoras = Aseguradora.objects.all()
    
    total_documentos = documentos.count()
    obligatorios = documentos.filter(obligatorio=True).count()
    opcionales = documentos.filter(obligatorio=False).count()
    activos = documentos.filter(activo=True).count()
    
    context = {
        'documentos': documentos,
        'aseguradoras': aseguradoras,
        'total_documentos': total_documentos,
        'obligatorios': obligatorios,
        'opcionales': opcionales,
        'activos': activos,
    }
    
    return render(request, 'administrador/components/documentos/lista_documentos.html', context)













@login_required(login_url='login')
@role_required(['administrador'])
@require_http_methods(["POST"])
def crear_documento(request):

    try:
        aseguradora_id = request.POST.get('aseguradora')
        siniestro_tipo = request.POST.get('siniestro_tipo')
        nombre_documento = request.POST.get('nombre_documento')
        descripcion = request.POST.get('descripcion', '')
        obligatorio = request.POST.get('obligatorio') == 'on'
        dias_max_entrega = request.POST.get('dias_max_documentacion', 3)
        
        # Validaciones
        if not nombre_documento:
            return JsonResponse({'success': False,'message': 'El nombre del documento es obligatorio'}, status=400)
        
        if not aseguradora_id:
            return JsonResponse({'success': False,'message': 'Debe seleccionar una aseguradora'}, status=400)

        if not dias_max_entrega:
            return JsonResponse({'success': False,'message': 'El número de días es obligatorio'}, status=400)
        
        aseguradora = get_object_or_404(Aseguradora, id_aseguradora=aseguradora_id)
        
        documento = DocumentosAseguradora.objects.create(
            aseguradora=aseguradora,
            siniestro_tipo=siniestro_tipo if siniestro_tipo else None,
            nombre_documento=nombre_documento,
            descripcion=descripcion,
            obligatorio=obligatorio,
            dias_max_entrega=int(dias_max_entrega),
            activo=True
        )
        
        return JsonResponse({'success': True,'message': 'Documento creado exitosamente','documento_id': documento.id_doc_req})
        
    except Aseguradora.DoesNotExist:
        return JsonResponse({'success': False,'message': 'Aseguradora no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False,'message': f'Error al crear el documento: {str(e)}'}, status=500)
























def aseguradora_create(request):
    if request.method == 'POST':
        form = AseguradoraForm(request.POST)
        if form.is_valid():
            aseguradora = form.save(commit=False)
            if not aseguradora.is_active:
                aseguradora.fecha_inactivacion = timezone.now()
            aseguradora.save()
            messages.success(request, 'Aseguradora creada correctamente.')
            return redirect('aseguradoras_list')
    else:
        form = AseguradoraForm()

    return render(
        request,
        'administrador/components/aseguradoras/form_aseguradora.html',
        {'form': form, 'modo': 'crear'},
    )































@login_required(login_url='login')
@role_required(['administrador'])
def detalle_documento(request, id_doc):

    print("legoooo a detalle documento")
    try:
        documento = get_object_or_404(DocumentosAseguradora, id_doc_req=id_doc)
        
        data = {
            'success': True,
            'documento': {
                'id': documento.id_doc_req,
                'nombre': documento.nombre_documento,
                'descripcion': documento.descripcion or 'Sin descripción',
                'aseguradora': documento.aseguradora.nombre if documento.aseguradora else 'No asignada',
                'siniestro_tipo': documento.siniestro_tipo,
                'obligatorio': documento.obligatorio,
                'dias_max_entrega': documento.dias_max_entrega,
                'fecha_version': documento.fecha_version.strftime('%d/%m/%Y'),
                'activo': documento.activo,
                'dias_max_entrega': documento.dias_max_entrega

            }
        }
        print("documento encontrado")
        print(data)
        return JsonResponse(data)
        
    except DocumentosAseguradora.DoesNotExist:
        print("documento no encontrado")
        return JsonResponse({'success': False,'message': 'Documento no encontrado'}, status=404)






def aseguradora_edit(request, aseguradora_id):
    aseguradora = get_object_or_404(Aseguradora, pk=aseguradora_id)

    if request.method == 'POST':
        form = AseguradoraForm(request.POST, instance=aseguradora)
        if form.is_valid():
            aseguradora = form.save(commit=False)
            if aseguradora.is_active:
                aseguradora.fecha_inactivacion = None
            else:
                if aseguradora.fecha_inactivacion is None:
                    aseguradora.fecha_inactivacion = timezone.now()
            aseguradora.save()
            messages.success(request, 'Aseguradora actualizada correctamente.')
            return redirect('aseguradoras_list')
    else:
        form = AseguradoraForm(instance=aseguradora)

    return render(
        request,
        'administrador/components/aseguradoras/form_aseguradora.html',
        {'form': form, 'modo': 'editar', 'aseguradora': aseguradora},
    )


@login_required(login_url='login')
@role_required(['administrador'])
@require_http_methods(["POST"])
def eliminar_documento(request, id_doc):
    try:
        documento = get_object_or_404(DocumentosAseguradora, id_doc_req=id_doc)
        documento.delete()
        
        return JsonResponse({'success': True,'message': 'Documento eliminado exitosamente'})
        
    except DocumentosAseguradora.DoesNotExist:
        return JsonResponse({'success': False,'message': 'Documento no encontrado'}, status=404)





def aseguradora_toggle(request, aseguradora_id):
    aseguradora = get_object_or_404(Aseguradora, pk=aseguradora_id)
    aseguradora.is_active = not aseguradora.is_active
    aseguradora.fecha_inactivacion = None if aseguradora.is_active else timezone.now()
    aseguradora.save(update_fields=['is_active', 'fecha_inactivacion'])
    return redirect('aseguradoras_list')


@login_required(login_url='login')
@role_required(['administrador'])
def politicas_list(request, aseguradora_id):
    aseguradora = get_object_or_404(Aseguradora, pk=aseguradora_id)
    politicas = aseguradora.politicas_versiones.all()
    return render(
        request,
        'administrador/components/politicas/lista_politicas.html',
        {
            'aseguradora': aseguradora,
            'politicas': politicas,
        },
    )


@login_required(login_url='login')
@role_required(['administrador'])
def politica_create(request, aseguradora_id):
    aseguradora = get_object_or_404(Aseguradora, pk=aseguradora_id)
    if request.method == 'POST':
        form = PoliticaAseguradoraForm(request.POST, request.FILES)
        if form.is_valid():
            politica = form.save(commit=False)
            politica.aseguradora = aseguradora
            politica.save()
            messages.success(request, 'Politica registrada correctamente.')
            return redirect('politicas_list', aseguradora_id=aseguradora.id_aseguradora)
    else:
        form = PoliticaAseguradoraForm()

    return render(
        request,
        'administrador/components/politicas/form_politica.html',
        {'form': form, 'aseguradora': aseguradora, 'modo': 'crear'},
    )


@login_required(login_url='login')
@role_required(['administrador'])
def politica_edit(request, politica_id):
    politica = get_object_or_404(PoliticaAseguradora, pk=politica_id)
    if request.method == 'POST':
        form = PoliticaAseguradoraForm(request.POST, request.FILES, instance=politica)
        if form.is_valid():
            form.save()
            messages.success(request, 'Politica actualizada correctamente.')
            return redirect('politicas_list', aseguradora_id=politica.aseguradora.id_aseguradora)
    else:
        form = PoliticaAseguradoraForm(instance=politica)

    return render(
        request,
        'administrador/components/politicas/form_politica.html',
        {'form': form, 'aseguradora': politica.aseguradora, 'modo': 'editar'},
    )


@login_required(login_url='login')
@role_required(['administrador'])
def politicas_publicas_admin(request):
    aseguradoras = Aseguradora.objects.filter(is_active=True).order_by('nombre')
    return render(
        request,
        'administrador/components/publico/terminos_aseguradoras.html',
        {'aseguradoras': aseguradoras},
    )


@login_required(login_url='login')
@role_required(['administrador'])
def politica_publica_detalle_admin(request, aseguradora_id):
    aseguradora = get_object_or_404(Aseguradora, pk=aseguradora_id)
    politica = aseguradora.politicas_versiones.order_by('-fecha_version').first()
    return render(
        request,
        'administrador/components/publico/terminos_aseguradora_detalle.html',
        {'aseguradora': aseguradora, 'politica': politica},
    )


def politicas_publicas(request):
    aseguradoras = Aseguradora.objects.filter(is_active=True).order_by('nombre')
    return render(
        request,
        'public/terminos_aseguradoras.html',
        {'aseguradoras': aseguradoras},
    )


def politica_publica_detalle(request, aseguradora_id):
    aseguradora = get_object_or_404(Aseguradora, pk=aseguradora_id)
    politica = aseguradora.politicas_versiones.order_by('-fecha_version').first()
    return render(
        request,
        'public/terminos_aseguradora_detalle.html',
        {'aseguradora': aseguradora, 'politica': politica},
    )
