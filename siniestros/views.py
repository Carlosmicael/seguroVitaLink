from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.contrib import messages
import json
import openpyxl

# Importación de tus modelos y formularios
from .models import Poliza, Siniestro, Factura, Pago, DocumentoSiniestro
from .forms import SiniestroForm
from configuracion.models import RequisitoSiniestro





class SiniestrosInicioView(TemplateView):
    """Vista para la página de inicio de gestión de siniestros"""
    template_name = 'siniestros/siniestro_report.html' #activacion request reception page
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Gestión de Siniestros - VitaLink'
        return context

class DashboardAsesorView(LoginRequiredMixin, TemplateView):
    template_name = "siniestros/dashboard_asesor.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = timezone.now()
        
        context['total_polizas'] = Poliza.objects.filter(fecha_vencimiento__gte=hoy).count()
        context['siniestros_pendientes'] = Siniestro.objects.exclude(estado='CERRADO').count()
        context['facturas_pendientes'] = Factura.objects.filter(pagada=False).count()
        
        total_mes = Pago.objects.filter(fecha_pago__month=hoy.month, fecha_pago__year=hoy.year).aggregate(Sum('monto'))['monto__sum']
        context['dinero_mes'] = total_mes if total_mes else 0
        
        # 1. Agrupar pagos por mes
        pagos_historicos = Pago.objects.annotate(
            mes=TruncMonth('fecha_pago')
        ).values('mes').annotate(
            total=Sum('monto')
        ).order_by('mes')

        # 2. Crear listas puras de Python
        labels = []
        data = []

        for p in pagos_historicos:
            # Fechas a string
            labels.append(p['mes'].strftime("%b %Y"))
            
            # Montos: Validamos que no sea None y convertimos a float (JSON no entiende Decimal)
            monto = p['total'] if p['total'] else 0
            data.append(float(monto))

        # 3. SERIALIZAR A JSON
        # Convertimos las listas a Strings de texto formato JSON: '["Ene", "Feb"]'
        context['labels_grafico'] = json.dumps(labels) 
        context['data_grafico'] = json.dumps(data)
        
        return context
    
    
    # Exportar siniestros pendientes a Excel -------- #
    
def exportar_siniestros_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Siniestros Pendientes"

    headers = ["ID", "Póliza", "Descripción", "Fecha Evento", "Estado", "Monto Estimado"]
    ws.append(headers)

    siniestros = Siniestro.objects.exclude(estado='CERRADO')

    for s in siniestros:
        # CORREGIDO: Usamos 's.fecha_evento' aquí también
        fecha = s.fecha_evento.strftime("%d/%m/%Y") if s.fecha_evento else "Sin fecha"
        
        ws.append([
            s.id,
            str(s.poliza),
            s.descripcion,
            fecha,
            s.estado,
            s.monto_estimado
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Reporte_Siniestros.xlsx"'
    wb.save(response)
    
    return response

class SiniestroListView(LoginRequiredMixin, ListView):
    model = Siniestro
    template_name = "siniestros/siniestro_list.html"
    context_object_name = "siniestros"
    paginate_by = 10

    def get_queryset(self):
        # CORREGIDO: Usamos 'fecha_evento' en lugar de 'fecha_siniestro'
        return Siniestro.objects.all().order_by('-fecha_evento')

# GESTIÓN DE REPORTES DE SINIESTROS -------- #

@login_required(login_url='/admin/login/')
def reportar_siniestro(request):
    """
    Vista única y corregida para reportar siniestros.
    Maneja la carga de archivos (HU-048) y evita duplicados.
    """
    # 1. Verificar si el usuario tiene póliza
    poliza = Poliza.objects.filter(usuario=request.user).first()
    
    if not poliza:
        messages.error(request, "No tienes una póliza registrada.")
        return redirect('admin:index')

    # 2. Obtener requisitos para mostrar en la plantilla (HU-048)
    requisitos_configurados = RequisitoSiniestro.objects.filter(aseguradora=poliza.aseguradora)

    if request.method == 'POST':
        form = SiniestroForm(request.POST)
        
        if form.is_valid():
            # 3. Guardar el Siniestro primero
            siniestro = form.save(commit=False)
            siniestro.poliza = poliza
            siniestro.estado = 'pendiente'
            siniestro.save()
            
            # 4. Guardar los Archivos adjuntos
            # Iteramos sobre todos los archivos enviados en el formulario
            count_files = 0
            for key, file in request.FILES.items():
                DocumentoSiniestro.objects.create(
                    siniestro=siniestro,
                    nombre=key,  # El nombre del input en el HTML (ej: "Informe Policial")
                    archivo=file
                )
                count_files += 1

            # Mensaje de éxito
            if count_files > 0:
                messages.success(request, f'Siniestro reportado correctamente con {count_files} documento(s).')
            else:
                messages.success(request, 'Siniestro reportado correctamente.')
                
            return redirect('dashboard')  # O redirige a donde prefieras
    else:
        form = SiniestroForm()

    return render(request, 'siniestros/form_reportar.html', {
        'form': form,
        'poliza': poliza,
        'requisitos': requisitos_configurados
    })