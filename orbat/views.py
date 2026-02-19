from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, IntegrityError, DatabaseError
import json

from .models import Regimiento, Miembro, Escuadra


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


def escuadras_dashboard(request):
    """Vista que muestra el tablero de escuadras y sus miembros."""
    escuadras = Escuadra.objects.select_related('peloton__compania').prefetch_related('miembro_set').all()
    # Preparar datos simples para la plantilla
    data = []
    for e in escuadras:
        miembros = list(e.miembro_set.filter(activo=True).values('id', 'nombre_milsim', 'rango'))
        data.append({
            'id': e.id,
            'nombre': str(e),
            'miembros': miembros,
        })

    return render(request, 'orbat/board.html', {
        'escuadras': data,
    })


@csrf_exempt
@require_POST
def transferir_personal(request):
    """API endpoint para transferir un miembro entre escuadras.

    Espera JSON con: { persona_id, escuadra_destino_id, persona_a_reemplazar_id? }

    Reglas:
    - Si la escuadra destino tiene < 5 miembros, mueve al miembro directamente.
    - Si tiene 5 y no se envía `persona_a_reemplazar_id`, devuelve 409 con la lista de miembros.
    - Si se envía `persona_a_reemplazar_id`, realiza un intercambio: A->destino, B->origen_de_A.

    Nota: se usa `transaction.atomic()` y `select_for_update()` para evitar condiciones de carrera.
    """

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid_json'}, status=400)

    persona_id = payload.get('persona_id')
    destino_id = payload.get('escuadra_destino_id')
    reemplazar_id = payload.get('persona_a_reemplazar_id')

    if not persona_id or not destino_id:
        return JsonResponse({'error': 'persona_id and escuadra_destino_id required'}, status=400)

    try:
        with transaction.atomic():
            miembro = Miembro.objects.select_for_update().select_related('escuadra').get(pk=persona_id)
            destino = Escuadra.objects.select_for_update().select_related('peloton__compania').get(pk=destino_id)

            origen_escuadra = miembro.escuadra

            miembros_destino_qs = Miembro.objects.select_for_update().filter(escuadra=destino)
            count_destino = miembros_destino_qs.count()

            # Caso 1: destino con espacio
            if count_destino < 5:
                miembro.escuadra = destino
                # Mantener coherencia jerárquica
                miembro.peloton = destino.peloton
                miembro.compania = destino.peloton.compania if destino.peloton else None
                miembro.save(update_fields=['escuadra', 'peloton', 'compania'])
                return JsonResponse({'status': 'moved', 'persona_id': miembro.id, 'destino_id': destino.id})

            # Caso 2: destino lleno
            if not reemplazar_id:
                miembros_list = list(miembros_destino_qs.values('id', 'nombre_milsim', 'rango'))
                return JsonResponse({'error': 'destination_full', 'miembros': miembros_list}, status=409)

            # Caso 3: intercambio solicitado
            try:
                reemplazar = miembros_destino_qs.get(pk=reemplazar_id)
            except Miembro.DoesNotExist:
                return JsonResponse({'error': 'persona_a_reemplazar_not_in_destination'}, status=400)

            # Mover A -> destino
            miembro.escuadra = destino
            miembro.peloton = destino.peloton
            miembro.compania = destino.peloton.compania if destino.peloton else None
            miembro.save(update_fields=['escuadra', 'peloton', 'compania'])

            # Mover B (reemplazar) -> origen de A (puede ser None)
            reemplazar.escuadra = origen_escuadra
            if origen_escuadra:
                reemplazar.peloton = origen_escuadra.peloton
                reemplazar.compania = origen_escuadra.peloton.compania if origen_escuadra.peloton else None
            else:
                reemplazar.peloton = None
                reemplazar.compania = None
            reemplazar.save(update_fields=['escuadra', 'peloton', 'compania'])

            return JsonResponse({
                'status': 'swapped',
                'moved': miembro.id,
                'moved_to': destino.id,
                'replaced': reemplazar.id,
                'replaced_moved_to': origen_escuadra.id if origen_escuadra else None,
            })

    except Miembro.DoesNotExist:
        return JsonResponse({'error': 'persona_not_found'}, status=404)
    except Escuadra.DoesNotExist:
        return JsonResponse({'error': 'escuadra_not_found'}, status=404)
    except (IntegrityError, DatabaseError) as exc:
        return JsonResponse({'error': 'db_error', 'details': str(exc)}, status=500)