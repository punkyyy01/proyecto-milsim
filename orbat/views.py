from django.shortcuts import render
from .models import Regimiento


def orbat_visual(request):
    """Renderiza el ORBAT con relaciones prefeteadas para reducir consultas.
    Acceso público — no requiere autenticación."""

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