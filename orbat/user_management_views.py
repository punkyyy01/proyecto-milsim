"""
Gestión de usuarios del sistema.
Solo accesible para miembros del grupo CREADOR_ERP.

Seguridad aplicada:
- Decorador creador_required (staff + grupo CREADOR_ERP o superuser)
- Todas las acciones mutantes requieren POST + CSRF token
- Validación de contraseña con los validators de Django
- Sanitización de username con regex
- Validación de grupos contra whitelist ERP
- Registro de auditoría en django.contrib.admin LogEntry
- Protección contra auto-eliminación y auto-degradación
"""

import logging
import re
from functools import wraps

from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import escape
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_http_methods

User = get_user_model()
logger = logging.getLogger(__name__)

# ── Regex estricto para nombres de usuario ───────────────────────────
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.\-@+]{1,150}$")

# ── Grupos ERP permitidos (whitelist) ────────────────────────────────

ERP_GROUPS = [
    "CREADOR_ERP",
    "ALTO_MANDO_ERP",
    "OFICIAL_ERP",
    "SARGENTO_ERP",
    "CONSULTA_ERP",
]

# ── Auditoría helper ────────────────────────────────────────────────


def _log_action(user, target_user, action_flag, message):
    """Registra la acción en la tabla LogEntry del admin de Django."""
    try:
        ct = ContentType.objects.get_for_model(target_user)
        LogEntry.objects.log_action(
            user_id=user.pk,
            content_type_id=ct.pk,
            object_id=target_user.pk,
            object_repr=str(target_user),
            action_flag=action_flag,
            change_message=message,
        )
    except Exception:
        logger.exception("Error al registrar auditoría de gestión de usuarios")


# ── Decorador: solo CREADOR_ERP ──────────────────────────────────────


def creador_required(view_func):
    """Restringe el acceso a miembros del grupo CREADOR_ERP (o 'creador' legacy).

    Requisitos:
    - El usuario debe ser staff (staff_member_required lo garantiza).
    - El usuario debe pertenecer a CREADOR_ERP / creador, o ser superuser.
    """

    @wraps(view_func)
    @staff_member_required
    @csrf_protect
    def _wrapped(request, *args, **kwargs):
        is_creador = request.user.groups.filter(
            name__in=["CREADOR_ERP", "creador"]
        ).exists()
        if not is_creador and not request.user.is_superuser:
            logger.warning(
                "Acceso denegado a gestión de usuarios: user=%s ip=%s path=%s",
                request.user.username,
                request.META.get("REMOTE_ADDR"),
                request.path,
            )
            messages.error(
                request, "No tienes permisos para acceder a esta sección."
            )
            return redirect("admin:index")
        return view_func(request, *args, **kwargs)

    return _wrapped


# ── Helpers ──────────────────────────────────────────────────────────


def _get_erp_groups():
    """Devuelve los grupos ERP que existan en la BD."""
    return Group.objects.filter(name__in=ERP_GROUPS).order_by("name")


def _validate_username(username):
    """Valida formato de nombre de usuario. Devuelve lista de errores."""
    errors = []
    if not username:
        errors.append("El nombre de usuario es obligatorio.")
    elif not USERNAME_RE.match(username):
        errors.append(
            "El nombre de usuario solo puede contener letras, números, "
            "y los caracteres _ . - @ + (máx. 150 caracteres)."
        )
    return errors


def _validate_selected_groups(selected_groups):
    """Filtra grupos seleccionados contra la whitelist ERP.
    Retorna solo los nombres válidos."""
    return [g for g in selected_groups if g in ERP_GROUPS]


def _validate_new_password(password, user=None):
    """Valida la contraseña con los validators de Django.
    Retorna lista de errores."""
    errors = []
    if not password:
        return errors
    try:
        validate_password(password, user=user)
    except ValidationError as e:
        errors.extend(e.messages)
    return errors


# ── LISTADO DE USUARIOS ─────────────────────────────────────────────


@creador_required
@require_http_methods(["GET"])
def user_list(request):
    users = User.objects.prefetch_related("groups").order_by("username")

    q = request.GET.get("q", "").strip()[:200]  # limitar longitud de búsqueda
    group_filter = request.GET.get("group", "").strip()
    status_filter = request.GET.get("status", "").strip()

    if q:
        users = users.filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
        )

    # Validar group_filter contra whitelist
    if group_filter and group_filter in ERP_GROUPS:
        users = users.filter(groups__name=group_filter)
    else:
        group_filter = ""

    valid_statuses = {"active", "inactive", "superuser", "staff"}
    if status_filter in valid_statuses:
        if status_filter == "active":
            users = users.filter(is_active=True)
        elif status_filter == "inactive":
            users = users.filter(is_active=False)
        elif status_filter == "superuser":
            users = users.filter(is_superuser=True)
        elif status_filter == "staff":
            users = users.filter(is_staff=True, is_superuser=False)
    else:
        status_filter = ""

    paginator = Paginator(users.distinct(), 25)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    context = {
        "title": "Gestión de Usuarios",
        "page_obj": page_obj,
        "q": q,
        "group_filter": group_filter,
        "status_filter": status_filter,
        "erp_groups": _get_erp_groups(),
    }
    return render(request, "admin/orbat/user_management/user_list.html", context)


# ── CREAR USUARIO ────────────────────────────────────────────────────


@creador_required
@require_http_methods(["GET", "POST"])
def user_create(request):
    erp_groups = _get_erp_groups()

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()[:150]
        last_name = request.POST.get("last_name", "").strip()[:150]
        is_staff = request.POST.get("is_staff") == "on"
        is_superuser = request.POST.get("is_superuser") == "on"
        is_active = request.POST.get("is_active") == "on"
        selected_groups = _validate_selected_groups(request.POST.getlist("groups"))

        # Validaciones
        errors = _validate_username(username)

        if not password:
            errors.append("La contraseña es obligatoria.")

        if User.objects.filter(username=username).exists():
            errors.append(f"Ya existe un usuario con el nombre «{escape(username)}».")

        # Validar contraseña con Django validators
        if password:
            errors.extend(_validate_new_password(password))

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(
                request,
                "admin/orbat/user_management/user_form.html",
                {
                    "title": "Crear Usuario",
                    "erp_groups": erp_groups,
                    "form_data": request.POST,
                    "is_new": True,
                },
            )

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.is_active = is_active
        user.save()

        if selected_groups:
            groups = Group.objects.filter(name__in=selected_groups)
            user.groups.set(groups)

        _log_action(
            request.user,
            user,
            ADDITION,
            f"Usuario creado por {request.user.username}. "
            f"Staff={is_staff}, Super={is_superuser}, Grupos={selected_groups}",
        )
        logger.info(
            "Usuario creado: %s por %s", username, request.user.username
        )
        messages.success(request, f"Usuario «{escape(username)}» creado correctamente.")
        return redirect("user_management_list")

    return render(
        request,
        "admin/orbat/user_management/user_form.html",
        {
            "title": "Crear Usuario",
            "erp_groups": erp_groups,
            "form_data": {},
            "is_new": True,
        },
    )


# ── EDITAR USUARIO ───────────────────────────────────────────────────


@creador_required
@require_http_methods(["GET", "POST"])
def user_edit(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    erp_groups = _get_erp_groups()

    if request.method == "POST":
        new_username = request.POST.get("username", target_user.username).strip()
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()[:150]
        last_name = request.POST.get("last_name", "").strip()[:150]
        is_staff = request.POST.get("is_staff") == "on"
        is_superuser = request.POST.get("is_superuser") == "on"
        is_active = request.POST.get("is_active") == "on"
        new_password = request.POST.get("password", "").strip()
        selected_groups = _validate_selected_groups(request.POST.getlist("groups"))

        # Validaciones
        errors = _validate_username(new_username)

        # Verificar unicidad si cambió el username
        if (
            new_username != target_user.username
            and User.objects.filter(username=new_username).exists()
        ):
            errors.append(
                f"Ya existe un usuario con el nombre «{escape(new_username)}»."
            )

        # Validar nueva contraseña si proporcionada
        if new_password:
            errors.extend(_validate_new_password(new_password, user=target_user))

        # Protección: no puedes quitarte superusuario/staff/activo a ti mismo
        if target_user == request.user:
            if not is_superuser and target_user.is_superuser:
                errors.append(
                    "No puedes quitarte el estatus de superusuario a ti mismo."
                )
            if not is_active:
                errors.append("No puedes desactivarte a ti mismo.")

        if errors:
            for e in errors:
                messages.error(request, e)
            form_data = {
                "username": new_username,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
                "is_active": is_active,
            }
            return render(
                request,
                "admin/orbat/user_management/user_form.html",
                {
                    "title": f"Editar: {target_user.username}",
                    "erp_groups": erp_groups,
                    "form_data": form_data,
                    "target_user": target_user,
                    "is_new": False,
                },
            )

        # Registrar cambios para auditoría
        changes = []
        if new_username != target_user.username:
            changes.append(f"username: {target_user.username} → {new_username}")
        if is_staff != target_user.is_staff:
            changes.append(f"staff: {target_user.is_staff} → {is_staff}")
        if is_superuser != target_user.is_superuser:
            changes.append(f"superuser: {target_user.is_superuser} → {is_superuser}")
        if is_active != target_user.is_active:
            changes.append(f"activo: {target_user.is_active} → {is_active}")
        if new_password:
            changes.append("contraseña cambiada")

        old_groups = set(target_user.groups.values_list("name", flat=True))
        new_groups_set = set(selected_groups)
        if old_groups != new_groups_set:
            changes.append(f"grupos: {old_groups} → {new_groups_set}")

        target_user.username = new_username
        target_user.email = email
        target_user.first_name = first_name
        target_user.last_name = last_name
        target_user.is_staff = is_staff
        target_user.is_superuser = is_superuser
        target_user.is_active = is_active

        if new_password:
            target_user.set_password(new_password)

        groups = Group.objects.filter(name__in=selected_groups)
        target_user.groups.set(groups)
        target_user.save()

        if changes:
            _log_action(
                request.user,
                target_user,
                CHANGE,
                f"Editado por {request.user.username}: {'; '.join(changes)}",
            )

        logger.info(
            "Usuario editado: %s por %s — %s",
            target_user.username,
            request.user.username,
            "; ".join(changes) if changes else "sin cambios",
        )
        messages.success(
            request, f"Usuario «{escape(target_user.username)}» actualizado."
        )
        return redirect("user_management_list")

    # GET: pre-poblar formulario
    form_data = {
        "username": target_user.username,
        "email": target_user.email,
        "first_name": target_user.first_name,
        "last_name": target_user.last_name,
        "is_staff": target_user.is_staff,
        "is_superuser": target_user.is_superuser,
        "is_active": target_user.is_active,
    }

    return render(
        request,
        "admin/orbat/user_management/user_form.html",
        {
            "title": f"Editar: {target_user.username}",
            "erp_groups": erp_groups,
            "form_data": form_data,
            "target_user": target_user,
            "is_new": False,
        },
    )


# ── ELIMINAR USUARIO ─────────────────────────────────────────────────


@creador_required
@require_http_methods(["GET", "POST"])
def user_delete(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)

    # No se puede eliminar a sí mismo
    if target_user == request.user:
        messages.error(request, "No puedes eliminarte a ti mismo.")
        return redirect("user_management_list")

    if request.method == "POST":
        username = target_user.username
        _log_action(
            request.user,
            target_user,
            DELETION,
            f"Usuario eliminado por {request.user.username}",
        )
        logger.info(
            "Usuario eliminado: %s por %s", username, request.user.username
        )
        target_user.delete()
        messages.success(request, f"Usuario «{escape(username)}» eliminado.")
        return redirect("user_management_list")

    return render(
        request,
        "admin/orbat/user_management/user_confirm_delete.html",
        {
            "title": f"Eliminar: {target_user.username}",
            "target_user": target_user,
        },
    )


# ── TOGGLE SUPERUSUARIO (solo POST) ──────────────────────────────────


@creador_required
@require_POST
def user_toggle_superuser(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)

    if target_user == request.user:
        messages.error(
            request, "No puedes cambiar tu propio estatus de superusuario."
        )
        return redirect("user_management_list")

    old_value = target_user.is_superuser
    target_user.is_superuser = not old_value
    target_user.save(update_fields=["is_superuser"])

    estado = "activado" if target_user.is_superuser else "desactivado"
    _log_action(
        request.user,
        target_user,
        CHANGE,
        f"Superusuario {estado} por {request.user.username} "
        f"({old_value} → {target_user.is_superuser})",
    )
    logger.info(
        "Toggle superusuario: %s %s → %s por %s",
        target_user.username,
        old_value,
        target_user.is_superuser,
        request.user.username,
    )
    messages.success(
        request,
        f"Superusuario {estado} para «{escape(target_user.username)}».",
    )
    return redirect("user_management_list")


# ── TOGGLE ACTIVO (solo POST) ────────────────────────────────────────


@creador_required
@require_POST
def user_toggle_active(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)

    if target_user == request.user:
        messages.error(request, "No puedes desactivarte a ti mismo.")
        return redirect("user_management_list")

    old_value = target_user.is_active
    target_user.is_active = not old_value
    target_user.save(update_fields=["is_active"])

    estado = "activado" if target_user.is_active else "desactivado"
    _log_action(
        request.user,
        target_user,
        CHANGE,
        f"Usuario {estado} por {request.user.username} "
        f"({old_value} → {target_user.is_active})",
    )
    logger.info(
        "Toggle activo: %s %s → %s por %s",
        target_user.username,
        old_value,
        target_user.is_active,
        request.user.username,
    )
    messages.success(
        request,
        f"Usuario «{escape(target_user.username)}» {estado}.",
    )
    return redirect("user_management_list")
