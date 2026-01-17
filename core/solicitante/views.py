import email
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from core.decorators import role_required
from django.contrib.auth.decorators import login_required
from core.forms import SolicitudForm
from core.models import Solicitud, Estudiante


@login_required(login_url='login')
@role_required(['solicitante'])
def solicitante_dashboard(request):
    return render(request, 'solicitante/components/dashboard/dashboard.html')





@login_required(login_url='login')
@role_required(['solicitante'])
def lista_solicitudes(request):
    try:
        profile = request.user.profile 
        solicitudes = Solicitud.objects.filter(profile=profile) 
    except Estudiante.DoesNotExist:
        solicitudes = []
        messages.warning(request, 'No se encontró un perfil de estudiante asociado.')
    
    return render(request, 'solicitante/components/solicitudes/lista_solicitudes.html', {
        'solicitudes': solicitudes
    })







@login_required(login_url='login')
@role_required(['solicitante'])
def crear_solicitud(request):
    estudiantes = Estudiante.objects.all()
    profile = request.user.profile

    if request.method == 'POST':
        form = SolicitudForm(request.POST)

        if form.is_valid():
            solicitud = form.save(commit=False)

            solicitud.profile = profile
            solicitud.estudiante = form.cleaned_data['estudiante']

            solicitud.save()

            return JsonResponse({'success': True})
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })

    return render(request,'solicitante/components/solicitudes/crear_solicitud.html',{'estudiantes': estudiantes})








@login_required(login_url='login')
@role_required(['solicitante'])
def detalle_solicitud(request, solicitud_id):
    try:
        estudiante = Estudiante.objects.get(email=request.user.email)
        solicitud = get_object_or_404(Solicitud, id=solicitud_id, estudiante=estudiante)
    except Estudiante.DoesNotExist:
        messages.error(request, 'No autorizado.')
        return redirect('lista_solicitudes')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'id': solicitud.id,
            'tipo_poliza': solicitud.tipo_poliza,
            'monto_solicitado': str(solicitud.monto_solicitado),
            'motivo': solicitud.motivo,
            'documento_identidad': solicitud.documento_identidad,
            'telefono': solicitud.telefono,
            'direccion': solicitud.direccion,
            'estado': solicitud.get_estado_display(),
            'fecha_solicitud': solicitud.fecha_solicitud.strftime('%d/%m/%Y %H:%M'),
            'estudiante_nombre': f"{solicitud.estudiante.nombres} {solicitud.estudiante.apellidos}",
            'estudiante_cedula': solicitud.estudiante.cedula,
            'estudiante_correo': solicitud.estudiante.email,
        }
        return JsonResponse(data)
    
    return render(request, 'solicitante/components/solicitudes/detalle_solicitud.html', {
        'solicitud': solicitud
    })