

from django.contrib.auth.decorators import login_required
from core.decorators import role_required
from django.shortcuts import render
from core.models import Solicitud
from django.contrib import messages

@login_required(login_url='login')
@role_required(['aseguradora'])
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