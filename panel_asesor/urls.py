from django.urls import path
from .views import registrar_beneficiario, registrar_estudiante, listar_estudiantes, buscar_estudiantes, inicio_asesor, cambiar_estado_estudiante, editar_estudiante , eliminar_estudiante, editar_beneficiario, eliminar_beneficiario
from . import views
app_name = 'panel_asesor'

urlpatterns = [
    path('', inicio_asesor, name='inicio'),  # <--- quita "views."
    path('registrar/', registrar_beneficiario, name='registrar'),
    # urls.py
path('beneficiario/editar/<int:beneficiario_id>/', views.editar_beneficiario, name='editar'),
path('beneficiario/eliminar/<int:beneficiario_id>/', views.eliminar_beneficiario, name='eliminar'),



    path('registrar/estudiante/', registrar_estudiante, name='registrar_estudiante'),
    path('estudiantes/', listar_estudiantes, name='listar_estudiantes'),
    path('estudiantes/buscar/', buscar_estudiantes, name='buscar_estudiantes'),
     path(
        'estudiante/cambiar-estado/',
        cambiar_estado_estudiante,
        name='cambiar_estado_estudiante'
    ),
    path(
        'estudiantes/editar/<int:estudiante_id>/',
        views.editar_estudiante,
        name='editar_estudiante'
    ),
path(
    'estudiantes/eliminar/',
    views.eliminar_estudiante,
    name='eliminar_estudiante'
),
]

