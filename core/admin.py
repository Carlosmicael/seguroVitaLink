from django.contrib import admin
from .models import Poliza, Profile, Estudiante , Notificaciones, Solicitud, TcasDocumentos

# Register your models here.
admin.site.register(Poliza)
admin.site.register(Profile)
admin.site.register(Estudiante)
admin.site.register(Notificaciones)
admin.site.register(Solicitud)
admin.site.register(TcasDocumentos)

