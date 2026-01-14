from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from configuracion.models import Aseguradora


class Poliza(models.Model):
    """Modelo para las pólizas de vida de estudiantes"""
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('inactiva', 'Inactiva'),
        ('suspendida', 'Suspendida'),
        ('vencida', 'Vencida'),
    ]
    
    TIPO_ESTUDIANTE_CHOICES = [
        ('GRADO', 'Grado'),
        ('POSTGRADO', 'Postgrado'),
    ]

    MODALIDAD_CHOICES = [
        ('PRESENCIAL', 'Presencial'),
        ('DISTANCIA', 'Distancia'),
    ]

    numero = models.CharField(max_length=50, unique=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    aseguradora = models.ForeignKey(Aseguradora, on_delete=models.PROTECT, null=True, blank=True)
    tipo_estudiante = models.CharField(max_length=20, choices=TIPO_ESTUDIANTE_CHOICES, default='GRADO')
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES, default='PRESENCIAL')
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
    fecha_evento = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Información de beneficiario
    nombre_beneficiario = models.CharField(max_length=150, blank=True)
    parentesco = models.CharField(max_length=50, blank=True)
    
    # Auditoría
    revisado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, 
                                    blank=True, related_name='siniestros_revisados')
    comentarios = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-fecha_reporte']
    
    def __str__(self):
        return f"Siniestro {self.id} - Póliza {self.poliza.numero}"


class Factura(models.Model):
    poliza = models.ForeignKey(Poliza, on_delete=models.CASCADE, related_name='facturas')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField() 
    pagada = models.BooleanField(default=False)

    def __str__(self):
        return f"Factura {self.id} - ${self.monto}"

class Pago(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateField()
    metodo_pago = models.CharField(
        max_length=50, 
        choices=[('TRANSFERENCIA', 'Transferencia'), ('TARJETA', 'Tarjeta')]
    )

    def __str__(self):
        return f"Pago {self.id} - ${self.monto}"
    

class DocumentoSiniestro(models.Model):
    """
    Almacena los archivos de evidencia (PDFs, Imágenes) que sube el estudiante
    para justificar un siniestro.
    """
    siniestro = models.ForeignKey(Siniestro, on_delete=models.CASCADE, related_name='documentos')
    nombre = models.CharField(max_length=200) # Ej: Informe Policial
    archivo = models.FileField(upload_to='evidencias_siniestros/%Y/%m/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Doc {self.nombre} para Siniestro {self.siniestro.id}"