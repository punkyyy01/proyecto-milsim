from django.contrib import admin
from django.utils.html import format_html
from .models import Regimiento, Compania, Peloton, Escuadra, Miembro, Curso

# --- INLINES (TABLAS DENTRO DE OTRAS PÁGINAS) ---

class MiembroInline(admin.TabularInline):
    model = Miembro
    # Mostramos los campos necesarios
    fields = ('rango', 'nombre_milsim', 'rol', 'activo')
    
    # ¡IMPORTANTE! Esto asegura que aparezca 1 línea vacía para escribir
    extra = 1 
    
    show_change_link = True
    verbose_name = "Operador"
    verbose_name_plural = "MIEMBROS DE LA ESCUADRA (Añadir aquí)"

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

# --- PANELES PRINCIPALES ---

@admin.register(Regimiento)
class RegimientoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'comandante')

@admin.register(Compania)
class CompaniaAdmin(admin.ModelAdmin):
    # Dentro de Compañía -> Ves Pelotones
    inlines = [PelotonInline]
    list_display = ('nombre', 'regimiento')
    list_filter = ('regimiento',)

@admin.register(Peloton)
class PelotonAdmin(admin.ModelAdmin):
    # Dentro de Pelotón -> Ves Escuadras
    inlines = [EscuadraInline] 
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
    search_fields = ('nombre_milsim', 'nombre_real')
    filter_horizontal = ('cursos',)
    
    fieldsets = (
        ("Datos Operativos", {
            "fields": ("rango", "nombre_milsim", "rol", "activo", "escuadra")
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
        if obj.escuadra:
            return f"{obj.escuadra.nombre}"
        return "-"
    get_unidad.short_description = "Unidad"

admin.site.register(Curso)