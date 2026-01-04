from django.urls import path
from .views import (
    SiniestrosInicioView, 
    FormularioActivacionView, 
    BeneficiarioLoginView,
    AdminSolicitudesListView,
    AdminSolicitudDetailView,
    AdminGestionSolicitudView
)

app_name = 'siniestros'

urlpatterns = [
    path('', SiniestrosInicioView.as_view(), name='inicio'),
    path('formulario/', FormularioActivacionView.as_view(), name='formulario'),
    path('login-beneficiario/', BeneficiarioLoginView.as_view(), name='login_beneficiario'),
    # URLs para administrador
    path('admin/solicitudes/', AdminSolicitudesListView.as_view(), name='admin_lista_solicitudes'),
    path('admin/solicitud/<int:pk>/', AdminSolicitudDetailView.as_view(), name='admin_detalle_solicitud'),
    path('admin/solicitud/<int:pk>/gestionar/', AdminGestionSolicitudView.as_view(), name='admin_gestionar_solicitud'),
]
