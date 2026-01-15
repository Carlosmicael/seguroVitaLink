from django.urls import path
from . import views
from .asesor import views as asesor_views
from .solicitante import views as solicitante_views




urlpatterns = [
    path('', views.login_view, name='login'),

    #solicitante
    path('solicitudes/', solicitante_views.lista_solicitudes, name='lista_solicitudes'),
    path('solicitudes/crear/', solicitante_views.crear_solicitud, name='crear_solicitud'),
    path('solicitudes/<int:solicitud_id>/', solicitante_views.detalle_solicitud, name='detalle_solicitud'),
    path('solicitante/', solicitante_views.solicitante_dashboard, name='solicitante_dashboard'),


    

    #asesor
    path('asesor/polizas/', asesor_views.lista_polizas, name='lista_polizas'),
    #path('polizas/<int:poliza_id>/', views.detalle_poliza, name='detalle_poliza'),
    path('asesor/', asesor_views.asesor_dashboard, name='asesor_dashboard'),
    path('polizas/crear/', asesor_views.crear_poliza, name='crear_poliza'),
    path('polizas/generar-numero/', asesor_views.generar_numero_poliza, name='generar_numero_poliza'),
    path('trigger-event/<int:user_id>/', asesor_views.trigger_event, name='trigger_event'),
    path('pusher/auth/', asesor_views.pusher_auth, name='pusher_auth'),
    path('obtener-notificaciones-usuario/<int:user_id>/', asesor_views.obtener_notificaciones_usuario, name='obtener_notificaciones_usuario'),
    path('marcar-notificaciones-leidas/<int:user_id>/', asesor_views.marcar_notificaciones_leidas, name='marcar_notificaciones_leidas'),

    #Documentos
    path("documentos/poliza/", views.obtener_documentos_por_proceso, name="obtener_documentos"),
    path("documentos/<int:doc_id>/descargar/", views.descargar_documento, name="descargar_documento"),
    path("documentos/<int:doc_id>/eliminar/", views.eliminar_documento, name="eliminar_documento"),
    path("documentos/<int:doc_id>/view/", views.view_documento, name="view_documento"),
    path("documentos/<int:doc_id>/remplazar/", views.remplazar_documento, name="remplazar_documento"),
    path("documentos/eliminar_drive/", views.eliminar_drive, name="eliminar_drive"),

    path('documentos/', views.documentos_view, name='documentos'),
    path("imagenesbytes/<int:doc_id>/", views.imagenesbytes, name="imagenesbytes"),
]






