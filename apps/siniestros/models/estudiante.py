# Modelo para estudiantes de la UTPL
from django.db import models


class Estudiante(models.Model):
    """Modelo para estudiantes de la Universidad Técnica Particular de Loja"""
    
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('egresado', 'Egresado'),
        ('suspendido', 'Suspendido'),
        ('graduado', 'Graduado'),
        ('retirado', 'Retirado'),
    ]
    
    # Identificación
    cedula = models.CharField(max_length=13, unique=True, verbose_name='Cédula')
    codigo_estudiante = models.CharField(max_length=20, unique=True, verbose_name='Código de Estudiante')
    
    # Información personal
    nombres = models.CharField(max_length=100, verbose_name='Nombres')
    apellidos = models.CharField(max_length=100, verbose_name='Apellidos')
    email = models.EmailField(verbose_name='Correo Electrónico')
    telefono = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    
    # Información académica
    carrera = models.CharField(max_length=150, verbose_name='Carrera')
    nivel = models.CharField(max_length=50, blank=True, verbose_name='Nivel/Semestre')
    
    # Estado
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo', verbose_name='Estado')
    
    # Fechas
    fecha_ingreso = models.DateField(null=True, blank=True, verbose_name='Fecha de Ingreso')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['apellidos', 'nombres']
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
    
    def __str__(self):
        return f"{self.codigo_estudiante} - {self.nombres} {self.apellidos}"
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del estudiante"""
        return f"{self.nombres} {self.apellidos}"

