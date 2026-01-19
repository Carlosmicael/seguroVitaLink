from django.shortcuts import render
from core.decorators import role_required
from core.models import Poliza, Estudiante, Profile, Notificaciones, Siniestro, Factura, Pago

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from core.forms import PolizaForm, FacturaForm, PagoForm
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
from django.db.models import Count, Sum
from django.db import transaction
from django.contrib import messages
from decimal import Decimal



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
    facturas_pendientes = (
        Siniestro.objects.filter(estado='aprobado', pagos__isnull=True).distinct().count()
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
def lista_polizas(request):
    polizas = Poliza.objects.all()
    estudiantes = Estudiante.objects.all() 
    total = polizas.count()
    pendientes = polizas.filter(estado='pendiente').count()
    activas = polizas.filter(estado='activa').count()
    vencidas = polizas.filter(estado='vencida').count()
    canceladas = polizas.filter(estado='cancelada').count()
    
    dias_vencimiento = {}
    for poliza in polizas:
        dias_vencimiento[poliza.numero_poliza] = poliza.dias_para_vencimiento()
    
    context = {
        'polizas': polizas,
        'total': total,
        'pendientes': pendientes,
        'activas': activas,
        'vencidas': vencidas,
        'canceladas': canceladas,
        'dias_vencimiento': dias_vencimiento,  
        'estudiantes': estudiantes,
    }
    return render(request, 'asesor/components/polizas/lista_polizas.html', context)






@login_required(login_url='login')
@role_required(['asesor'])
@require_http_methods(["POST"])
def crear_poliza(request):
    try:
        data = request.POST
        form = PolizaForm(data)
        fecha_hora_str = request.POST.get('fecha_fin')
        
        if form.is_valid() and fecha_hora_str:

            print("Formulario válido")
            print("Fecha hora str:", fecha_hora_str)


            poliza = form.save(commit=False)
            poliza.fecha_fin = fecha_hora_str
            poliza.save()

            fecha_hora_naive = datetime.fromisoformat(fecha_hora_str)
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
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False,'errors': form.errors}, status=400)
            
    except Exception as e:
        return JsonResponse({'success': False,'message': str(e)}, status=500)






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
def generar_numero_poliza(request):
    return JsonResponse({'numero_poliza': Poliza.generar_numero_poliza()})




@login_required(login_url='/login')
def obtener_notificaciones_usuario(request, user_id):
    profile = Profile.objects.get(user=user_id)
    mensajes = Notificaciones.objects.filter(not_codcli=profile).order_by('-not_fecha_creacion').values('not_id', 'not_poliza', 'not_fecha_proceso', 'not_estado', 'not_mensaje', 'not_fecha_creacion', 'not_read')
    return JsonResponse(list(mensajes), safe=False)



@login_required(login_url='/login')
def marcar_notificaciones_leidas(request, user_id):
    profile = Profile.objects.get(user=user_id)
    Notificaciones.objects.filter(not_codcli=profile, not_read=True).update(not_read=False)
    return JsonResponse({'status': 'ok'})








from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from core.models import Siniestro, TcasDocumentos
from django.contrib.auth.decorators import login_required

@login_required(login_url='/login')
def lista_siniestros(request):
    # Traer todos los siniestros sin filtros
    siniestros = Siniestro.objects.all().select_related('poliza').order_by('-fecha_reporte')
    context = {
        'siniestros': siniestros
    }
    return render(request, 'asesor/components/documentos/siniestros_lista.html', context)

@login_required(login_url='/login')
def obtener_beneficiarios_por_siniestro(request, siniestro_id):
    siniestro = get_object_or_404(Siniestro, pk=siniestro_id)
    beneficiarios = siniestro.beneficiarios.all().values(
        'id_beneficiario', 'nombre', 'correo', 'telefono', 'numero_cuenta'
    )
    return JsonResponse(list(beneficiarios), safe=False)

@login_required(login_url='/login')
def obtener_documentos_por_beneficiario(request, beneficiario_id):
    documentos = TcasDocumentos.objects.filter(beneficiario_id=beneficiario_id).values(
        "doc_cod_doc", "doc_descripcion", "doc_file", "doc_size", "fec_creacion", "fecha_edit", "estado"
    ).order_by('-fec_creacion')
    return JsonResponse(list(documentos), safe=False)

## Gestión de Liquidaciones - RONAL ----


@login_required(login_url='/login')
@role_required(['asesor'])
def siniestros_pendientes_pago(request):
    siniestros = (
        Siniestro.objects.filter(estado='aprobado', pagos__isnull=True)
        .select_related('poliza')
        .order_by('-fecha_reporte')
        .distinct()
    )
    return render(
        request,
        'asesor/components/liquidaciones/siniestros_pendientes.html',
        {'siniestros': siniestros},
    )


@login_required(login_url='/login')
@role_required(['asesor'])
def registrar_liquidacion(request, siniestro_id):
    siniestro = get_object_or_404(Siniestro, pk=siniestro_id)

    if siniestro.estado == 'pagado':
        messages.info(request, 'El siniestro ya fue liquidado.')
        return redirect('siniestros_pendientes_pago')

    if Factura.objects.filter(siniestro=siniestro).exists() or Pago.objects.filter(siniestro=siniestro).exists():
        messages.warning(request, 'Ya existe una liquidacion registrada para este siniestro.')
        return redirect('siniestros_pendientes_pago')

    if request.method == 'POST':
        factura_form = FacturaForm(request.POST, prefix='factura')
        pago_form = PagoForm(request.POST, prefix='pago')

        if factura_form.is_valid() and pago_form.is_valid():
            monto_factura = factura_form.cleaned_data['monto']
            monto_pagado = pago_form.cleaned_data['monto_pagado']

            if monto_factura != monto_pagado:
                pago_form.add_error(
                    'monto_pagado',
                    'El monto pagado debe coincidir con el monto facturado.',
                )
            else:
                with transaction.atomic():
                    factura = factura_form.save(commit=False)
                    factura.siniestro = siniestro
                    factura.save()

                    pago = pago_form.save(commit=False)
                    pago.siniestro = siniestro
                    pago.factura = factura
                    pago.save()

                    if siniestro.estado != 'pagado':
                        siniestro.estado = 'pagado'
                        siniestro.save(update_fields=['estado'])

                messages.success(request, 'Liquidacion registrada correctamente.')
                return redirect('siniestros_pendientes_pago')
    else:
        factura_form = FacturaForm(prefix='factura')
        pago_form = PagoForm(prefix='pago')

    return render(
        request,
        'asesor/components/liquidaciones/registrar_liquidacion.html',
        {
            'siniestro': siniestro,
            'factura_form': factura_form,
            'pago_form': pago_form,
        },
    )


@login_required(login_url='/login')
@role_required(['asesor'])
def reportes_liquidacion(request):
    total_facturado = Factura.objects.aggregate(total=Sum('monto')).get('total') or Decimal('0.00')
    total_pagado = Pago.objects.aggregate(total=Sum('monto_pagado')).get('total') or Decimal('0.00')

    siniestros_liquidados = (
        Siniestro.objects.filter(estado='pagado')
        .select_related('poliza', 'factura')
        .prefetch_related('pagos')
        .order_by('-fecha_actualizacion')
    )

    liquidaciones = []
    for siniestro in siniestros_liquidados:
        factura = getattr(siniestro, 'factura', None)
        pago = siniestro.pagos.order_by('-fecha_pago').first()
        liquidaciones.append(
            {
                'siniestro': siniestro,
                'factura': factura,
                'pago': pago,
            }
        )

    return render(
        request,
        'asesor/components/reportes/liquidaciones_reportes.html',
        {
            'total_facturado': total_facturado,
            'total_pagado': total_pagado,
            'liquidaciones': liquidaciones,
        },
    )
