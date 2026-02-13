from django.contrib import admin
from django.urls import path
from orbat.views import orbat_visual # <--- Importamos la vista
from orbat.audit_views import audit_log_list, audit_log_detail

urlpatterns = [
    path('admin/auditoria/', audit_log_list, name='audit_log_list'),
    path('admin/auditoria/<int:entry_id>/', audit_log_detail, name='audit_log_detail'),
    path('admin/', admin.site.urls),
    path('orbat/', orbat_visual, name='orbat_visual'), # <--- Nueva ruta
]