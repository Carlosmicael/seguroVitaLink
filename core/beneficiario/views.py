from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.decorators import role_required
from core.models import Beneficiario, Siniestro, Poliza, Aseguradora, DocumentosAseguradora, TcasDocumentos,Profile,Notificaciones
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime

@login_required(login_url='login')
@role_required(['beneficiario'])
def beneficiario_dashboard(request):
    return render(request, 'beneficiario/components/dashboard/dashboard.html')







@login_required
def mis_siniestros_view(request):
    user = request.user
    profile = getattr(user, 'profile', None) 

    beneficiarios = Beneficiario.objects.filter(profile=profile)

    siniestros_list = []
    for ben in beneficiarios:
        siniestros = Siniestro.objects.filter(beneficiarios=ben) 
        for s in siniestros:
            siniestros_list.append({
                "id": s.id,
                "tipo": s.tipo,
                "descripcion": s.descripcion,
                "estado": s.estado,
                "fecha_evento": s.fecha_evento,
                "fecha_reporte": s.fecha_reporte,
                "beneficiario_id": ben.id_beneficiario,
                "beneficiario_nombre": ben.nombre,
                "poliza_numero": s.poliza.numero_poliza if s.poliza else "Sin póliza",
            })

    context = {"siniestros": siniestros_list}

    return render(request, "beneficiario/components/documentos/mis_siniestros.html", context)

















def documentos_aseguradora_api(request, poliza_numero):
    print("=== POLIZA NUMERO ===")
    print(poliza_numero)
    print("=== FIN POLIZA NUMERO ===")
    try:
        perfil = request.user.profile
        beneficiario = perfil.beneficiarios.first()
        if not beneficiario:
            return JsonResponse({'error': 'No se encontró perfil de beneficiario'}, status=403)
        
        siniestro = beneficiario.siniestro
        tipo_siniestro_beneficiario = siniestro.tipo
        aseguradora = siniestro.poliza.aseguradora

        docs_queryset = DocumentosAseguradora.objects.filter(aseguradora=aseguradora,siniestro_tipo=tipo_siniestro_beneficiario,activo=True).order_by('dias_max_entrega')
        fechas_limite = beneficiario.fechas_limite or []
        fecha_hoy = timezone.now().date()
        data = []

        for doc, fecha_str in zip(docs_queryset, fechas_limite):

            fecha_limite_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()

            if fecha_hoy < fecha_limite_obj:
                data.append({
                    "siniestro_tipo": doc.siniestro_tipo,
                    "nombre_documento": doc.nombre_documento,
                    "descripcion": doc.descripcion,
                    "obligatorio": doc.obligatorio,
                    "fecha_version": doc.fecha_version,
                    "fecha_vencimiento": fecha_str
                })

        return JsonResponse(data, safe=False)

    except Poliza.DoesNotExist:
        return JsonResponse([], safe=False)










@login_required(login_url='login')
@csrf_exempt  
def subir_documento(request):

    if request.method == 'POST':
        try:
            descripcion = request.POST.get('doc_descripcion')
            archivo = request.FILES.get('archivo')
            beneficiario_id = request.POST.get('beneficiario_id')

            if not descripcion or not archivo or not beneficiario_id:
                return JsonResponse({'error': 'Faltan datos obligatorios.'}, status=400)

            beneficiario = Beneficiario.objects.get(id_beneficiario=beneficiario_id)

            documentos = TcasDocumentos.objects.create(
                doc_descripcion=descripcion,
                doc_file=archivo,
                fecha_edit=timezone.now(),
                beneficiario=beneficiario
            )
            documentos.save()

            return JsonResponse({'success': True, 'mensaje': 'Documento subido correctamente!'})

        except Beneficiario.DoesNotExist:
            return JsonResponse({'error': 'Beneficiario no encontrado.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)














































from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from core.decorators import role_required
import json
import pusher
from django.conf import settings
from django.contrib.auth.models import User

# Cliente Pusher
pusher_client = pusher.Pusher(app_id=settings.PUSHER_APP_ID,key=settings.PUSHER_KEY,secret=settings.PUSHER_SECRET,cluster=settings.PUSHER_CLUSTER,ssl=True)




@login_required(login_url='/login')
@role_required(['beneficiario'])
@csrf_exempt
def enviar_mensaje_beneficiario(request):
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            
            if len(message) == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'El mensaje no puede estar vacío'
                }, status=400)
            
            if len(message) > 200:
                return JsonResponse({
                    'status': 'error',
                    'message': 'El mensaje no puede superar los 200 caracteres'
                }, status=400)
      
            profile = request.user.profile
            beneficiario = profile.beneficiarios.first()
            
            if not beneficiario:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No se encontró el perfil de beneficiario'
                }, status=404)
            
            
            try:
                siniestro = beneficiario.siniestro
                asesor = siniestro.revisado_por
                channel_name = f"private-user-{asesor.id}"
                print(f"Enviando mensaje a channel: {channel_name}")
                    
                pusher_client.trigger(channel_name, 'chat-message', 
                    {'message': message,'from_user_id': request.user.id,'from_user_name': f"{request.user.first_name} {request.user.last_name}",'timestamp': str(timezone.now()),'beneficiario_id': beneficiario.id_beneficiario,}
                )

            except Exception as e:
                print(f"Error al obtener asesor: {e}")
                return JsonResponse({
                    'status': 'error',
                    'message': 'No se pudo encontrar el asesor asignado'
                }, status=404)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Mensaje enviado correctamente'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Formato de datos inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error al enviar mensaje: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)







@csrf_exempt
@login_required(login_url='/login')
@role_required(['beneficiario'])
def pusher_auth(request):
    print("Llegó a pusher_auth beneficiario!")
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
@role_required(['beneficiario'])
def trigger_event(request, user_id):
    channel_name = f"private-user-{user_id}"
    pusher_client.trigger(channel_name, 'my-event', {'message': f'Hola, usuario {user_id}! Tienes una nueva notificación.'})
    return JsonResponse({'status': 'Evento enviado correctamente'})




@login_required(login_url='login')
@role_required(['beneficiario'])
def obtener_notificaciones_usuario(request, user_id):
    profile = Profile.objects.get(user=user_id)
    print(profile)
    mensajes = Notificaciones.objects.filter(not_codcli=profile).order_by('-not_fecha_creacion').values('not_id', 'not_poliza', 'not_fecha_proceso', 'not_estado', 'not_mensaje', 'not_fecha_creacion', 'not_read')
    print(mensajes)
    return JsonResponse(list(mensajes), safe=False)



@login_required(login_url='login')
@role_required(['beneficiario'])
def marcar_notificaciones_leidas(request, user_id):
    profile = Profile.objects.get(user=user_id)
    Notificaciones.objects.filter(not_codcli=profile, not_read=True).update(not_read=False)
    return JsonResponse({'status': 'ok'})



