from django.urls import path
from .views import SiniestrosInicioView, FormularioActivacionView

app_name = 'siniestros'

urlpatterns = [
    path('', SiniestrosInicioView.as_view(), name='inicio'),
    path('formulario/', FormularioActivacionView.as_view(), name='formulario'),
]
