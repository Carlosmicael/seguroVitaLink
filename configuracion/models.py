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

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Aseguradora"
        verbose_name_plural = "Aseguradoras"
