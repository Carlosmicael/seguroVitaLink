from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect

from .models import DocumentoFacturacion
from .forms import DocumentoFacturacionForm

# Helper para verificar si el usuario es staff
def is_staff_user(user):
    return user.is_staff

class DocumentoFacturacionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = DocumentoFacturacion
    template_name = 'facturacion/admin_lista_documentos.html'
    context_object_name = 'documentos'
    paginate_by = 10

    def test_func(self):
        return is_staff_user(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para acceder a esta página.")
        return redirect(reverse_lazy('admin:index')) # Redirige al admin de Django si no tiene permiso

class DocumentoFacturacionUploadView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = DocumentoFacturacion
    form_class = DocumentoFacturacionForm
    template_name = 'facturacion/admin_subir_documento.html'
    success_url = reverse_lazy('facturacion:admin_lista_documentos')

    def test_func(self):
        return is_staff_user(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para acceder a esta página.")
        return redirect(reverse_lazy('admin:index'))

    def form_valid(self, form):
        form.instance.subido_por = self.request.user
        messages.success(self.request, "Documento de facturación subido exitosamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Ha ocurrido un error al subir el documento.")
        return super().form_invalid(form)

class DocumentoFacturacionDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = DocumentoFacturacion
    template_name = 'facturacion/admin_detalle_documento.html'
    context_object_name = 'documento'

    def test_func(self):
        return is_staff_user(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para acceder a esta página.")
        return redirect(reverse_lazy('admin:index'))
