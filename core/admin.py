from django.contrib import admin
from .models import (
    Poliza,
    Profile,
    Estudiante,
    Notificaciones,
    Solicitud,
    TcasDocumentos,
    Siniestro,
    Aseguradora,
    Beneficiario,
    DocumentosAseguradora,
    Factura, # FACTURA - RONAL
    Pago, # PAGO - RONAL
    PoliticaAseguradora, # POLITICAS - RONAL
)

# Register your models here.
admin.site.register(Profile)
admin.site.register(Notificaciones)
admin.site.register(Solicitud)
admin.site.register(TcasDocumentos)
admin.site.register(Aseguradora)
admin.site.register(Beneficiario)
admin.site.register(DocumentosAseguradora) 
admin.site.register(Factura) # FACTURA - RONAL
admin.site.register(Pago) # PAGO - RONAL
admin.site.register(PoliticaAseguradora) # POLITICAS - RONAL




@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('codigo_estudiante', 'nombre_completo', 'cedula', 'carrera', 'estado', 'email')
    list_filter = ('estado', 'carrera', 'fecha_ingreso')
    search_fields = ('codigo_estudiante', 'cedula', 'nombres', 'apellidos', 'email')
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    fieldsets = (
        ('Identificación', {
            'fields': ('cedula', 'codigo_estudiante')
        }),
        ('Información Personal', {
            'fields': ('nombres', 'apellidos', 'email', 'telefono')
        }),
        ('Información Académica', {
            'fields': ('carrera', 'nivel', 'estado', 'fecha_ingreso')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Poliza)
class PolizaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'estudiante', 'estado', 'monto_cobertura', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('numero', 'estudiante__codigo_estudiante', 'estudiante__nombres', 'estudiante__apellidos', 'estudiante__cedula')
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ('fecha_creacion',)


@admin.register(Siniestro)
class SiniestroAdmin(admin.ModelAdmin):
    list_display = ('id', 'poliza', 'tipo', 'nombre_beneficiario', 'estado', 'fecha_reporte', 'revisado_por')
    list_filter = ('estado', 'tipo', 'fecha_reporte', 'revisado_por')
    search_fields = ('poliza__numero', 'descripcion', 'nombre_beneficiario', 'email_contacto', 'revisado_por__username', 'poliza__estudiante__nombres', 'poliza__estudiante__apellidos')
    date_hierarchy = 'fecha_reporte'
    readonly_fields = ('fecha_reporte', 'fecha_actualizacion')
    autocomplete_fields = ['poliza', 'revisado_por'] # Permite buscar la póliza y el revisor
    
    fieldsets = (
        ('Información del Siniestro', {
            'fields': ('poliza', 'tipo', 'descripcion', 'fecha_evento', 'estado', 'comentarios')
        }),
        ('Datos del Beneficiario', {
            'fields': ('nombre_beneficiario', 'relacion_beneficiario', 'parentesco', 'telefono_contacto', 'email_contacto')
        }),
        ('Documentación', {
            'fields': ('documento',)
        }),
        ('Auditoría', {
            'fields': ('fecha_reporte', 'fecha_actualizacion', 'revisado_por'),
            'classes': ('collapse',)
        }),
    )
