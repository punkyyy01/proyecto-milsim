from django.shortcuts import render
from django.contrib.auth.decorators import login_required 
from .models import Regimiento

@login_required 
def orbat_visual(request):
    """
    Carga la jerarquía militar completa en una sola consulta optimizada.
    Usamos prefetch_related para evitar el problema de consultas N+1.
    """
    
    # 1. Optimización: 'prefetch_related' trae todas las tablas relacionadas
    # de un solo viaje, en lugar de hacer una consulta por cada escuadra.
    regimientos = Regimiento.objects.prefetch_related(
        'companias__pelotones__escuadras__miembro_set'
    ).all()
    
    # 2. Contexto: Pasamos los datos al template
    return render(request, 'orbat/visual_chart.html', {
        'regimientos': regimientos,
        'user': request.user # Útil si quieres mostrar "Bienvenido, [Nombre]"
    })