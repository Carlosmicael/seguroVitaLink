from django.contrib import admin
from .models import Estudiante, Beneficiario


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = (
        'cedula',
        'nombres',
        'apellidos',
        'carrera',
        'nivel',
        'modalidad',
        'periodo_academico',
        'estado',
        'fecha_creacion'
    )

    search_fields = (
        'cedula',
        'nombres',
        'apellidos',
        'correo'
    )

    list_filter = (
        'estado',
        'nivel',
        'modalidad',
        'periodo_academico'
    )


@admin.register(Beneficiario)
class BeneficiarioAdmin(admin.ModelAdmin):
    list_display = (
        'cedula',
        'relacion',
        'telefono',
        'cuenta_bancaria',
        'created_at'
    )

    search_fields = ('cedula', 'relacion')
