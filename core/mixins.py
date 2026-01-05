from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy

class RoleRequiredMixin(AccessMixin):
    """
    Mixin to check if the user has a specific role.
    If the user is not authenticated, they are redirected to the login page.
    If the user does not have the required role, they are redirected to their respective dashboard.
    """
    required_role = None  # Must be 'admin' or 'asesor'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if self.required_role and request.user.rol != self.required_role:
            if request.user.rol == 'admin':
                return redirect(reverse_lazy('admin_dashboard'))
            elif request.user.rol == 'asesor':
                return redirect(reverse_lazy('asesor_dashboard'))
            else:
                # Default redirect if role is not admin or asesor
                return redirect(reverse_lazy('login')) # Assuming a 'login' URL exists
        return super().dispatch(request, *args, **kwargs)
