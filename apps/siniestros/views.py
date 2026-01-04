from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, FormView, ListView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from datetime import timedelta
from .forms import ActivacionPolizaForm, BeneficiarioLoginForm, GestionSolicitudForm
from .models import Siniestro, Poliza, Estudiante


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
        descripcion = form.cleaned_data['descripcion']
        nombre_beneficiario = form.cleaned_data['nombre_beneficiario']
        relacion_beneficiario = form.cleaned_data['relacion_beneficiario']
        telefono = form.cleaned_data['telefono']
        email = form.cleaned_data['email']
        archivo = form.cleaned_data.get('archivo_documento')
        
        # Crear registro del siniestro sin requerir póliza ni tipo
        # El equipo de UTPL buscará la póliza del estudiante y asignará el tipo
        try:
            # Necesitamos una póliza dummy para crear el siniestro
            # El administrador actualizará estos datos después
            # Crear estudiante dummy si no existe
            estudiante_dummy, _ = Estudiante.objects.get_or_create(
                codigo_estudiante='TEMP-PENDIENTE',
                defaults={
                    'cedula': '0000000000',
                    'nombres': 'Estudiante',
                    'apellidos': 'Pendiente',
                    'email': 'temp@utpl.edu.ec',
                    'carrera': 'Temporal',
                    'estado': 'activo'
                }
            )
            
            # Crear póliza dummy
            poliza_dummy, created = Poliza.objects.get_or_create(
                numero='TEMP-PENDIENTE',
                defaults={
                    'estudiante': estudiante_dummy,
                    'estado': 'inactiva'
                }
            )
            
            siniestro = Siniestro(
                poliza=poliza_dummy,  # Será actualizada por el equipo administrativo
                tipo=None,  # Será asignado por el administrador
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


class BeneficiarioLoginView(TemplateView):
    """Vista para el login de beneficiarios (solo página, sin autenticación por ahora)"""
    template_name = 'siniestros/login_beneficiario.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = BeneficiarioLoginForm()  # Solo para mostrar el formulario
        return context
    
    def post(self, request, *args, **kwargs):
        # Por ahora solo muestra mensaje informativo
        messages.info(request, 'La autenticación estará disponible próximamente.')
        return self.get(request, *args, **kwargs)


def is_staff_user(user):
    """Verificar si el usuario es staff"""
    return user.is_authenticated and user.is_staff


class AdminSolicitudesListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Vista para listar todas las solicitudes (siniestros) para el administrador"""
    model = Siniestro
    template_name = 'siniestros/admin_lista_solicitudes.html'
    context_object_name = 'solicitudes'
    paginate_by = 20
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def get_queryset(self):
        return Siniestro.objects.all().select_related('poliza', 'poliza__estudiante').order_by('-fecha_reporte')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ahora = timezone.now()
        
        # Calcular días restantes para cada solicitud
        solicitudes_con_plazo = []
        for solicitud in context['solicitudes']:
            fecha_vencimiento = solicitud.fecha_reporte + timedelta(days=4)
            dias_restantes = (fecha_vencimiento - ahora).days
            horas_restantes = (fecha_vencimiento - ahora).total_seconds() / 3600
            
            solicitudes_con_plazo.append({
                'solicitud': solicitud,
                'fecha_vencimiento': fecha_vencimiento,
                'dias_restantes': dias_restantes,
                'horas_restantes': horas_restantes,
                'vencido': dias_restantes < 0,
                'por_vencer': 0 <= dias_restantes <= 1
            })
        
        context['solicitudes_con_plazo'] = solicitudes_con_plazo
        return context


class AdminSolicitudDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Vista para ver el detalle de una solicitud"""
    model = Siniestro
    template_name = 'siniestros/admin_detalle_solicitud.html'
    context_object_name = 'solicitud'
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        solicitud = context['solicitud']
        ahora = timezone.now()
        fecha_vencimiento = solicitud.fecha_reporte + timedelta(days=4)
        dias_restantes = (fecha_vencimiento - ahora).days
        horas_restantes = (fecha_vencimiento - ahora).total_seconds() / 3600
        
        context['fecha_vencimiento'] = fecha_vencimiento
        context['dias_restantes'] = dias_restantes
        context['horas_restantes'] = horas_restantes
        context['vencido'] = dias_restantes < 0
        context['por_vencer'] = 0 <= dias_restantes <= 1
        context['form'] = GestionSolicitudForm(instance=solicitud)
        return context


class AdminGestionSolicitudView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Vista para gestionar una solicitud (asignar tipo, estudiante, etc.)"""
    model = Siniestro
    form_class = GestionSolicitudForm
    template_name = 'siniestros/admin_gestionar_solicitud.html'
    context_object_name = 'solicitud'
    
    def test_func(self):
        return is_staff_user(self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('siniestros:admin_detalle_solicitud', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Obtener el estudiante seleccionado
        estudiante = form.cleaned_data['estudiante']
        
        # Obtener o crear la póliza del estudiante (OneToOneField)
        poliza, created = Poliza.objects.get_or_create(
            estudiante=estudiante,
            defaults={
                'numero': f'POL-{estudiante.codigo_estudiante}-{estudiante.id}',
                'estado': 'activa'
            }
        )
        
        # Guardar primero los campos del ModelForm
        siniestro = form.save(commit=False)
        
        # Asignar la póliza al siniestro
        siniestro.poliza = poliza
        siniestro.revisado_por = self.request.user
        siniestro.save()
        
        messages.success(self.request, f'Solicitud #{siniestro.id} actualizada correctamente.')
        return redirect(self.get_success_url())
