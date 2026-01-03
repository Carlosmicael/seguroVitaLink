from django.shortcuts import render, redirect
from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from siniestros.forms import ActivacionPolizaForm
from siniestros.models import Siniestro, Poliza


class SiniestrosInicioView(TemplateView):
    """Vista para la página de inicio de gestión de siniestros"""
    template_name = 'siniestros/siniestro_report.html' #activacion request reception page
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Gestión de Siniestros - VitaLink'
        return context


class FormularioActivacionView(FormView):
    """Vista para el formulario de activación de póliza y reporte de evento"""
    template_name = 'siniestros/formulario_activacion.html'
    form_class = ActivacionPolizaForm
    success_url = reverse_lazy('siniestros:inicio')
    
    def form_valid(self, form):
        """Procesar el formulario válido"""
        # Obtener datos del formulario
        tipo_evento = form.cleaned_data['tipo_evento']
        descripcion = form.cleaned_data['descripcion']
        nombre_beneficiario = form.cleaned_data['nombre_beneficiario']
        relacion_beneficiario = form.cleaned_data['relacion_beneficiario']
        telefono = form.cleaned_data['telefono']
        email = form.cleaned_data['email']
        archivo = form.cleaned_data.get('archivo_documento')
        
        # Crear registro del siniestro sin requerir póliza
        # El equipo de UTPL buscará la póliza del estudiante
        try:
            # Por ahora, creamos el siniestro con una póliza dummy o null
            # El equipo administrativo verificará los datos
            siniestro = Siniestro(
                poliza_id=1,  # Será actualizada por el equipo administrativo
                tipo=tipo_evento,
                descripcion=descripcion,
                nombre_beneficiario=nombre_beneficiario,
                relacion_beneficiario=relacion_beneficiario,
                telefono_contacto=telefono,
                email_contacto=email,
                documento=archivo if archivo else None,
                estado='pendiente'
            )
            siniestro.save()
            
            messages.success(
                self.request, 
                f'✓ Reporte #{siniestro.id} registrado exitosamente. El equipo de UTPL se contactará con los beneficiarios utilizando los datos proporcionados.'
            )
        except Poliza.DoesNotExist:
            messages.error(self.request, 'Error al procesar el reporte. Por favor, intenta de nuevo.')
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'Error al procesar el siniestro: {str(e)}')
            return self.form_invalid(form)
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Procesar formulario inválido"""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)
