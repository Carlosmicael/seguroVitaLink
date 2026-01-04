# Modelo para las pilizas de vida y siniestros asociados
from django.db import models
from .estudiante import Estudiante

class Poliza(models.Model):
    """Modelo para las pólizas de vida de estudiantes"""
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('inactiva', 'Inactiva'),
        ('suspendida', 'Suspendida'),
        ('vencida', 'Vencida'),
    ]
    
    numero = models.CharField(max_length=50, unique=True)
    estudiante = models.OneToOneField(Estudiante, on_delete=models.CASCADE, related_name='poliza')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='inactiva')
    monto_cobertura = models.DecimalField(max_digits=10, decimal_places=2, default=10000)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Póliza {self.numero} - {self.estado}"