from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.db.models import JSONField
import datetime




class Poliza(models.Model):
    
    ESTADO_CHOICES = [('pendiente', 'Pendiente'),('activa', 'Activa'),('vencida', 'Vencida'),('cancelada', 'Cancelada')]
    
    TIPO_COBERTURA_CHOICES = [('basica', 'Cobertura Básica'),('ampliada', 'Cobertura Ampliada'),('completa', 'Cobertura Completa')]
    
    estudiante = models.ForeignKey('Estudiante',on_delete=models.CASCADE,related_name='polizas',verbose_name="Estudiante",null=True,blank=True)

    numero_poliza = models.CharField(max_length=50,unique=True,verbose_name="Número de Póliza",help_text="Identificador único de la póliza")
    estado = models.CharField(max_length=20,choices=ESTADO_CHOICES,default='pendiente',verbose_name="Estado")
    tipo_cobertura = models.CharField(max_length=20,choices=TIPO_COBERTURA_CHOICES,default='basica',verbose_name="Tipo de Cobertura")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio",help_text="Fecha en que la póliza entra en vigencia")
    fecha_fin = models.DateTimeField(verbose_name="Fecha de Fin",help_text="Fecha en que la póliza expira")
    prima_neta = models.DecimalField(max_digits=10,decimal_places=2,validators=[MinValueValidator(0.01)],verbose_name="Prima Neta",help_text="Valor mensual de la prima")
    fecha_creacion = models.DateTimeField(auto_now_add=True,verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True,verbose_name="Última Actualización")
    

    class Meta:
        verbose_name = "Póliza"
        verbose_name_plural = "Pólizas"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['numero_poliza']),
            models.Index(fields=['estado']),
            models.Index(fields=['estudiante', 'estado']),
        ]
    
    def __str__(self):
        return f"Póliza {self.numero_poliza} - {self.tipo_cobertura} - {self.estado}"





    def calcular_valor_mensual(self):
        valor_base = float(self.prima_neta)
        multiplicadores = {'basica': 1.0,'ampliada': 1.5,'completa': 2.0}
        multiplicador = multiplicadores.get(self.tipo_cobertura, 1.0)
        return valor_base * multiplicador
    

    def esta_vigente(self):
        hoy = timezone.now().date()
        return (self.estado == 'activa' and self.fecha_inicio <= hoy <= self.fecha_fin.date())
    

    def dias_para_vencimiento(self):
        hoy = timezone.now().date()
        delta = self.fecha_fin.date() - hoy
        return delta.days
    
    def renovar_poliza(self, nueva_fecha_fin):
        if not self.esta_vigente():
            raise ValueError("No se puede renovar una póliza no vigente")

        self.fecha_fin = nueva_fecha_fin
        self.estado = 'activa'
        self.save()
    

    def activar(self):
        if self.estado == 'pendiente':
            self.estado = 'activa'
            self.save()
    

    def cancelar(self):
        self.estado = 'cancelada'
        self.save()
    

    def verificar_vencimiento(self):
        if self.estado == 'activa' and timezone.now().date() > self.fecha_fin.date():
            self.estado = 'vencida'
            self.save()
            return True
        return False
    
    @property
    def duracion_meses(self):
        delta = self.fecha_fin.date() - self.fecha_inicio
        return round(delta.days / 30)
    
    @property
    def valor_total(self):
        return self.calcular_valor_mensual() * self.duracion_meses
    

    @staticmethod
    def generar_numero_poliza():
        from datetime import datetime
        fecha_str = datetime.now().strftime('%Y%m%d')
        ultimo = Poliza.objects.filter(numero_poliza__startswith=f'POL-{fecha_str}').count()
        secuencia = str(ultimo + 1).zfill(5)
        return f'POL-{fecha_str}-{secuencia}'








class Estudiante(models.Model):

    TIPO_ESTUDIO_CHOICES = [('presencial', 'Presencial'),('distancia', 'Distancia')]
    ESTADO_CHOICES = [('activo', 'Activo'),('inactivo', 'Inactivo'),('fallecido', 'Fallecido')]

    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, unique=True)
    correo = models.EmailField(unique=True)
    estado = models.CharField(max_length=20,choices=ESTADO_CHOICES,default='activo')
    tipo_estudio = models.CharField(max_length=20,choices=TIPO_ESTUDIO_CHOICES)
    fecha_defuncion = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.cedula}"


    def cambiar_estado(self, nuevo_estado):
        self.estado = nuevo_estado
        self.save()

    def registrar_defuncion(self, fecha):
        self.estado = 'fallecido'
        self.fecha_defuncion = fecha
        self.save()

    def obtener_polizas(self):
        return self.polizas.all()  


class Solicitud(models.Model):
    ESTADO_CHOICES = [('pendiente', 'Pendiente'),('aprobada', 'Aprobada'),('rechazada', 'Rechazada'),('en_proceso', 'En Proceso'),]
    
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='solicitudes')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    tipo_poliza = models.CharField(max_length=100)
    monto_solicitado = models.DecimalField(max_digits=10, decimal_places=2)
    motivo = models.TextField()
    documento_identidad = models.CharField(max_length=20)
    telefono = models.CharField(max_length=20)
    direccion = models.TextField()
    
    # Para notificación al asesor
    notificacion_enviada = models.BooleanField(default=False)
    asesor_notificado = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_recibidas')
    
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_solicitud']
    
    def __str__(self):
        return f"Solicitud #{self.id} - {self.estudiante.nombres} - {self.estado}"






class Profile(models.Model):

    ROLE_CHOICES = (('asesor', 'Asesor'),('solicitante', 'Solicitante'))

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.rol}"





class Notificaciones(models.Model):
    not_id = models.AutoField(primary_key=True)
    not_codcli = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="notificaciones", blank=True, null=True)
    not_poliza = models.ForeignKey(Poliza, on_delete=models.CASCADE, related_name="notificaciones", blank=True, null=True)
    not_fecha_creacion = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    not_fecha_proceso = models.DateTimeField(blank=True, null=True)
    not_mensaje = models.TextField(blank=True, null=True)
    not_read = models.BooleanField(default=False, blank=True, null=True)
    not_estado = models.BooleanField(default=False, blank=True, null=True)
    not_celery_task_id = models.CharField(max_length=255, null=True, blank=True, unique=True)

    def __str__(self):
        return f"Notificación {self.not_id}"





























class TcasDocumentos(models.Model):
    doc_cod_doc = models.AutoField(primary_key=True)
    doc_descripcion = models.TextField()
    doc_file = models.FileField(upload_to="documentos/", null=True, blank=True)
    doc_size = models.PositiveIntegerField(null=True, blank=True) 
    fec_creacion = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    fecha_edit = models.DateTimeField(blank=True,null=True)


    def save(self, *args, **kwargs):
        if self.doc_file and not self.doc_file._committed:
            self.doc_size = self.doc_file.size
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Documento {self.doc_cod_doc} ({self.doc_size} bytes)"


















