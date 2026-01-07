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
from django.db.models import Sum, Count, Q
from django.utils import timezone
from siniestros.models import Siniestro
from django.utils import timezone
from siniestros.models import Factura

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

# SINIESTROS ATENDIDOS ---- #

def reporte_siniestros(request):
    # 1. Obtener año actual o el seleccionado
    anio_actual = timezone.now().year
    anio_seleccionado = request.GET.get('anio', anio_actual)

    # 2. Filtrar Siniestros por esa vigencia (Año)
    siniestros = Siniestro.objects.filter(fecha_reporte__year=anio_seleccionado)

    # 3. Calcular KPIs Generales (Tarjetas Superiores)
    # Total de casos en el año
    total_siniestros = siniestros.count()
    
    # Pendientes (estado 'pendiente')
    pendientes = siniestros.filter(estado='pendiente').count()
    
    # Monto Pagado: Suma de la cobertura de pólizas en siniestros con estado 'pagado'
    # (Usamos monto_cobertura como proxy del pago, ya que no hay campo 'monto_pagado' en Siniestro)
    monto_pagado = siniestros.filter(estado='pagado').aggregate(
        total=Sum('poliza__monto_cobertura')
    )['total'] or 0

    # 4. Desglose por Tipo (La "Separación" que pediste)
    # Agrupa por el campo 'tipo' (Accidente, Fallecimiento, Enfermedad, etc.)
    desglose_tipos = siniestros.values('tipo').annotate(
        cantidad=Count('id'),
        monto_total=Sum('poliza__monto_cobertura')
    ).order_by('-cantidad')

    # 5. Listado de años para el filtro
    anios_disponibles = Siniestro.objects.dates('fecha_reporte', 'year')

    context = {
        'anio_seleccionado': int(anio_seleccionado),
        'anios_disponibles': anios_disponibles,
        'total_siniestros': total_siniestros,
        'pendientes': pendientes,
        'monto_pagado': monto_pagado,
        'desglose_tipos': desglose_tipos,
        # Pasamos los siniestros individuales por si quieres mostrar la tabla detalle abajo
        'lista_siniestros': siniestros.select_related('poliza', 'poliza__usuario'),
    }
    return render(request, 'reportes/siniestros_atendidos.html', context)


# FACTURAS PENDIENTES ---- #

def reporte_facturas_pendientes(request):
    # 1. Obtener todas las facturas NO pagadas
    facturas = Factura.objects.filter(pagada=False).select_related('poliza', 'poliza__usuario')

    # 2. Lógica de Vencimiento y Totales
    hoy = timezone.now().date()
    total_pendiente = 0
    cantidad_vencidas = 0

    # Iteramos para calcular totales y marcar las vencidas
    # (Nota: En proyectos grandes esto se hace con annotations de DB, pero así es más claro para aprender)
    for f in facturas:
        total_pendiente += f.monto
        # Agregamos un atributo temporal al objeto para usarlo en el HTML
        f.esta_vencida = f.fecha_vencimiento < hoy
        if f.esta_vencida:
            cantidad_vencidas += 1

    # 3. Filtros opcionales (Mes/Año de emisión)
    mes = request.GET.get('mes')
    if mes:
        facturas = facturas.filter(fecha_emision__month=mes)

    context = {
        'facturas': facturas,
        'total_pendiente': total_pendiente,
        'cantidad_vencidas': cantidad_vencidas,
        'hoy': hoy, # Para comparar en el template si hace falta
    }
    return render(request, 'reportes/facturas_pendientes.html', context)