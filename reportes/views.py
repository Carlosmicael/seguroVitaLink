from django.shortcuts import render
from django.shortcuts import render
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from siniestros.models import Pago

# Create your views here.

# PAGOS ----#

def reporte_pagos(request):
    # 1. Obtener todos los pagos base optimizando la consulta
    pagos = Pago.objects.all().select_related('factura__poliza')

    # 2. Filtros de Fechas (Si vienen en la URL)
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if fecha_inicio and fecha_fin:
        pagos = pagos.filter(fecha_pago__range=[fecha_inicio, fecha_fin])

    # 3. Agrupación Táctica: Por Mes y Tipo de Estudiante
    reporte = pagos.annotate(
        mes=TruncMonth('fecha_pago')
    ).values(
        'mes', 
        'factura__poliza__tipo_estudiante'
    ).annotate(
        total_monto=Sum('monto'),
        total_pagos=Count('id')
    ).order_by('-mes')

    # Calcular totales generales para el marcador
    total_general = pagos.aggregate(Sum('monto'))['monto__sum'] or 0

    context = {
        'reporte': reporte,
        'total_general': total_general,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'reportes/pagos_realizados.html', context)