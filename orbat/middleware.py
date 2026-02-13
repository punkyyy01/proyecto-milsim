from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class BlockAdminCredentialChangesMiddleware:
    """Bloquea cambios de credenciales desde el admin para cualquier usuario autenticado."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            admin_password_change_path = reverse('admin:password_change')
            admin_password_change_done_path = reverse('admin:password_change_done')
            if request.path in {admin_password_change_path, admin_password_change_done_path}:
                messages.error(request, 'El cambio de contraseña desde esta interfaz está deshabilitado.')
                return redirect('admin:index')

        return self.get_response(request)
