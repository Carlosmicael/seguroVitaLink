from django.urls import path
from .views import SiniestrosInicioView

app_name = 'siniestros'

urlpatterns = [
    path('', SiniestrosInicioView.as_view(), name='inicio'),
]
