from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from orbat.views import orbat_visual, transferir_personal, escuadras_dashboard
from orbat.audit_views import audit_log_list, audit_log_detail
from orbat.user_management_views import (
    user_list,
    user_create,
    user_edit,
    user_delete,
    user_toggle_superuser,
    user_toggle_active,
)

urlpatterns = [
    # Redirige la raíz del sitio al panel de admin
    path('', lambda request: redirect('/admin/')),
    path('admin/auditoria/', audit_log_list, name='audit_log_list'),
    path('admin/auditoria/<int:entry_id>/', audit_log_detail, name='audit_log_detail'),
    # Gestión de usuarios (solo CREADOR_ERP)
    path('admin/usuarios/', user_list, name='user_management_list'),
    path('admin/usuarios/crear/', user_create, name='user_management_create'),
    path('admin/usuarios/<int:user_id>/editar/', user_edit, name='user_management_edit'),
    path('admin/usuarios/<int:user_id>/eliminar/', user_delete, name='user_management_delete'),
    path('admin/usuarios/<int:user_id>/toggle-super/', user_toggle_superuser, name='user_management_toggle_super'),
    path('admin/usuarios/<int:user_id>/toggle-activo/', user_toggle_active, name='user_management_toggle_active'),
    # Ruta legacy redirige a la nueva (requiere staff)
    path('admin/user-tools/', lambda request: redirect('/admin/usuarios/') if request.user.is_authenticated and request.user.is_staff else redirect('/admin/login/?next=/admin/usuarios/'), name='admin_user_tools'),
    path('admin/', admin.site.urls),
    path('orbat/', orbat_visual, name='orbat_visual'),
    path('orbat/board/', escuadras_dashboard, name='escuadras_dashboard'),
    path('api/transferir_personal/', transferir_personal, name='transferir_personal'),
]