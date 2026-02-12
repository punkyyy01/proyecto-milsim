# orbat/views.py
from django.shortcuts import render
from .models import Regimiento

def orbat_publico(request): # <--- Este nombre debe coincidir con el de urls.py
    regimiento = Regimiento.objects.first() 
    return render(request, 'orbat/orbat_publico.html', {
        'regimiento': regimiento
    })