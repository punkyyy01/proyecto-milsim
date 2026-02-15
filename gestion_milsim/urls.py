from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from orbat.views import orbat_visual
from orbat.audit_views import audit_log_list, audit_log_detail

urlpatterns = [
    # Redirige la raíz del sitio al ORBAT visual
    path('', lambda request: redirect('orbat_visual')),
    path('admin/auditoria/', audit_log_list, name='audit_log_list'),
    path('admin/auditoria/<int:entry_id>/', audit_log_detail, name='audit_log_detail'),
    path('admin/', admin.site.urls),
    path('orbat/', orbat_visual, name='orbat_visual'),
]