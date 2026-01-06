from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic import TemplateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.utils import timezone
from .models import Poliza, Siniestro, Factura, Pago
from django.db.models.functions import TruncMonth
from django.views.generic import TemplateView
import json
import openpyxl 
from django.http import HttpResponse


class SiniestrosInicioView(TemplateView):
    """Vista para la página de inicio de gestión de siniestros"""
    template_name = 'siniestros/siniestro_report.html' #activacion request reception page
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Gestión de Siniestros - VitaLink'
        return context

class DashboardAsesorView(LoginRequiredMixin, TemplateView):
    template_name = "siniestros/dashboard_asesor.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = timezone.now()
        
        context['total_polizas'] = Poliza.objects.filter(fecha_vencimiento__gte=hoy).count()
        context['siniestros_pendientes'] = Siniestro.objects.exclude(estado='CERRADO').count()
        context['facturas_pendientes'] = Factura.objects.filter(pagada=False).count()
        
        total_mes = Pago.objects.filter(fecha_pago__month=hoy.month, fecha_pago__year=hoy.year).aggregate(Sum('monto'))['monto__sum']
        context['dinero_mes'] = total_mes if total_mes else 0
        
        # 1. Agrupar pagos por mes
        pagos_historicos = Pago.objects.annotate(
            mes=TruncMonth('fecha_pago')
        ).values('mes').annotate(
            total=Sum('monto')
        ).order_by('mes')

        # 2. Crear listas puras de Python
        labels = []
        data = []

        for p in pagos_historicos:
            # Fechas a string
            labels.append(p['mes'].strftime("%b %Y"))
            
            # Montos: Validamos que no sea None y convertimos a float (JSON no entiende Decimal)
            monto = p['total'] if p['total'] else 0
            data.append(float(monto))

        # 3. SERIALIZAR A JSON
        # Convertimos las listas a Strings de texto formato JSON: '["Ene", "Feb"]'
        context['labels_grafico'] = json.dumps(labels) 
        context['data_grafico'] = json.dumps(data)
        
        return context
    
    
    # Exportar siniestros pendientes a Excel -------- #
    
def exportar_siniestros_excel(request):
    # 1. Crear el libro de Excel y la hoja
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Siniestros Pendientes"

    # 2. Escribir los Encabezados (La primera fila)
    headers = ["ID", "Póliza", "Descripción", "Fecha Siniestro", "Estado", "Monto Estimado"]
    ws.append(headers)

    # 3. Consultar los datos (Siniestros NO cerrados)
    siniestros = Siniestro.objects.exclude(estado='CERRADO')

    # 4. Escribir los datos fila por fila
    for s in siniestros:
        # Nota: Asegúrate de que fecha_siniestro no sea None para evitar error
        fecha = s.fecha_siniestro.strftime("%d/%m/%Y") if s.fecha_siniestro else "Sin fecha"
        
        ws.append([
            s.id,
            str(s.poliza),      # Convertimos a texto por si acaso
            s.descripcion,
            fecha,
            s.estado,
            s.monto_estimado
        ])

    # 5. Preparar la respuesta HTTP para descarga
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Reporte_Siniestros.xlsx"'

    # 6. Guardar el libro en la respuesta
    wb.save(response)
    return response