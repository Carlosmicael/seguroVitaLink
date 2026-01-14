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

    dias_maximos_reporte = models.PositiveIntegerField(
        default=30, 
        verbose_name="Días máximos para reportar",
        help_text="Límite de días tras el evento para aceptar el reclamo."
    )

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
    

# En configuracion/models.py

class RequisitoSiniestro(models.Model):
    # USAMOS EXACTAMENTE TUS OPCIONES DE SINIESTRO
    TIPOS_SINIESTRO = [
        ('accidente', 'Accidente'),
        ('enfermedad', 'Enfermedad grave'),
        ('hospitalizacion', 'Hospitalización'),
        ('fallecimiento', 'Fallecimiento'),
        ('otro', 'Otro'),
    ]

    aseguradora = models.ForeignKey(Aseguradora, on_delete=models.CASCADE, related_name='requisitos')
    nombre_documento = models.CharField(max_length=200, verbose_name="Nombre del Documento (Ej: Acta Defunción)")
    
    # Aquí usamos tu lista corregida
    tipo_siniestro = models.CharField(max_length=20, choices=TIPOS_SINIESTRO, verbose_name="Aplica para")
    
    obligatorio = models.BooleanField(default=True, verbose_name="¿Es obligatorio?")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_documento} ({self.get_tipo_siniestro_display()})"  