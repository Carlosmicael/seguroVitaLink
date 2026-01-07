from django.urls import path
from . import views

urlpatterns = [
    path('aseguradoras/', views.lista_aseguradoras, name='lista_aseguradoras'),
    path('aseguradoras/nueva/', views.crear_aseguradora, name='crear_aseguradora'),
    path('aseguradoras/editar/<int:id>/', views.editar_aseguradora, name='editar_aseguradora'),
    path('aseguradoras/eliminar/<int:id>/', views.eliminar_aseguradora, name='eliminar_aseguradora'),
]