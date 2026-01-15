from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('usuario')
        password = request.POST.get('contrasena')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            rol = user.profile.rol

            if rol == 'ADMIN':
                return redirect('siniestros:inicio')
            elif rol == 'ASEGURADORA':
                return redirect('siniestros:inicio')
            elif rol == 'BENEFICIARIO':
                return redirect('siniestros:inicio')
            elif rol == 'ASESOR':
                return redirect('panel_asesor:inicio')
        else:
            return render(request, 'components/login/login.html', {
                'error': 'Credenciales incorrectas'
            })

    return render(request, 'components/login/login.html')
