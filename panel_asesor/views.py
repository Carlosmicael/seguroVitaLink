from django.shortcuts import render, redirect
from dateutil.relativedelta import relativedelta
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404


from .models import Beneficiario, Estudiante
from .forms import BeneficiarioForm, EstudianteForm, ImportarEstudiantesForm, BeneficiarioEditForm
from .utils import generar_usuario, generar_password
from login.models import Profile
from datetime import datetime, date


@login_required(login_url='login')
def inicio_asesor(request):
    beneficiarios = Beneficiario.objects.select_related('profile__user')
    return render(
        request,
        'components/AscesorBeneficiario/listado.html',
        {'beneficiarios': beneficiarios}
    )


@login_required(login_url='login')
def registrar_beneficiario(request):
    credenciales = None

    if request.method == 'POST':
        form = BeneficiarioForm(request.POST)

        if form.is_valid():
            with transaction.atomic():

                beneficiario = form.save(commit=False)

                # Datos del usuario
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                email = request.POST.get('email')

                # Credenciales
                username = generar_usuario(first_name, last_name)
                password_plano = generar_password()

                # Crear USER
                user = User.objects.create_user(
                    username=username,
                    password=password_plano,
                    first_name=first_name,
                    last_name=last_name,
                    email=email
                )

                # Crear PROFILE
                profile = Profile.objects.create(
                    user=user,
                    rol='BENEFICIARIO'
                )

                # Relacionar beneficiario
                beneficiario.profile = profile
                beneficiario.save()

                credenciales = {
                    'usuario': username,
                    'password': password_plano
                }

                return render(
                    request,
                    'components/AscesorBeneficiario/confirmacion.html',
                    {
                        'beneficiario': beneficiario,
                        'credenciales': credenciales
                    }
                )
    else:
        form = BeneficiarioForm()

    return render(
        request,
        'components/AscesorBeneficiario/registrar.html',
        {'form': form}
    )

@login_required
def editar_beneficiario(request, beneficiario_id):
    beneficiario = get_object_or_404(Beneficiario, id=beneficiario_id)
    user = beneficiario.profile.user

    # Limpiar credenciales temporales al iniciar GET (no POST)
    if request.method == 'GET' and 'nuevas_credenciales' in request.session:
        del request.session['nuevas_credenciales']
        nuevas_credenciales = None
    else:
        nuevas_credenciales = request.session.get('nuevas_credenciales', None)

    if request.method == 'POST':
        form = BeneficiarioEditForm(request.POST, instance=beneficiario)

        generar_nuevas = request.POST.get('generar_nuevas', None)

        if generar_nuevas:
            # Generar nueva contraseña sin cambiar el usuario
            nuevas_credenciales = {
                'usuario': user.username,  # usuario no cambia
                'password': generar_password()
            }
            request.session['nuevas_credenciales'] = nuevas_credenciales

        elif form.is_valid():
            # Guardar cambios del Beneficiario
            form.save()
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.email = request.POST.get('email')

            # Aplicar nueva contraseña si fue generada
            if nuevas_credenciales:
                user.set_password(nuevas_credenciales['password'])
                del request.session['nuevas_credenciales']  # limpiar sesión

            user.save()
            messages.success(request, "Beneficiario actualizado correctamente")
            return redirect('panel_asesor:inicio')

    else:
        # Inicializar formulario con datos del usuario
        initial = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'username': user.username
        }
        form = BeneficiarioEditForm(instance=beneficiario, initial=initial)

    return render(request, 'components/AscesorBeneficiario/editarBeneficiario.html', {
        'form': form,
        'beneficiario': beneficiario,
        'nuevas_credenciales': nuevas_credenciales
    })


@login_required
@require_POST
def eliminar_beneficiario(request, beneficiario_id):
    beneficiario = get_object_or_404(Beneficiario, id=beneficiario_id)
    beneficiario.delete()
    messages.success(request, "Beneficiario eliminado correctamente")
    return redirect('panel_asesor:inicio')


@login_required
def registrar_estudiante(request):
    if request.method == 'POST':
        form = EstudianteForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Estudiante registrado correctamente.'
            )

            return redirect('panel_asesor:listar_estudiantes')
    else:
        form = EstudianteForm()

    return render(
        request,
        'components/AscesorBeneficiario/gestionEstudiante/gestionCrearEstudiante.html',
        {'form': form}
    )

@login_required
def listar_estudiantes(request):
    estudiantes = Estudiante.objects.all().order_by('-fecha_creacion')
    paginator = Paginator(estudiantes, 10)
    page_number = request.GET.get('page')
    estudiantes_page = paginator.get_page(page_number)

    return render(
        request,
        'components/AscesorBeneficiario/gestionEstudiante/gestionEstudiantes.html',
        {'estudiantes': estudiantes_page}
    )

@login_required
def buscar_estudiantes(request):
    q = request.GET.get('q', '').strip()

    estudiantes = Estudiante.objects.filter(
        Q(cedula__icontains=q) |
        Q(nombres__icontains=q) |
        Q(apellidos__icontains=q)
    ).select_related('poliza')

    data = []
    for e in estudiantes:
        if e.estado == 'fallecido' and e.fecha_defuncion:
            delta = relativedelta(date.today(), e.fecha_defuncion)
            tiempo = f"{delta.months} meses {delta.days} días"
        else:
            tiempo = '-'

        poliza_estado = e.poliza.get_estado_display() if hasattr(e, 'poliza') and e.poliza else 'Sin póliza'

        data.append({
            'id': e.id,
            'cedula': e.cedula,
            'nombres': e.nombres,
            'apellidos': e.apellidos,
            'carrera': e.carrera,
            'nivel': e.get_nivel_display(),
            'modalidad': e.get_modalidad_display(),
            'periodo': e.periodo_academico,
            'estado': e.estado,
            'fecha_defuncion': e.fecha_defuncion.isoformat() if e.fecha_defuncion else '',
            'dias_transcurridos': tiempo,
            'poliza': poliza_estado,
        })

    return JsonResponse(data, safe=False)
@login_required
@require_POST
def cambiar_estado_estudiante(request):
    estudiante_id = request.POST.get('id')
    nuevo_estado = request.POST.get('estado')
    fecha_defuncion = request.POST.get('fecha_defuncion')

    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    estudiante.estado = nuevo_estado

    if nuevo_estado == 'fallecido':
        if not fecha_defuncion:
            return JsonResponse({
                'success': False,
                'error': 'Fecha de defunción obligatoria'
            })

        fecha_def = date.fromisoformat(fecha_defuncion)
        hoy = date.today()

        delta = relativedelta(hoy, fecha_def)

        estudiante.fecha_defuncion = fecha_def
        estudiante.tiempo_transcurrido = f"{delta.months} meses {delta.days} días"

    else:
        estudiante.fecha_defuncion = None
        estudiante.tiempo_transcurrido = None

    estudiante.save()

    return JsonResponse({'success': True})

@login_required
def editar_estudiante(request, estudiante_id):
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)

    if request.method == 'POST':
        form = EstudianteForm(request.POST, instance=estudiante)

        if form.is_valid():
            form.save()
            messages.success(request, 'Estudiante actualizado correctamente.')
            return redirect('panel_asesor:listar_estudiantes')
    else:
        form = EstudianteForm(instance=estudiante)

    return render(
        request,
        'components/AscesorBeneficiario/gestionEstudiante/gestionEditarEstudiante.html',
        {
            'form': form,
            'estudiante': estudiante
        }
    )

@login_required
@require_POST
def eliminar_estudiante(request):
    estudiante_id = request.POST.get('id')
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    estudiante.delete()
    return JsonResponse({'success': True})

@login_required
def listar_estudiantes(request):
    estudiantes = Estudiante.objects.all().select_related('poliza')

    # 🔹 Manejo de importación Excel en POST
    if request.method == 'POST' and 'archivo' in request.FILES:
        archivo = request.FILES['archivo']
        try:
            if archivo.name.endswith('.xlsx'):
                df = pd.read_excel(archivo)
            elif archivo.name.endswith('.csv'):
                df = pd.read_csv(archivo)
            else:
                messages.error(request, 'Formato no soportado. Usa .xlsx o .csv')
                return redirect('panel_asesor:listar_estudiantes')

            with transaction.atomic():
                for _, row in df.iterrows():
                    Estudiante.objects.create(
                        cedula=row['cedula'],
                        nombres=row['nombres'],
                        apellidos=row['apellidos'],
                        correo=row['correo'],
                        modalidad=row['modalidad'],
                        nivel=row['nivel'],
                        carrera=row['carrera'],
                        periodo_academico=row['periodo_academico']
                    )

            messages.success(request, 'Estudiantes importados correctamente')
            return redirect('panel_asesor:listar_estudiantes')

        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {e}')
            return redirect('panel_asesor:listar_estudiantes')

    return render(request, 'components/AscesorBeneficiario/gestionEstudiante/gestionEstudiantes.html', {
        'estudiantes': estudiantes,
    })