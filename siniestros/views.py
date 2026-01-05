from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic import TemplateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.utils import timezone
from .models import Poliza, Siniestro, Factura, Pago


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
        
        # Obtener fecha actual para filtros de mes
        hoy = timezone.now()

        # 1. Total Pólizas Activas (Asumiendo que no tienen fecha de fin o es futura)
        context['total_polizas'] = Poliza.objects.filter(
            fecha_vencimiento__gte=hoy
        ).count()

        # 2. Siniestros en Proceso (Ajusta el estado según tus choices del modelo)
        context['siniestros_pendientes'] = Siniestro.objects.filter(
            estado__in=['PENDIENTE', 'EN_PROCESO'] 
        ).count()

        # 3. Facturas Pendientes de Pago
        context['facturas_pendientes'] = Factura.objects.filter(
            pagada=False
        ).count()

        # 4. Monto Total Pagado en el Mes Actual
        total_mes = Pago.objects.filter(
            fecha_pago__month=hoy.month,
            fecha_pago__year=hoy.year
        ).aggregate(Sum('monto'))['monto__sum']
        
        # Si no hay pagos, devuelve 0 en lugar de None
        context['dinero_mes'] = total_mes if total_mes else 0

        return context