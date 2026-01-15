from django.urls import path
from .views import registrar_beneficiario, registrar_estudiante, listar_estudiantes, buscar_estudiantes, inicio_asesor, cambiar_estado_estudiante

app_name = 'panel_asesor'

urlpatterns = [
    path('', inicio_asesor, name='inicio'),  # <--- quita "views."
    path('registrar/', registrar_beneficiario, name='registrar'),
    path('registrar/estudiante/', registrar_estudiante, name='registrar_estudiante'),
    path('estudiantes/', listar_estudiantes, name='listar_estudiantes'),
    path('estudiantes/buscar/', buscar_estudiantes, name='buscar_estudiantes'),
     path(
        'estudiante/cambiar-estado/',
        cambiar_estado_estudiante,
        name='cambiar_estado_estudiante'
    ),

]

