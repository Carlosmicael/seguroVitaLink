from django.urls import path
from . import views

urlpatterns = [
    path('pagos/', views.reporte_pagos, name='reporte_pagos'),
    path('estudiantes/', views.reporte_estudiantes, name='reporte_estudiantes'),
    path('estudiantes/exportar/', views.exportar_estudiantes_csv, name='exportar_estudiantes'),
    path('siniestros/', views.reporte_siniestros, name='reporte_siniestros'),
]