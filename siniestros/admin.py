from django.contrib import admin
from .models import Poliza, Siniestro, Factura, Pago

@admin.register(Poliza)
class PolizaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'usuario', 'estado', 'monto_cobertura', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('numero', 'usuario__username', 'usuario__email')
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ('fecha_creacion',)


@admin.register(Siniestro)
class SiniestroAdmin(admin.ModelAdmin):
    list_display = ('id', 'poliza', 'tipo', 'estado', 'fecha_reporte')
    list_filter = ('estado', 'tipo', 'fecha_reporte')
    search_fields = ('poliza__numero', 'descripcion', 'nombre_beneficiario')
    date_hierarchy = 'fecha_reporte'
    readonly_fields = ('fecha_reporte', 'fecha_actualizacion')

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('id', 'poliza', 'monto', 'fecha_vencimiento', 'pagada')
    list_filter = ('pagada', 'fecha_vencimiento')
    search_fields = ('poliza__numero',)

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'factura', 'monto', 'fecha_pago', 'metodo_pago')
    list_filter = ('fecha_pago', 'metodo_pago')
