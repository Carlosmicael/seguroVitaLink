import os
import django
import random
from datetime import timedelta
from django.utils import timezone

# 1. Configuración del entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings') # Asegúrate que coincida con tu carpeta de settings
django.setup()

# 2. Importar Modelos
from django.contrib.auth import get_user_model
User = get_user_model()
from configuracion.models import Aseguradora
from siniestros.models import Poliza, Siniestro, Factura, Pago

print("🌱 Iniciando proceso de siembra de datos...")

# --- DATOS DUMMY ---
NOMBRES = ["Juan", "Maria", "Pedro", "Luisa", "Carlos", "Ana", "Jose", "Sofia", "Miguel", "Lucia"]
APELLIDOS = ["Perez", "Gomez", "Diaz", "Rodriguez", "Lopez", "Fernandez", "Garcia", "Martinez", "Sanchez", "Romero"]
ASEGURADORAS_LIST = ["Seguros Pichincha", "Chubb Seguros", "Mapfre Atlas", "Ecuatoriana de Suiza"]
TIPOS_SINIESTRO = ['accidente', 'enfermedad', 'hospitalizacion', 'fallecimiento']
ESTADOS_SINIESTRO = ['pendiente', 'aprobado', 'rechazado', 'pagado']

def fecha_random(dias_atras=365):
    """Retorna una fecha aleatoria dentro del último año"""
    return timezone.now() - timedelta(days=random.randint(0, dias_atras))

def limpiar_base_datos():
    print("🧹 Limpiando datos antiguos...")
    Siniestro.objects.all().delete()
    Pago.objects.all().delete()
    Factura.objects.all().delete()
    Poliza.objects.all().delete()
    Aseguradora.objects.all().delete()
    # No borramos superusuarios para no bloquearte el acceso
    User.objects.filter(is_superuser=False).delete()

def crear_aseguradoras():
    print("🏢 Creando Aseguradoras...")
    objs = []
    for nombre in ASEGURADORAS_LIST:
        aseg = Aseguradora.objects.create(
            nombre=nombre,
            sitio_web=f"https://{nombre.lower().replace(' ', '')}.com",
            direccion="Av. Amazonas y Naciones Unidas",
            telefono=f"022{random.randint(100000, 999999)}",
            email=f"contacto@{nombre.lower().replace(' ', '')}.com",
            activa=True
        )
        objs.append(aseg)
    return objs

def crear_usuarios_y_polizas(aseguradoras):
    print("👥 Creando Estudiantes y Pólizas...")
    polizas_creadas = []
    
    for i in range(20): # Crearemos 20 estudiantes
        nombre = random.choice(NOMBRES)
        apellido = random.choice(APELLIDOS)
        username = f"{nombre.lower()}.{apellido.lower()}{i}"
        
        user = User.objects.create_user(username=username, password='password123', email=f"{username}@utpl.edu.ec")
        
        # Crear Póliza
        estado_poliza = random.choice(['activa', 'activa', 'activa', 'inactiva', 'suspendida']) # Más prob. de activa
        poliza = Poliza.objects.create(
            numero=f"POL-{random.randint(10000, 99999)}",
            usuario=user,
            aseguradora=random.choice(aseguradoras),
            tipo_estudiante=random.choice(['GRADO', 'POSTGRADO']),
            modalidad=random.choice(['PRESENCIAL', 'DISTANCIA']),
            estado=estado_poliza,
            monto_cobertura=random.choice([5000, 10000, 15000, 20000]),
            fecha_inicio=fecha_random(365),
            fecha_vencimiento=timezone.now() + timedelta(days=365)
        )
        polizas_creadas.append(poliza)
    return polizas_creadas

def crear_facturas_y_pagos(polizas):
    print("💰 Generando Facturas y Pagos...")
    for poliza in polizas:
        # Cada póliza tendrá entre 1 y 5 facturas
        for _ in range(random.randint(1, 5)):
            es_pagada = random.choice([True, True, False]) # 66% prob. de estar pagada
            fecha_emi = fecha_random(180)
            fecha_venc = fecha_emi + timedelta(days=30)
            monto = random.choice([50.00, 80.00, 120.50, 200.00])

            factura = Factura.objects.create(
                poliza=poliza,
                monto=monto,
                fecha_emision=fecha_emi,
                fecha_vencimiento=fecha_venc,
                pagada=es_pagada
            )

            if es_pagada:
                # Si está pagada, creamos el registro de pago
                Pago.objects.create(
                    factura=factura,
                    monto=monto,
                    fecha_pago=fecha_emi + timedelta(days=random.randint(0, 5)), # Pagó unos días después
                    metodo_pago=random.choice(['TRANSFERENCIA', 'TARJETA'])
                )

def crear_siniestros(polizas):
    print("🚑 Registrando Siniestros e Historial...")
    for poliza in polizas:
        # Solo algunas pólizas tienen siniestros (30% de probabilidad)
        if random.random() < 0.3:
            estado = random.choice(ESTADOS_SINIESTRO)
            fecha = fecha_random(200)
            
            Siniestro.objects.create(
                poliza=poliza,
                tipo=random.choice(TIPOS_SINIESTRO),
                descripcion="Descripción genérica del evento reportado por el estudiante.",
                fecha_evento=fecha,
                estado=estado,
                fecha_reporte=fecha + timedelta(days=1),
                nombre_beneficiario=f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)}",
                parentesco=random.choice(["Padre", "Madre", "Hermano/a"]),
                comentarios="Revisión automática del sistema."
            )

# --- EJECUCIÓN ---
if __name__ == '__main__':
    try:
        limpiar_base_datos()
        lista_aseguradoras = crear_aseguradoras()
        lista_polizas = crear_usuarios_y_polizas(lista_aseguradoras)
        crear_facturas_y_pagos(lista_polizas)
        crear_siniestros(lista_polizas)
        print("\n✅ ¡ÉXITO! Base de datos poblada correctamente.")
        print("   - Usuarios creados: 20 (password: 'password123')")
        print("   - Aseguradoras: 4")
        print("   - Datos financieros y siniestros generados aleatoriamente.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("Asegúrate de haber ejecutado las migraciones primero: python manage.py migrate")