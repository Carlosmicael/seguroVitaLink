from django.urls import path
from .views import SiniestrosInicioView
from .views import DashboardAsesorView, exportar_siniestros_excel, SiniestroListView
from . import views


app_name = 'siniestros'

urlpatterns = [
    path('', SiniestrosInicioView.as_view(), name='inicio'),
    path('dashboard/', DashboardAsesorView.as_view(), name='dashboard_asesor'),

    #Ronal
    path('exportar-siniestros/', exportar_siniestros_excel, name='exportar_siniestros'),
    path('lista/', SiniestroListView.as_view(), name='siniestro_list'),
    path('reportar/', views.reportar_siniestro, name='reportar_siniestro'),

    path('detalle/<int:pk>/', views.SiniestroDetailView.as_view(), name='detalle_siniestro'),
    path('editar/<int:pk>/', views.SiniestroUpdateView.as_view(), name='editar_siniestro'),
    path('exportar/', views.exportar_siniestros_excel, name='exportar_siniestros'),
]
