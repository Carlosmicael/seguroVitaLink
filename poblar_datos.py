import os
from decimal import Decimal
from datetime import timedelta

import django
from django.utils import timezone


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


from django.contrib.auth.models import User  # noqa: E402
from core.models import (  # noqa: E402
    Aseguradora,
    Estudiante,
    Poliza,
    Siniestro,
    Profile,
    Solicitud,
    Beneficiario,
    DocumentosAseguradora,
    TcasDocumentos,
)


def create_user_with_role(username, email, password, role):
    user, created = User.objects.get_or_create(username=username, defaults={"email": email})
    if created:
        user.set_password(password)
        user.save()
    profile, _ = Profile.objects.get_or_create(user=user, defaults={"rol": role})
    if profile.rol != role:
        profile.rol = role
        profile.save()
    return user, created


def clear_data():
    TcasDocumentos.objects.all().delete()
    Beneficiario.objects.all().delete()
    Siniestro.objects.all().delete()
    Poliza.objects.all().delete()
    Solicitud.objects.all().delete()
    DocumentosAseguradora.objects.all().delete()
    Estudiante.objects.all().delete()
    Aseguradora.objects.all().delete()
    Profile.objects.all().delete()
    User.objects.filter(is_superuser=False).delete()


def seed():
    suffix = timezone.now().strftime("%y%m%d%H%M")
    password = "123"
    clear_data()

    asesor_user, asesor_created = create_user_with_role(
        "asesor", "asesor@example.com", password, "asesor"
    )
    solicitante_user, solicitante_created = create_user_with_role(
        "solicitante", "solicitante@example.com", password, "solicitante"
    )
    beneficiario_user, beneficiario_created = create_user_with_role(
        "beneficiario", "beneficiario@example.com", password, "beneficiario"
    )

    aseguradoras = [
        Aseguradora.objects.create(
            nombre="Andes Seguros",
            direccion="Av. Central 123",
            telefono="0991234567",
        ),
        Aseguradora.objects.create(
            nombre="Pacifico Vida",
            direccion="Calle 10 y Loja",
            telefono="0987654321",
        ),
    ]

    estudiantes_data = [
        ("Juan", "Perez", "0101010101", "UTPL0001", "juan.perez@example.com"),
        ("Maria", "Lopez", "0202020202", "UTPL0002", "maria.lopez@example.com"),
        ("Carlos", "Mena", "0303030303", "UTPL0003", "carlos.mena@example.com"),
        ("Ana", "Vera", "0404040404", "UTPL0004", "ana.vera@example.com"),
        ("Luis", "Soto", "0505050505", "UTPL0005", "luis.soto@example.com"),
        ("Diana", "Rios", "0606060606", "UTPL0006", "diana.rios@example.com"),
    ]
    estudiantes = []
    for i, (nombres, apellidos, cedula, codigo, email) in enumerate(estudiantes_data):
        estudiante = Estudiante.objects.create(
            nombres=nombres,
            apellidos=apellidos,
            cedula=cedula,
            codigo_estudiante=codigo,
            email=email,
            estado="activo",
            tipo_estudio="presencial" if i % 2 == 0 else "distancia",
            carrera="Ingenieria de Software",
            nivel="7mo",
            telefono=f"09870000{i + 1}",
            fecha_ingreso=timezone.now().date() - timedelta(days=365 + i * 7),
        )
        estudiantes.append(estudiante)

    polizas = []
    for i, estudiante in enumerate(estudiantes):
        aseguradora = aseguradoras[i % len(aseguradoras)]
        estado = "activa" if i % 3 != 0 else "pendiente"
        poliza = Poliza.objects.create(
            estudiante=estudiante,
            aseguradora=aseguradora,
            numero_poliza=f"POL-{suffix}-{i + 1:03d}",
            numero=f"NUM-{suffix}-{i + 1:03d}",
            estado=estado,
            monto_cobertura=Decimal("10000.00"),
            tipo_cobertura="basica" if i % 2 == 0 else "ampliada",
            fecha_inicio=timezone.now().date() - timedelta(days=30 + i * 3),
            fecha_fin=timezone.now() + timedelta(days=365 + i * 7),
            prima_neta=Decimal("25.00"),
        )
        polizas.append(poliza)

    siniestros = []
    estados_siniestro = ["pendiente", "aprobado", "pagado"]
    tipos_siniestro = ["accidente", "enfermedad", "hospitalizacion"]
    for i, poliza in enumerate(polizas):
        for j in range(2):
            estado = estados_siniestro[(i + j) % len(estados_siniestro)]
            siniestro = Siniestro.objects.create(
                poliza=poliza,
                tipo=tipos_siniestro[(i + j) % len(tipos_siniestro)],
                descripcion=f"Siniestro generado {i + 1}-{j + 1}",
                fecha_evento=timezone.now().date() - timedelta(days=10 + j),
                estado=estado,
                nombre_beneficiario=f"Beneficiario {i + 1}",
                relacion_beneficiario="Familiar",
                telefono_contacto=f"09880000{i + 1}",
                email_contacto=f"beneficiario{i + 1}_{suffix}@example.com",
            )
            siniestros.append(siniestro)

    start_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    for siniestro in siniestros:
        if siniestro.estado == "pagado":
            Siniestro.objects.filter(pk=siniestro.pk).update(
                fecha_actualizacion=start_month + timedelta(days=2)
            )

    beneficiario_profile = Profile.objects.get(user=beneficiario_user)
    for i, siniestro in enumerate(siniestros):
        Beneficiario.objects.create(
            siniestro=siniestro,
            nombre=f"Beneficiario {i + 1}",
            correo=f"beneficiario{i + 1}@example.com",
            numero_cuenta=f"001-000{i + 1:03d}",
            telefono=f"09950000{i + 1}",
            profile=beneficiario_profile,
        )

    solicitante_profile = Profile.objects.get(user=solicitante_user)
    for i, estudiante in enumerate(estudiantes[:4]):
        Solicitud.objects.create(
            estudiante=estudiante,
            profile=solicitante_profile,
            estado="pendiente",
            tipo_poliza="Basica",
            monto_solicitado=Decimal("2500.00"),
            motivo="Solicitud de prueba",
            documento_identidad=estudiante.cedula,
            telefono=f"09770000{i + 1}",
            direccion=f"Direccion solicitante {i + 1}",
        )

    for aseguradora in aseguradoras:
        for tipo in tipos_siniestro:
            DocumentosAseguradora.objects.create(
                aseguradora=aseguradora,
                siniestro_tipo=tipo,
                nombre_documento=f"Documento {tipo}",
                descripcion="Documento requerido",
                obligatorio=True,
            )

    for i in range(3):
        TcasDocumentos.objects.create(
            doc_descripcion=f"Documento de prueba {i + 1}",
        )

    print("Seed completo.")
    print(f"Usuario asesor: {asesor_user.username}")
    print(f"Usuario solicitante: {solicitante_user.username}")
    print(f"Usuario beneficiario: {beneficiario_user.username}")
    print(f"Password para los usuarios creados: {password}")
    print(f"Polizas creadas: {len(polizas)}")
    print(f"Siniestros creados: {len(siniestros)}")


if __name__ == "__main__":
    seed()
