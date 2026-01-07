from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import ProtectedError
from .models import Aseguradora
from .forms import AseguradoraForm
from .forms import DocumentoPoliticaForm
from .models import DocumentoPolitica

# 1. LISTAR (Read)
def lista_aseguradoras(request):
    aseguradoras = Aseguradora.objects.all().order_by('nombre')
    return render(request, 'configuracion/lista_aseguradoras.html', {'aseguradoras': aseguradoras})

# 2. CREAR (Create)
def crear_aseguradora(request):
    if request.method == 'POST':
        form = AseguradoraForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aseguradora creada correctamente.')
            return redirect('lista_aseguradoras')
    else:
        form = AseguradoraForm()
    return render(request, 'configuracion/form_aseguradora.html', {'form': form, 'titulo': 'Nueva Aseguradora'})

# 3. EDITAR (Update)
def editar_aseguradora(request, id):
    aseguradora = get_object_or_404(Aseguradora, id=id)
    if request.method == 'POST':
        form = AseguradoraForm(request.POST, instance=aseguradora)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aseguradora actualizada correctamente.')
            return redirect('lista_aseguradoras')
    else:
        form = AseguradoraForm(instance=aseguradora)
    return render(request, 'configuracion/form_aseguradora.html', {'form': form, 'titulo': f'Editar {aseguradora.nombre}'})

# 4. ELIMINAR (Delete)
def eliminar_aseguradora(request, id):
    aseguradora = get_object_or_404(Aseguradora, id=id)
    
    try:
        # Intentamos borrar físicamente
        aseguradora.delete()
        messages.success(request, 'Aseguradora eliminada permanentemente.')
        
    except ProtectedError:
        # Si tiene pólizas vinculadas, NO la borramos, solo la desactivamos
        aseguradora.activa = False
        aseguradora.save()
        messages.warning(request, f'No se puede eliminar "{aseguradora.nombre}" porque tiene historial de pólizas. Se ha DESACTIVADO para mantener la integridad del sistema.')
        
    return redirect('lista_aseguradoras')


# --- VISTAS DE ADMIN PARA GESTIÓN DE DOCUMENTOS DE POLÍTICAS Y TÉRMINOS Y CONDICIONES ---

def gestionar_politicas(request):
    documentos = DocumentoPolitica.objects.all().order_by('-fecha_vigencia')
    return render(request, 'configuracion/lista_politicas.html', {'documentos': documentos})

def subir_politica(request):
    if request.method == 'POST':
        # Nota: request.FILES es OBLIGATORIO para subir archivos
        form = DocumentoPoliticaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Documento y políticas cargados exitosamente.')
            return redirect('gestionar_politicas')
    else:
        form = DocumentoPoliticaForm()
    return render(request, 'configuracion/form_politica.html', {'form': form})


# --- VISTA PÚBLICA DE TÉRMINOS Y CONDICIONES ---

def ver_terminos_publico(request, id_aseguradora):
    # Obtiene la aseguradora
    aseguradora = get_object_or_404(Aseguradora, id=id_aseguradora)
    
    # Busca el documento ACTIVO más reciente
    documento = DocumentoPolitica.objects.filter(
        aseguradora=aseguradora, 
        activo=True
    ).order_by('-fecha_vigencia').first()
    
    return render(request, 'configuracion/ver_terminos_publico.html', {
        'aseguradora': aseguradora,
        'documento': documento
    })