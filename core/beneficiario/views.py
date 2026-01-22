from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.decorators import role_required
from core.models import Beneficiario, Siniestro, Poliza, Aseguradora, DocumentosAseguradora, TcasDocumentos
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone


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
        poliza = Poliza.objects.get(numero_poliza=poliza_numero)
        aseguradora = poliza.aseguradora 
        docs = DocumentosAseguradora.objects.filter(aseguradora=aseguradora)
        data = [{
            "siniestro_tipo": d.siniestro_tipo,
            "nombre_documento": d.nombre_documento,
            "descripcion": d.descripcion,
            "obligatorio": d.obligatorio,
            "fecha_version": d.fecha_version
        } for d in docs]
        
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

