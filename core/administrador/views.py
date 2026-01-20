from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from core.decorators import role_required
from core.models import Aseguradora, PoliticaAseguradora
from core.forms import AseguradoraForm, PoliticaAseguradoraForm


@login_required(login_url='login')
@role_required(['administrador'])
def aseguradoras_list(request):
    aseguradoras = Aseguradora.objects.all().order_by('-fecha_creacion')
    return render(
        request,
        'administrador/components/aseguradoras/lista_aseguradoras.html',
        {'aseguradoras': aseguradoras},
    )


@login_required(login_url='login')
@role_required(['administrador'])
def aseguradora_create(request):
    if request.method == 'POST':
        form = AseguradoraForm(request.POST)
        if form.is_valid():
            aseguradora = form.save(commit=False)
            if not aseguradora.is_active:
                aseguradora.fecha_inactivacion = timezone.now()
            aseguradora.save()
            messages.success(request, 'Aseguradora creada correctamente.')
            return redirect('aseguradoras_list')
    else:
        form = AseguradoraForm()

    return render(
        request,
        'administrador/components/aseguradoras/form_aseguradora.html',
        {'form': form, 'modo': 'crear'},
    )


@login_required(login_url='login')
@role_required(['administrador'])
def aseguradora_edit(request, aseguradora_id):
    aseguradora = get_object_or_404(Aseguradora, pk=aseguradora_id)

    if request.method == 'POST':
        form = AseguradoraForm(request.POST, instance=aseguradora)
        if form.is_valid():
            aseguradora = form.save(commit=False)
            if aseguradora.is_active:
                aseguradora.fecha_inactivacion = None
            else:
                if aseguradora.fecha_inactivacion is None:
                    aseguradora.fecha_inactivacion = timezone.now()
            aseguradora.save()
            messages.success(request, 'Aseguradora actualizada correctamente.')
            return redirect('aseguradoras_list')
    else:
        form = AseguradoraForm(instance=aseguradora)

    return render(
        request,
        'administrador/components/aseguradoras/form_aseguradora.html',
        {'form': form, 'modo': 'editar', 'aseguradora': aseguradora},
    )


@login_required(login_url='login')
@role_required(['administrador'])
def aseguradora_toggle(request, aseguradora_id):
    aseguradora = get_object_or_404(Aseguradora, pk=aseguradora_id)
    aseguradora.is_active = not aseguradora.is_active
    aseguradora.fecha_inactivacion = None if aseguradora.is_active else timezone.now()
    aseguradora.save(update_fields=['is_active', 'fecha_inactivacion'])
    return redirect('aseguradoras_list')


@login_required(login_url='login')
@role_required(['administrador'])
def politicas_list(request, aseguradora_id):
    aseguradora = get_object_or_404(Aseguradora, pk=aseguradora_id)
    politicas = aseguradora.politicas_versiones.all()
    return render(
        request,
        'administrador/components/politicas/lista_politicas.html',
        {
            'aseguradora': aseguradora,
            'politicas': politicas,
        },
    )


@login_required(login_url='login')
@role_required(['administrador'])
def politica_create(request, aseguradora_id):
    aseguradora = get_object_or_404(Aseguradora, pk=aseguradora_id)
    if request.method == 'POST':
        form = PoliticaAseguradoraForm(request.POST, request.FILES)
        if form.is_valid():
            politica = form.save(commit=False)
            politica.aseguradora = aseguradora
            politica.save()
            messages.success(request, 'Politica registrada correctamente.')
            return redirect('politicas_list', aseguradora_id=aseguradora.id_aseguradora)
    else:
        form = PoliticaAseguradoraForm()

    return render(
        request,
        'administrador/components/politicas/form_politica.html',
        {'form': form, 'aseguradora': aseguradora, 'modo': 'crear'},
    )


@login_required(login_url='login')
@role_required(['administrador'])
def politica_edit(request, politica_id):
    politica = get_object_or_404(PoliticaAseguradora, pk=politica_id)
    if request.method == 'POST':
        form = PoliticaAseguradoraForm(request.POST, request.FILES, instance=politica)
        if form.is_valid():
            form.save()
            messages.success(request, 'Politica actualizada correctamente.')
            return redirect('politicas_list', aseguradora_id=politica.aseguradora.id_aseguradora)
    else:
        form = PoliticaAseguradoraForm(instance=politica)

    return render(
        request,
        'administrador/components/politicas/form_politica.html',
        {'form': form, 'aseguradora': politica.aseguradora, 'modo': 'editar'},
    )


@login_required(login_url='login')
@role_required(['administrador'])
def politicas_publicas_admin(request):
    aseguradoras = Aseguradora.objects.filter(is_active=True).order_by('nombre')
    return render(
        request,
        'administrador/components/publico/terminos_aseguradoras.html',
        {'aseguradoras': aseguradoras},
    )


@login_required(login_url='login')
@role_required(['administrador'])
def politica_publica_detalle_admin(request, aseguradora_id):
    aseguradora = get_object_or_404(Aseguradora, pk=aseguradora_id)
    politica = aseguradora.politicas_versiones.order_by('-fecha_version').first()
    return render(
        request,
        'administrador/components/publico/terminos_aseguradora_detalle.html',
        {'aseguradora': aseguradora, 'politica': politica},
    )


def politicas_publicas(request):
    aseguradoras = Aseguradora.objects.filter(is_active=True).order_by('nombre')
    return render(
        request,
        'public/terminos_aseguradoras.html',
        {'aseguradoras': aseguradoras},
    )


def politica_publica_detalle(request, aseguradora_id):
    aseguradora = get_object_or_404(Aseguradora, pk=aseguradora_id)
    politica = aseguradora.politicas_versiones.order_by('-fecha_version').first()
    return render(
        request,
        'public/terminos_aseguradora_detalle.html',
        {'aseguradora': aseguradora, 'politica': politica},
    )
