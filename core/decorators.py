from django.shortcuts import redirect
from functools import wraps

def role_required(allowed_roles=[]):

    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.profile.rol in allowed_roles:
                    return view_func(request, *args, **kwargs)
            return redirect('login')
        return wrapper
    return decorator

# Decorador para vistas que requieren que el usuario sea staff - RONAL

def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper
