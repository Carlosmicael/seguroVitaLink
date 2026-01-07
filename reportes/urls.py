from django.urls import path
from . import views

urlpatterns = [
    path('pagos/', views.reporte_pagos, name='reporte_pagos'),
]