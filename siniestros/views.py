from django.shortcuts import render
from django.views.generic import TemplateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.utils import timezone
from .models import Poliza, Siniestro, Factura, Pago
from django.db.models.functions import TruncMonth
import json
import openpyxl 
from django.http import HttpResponse
from .forms import SiniestroForm
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required




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
    
@login_required(login_url='/admin/login/') # <--- 2. Proteger la vista
def reportar_siniestro(request):
    # 3. BUSCAR LA PÓLIZA DEL USUARIO CONECTADO
    # Filtramos por el usuario que hace la petición (request.user)
    poliza = Poliza.objects.filter(usuario=request.user).first()
    
    # 4. VALIDACIÓN DE ACCESO
    # Si el usuario no tiene póliza (ej. es el Admin o un usuario nuevo sin datos)
    if not poliza:
        messages.error(request, "No tienes una póliza registrada para reportar siniestros.")
        # Lo mandamos al admin o al home para que no vea un error feo
        return redirect('admin:index') 

    if request.method == 'POST':
        form = SiniestroForm(request.POST)
        # Asignamos la póliza encontrada (la del usuario) al formulario
        form.instance.poliza = poliza 
        
        if form.is_valid():
            siniestro = form.save(commit=False)
            siniestro.poliza = poliza
            siniestro.estado = 'pendiente'
            siniestro.save()
            messages.success(request, f'Siniestro reportado a {poliza.aseguradora.nombre} correctamente.')
            return redirect('admin:index') # O redirige a una lista de siniestros si tienes
    else:
        form = SiniestroForm()

    return render(request, 'siniestros/form_reportar.html', {
        'form': form, 
        'poliza': poliza
    })