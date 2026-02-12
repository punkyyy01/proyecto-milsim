from django.contrib import admin
from django.urls import path
from orbat.views import orbat_visual # <--- Importamos la vista

urlpatterns = [
    path('admin/', admin.site.urls),
    path('orbat/', orbat_visual, name='orbat_visual'), # <--- Nueva ruta
]