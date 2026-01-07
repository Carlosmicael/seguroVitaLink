from django.shortcuts import render
from django.shortcuts import render
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from siniestros.models import Pago
import csv
from django.http import HttpResponse
from django.shortcuts import render
from django.db.models import Count
from siniestros.models import Poliza
import json

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


def reporte_estudiantes(request):
    # 1. Obtener datos base
    polizas = Poliza.objects.all()

    # 2. Filtros (Si se seleccionan en el HTML)
    modalidad = request.GET.get('modalidad')
    tipo = request.GET.get('tipo')

    if modalidad:
        polizas = polizas.filter(modalidad=modalidad)
    if tipo:
        polizas = polizas.filter(tipo_estudiante=tipo)

    # 3. Preparar datos para Gráficos (Agrupación)
    # Gráfico 1: Por Tipo de Estudiante (Pie Chart)
    por_tipo = polizas.values('tipo_estudiante').annotate(total=Count('id'))
    
    # Gráfico 2: Por Modalidad (Bar Chart)
    por_modalidad = polizas.values('modalidad').annotate(total=Count('id'))

    # Convertir a listas simples para pasarlas a JavaScript
    labels_tipo = [item['tipo_estudiante'] for item in por_tipo]
    data_tipo = [item['total'] for item in por_tipo]

    labels_mod = [item['modalidad'] for item in por_modalidad]
    data_mod = [item['total'] for item in por_modalidad]

    context = {
        'polizas': polizas, # Para mostrar la lista/tabla abajo si quieres
        'labels_tipo': json.dumps(labels_tipo),
        'data_tipo': json.dumps(data_tipo),
        'labels_mod': json.dumps(labels_mod),
        'data_mod': json.dumps(data_mod),
    }
    return render(request, 'reportes/estudiantes_asegurados.html', context)

def exportar_estudiantes_csv(request):
    # Configuración del archivo de respuesta
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="estudiantes_asegurados.csv"'

    writer = csv.writer(response)
    writer.writerow(['No. Póliza', 'Usuario', 'Tipo Estudiante', 'Modalidad', 'Estado', 'Monto Cobertura'])

    polizas = Poliza.objects.all().select_related('usuario')
    
    # Aplicar los mismos filtros si quisieras (opcional, aquí descarga todo por defecto)
    for p in polizas:
        writer.writerow([p.numero, p.usuario.username, p.tipo_estudiante, p.modalidad, p.estado, p.monto_cobertura])

    return response