from django.db import models


class Aseguradora(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    sitio_web = models.URLField(blank=True)
    activa = models.BooleanField(default=True, help_text="Marcar si la aseguradora sigue operando con nosotros")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ruc = models.CharField("RUC", max_length=20, blank=True, null=True, unique=True)
    politicas = models.TextField(blank=True, null=True, verbose_name="Políticas y Condiciones")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Aseguradora"
        verbose_name_plural = "Aseguradoras"

# Nueva clase para Documentos de Políticas asociadas a una Aseguradora ---------- # 

class DocumentoPolitica(models.Model):
    aseguradora = models.ForeignKey(Aseguradora, on_delete=models.CASCADE, related_name='documentos')
    titulo = models.CharField(max_length=200, help_text="Ej: Políticas 2026 - Versión 1")
    
    # Upload de PDF
    archivo_pdf = models.FileField(upload_to='politicas_pdfs/', verbose_name="Documento PDF")
    
    # Texto para visualización web rápida
    terminos_texto = models.TextField(verbose_name="Términos y Condiciones (Texto)")
    
    # Control de versiones
    version = models.CharField(max_length=20, default="1.0")
    fecha_vigencia = models.DateField()
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.aseguradora.nombre}"