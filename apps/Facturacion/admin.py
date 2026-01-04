from django.contrib import admin
from .models import DocumentoFacturacion

@admin.register(DocumentoFacturacion)
class DocumentoFacturacionAdmin(admin.ModelAdmin):
    list_display = ('codigo_documento', 'poliza', 'fecha_subida', 'subido_por')
    list_filter = ('fecha_subida', 'subido_por', 'poliza__estudiante__carrera')
    search_fields = ('codigo_documento', 'poliza__numero', 'poliza__estudiante__nombres', 'poliza__estudiante__apellidos', 'comentarios')
    raw_id_fields = ('poliza', 'subido_por') # Mejora la selección de pólizas y usuarios
    date_hierarchy = 'fecha_subida'
    readonly_fields = ('fecha_subida', 'subido_por')

    fieldsets = (
        (None, {
            'fields': ('poliza', 'codigo_documento', 'documento', 'comentarios')
        }),
        ('Información de Auditoría', {
            'fields': ('fecha_subida', 'subido_por'),
            'classes': ('collapse',)
        }),
    )
