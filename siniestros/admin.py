from django.contrib import admin
from .models import Poliza, Siniestro


@admin.register(Poliza)
class PolizaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'usuario', 'estado', 'monto_cobertura', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('numero', 'usuario__username', 'usuario__email')
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ('fecha_creacion',)


@admin.register(Siniestro)
class SiniestroAdmin(admin.ModelAdmin):
    list_display = ('id', 'poliza', 'tipo', 'nombre_beneficiario', 'estado', 'fecha_reporte')
    list_filter = ('estado', 'tipo', 'fecha_reporte')
    search_fields = ('poliza__numero', 'descripcion', 'nombre_beneficiario', 'email_contacto')
    date_hierarchy = 'fecha_reporte'
    readonly_fields = ('fecha_reporte', 'fecha_actualizacion')
    
    fieldsets = (
        ('Información de Póliza', {
            'fields': ('poliza', 'tipo', 'descripcion')
        }),
        ('Información del Beneficiario', {
            'fields': ('nombre_beneficiario', 'relacion_beneficiario', 'parentesco')
        }),
        ('Contacto', {
            'fields': ('telefono_contacto', 'email_contacto')
        }),
        ('Documentación', {
            'fields': ('documento',)
        }),
        ('Estado', {
            'fields': ('estado', 'comentarios')
        }),
        ('Auditoría', {
            'fields': ('fecha_reporte', 'fecha_actualizacion', 'revisado_por'),
            'classes': ('collapse',)
        }),
    )
