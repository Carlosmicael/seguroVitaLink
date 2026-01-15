from django.shortcuts import render
from core.decorators import role_required
from core.models import Poliza, Estudiante, Profile, Notificaciones

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from core.forms import PolizaForm
from django.contrib.auth.decorators import login_required
from core.tasks import ejecutar_recordatorio
from django.utils.timezone import make_aware
from django.utils import timezone
import logging
from datetime import datetime
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
import pusher
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt



logger = logging.getLogger(__name__)






@login_required(login_url='login')
@role_required(['asesor'])
def asesor_dashboard(request):
    return render(request, 'asesor/components/dashboard/dashboard.html')




@login_required(login_url='login')
@role_required(['asesor'])
def lista_polizas(request):
    polizas = Poliza.objects.all()
    estudiantes = Estudiante.objects.all() 
    total = polizas.count()
    pendientes = polizas.filter(estado='pendiente').count()
    activas = polizas.filter(estado='activa').count()
    vencidas = polizas.filter(estado='vencida').count()
    canceladas = polizas.filter(estado='cancelada').count()
    
    dias_vencimiento = {}
    for poliza in polizas:
        dias_vencimiento[poliza.numero_poliza] = poliza.dias_para_vencimiento()
    
    context = {
        'polizas': polizas,
        'total': total,
        'pendientes': pendientes,
        'activas': activas,
        'vencidas': vencidas,
        'canceladas': canceladas,
        'dias_vencimiento': dias_vencimiento,  
        'estudiantes': estudiantes,
    }
    return render(request, 'asesor/components/polizas/lista_polizas.html', context)






@login_required(login_url='login')
@role_required(['asesor'])
@require_http_methods(["POST"])
def crear_poliza(request):
    try:
        data = request.POST
        form = PolizaForm(data)
        fecha_hora_str = request.POST.get('fecha_fin')
        
        if form.is_valid() and fecha_hora_str:

            print("Formulario válido")
            print("Fecha hora str:", fecha_hora_str)


            poliza = form.save(commit=False)
            poliza.fecha_fin = fecha_hora_str
            poliza.save()

            fecha_hora_naive = datetime.fromisoformat(fecha_hora_str)
            fecha_hora_aware = timezone.make_aware(fecha_hora_naive)
            print(f"Programando tarea para: {fecha_hora_aware}")
            task = ejecutar_recordatorio.apply_async(eta=fecha_hora_aware)
            profile = Profile.objects.get(user=request.user)


            recordatorio = Notificaciones.objects.create(
                not_codcli=profile,
                not_poliza=poliza,  
                not_fecha_proceso=fecha_hora_aware, 
                not_fecha_creacion=timezone.now(),
                not_mensaje=f"Recordatorio de vencimiento de póliza para {poliza.numero_poliza} su estado actual es {poliza.estado}",
                not_read=False,
                not_estado=False,
                not_celery_task_id=task.id,
            )

            recordatorio.save()
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False,'errors': form.errors}, status=400)
            
    except Exception as e:
        return JsonResponse({'success': False,'message': str(e)}, status=500)






pusher_client = pusher.Pusher(app_id=settings.PUSHER_APP_ID,key=settings.PUSHER_KEY,secret=settings.PUSHER_SECRET,cluster=settings.PUSHER_CLUSTER,ssl=True)



@login_required(login_url='/login')
@role_required(['asesor'])
@csrf_exempt
def pusher_auth(request):
    print("Llegó a pusher_auth!")
    if not request.user.is_authenticated:
        return HttpResponseForbidden()

    channel_name = request.POST.get('channel_name')
    socket_id = request.POST.get('socket_id')
    expected_channel = f"private-user-{request.user.id}"

    if channel_name != expected_channel:
        return HttpResponseForbidden("Canal no autorizado")
    
    auth = pusher_client.authenticate(channel=channel_name,socket_id=socket_id)
    return JsonResponse(auth)




@csrf_exempt
@login_required(login_url='/login')
@role_required(['asesor'])
def trigger_event(request, user_id):
    channel_name = f"private-user-{user_id}"
    pusher_client.trigger(channel_name, 'my-event', {'message': f'Hola, usuario {user_id}! Tienes una nueva notificación.'})
    return JsonResponse({'status': 'Evento enviado correctamente'})




@login_required(login_url='login')
@role_required(['asesor'])
def generar_numero_poliza(request):
    return JsonResponse({'numero_poliza': Poliza.generar_numero_poliza()})




@login_required(login_url='/login')
def obtener_notificaciones_usuario(request, user_id):
    profile = Profile.objects.get(user=user_id)
    mensajes = Notificaciones.objects.filter(not_codcli=profile).order_by('-not_fecha_creacion').values('not_id', 'not_poliza', 'not_fecha_proceso', 'not_estado', 'not_mensaje', 'not_fecha_creacion', 'not_read')
    return JsonResponse(list(mensajes), safe=False)



@login_required(login_url='/login')
def marcar_notificaciones_leidas(request, user_id):
    profile = Profile.objects.get(user=user_id)
    Notificaciones.objects.filter(not_codcli=profile, not_read=True).update(not_read=False)
    return JsonResponse({'status': 'ok'})





