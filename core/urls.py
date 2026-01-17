from django.urls import path
from . import views
from .asesor import views as asesor_views
from .solicitante import views as solicitante_views
from .beneficiario import views as beneficiario_views
from .aseguradora import views as aseguradora_views




urlpatterns = [
    path('login/', views.login_view, name='login'),

    #solicitante
    path('solicitudes/', solicitante_views.lista_solicitudes, name='lista_solicitudes'),
    path('solicitudes/crear/', solicitante_views.crear_solicitud, name='crear_solicitud'),
    path('solicitudes/<int:solicitud_id>/', solicitante_views.detalle_solicitud, name='detalle_solicitud'),
    path('solicitante/', solicitante_views.solicitante_dashboard, name='solicitante_dashboard'),

    

    #beneficiario
    path('beneficiario/', beneficiario_views.beneficiario_dashboard, name='beneficiario_dashboard'),
    path('beneficiario/documentos/', beneficiario_views.mis_siniestros_view, name='beneficiario_documentos'),
    path('api/documentos_aseguradora/<int:poliza_id>/', beneficiario_views.documentos_aseguradora_api, name='documentos_aseguradora_api'),
    path('api/subir-documento/', beneficiario_views.subir_documento, name='subir_documento_api'),
    
    


    

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
    


    # Siniestros cristhian 
    path('', views.SiniestrosInicioView.as_view(), name='inicio'),
    path('formulario/', views.FormularioActivacionView.as_view(), name='formulario'),
    path('siniestros/admin/solicitudes/', views.AdminSolicitudesListView.as_view(), name='admin_lista_solicitudes'),
    path('siniestros/admin/solicitud/<int:pk>/', views.AdminSolicitudDetailView.as_view(), name='admin_detalle_solicitud'),
    path('siniestros/admin/solicitud/<int:pk>/gestionar/', views.AdminGestionSolicitudView.as_view(), name='admin_gestionar_solicitud'),

    path('sinies/asesor/', asesor_views.lista_siniestros, name='siniestros_lista'),
    path('api/beneficiarios/<int:siniestro_id>/', asesor_views.obtener_beneficiarios_por_siniestro, name='api_beneficiarios_siniestro'),
    path('api/documentos/<int:beneficiario_id>/', asesor_views.obtener_documentos_por_beneficiario, name='api_documentos_beneficiario'),

]












