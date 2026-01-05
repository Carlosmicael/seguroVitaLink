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