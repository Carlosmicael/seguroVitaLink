from django.urls import path
from . import views
from .asesor import views as asesor_views
from .solicitante import views as solicitante_views
from .beneficiario import views as beneficiario_views
from .aseguradora import views as aseguradora_views
from .administrador import views as administrador_views





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
    path('api/documentos_aseguradora/<str:poliza_numero>/', beneficiario_views.documentos_aseguradora_api, name='documentos_aseguradora_api'),
    path('api/subir-documento/', beneficiario_views.subir_documento, name='subir_documento_api'),








    #administrador
    path('administrador/', administrador_views.administrador_dashboard, name='administrador_dashboard'),
    
    # === PÓLIZAS ===
    path('polizas/', administrador_views.lista_polizas, name='admin_lista_polizas'),
    path('polizas/crear/', administrador_views.crear_poliza, name='admin_crear_poliza'),
    path('polizas/generar-numero/', administrador_views.generar_numero_poliza, name='admin_generar_numero_poliza'),
    path('polizas/regla/<int:id_regla>/', administrador_views.obtener_regla_poliza, name='admin_obtener_regla_poliza'),
    path('polizas/detalle/<str:numero_poliza>/', administrador_views.detalle_poliza, name='admin_detalle_poliza'),
    
    # === SINIESTROS ===
    path('administrador/siniestros/', administrador_views.lista_siniestros, name='admin_lista_siniestros'),
    path('administrador/siniestros/configuracion/', administrador_views.configuracion_siniestros, name='admin_config_siniestros'),
    path('administrador/siniestros/guardar-config/', administrador_views.guardar_config_siniestro, name='admin_guardar_config_siniestro'),
    
    # === DOCUMENTOS ===
    path('documentos/', administrador_views.lista_documentos, name='lista_documentos'),
    path('documentos/crear/', administrador_views.crear_documento, name='crear_documento'),
    path('documentos/detalle/<int:id_doc>/', administrador_views.detalle_documento, name='detalle_documento'),
    path('documentos/eliminar/<int:id_doc>/', administrador_views.eliminar_documento, name='eliminar_documento'),

    path('trigger-event/<int:user_id>/', administrador_views.trigger_event, name='trigger_event'),
    path('pusher/auth/', administrador_views.pusher_auth, name='pusher_auth'),
    path('obtener-notificaciones-usuario/<int:user_id>/', administrador_views.obtener_notificaciones_usuario, name='obtener_notificaciones_usuario'),
    path('marcar-notificaciones-leidas/<int:user_id>/', administrador_views.marcar_notificaciones_leidas, name='marcar_notificaciones_leidas'),
    
    
    







    

    #asesor
    path('asesor/', asesor_views.asesor_dashboard, name='asesor_dashboard'),

    #Notificaciones
    path('trigger-event/asesor/<int:user_id>/', asesor_views.trigger_event, name='trigger_event'),
    path('pusher/auth/asesor', asesor_views.pusher_auth, name='pusher_auth'),
    path('obtener-notificaciones-usuario/asesor/<int:user_id>/', asesor_views.obtener_notificaciones_usuario, name='obtener_notificaciones_usuario'),
    path('marcar-notificaciones-leidas/asesor/<int:user_id>/', asesor_views.marcar_notificaciones_leidas, name='marcar_notificaciones_leidas'),





    path('asesor/dashboard/metrics/', asesor_views.asesor_dashboard_metrics, name='asesor_dashboard_metrics'),
    # Ronal - Gestión de Liquidaciones
    path('asesor/liquidaciones/', asesor_views.siniestros_pendientes_pago, name='siniestros_pendientes_pago'),
    path('asesor/liquidaciones/beneficiario/<int:beneficiario_id>/', asesor_views.registrar_liquidacion, name='registrar_liquidacion'),
    path('asesor/reportes/liquidaciones/', asesor_views.reportes_liquidacion, name='reportes_liquidacion'),
    path('asesor/reportes/liquidaciones/factura/<int:factura_id>/', asesor_views.factura_detalle, name='factura_detalle'),
    # Ronal - Fin Gestión de Liquidaciones


    #Documentos
    path("documentos/poliza/", views.obtener_documentos_por_proceso, name="obtener_documentos"),
    path("documentos/<int:doc_id>/descargar/", views.descargar_documento, name="descargar_documento"),
    path("documentos/<int:doc_id>/eliminar/", views.eliminar_documento, name="eliminar_documento"),
    path("documentos/<int:doc_id>/view/", views.view_documento, name="view_documento"),
    path("documentos/<int:doc_id>/remplazar/", views.remplazar_documento, name="remplazar_documento"),
    path("documentos/eliminar_drive/", views.eliminar_drive, name="eliminar_drive"),
    path('documentos/', views.documentos_view, name='documentos'),
    path("imagenesbytes/<int:doc_id>/", views.imagenesbytes, name="imagenesbytes"),

    #Reportes
    path('reportes/', asesor_views.lista_reportes, name='lista_reportes'),
    path('reportes/<int:id>/', asesor_views.detalle_reporte, name='detalle_reporte'),
    path('reportes/eliminar/<int:id>/', asesor_views.eliminar_reporte, name='eliminar_reporte'),
    path('reportes/cambiar-estado/<int:id>/', asesor_views.cambiar_estado_reporte, name='cambiar_estado_reporte'),

    #Beneficiarios
    path('sinies/asesor/', asesor_views.lista_siniestros, name='siniestros_lista'),
    path('api/beneficiarios/<int:siniestro_id>/', asesor_views.obtener_beneficiarios_por_siniestro, name='api_beneficiarios_siniestro'),
    path('api/documentos/<int:beneficiario_id>/', asesor_views.obtener_documentos_por_beneficiario, name='api_documentos_beneficiario'),

    # Siniestros module
    path('siniestros/', asesor_views.siniestros_module_lista, name='siniestros_module_lista'),
    path('siniestros/crear/', asesor_views.siniestros_module_crear, name='siniestros_module_crear'),
    path('siniestros/<int:id>/', asesor_views.siniestros_module_detalle, name='siniestros_module_detalle'),
    path('siniestros/<int:id>/enviar/', asesor_views.siniestros_module_enviar, name='siniestros_module_enviar'),
    path('siniestros/<int:id>/eliminar/', asesor_views.siniestros_module_eliminar, name='siniestros_module_eliminar'),

     # URLs del módulo de beneficiarios
    path('beneficiarios/', asesor_views.beneficiarios_module_lista, name='beneficiarios_module_lista'),
    path('beneficiarios/crear/', asesor_views.beneficiarios_module_crear, name='beneficiarios_module_crear'),
    path('beneficiarios/<int:id>/', asesor_views.beneficiarios_module_detalle, name='beneficiarios_module_detalle'),
    




    # Siniestros cristhian 
    path('', views.SiniestrosInicioView.as_view(), name='inicio'),
    path('formulario/', views.FormularioActivacionView.as_view(), name='formulario'),
    path('siniestros/admin/solicitudes/', views.AdminSolicitudesListView.as_view(), name='admin_lista_solicitudes'),
    path('siniestros/admin/solicitud/<int:pk>/', views.AdminSolicitudDetailView.as_view(), name='admin_detalle_solicitud'),
    path('siniestros/admin/solicitud/<int:pk>/gestionar/', views.AdminGestionSolicitudView.as_view(), name='admin_gestionar_solicitud'),
    path('reportar-evento/', views.reportar_evento, name='reportar_evento'),


    # Administrador - Aseguradoras y Políticas - RONAL
    path('administrador/aseguradoras/<int:aseguradora_id>/politicas/crear/', administrador_views.politica_create, name='politica_create'),
    path('administrador/politicas/<int:politica_id>/editar/', administrador_views.politica_edit, name='politica_edit'),
    path('administrador/publico/aseguradoras/', administrador_views.politicas_publicas_admin, name='politicas_publicas_admin'),
    path('administrador/publico/aseguradoras/<int:aseguradora_id>/', administrador_views.politica_publica_detalle_admin, name='politica_publica_detalle_admin'),

    # Publico - terminos y politicas - RONAL
    path('aseguradoras/terminos/', administrador_views.politicas_publicas, name='politicas_publicas'),
    path('aseguradoras/<int:aseguradora_id>/terminos/', administrador_views.politica_publica_detalle, name='politica_publica_detalle'),

]












