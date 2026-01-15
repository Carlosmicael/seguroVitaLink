from django.db import models
from login.models import Profile

class Beneficiario(models.Model):

    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name='beneficiario'
    )

    cedula = models.CharField(max_length=10, unique=True)
    telefono = models.CharField(max_length=20)
    relacion = models.CharField(max_length=50)
    cuenta_bancaria = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'beneficiario'

class Estudiante(models.Model):

    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('fallecido', 'Fallecido'),
        ('inactivo', 'Inactivo'),
    ]

    MODALIDAD_CHOICES = [
        ('presencial', 'Presencial'),
        ('virtual', 'Virtual'),
        ('hibrida', 'Híbrida'),
    ]

    NIVEL_CHOICES = [
        ('grado', 'Grado'),
        ('posgrado', 'Posgrado'),
    ]
    PERIODO_ACADEMICO_CHOICES = [
        ('OCT/2025-FEB/2026', 'OCT/2025 - FEB/2026'),
        ('ABR/2026-AGO/2026', 'ABR/2026 - AGO/2026'),
    ]


    cedula = models.CharField(max_length=10, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    correo = models.EmailField()

    modalidad = models.CharField(
        max_length=15,
        choices=MODALIDAD_CHOICES
    )

    nivel = models.CharField(
        max_length=15,
        choices=NIVEL_CHOICES
    )
    

    carrera = models.CharField(max_length=100)

    periodo_academico = models.CharField(
        max_length=20,
        choices=PERIODO_ACADEMICO_CHOICES
    )


    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='activo'
    )

    fecha_defuncion = models.DateField(null=True, blank=True)
    tiempo_transcurrido = models.CharField(max_length=50, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.cedula})"