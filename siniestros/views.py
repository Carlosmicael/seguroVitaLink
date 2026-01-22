from django.shortcuts import render
from django.views.generic import TemplateView


class SiniestrosInicioView(TemplateView):
    """Vista para la página de inicio de gestión de siniestros"""
    template_name = 'siniestros/siniestro_report.html' #activacion request reception page
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Gestión de Siniestros - VitaLink'
        return context
