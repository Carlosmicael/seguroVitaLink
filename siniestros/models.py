from django.db import models
from django.contrib.auth.models import User


class Poliza(models.Model):
    """Modelo para las pólizas de vida de estudiantes"""
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('inactiva', 'Inactiva'),
        ('suspendida', 'Suspendida'),
        ('vencida', 'Vencida'),
    ]
    
    numero = models.CharField(max_length=50, unique=True)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='inactiva')
    monto_cobertura = models.DecimalField(max_digits=10, decimal_places=2, default=10000)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Póliza {self.numero} - {self.estado}"


class Siniestro(models.Model):
    """Modelo para registrar siniestros y activación de pólizas"""
    TIPO_CHOICES = [
        ('accidente', 'Accidente'),
        ('enfermedad', 'Enfermedad grave'),
        ('hospitalizacion', 'Hospitalización'),
        ('fallecimiento', 'Fallecimiento'),
        ('otro', 'Otro'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de revisión'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('pagado', 'Pagado'),
    ]
    
    poliza = models.ForeignKey(Poliza, on_delete=models.CASCADE, related_name='siniestros')
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    descripcion = models.TextField()
    fecha_evento = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Información de beneficiario
    nombre_beneficiario = models.CharField(max_length=150, blank=True)
    relacion_beneficiario = models.CharField(max_length=50, blank=True)
    parentesco = models.CharField(max_length=50, blank=True)
    
    # Contacto
    telefono_contacto = models.CharField(max_length=20, blank=True)
    email_contacto = models.EmailField(blank=True)
    
    # Documentación
    documento = models.FileField(upload_to='siniestros/', null=True, blank=True)
    
    # Auditoría
    revisado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                    blank=True, related_name='siniestros_revisados')
    comentarios = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-fecha_reporte']
    
    def __str__(self):
        return f"Siniestro {self.id} - Póliza {self.poliza.numero}"
