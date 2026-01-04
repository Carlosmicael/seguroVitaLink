from django.urls import path
from .views import DocumentoFacturacionListView, DocumentoFacturacionUploadView, DocumentoFacturacionDetailView

app_name = 'facturacion'

urlpatterns = [
    path('admin/documentos/', DocumentoFacturacionListView.as_view(), name='admin_lista_documentos'),
    path('admin/documentos/subir/', DocumentoFacturacionUploadView.as_view(), name='admin_subir_documento'),
    path('admin/documentos/<int:pk>/detalle/', DocumentoFacturacionDetailView.as_view(), name='admin_detalle_documento'),
]

