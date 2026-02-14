from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.admin import GroupAdmin as DefaultGroupAdmin
from django.contrib.admin.views.main import ChangeList
from django.utils.html import format_html
from django.http import HttpResponse
import csv
from django.db.models import Case, Count, IntegerField, Value, When
from .models import Regimiento, Compania, Peloton, Escuadra, Miembro, Curso

User = get_user_model()

# Inlines

class MiembroInline(admin.TabularInline):
    """Inline de SOLO LECTURA para ver miembros asignados a la unidad.
    No permite crear ni borrar miembros desde aquí.
    Para gestionar miembros, usar la sección Personal."""
    model = Miembro
    fields = ('rango', 'nombre_milsim', 'rol', 'activo')
    readonly_fields = ('rango', 'nombre_milsim', 'rol', 'activo')
    extra = 0
    max_num = 0  # Impide añadir nuevos desde aquí
    can_delete = False  # No borrar miembros desde la unidad
    show_change_link = True
    verbose_name = "Operador asignado"
    verbose_name_plural = "Miembros asignados (gestionar desde Personal)"

class EscuadraInline(admin.TabularInline):
    model = Escuadra
    fields = ('nombre', 'indicativo_radio')
    extra = 0
    show_change_link = True
    verbose_name = "Escuadra"
    verbose_name_plural = "Escuadras del pelotón"

    class Media:
        js = ('admin_inline_delete.js',)

class PelotonInline(admin.TabularInline):
    model = Peloton
    fields = ('nombre',)
    extra = 0
    show_change_link = True
    verbose_name = "Pelotón"
    verbose_name_plural = "Pelotones de la compañía"

    class Media:
        js = ('admin_inline_delete.js',)

# Paneles principales

@admin.register(Regimiento)
class RegimientoAdmin(admin.ModelAdmin):
    # Miembros asignados directamente al regimiento
    inlines = [MiembroInline]
    list_display = ('nombre', 'comandante', 'total_efectivos')
    search_fields = ('nombre', 'comandante')
    list_per_page = 20
    ordering = ('nombre',)
    list_display_links = ('nombre',)
    save_on_top = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Totales para mostrar en listado sin consultas por fila
        qs = qs.annotate(
            efectivos_hq=Count('miembro', distinct=True),
            efectivos_cia=Count('companias__miembro', distinct=True),
            efectivos_plt=Count('companias__pelotones__miembro', distinct=True),
            efectivos_sqd=Count('companias__pelotones__escuadras__miembro', distinct=True),
        )
        return qs

    def total_efectivos(self, obj):
        # Miembros de HQ reg + HQ compañía + HQ pelotón + escuadra
        try:
            return (
                (getattr(obj, 'efectivos_hq', 0) or 0)
                + (getattr(obj, 'efectivos_cia', 0) or 0)
                + (getattr(obj, 'efectivos_plt', 0) or 0)
                + (getattr(obj, 'efectivos_sqd', 0) or 0)
            )
        except Exception:
            return obj.total_efectivos()
    total_efectivos.short_description = 'Efectivos'

@admin.register(Compania)
class CompaniaAdmin(admin.ModelAdmin):
    # Pelotones y miembros de HQ de compañía
    inlines = [PelotonInline, MiembroInline]
    list_display = ('nombre', 'regimiento', 'logo_preview')
    list_filter = ('regimiento',)
    list_display_links = ('nombre',)
    save_on_top = True
    search_fields = ('nombre', 'regimiento__nombre')
    autocomplete_fields = ('regimiento',)

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="height:28px;object-fit:contain;border-radius:3px;"/>', obj.logo)
        return '-'
    logo_preview.short_description = 'Logo'

@admin.register(Peloton)
class PelotonAdmin(admin.ModelAdmin):
    # Escuadras y miembros de HQ de pelotón
    inlines = [EscuadraInline, MiembroInline]
    list_display = ('nombre', 'compania', 'num_escuadras')
    list_filter = ('compania',)
    list_display_links = ('nombre',)
    save_on_top = True
    search_fields = ('nombre', 'compania__nombre')
    autocomplete_fields = ('compania',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_num_escuadras=Count('escuadras'))

    def num_escuadras(self, obj):
        return getattr(obj, '_num_escuadras', obj.escuadras.count())
    num_escuadras.short_description = 'Escuadras'

@admin.register(Escuadra)
class EscuadraAdmin(admin.ModelAdmin):
    # Miembros de la escuadra
    inlines = [MiembroInline]
    list_display = ('nombre', 'peloton', 'indicativo_radio', 'get_efectivos')
    list_filter = ('peloton',)
    list_display_links = ('nombre',)
    save_on_top = True
    search_fields = ('nombre', 'peloton__nombre')
    autocomplete_fields = ('peloton',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_efectivos=Count('miembro'))

    def get_efectivos(self, obj):
        return getattr(obj, '_efectivos', obj.miembro_set.count())
    get_efectivos.short_description = "Efectivos"

@admin.register(Miembro)
class MiembroAdmin(admin.ModelAdmin):
    list_display = ('rango', 'nombre_milsim', 'rol', 'get_unidad', 'activo', 'usuario_link')
    list_filter = ('activo', 'rango', 'escuadra')
    list_editable = ('activo', 'rol')
    list_display_links = ('nombre_milsim',)
    save_on_top = True
    list_per_page = 50

    search_fields = ('nombre_milsim', 'usuario__first_name', 'usuario__last_name', 'usuario__username')

    filter_horizontal = ('cursos',)

    fieldsets = (
        ("Datos Operativos", {
            "fields": ("rango", "nombre_milsim", "rol", "activo", "regimiento", "compania", "peloton", "escuadra")
        }),
        ("Sistema", {
            "fields": ("usuario", "discord_id", "steam_id"),
            "classes": ("collapse",),
        }),
        ("Expediente", {
            "fields": ("cursos", "fecha_ingreso", "notas_admin")
        }),
    )
    readonly_fields = ('fecha_ingreso',)
    autocomplete_fields = ('regimiento', 'compania', 'peloton', 'escuadra', 'cursos')

    def export_members_csv(self, request, queryset):
        """Exporta los miembros seleccionados como CSV"""
        field_names = ['rango', 'nombre_milsim', 'rol', 'usuario', 'regimiento', 'compania', 'peloton', 'escuadra', 'activo']

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=miembros.csv'

        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset.select_related('usuario', 'regimiento', 'compania', 'peloton', 'escuadra'):
            writer.writerow([
                obj.rango,
                obj.nombre_milsim,
                obj.rol,
                obj.usuario.username if obj.usuario else '',
                obj.regimiento.nombre if obj.regimiento else '',
                obj.compania.nombre if obj.compania else '',
                obj.peloton.nombre if obj.peloton else '',
                obj.escuadra.nombre if obj.escuadra else '',
                obj.activo,
            ])
        return response
    export_members_csv.short_description = 'Exportar miembros seleccionados a CSV'

    actions = ('marcar_activo', 'marcar_inactivo', 'export_members_csv')

    def marcar_activo(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f"{updated} miembros activados.")
    marcar_activo.short_description = 'Marcar seleccionados como activos'

    def marcar_inactivo(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f"{updated} miembros desactivados.")
    marcar_inactivo.short_description = 'Marcar seleccionados como inactivos'

    def get_unidad(self, obj):
        if obj.escuadra:
            return obj.escuadra.nombre
        if obj.peloton:
            return f"HQ {obj.peloton.nombre}"
        if obj.compania:
            return f"HQ {obj.compania.nombre}"
        if obj.regimiento:
            return "Plana Mayor Regimiento"
        return "-"
    get_unidad.short_description = "Unidad"

    def usuario_link(self, obj):
        if obj.usuario:
            return obj.usuario.username
        return '-'
    usuario_link.short_description = 'Usuario'

    class Media:
        js = ('js/admin_doble_click.js',)
        css = { 'all': ('admin/css/widgets.css', 'custom_admin.css') }

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('sigla', 'nombre')
    search_fields = ('sigla', 'nombre')

# Vincula el perfil Miembro en el admin de User
class MiembroUserInline(admin.StackedInline):
    model = Miembro
    can_delete = False
    verbose_name = 'Perfil Operador'
    verbose_name_plural = 'Perfil Operador'
    fk_name = 'usuario'


class UserAdmin(DefaultUserAdmin):
    inlines = (MiembroUserInline,)

    def has_module_permission(self, request):
        return request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ERPGroupChangeList(ChangeList):
    def get_ordering(self, request, queryset):
        return ["erp_order", "name"]


class GroupAdmin(DefaultGroupAdmin):
    ERP_GROUP_ORDER = [
        "CREADOR_ERP",
        "ALTO_MANDO_ERP",
        "OFICIAL_ERP",
        "SARGENTO_ERP",
        "CONSULTA_ERP",
    ]

    def get_queryset(self, request):
        qs = self.model._default_manager.get_queryset()
        order_cases = [
            When(name=group_name, then=Value(index))
            for index, group_name in enumerate(self.ERP_GROUP_ORDER)
        ]
        return qs.annotate(
            erp_order=Case(
                *order_cases,
                default=Value(len(self.ERP_GROUP_ORDER)),
                output_field=IntegerField(),
            )
        ).order_by("erp_order", "name")

    def get_changelist(self, request, **kwargs):
        return ERPGroupChangeList

    def has_module_permission(self, request):
        return request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Re-registro de User y Group con permisos de solo lectura
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)