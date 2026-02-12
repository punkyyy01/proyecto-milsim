from django.contrib import admin
from django.utils.html import format_html
from .models import Regimiento, Compania, Peloton, Escuadra, Miembro, Curso

# --- 1. INLINES (Tablas dentro de otras páginas) ---

class MiembroInline(admin.TabularInline):
    model = Miembro
    # Mostramos los campos necesarios para HQ o Escuadras
    fields = ('rango', 'nombre_milsim', 'rol', 'activo')
    extra = 1 
    show_change_link = True
    verbose_name = "Operador"
    verbose_name_plural = "MIEMBROS / HQ (Añadir aquí)"

class EscuadraInline(admin.TabularInline):
    model = Escuadra
    fields = ('nombre', 'indicativo_radio')
    extra = 1
    show_change_link = True
    verbose_name = "Escuadra"
    verbose_name_plural = "ESCUADRAS DEL PELOTÓN"

class PelotonInline(admin.TabularInline):
    model = Peloton
    fields = ('nombre',)
    extra = 1
    show_change_link = True
    verbose_name = "Pelotón"
    verbose_name_plural = "PELOTONES DE LA COMPAÑÍA"

# --- 2. PANELES PRINCIPALES (Configuración de cada sección) ---

@admin.register(Regimiento)
class RegimientoAdmin(admin.ModelAdmin):
    # AQUÍ SE AÑADE: Permite agregar miembros de Plana Mayor al Regimiento
    inlines = [MiembroInline]
    list_display = ('nombre', 'comandante')

@admin.register(Compania)
class CompaniaAdmin(admin.ModelAdmin):
    # AQUÍ SE AÑADE: Ves los Pelotones Y puedes agregar miembros de HQ de Compañía
    inlines = [PelotonInline, MiembroInline]
    list_display = ('nombre', 'regimiento')
    list_filter = ('regimiento',)

@admin.register(Peloton)
class PelotonAdmin(admin.ModelAdmin):
    # AQUÍ SE AÑADE: Ves las Escuadras Y puedes agregar miembros al Pelotón
    inlines = [EscuadraInline, MiembroInline] 
    list_display = ('nombre', 'compania')
    list_filter = ('compania',)

@admin.register(Escuadra)
class EscuadraAdmin(admin.ModelAdmin):
    # Dentro de Escuadra -> Ves Miembros
    inlines = [MiembroInline]
    list_display = ('nombre', 'peloton', 'indicativo_radio', 'get_efectivos')
    list_filter = ('peloton',)
    search_fields = ('nombre',)

    def get_efectivos(self, obj):
        return obj.miembro_set.count()
    get_efectivos.short_description = "Efectivos"

@admin.register(Miembro)
class MiembroAdmin(admin.ModelAdmin):
    list_display = ('rango', 'nombre_milsim', 'rol', 'get_unidad', 'activo')
    list_filter = ('activo', 'rango', 'escuadra')
    
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

    def get_unidad(self, obj):
        # Muestra en qué nivel está el miembro en la lista general
        if obj.escuadra: return obj.escuadra.nombre
        if obj.peloton: return f"HQ {obj.peloton.nombre}"
        if obj.compania: return f"HQ {obj.compania.nombre}"
        if obj.regimiento: return "Plana Mayor Regimiento"
        return "-"
    get_unidad.short_description = "Unidad"

    class Media:
        js = ('js/admin_doble_click.js',)
        css = { 'all': ('admin/css/widgets.css',) }

admin.site.register(Curso)