from django.contrib import admin
from django.utils.html import format_html
from .models import Regimiento, Compania, Escuadra, Miembro, Fase, Curso

# --- INLINES (La clave de la navegación eficiente) ---

class MiembroInline(admin.TabularInline):
    model = Miembro
    extra = 0
    fields = ('nombre_milsim', 'rango', 'activo')
    show_change_link = True # El "botón mágico" para ir al perfil completo

class EscuadraInline(admin.TabularInline):
    model = Escuadra
    extra = 1
    show_change_link = True

# --- PANELES PRINCIPALES ---

@admin.register(Regimiento)
class RegimientoAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not Regimiento.objects.exists()
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Compania)
class CompaniaAdmin(admin.ModelAdmin):
    inlines = [EscuadraInline]
    list_display = ('nombre',)
    exclude = ('regimiento',)

    def save_model(self, request, obj, form, change):
        if not obj.regimiento_id:
            obj.regimiento = Regimiento.objects.first()
        super().save_model(request, obj, form, change)

@admin.register(Escuadra)
class EscuadraAdmin(admin.ModelAdmin):
    inlines = [MiembroInline] # Ver soldados sin salir de la escuadra
    list_display = ('nombre', 'compania')
    list_filter = ('compania',)

# orbat/admin.py

@admin.register(Miembro)
class MiembroAdmin(admin.ModelAdmin):
    # Agregamos 'activo' aquí para que coincida con list_editable
    list_display = ('get_status_icon', 'nombre_milsim', 'rango', 'escuadra', 'get_cursos_count', 'activo')
    
    list_display_links = ('nombre_milsim',)
    list_filter = ('rango', 'escuadra__compania', 'activo')
    search_fields = ('nombre_milsim',)
    filter_horizontal = ('cursos',) 
    
    # Ambos deben estar en list_display
    list_editable = ('rango', 'activo') 

    # --- Tus funciones de visualización ---
    def get_status_icon(self, obj):
        color = "#28a745" if obj.activo else "#dc3545"
        return format_html('<span style="color: {}; font-size: 1.2em;">●</span>', color)
    get_status_icon.short_description = "ST"

    def get_cursos_count(self, obj):
        count = obj.cursos.count()
        return format_html('<b>{}</b> Certs.', count)
    get_cursos_count.short_description = "Academia"
# --- ACADEMIA ---

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('sigla', 'nombre', 'fase')
    list_filter = ('fase',)
    search_fields = ('sigla', 'nombre')

@admin.register(Fase)
class FaseAdmin(admin.ModelAdmin):
    pass