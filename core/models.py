from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.db.models import JSONField
import datetime


# Modelo de Aseguradora y Politicas - RONAL --------------------------------------

class Aseguradora(models.Model):
    id_aseguradora = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    politicas = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_inactivacion = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class PoliticaAseguradora(models.Model):
    aseguradora = models.ForeignKey(Aseguradora, on_delete=models.CASCADE, related_name="politicas_versiones")
    documento = models.FileField(upload_to="politicas/", blank=True, null=True)
    terminos = models.TextField()
    fecha_version = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-fecha_version', '-id']

    def __str__(self):
        return f"Politica {self.aseguradora.nombre} - {self.fecha_version}"

# ---------------------------------------



class Poliza(models.Model):
    
    ESTADO_CHOICES = [('pendiente', 'Pendiente'),('activa', 'Activa'),('vencida', 'Vencida'),('cancelada', 'Cancelada'),('inactiva', 'Inactiva'),('suspendida', 'Suspendida'),]
    
    TIPO_COBERTURA_CHOICES = [('basica', 'Cobertura Básica'),('ampliada', 'Cobertura Ampliada'),('completa', 'Cobertura Completa')]
    
    estudiante = models.ForeignKey('Estudiante',on_delete=models.CASCADE,related_name='poliza',verbose_name="Estudiante",null=True,blank=True)
    aseguradora = models.ForeignKey(Aseguradora, on_delete=models.CASCADE, related_name='polizas' ,null=True,blank=True)

    numero_poliza = models.CharField(max_length=50,unique=True,verbose_name="Número de Póliza",help_text="Identificador único de la póliza")
    numero = models.CharField(max_length=50, unique=True)
    estado = models.CharField(max_length=20,choices=ESTADO_CHOICES,default='pendiente',verbose_name="Estado")
    monto_cobertura = models.DecimalField(max_digits=10, decimal_places=2, default=10000)
    tipo_cobertura = models.CharField(max_length=20,choices=TIPO_COBERTURA_CHOICES,default='basica',verbose_name="Tipo de Cobertura")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio",help_text="Fecha en que la póliza entra en vigencia")
    fecha_fin = models.DateTimeField(verbose_name="Fecha de Fin",help_text="Fecha en que la póliza expira")
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)
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
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, null=True, blank=True)
    descripcion = models.TextField()
    fecha_evento = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Información de solicitante
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
        if self.poliza:
            return f"Siniestro {self.id} - Póliza {self.poliza.numero}"
        return f"Siniestro {self.id} - Sin póliza asignada"









class Estudiante(models.Model):

    TIPO_ESTUDIO_CHOICES = [('presencial', 'Presencial'),('distancia', 'Distancia')]
    ESTADO_CHOICES = [('activo', 'Activo'),('inactivo', 'Inactivo'),('fallecido', 'Fallecido'),
    ('egresado', 'Egresado'),
    ('suspendido', 'Suspendido'),
    ('graduado', 'Graduado'),
    ('retirado', 'Retirado'),
]

    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, unique=True)
    codigo_estudiante = models.CharField(max_length=20, unique=True, verbose_name='Código de Estudiante')
    email = models.EmailField(unique=True)
    estado = models.CharField(max_length=20,choices=ESTADO_CHOICES,default='activo')
    tipo_estudio = models.CharField(max_length=20,choices=TIPO_ESTUDIO_CHOICES)
    fecha_defuncion = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    telefono = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    # Información académica
    carrera = models.CharField(max_length=150, verbose_name='Carrera')
    nivel = models.CharField(max_length=50, blank=True, verbose_name='Nivel/Semestre')

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_ingreso = models.DateField(null=True, blank=True) 


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

    class Meta:
        ordering = ['apellidos', 'nombres']
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
    
    def __str__(self):
        return f"{self.codigo_estudiante} - {self.nombres} {self.apellidos}"
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del estudiante"""
        return f"{self.nombres} {self.apellidos}"




class Profile(models.Model):

    ROLE_CHOICES = (
        ('asesor', 'Asesor'),
        ('solicitante', 'Solicitante'),
        ('beneficiario', 'Beneficiario'),
        ('administrador', 'Administrador'), # RONAL added administrator role
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.rol}"



class Solicitud(models.Model):
    ESTADO_CHOICES = [('pendiente', 'Pendiente'),('aprobada', 'Aprobada'),('rechazada', 'Rechazada'),('en_proceso', 'En Proceso'),]
    
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='solicitudes')
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='solicitudes', null=True, blank=True)
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



class Beneficiario(models.Model):
    id_beneficiario = models.AutoField(primary_key=True)
    siniestro = models.ForeignKey(Siniestro, on_delete=models.CASCADE, related_name="beneficiarios")
    nombre = models.CharField(max_length=200)
    correo = models.EmailField()
    numero_cuenta = models.CharField(max_length=50, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="beneficiarios", blank=True, null=True)

    def __str__(self):
        return self.nombre




class TcasDocumentos(models.Model):
    CHOICES_ESTADO = (
        ("pendiente", "Pendiente"),
        ("aprobado", "Aprobado"),
        ("rechazado", "Rechazado"),
    )
    doc_cod_doc = models.AutoField(primary_key=True)
    doc_descripcion = models.TextField()
    doc_file = models.FileField(upload_to="documentos/", null=True, blank=True)
    doc_size = models.PositiveIntegerField(null=True, blank=True) 
    fec_creacion = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    fecha_edit = models.DateTimeField(blank=True,null=True)
    estado = models.CharField(max_length=10, choices=CHOICES_ESTADO, default="pendiente",blank=True,null=True)
    beneficiario = models.ForeignKey(Beneficiario, on_delete=models.CASCADE, related_name="documentos",blank=True,null=True)


    def save(self, *args, **kwargs):
        if self.doc_file and not self.doc_file._committed:
            self.doc_size = self.doc_file.size
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Documento {self.doc_cod_doc} ({self.doc_size} bytes)"





class DocumentosAseguradora(models.Model):
    id_doc_req = models.AutoField(primary_key=True)
    aseguradora = models.ForeignKey(Aseguradora, on_delete=models.CASCADE, related_name="documentos_requeridos" ,blank=True,null=True)
    siniestro_tipo = models.CharField(max_length=100,blank=True,null=True)
    nombre_documento = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    obligatorio = models.BooleanField(default=True)
    fecha_version = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_documento} ({'Obligatorio' if self.obligatorio else 'Opcional'})"

## Factura y Pago Models - RONAL --------------------------------------

class Factura(models.Model):
    siniestro = models.OneToOneField(Siniestro, on_delete=models.CASCADE, related_name="factura")
    numero_factura = models.CharField(max_length=50, verbose_name="Numero de Factura")
    monto = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    fecha = models.DateField()

    def __str__(self):
        return f"Factura {self.numero_factura} - Siniestro {self.siniestro_id}"


class Pago(models.Model):
    METODO_PAGO_CHOICES = [
        ("transferencia", "Transferencia"),
        ("cheque", "Cheque"),
        ("efectivo", "Efectivo"),
        ("tarjeta", "Tarjeta"),
        ("otro", "Otro"),
    ]

    siniestro = models.ForeignKey(Siniestro, on_delete=models.CASCADE, related_name="pagos")
    factura = models.ForeignKey(Factura, on_delete=models.SET_NULL, null=True, blank=True, related_name="pagos")
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    fecha_pago = models.DateField()
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)

    def __str__(self):
        return f"Pago {self.id} - Siniestro {self.siniestro_id}"













