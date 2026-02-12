# gestion_milsim/urls.py

from django.contrib import admin
from django.urls import path
from orbat import views

urlpatterns = [
    # Corregido: Quitamos el ".admin" de en medio
    path('admin/', admin.site.urls), 
    
    # Esta es la que configuramos antes
    path('', views.orbat_publico, name='home'), 
]