from django.contrib import admin
from .models import Poliza, Profile, Estudiante , Notificaciones, Solicitud, TcasDocumentos, Siniestro, Aseguradora, Beneficiario, DocumentosAseguradora, ReglasPoliza, ConfiguracionSiniestro, ReporteEvento

# Register your models here.
admin.site.register(Profile)
admin.site.register(Notificaciones)
admin.site.register(Solicitud)
admin.site.register(TcasDocumentos)
admin.site.register(Aseguradora)
admin.site.register(Beneficiario)
admin.site.register(DocumentosAseguradora)
admin.site.register(ReglasPoliza)
admin.site.register(ConfiguracionSiniestro)
admin.site.register(Poliza)
admin.site.register(Estudiante)
admin.site.register(Siniestro)
admin.site.register(ReporteEvento)






