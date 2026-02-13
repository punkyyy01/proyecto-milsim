import csv
from datetime import timedelta

from django.contrib.admin.models import LogEntry
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone


def _base_queryset():
    return LogEntry.objects.select_related("user", "content_type").order_by("-action_time")


@staff_member_required
def audit_log_list(request):
    entries = _base_queryset()

    query = request.GET.get("q", "").strip()
    action_flag = request.GET.get("action", "").strip()
    model_filter = request.GET.get("model", "").strip()
    user_filter = request.GET.get("user", "").strip()
    date_from = request.GET.get("from", "").strip()
    date_to = request.GET.get("to", "").strip()
    preset = request.GET.get("preset", "").strip().lower()

    if preset == "today":
        today = timezone.localdate().isoformat()
        date_from = today
        date_to = today
    elif preset == "7d":
        today = timezone.localdate()
        date_to = today.isoformat()
        date_from = (today - timedelta(days=6)).isoformat()

    if query:
        entries = entries.filter(
            Q(object_repr__icontains=query)
            | Q(change_message__icontains=query)
            | Q(user__username__icontains=query)
            | Q(content_type__model__icontains=query)
        )

    if action_flag in {"1", "2", "3"}:
        entries = entries.filter(action_flag=int(action_flag))

    if model_filter:
        entries = entries.filter(content_type__model__icontains=model_filter)

    if user_filter:
        entries = entries.filter(user__username__icontains=user_filter)

    if date_from:
        entries = entries.filter(action_time__date__gte=date_from)

    if date_to:
        entries = entries.filter(action_time__date__lte=date_to)

    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=auditoria_orbat.csv"
        writer = csv.writer(response)
        writer.writerow(["fecha_hora", "usuario", "accion", "modelo", "objeto", "detalle"])

        action_map = {1: "Añadido", 2: "Modificado", 3: "Eliminado"}
        for entry in entries:
            writer.writerow(
                [
                    timezone.localtime(entry.action_time).strftime("%Y-%m-%d %H:%M:%S"),
                    entry.user.username if entry.user else "-",
                    action_map.get(entry.action_flag, "-"),
                    entry.content_type.model if entry.content_type else "-",
                    entry.object_repr,
                    entry.change_message,
                ]
            )

        return response

    paginator = Paginator(entries, 30)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    context = {
        "title": "Auditoría de cambios",
        "page_obj": page_obj,
        "query": query,
        "action_flag": action_flag,
        "model_filter": model_filter,
        "user_filter": user_filter,
        "date_from": date_from,
        "date_to": date_to,
        "preset": preset,
    }
    return render(request, "admin/orbat/audit_log_list.html", context)


@staff_member_required
def audit_log_detail(request, entry_id):
    entry = get_object_or_404(
        LogEntry.objects.select_related("user", "content_type"),
        id=entry_id,
    )

    try:
        pretty_message = entry.get_change_message() or "Sin detalle adicional"
    except Exception:
        pretty_message = entry.change_message or "Sin detalle adicional"

    return render(
        request,
        "admin/orbat/audit_log_detail.html",
        {
            "title": f"Evento #{entry.id}",
            "entry": entry,
            "pretty_message": pretty_message,
        },
    )
