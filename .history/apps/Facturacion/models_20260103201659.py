from django.db import models
from django.contrib.auth.models import User
from apps.siniestros.models import Poliza # Importa el modelo Poliza desde siniestros

class DocumentoFacturacion(models.Model):
    poliza = models.ForeignKey(Poliza, on_delete=models.CASCADE, related_name='documentos_facturacion')
    documento = models.FileField(upload_to='facturacion/documentos/')
    codigo_documento = models.CharField(max_length=100, unique=True, verbose_name='Código de Documento')
    comentarios = models.TextField(blank=True, null=True, verbose_name='Comentarios')
    fecha_subida = models.DateTimeField(auto_now_add=True)
    subido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Subido Por')

    class Meta:
        verbose_name = 'Documento de Facturación'
        verbose_name_plural = 'Documentos de Facturación'
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"Documento {self.codigo_documento} para Póliza {self.poliza.numero}"
