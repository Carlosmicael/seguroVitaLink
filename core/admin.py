from django.contrib import admin
from .models import Poliza, Profile, Estudiante , Notificaciones, Solicitud, TcasDocumentos, Siniestro, Aseguradora, Beneficiario, DocumentosAseguradora, ReglasPoliza, ConfiguracionSiniestro, ReporteEvento,Factura,Pago,PoliticaAseguradora


# Register your models here.
admin.site.register(Profile)
admin.site.register(Notificaciones)
admin.site.register(Solicitud)
admin.site.register(TcasDocumentos)
admin.site.register(Aseguradora)
admin.site.register(Beneficiario)
admin.site.register(DocumentosAseguradora)
admin.site.register(ReglasPoliza)
admin.site.register(ConfiguracionSiniestro)
admin.site.register(Estudiante)
admin.site.register(ReporteEvento)
admin.site.register(Factura) # FACTURA - RONAL
admin.site.register(Pago) # PAGO - RONAL
admin.site.register(PoliticaAseguradora) # POLITICAS - RONAL



@admin.register(Poliza)
class PolizaAdmin(admin.ModelAdmin):
    list_display = ('numero_poliza', 'get_estudiantes', 'estado', 'monto_cobertura', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('numero_poliza', 'numero', 'estudiantes__codigo_estudiante', 'estudiantes__nombres', 'estudiantes__apellidos', 'estudiantes__cedula')
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ('fecha_creacion',)
    filter_horizontal = ('estudiantes',)  
    
    def get_estudiantes(self, obj):
        estudiantes = obj.estudiantes.all()[:3]  
        if estudiantes:
            nombres = ", ".join([f"{e.nombres} {e.apellidos}" for e in estudiantes])
            total = obj.estudiantes.count()
            if total > 3:
                return f"{nombres}... (+{total-3} más)"
            return nombres
        return "Sin estudiantes"
    get_estudiantes.short_description = 'Estudiantes'




    

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
