from django.shortcuts import render
from django.contrib.auth.decorators import login_required 
from .models import Regimiento

@login_required 
def orbat_visual(request):
    """Renderiza el ORBAT con relaciones prefeteadas para reducir consultas."""

    regimientos = Regimiento.objects.prefetch_related(
        'miembro_set',
        'companias__miembro_set',
        'companias__pelotones__miembro_set',
        'companias__pelotones__escuadras__miembro_set'
    ).all()

    return render(request, 'orbat/visual_chart.html', {
        'regimientos': regimientos,
        'user': request.user
    })