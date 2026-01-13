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
]
