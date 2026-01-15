from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):

    ROLES = (
        ('ADMIN', 'Administrador'),
        ('ASEGURADORA', 'Aseguradora'),
        ('BENEFICIARIO', 'Beneficiario'),
        ('ASESOR', 'Asesor'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    rol = models.CharField(max_length=20, choices=ROLES)

    class Meta:
        db_table = 'profile'
