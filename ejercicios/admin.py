# ejercicios/admin.py
from django.contrib import admin
from .models import CategoriaEjercicio, Ejercicio, BloquePrevio


@admin.register(CategoriaEjercicio)
class CategoriaEjercicioAdmin(admin.ModelAdmin):
    """
    Admin para categorías de ejercicios.
    """
    list_display = ('codigo', 'nombre', 'orden', 'activa')
    list_filter = ('activa',)
    search_fields = ('codigo', 'nombre')
    ordering = ('orden',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion')
        }),
        ('Configuración', {
            'fields': ('orden', 'activa')
        }),
    )


@admin.register(Ejercicio)
class EjercicioAdmin(admin.ModelAdmin):
    """
    Admin para ejercicios.
    """
    list_display = ('codigo', 'nombre', 'categoria', 'nivel', 'bloque', 'requiere_pro', 'activo')
    list_filter = ('categoria', 'nivel', 'bloque', 'requiere_pro', 'activo')
    search_fields = ('codigo', 'nombre', 'descripcion')
    ordering = ('bloque', 'categoria__orden', 'orden_en_bloque')
    
    fieldsets = (
        ('Identificación', {
            'fields': ('categoria', 'codigo', 'nombre')
        }),
        ('Contenido', {
            'fields': ('descripcion', 'instrucciones')
        }),
        ('Configuración', {
            'fields': ('nivel', 'bloque', 'orden_en_bloque', 'configuracion')
        }),
        ('Control de Acceso', {
            'fields': ('requiere_pro', 'activo')
        }),
    )
    
    # Acciones personalizadas
    actions = ['activar_ejercicios', 'desactivar_ejercicios', 'marcar_como_pro']
    
    def activar_ejercicios(self, request, queryset):
        queryset.update(activo=True)
        self.message_user(request, f'{queryset.count()} ejercicios activados')
    activar_ejercicios.short_description = "Activar ejercicios seleccionados"
    
    def desactivar_ejercicios(self, request, queryset):
        queryset.update(activo=False)
        self.message_user(request, f'{queryset.count()} ejercicios desactivados')
    desactivar_ejercicios.short_description = "Desactivar ejercicios seleccionados"
    
    def marcar_como_pro(self, request, queryset):
        queryset.update(requiere_pro=True)
        self.message_user(request, f'{queryset.count()} ejercicios marcados como Pro')
    marcar_como_pro.short_description = "Marcar como ejercicios Pro"
    
    # Filtros personalizados
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('categoria')


@admin.register(BloquePrevio)
class BloquePrevioAdmin(admin.ModelAdmin):
    """
    Admin para configurar prerequisitos de bloques.
    """
    list_display = ('bloque_actual', 'bloques_requeridos', 'test_requerido')
    ordering = ('bloque_actual',)
    
    fieldsets = (
        ('Configuración de Prerequisitos', {
            'fields': ('bloque_actual', 'bloques_requeridos', 'test_requerido'),
            'description': 'Configura qué bloques y tests son necesarios para acceder a cada bloque.'
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Agregar ayuda para los campos
        form.base_fields['bloques_requeridos'].help_text = 'Números de bloques separados por comas (ej: 1,2)'
        form.base_fields['test_requerido'].help_text = 'Nombre del test requerido (ej: inicial, test_1)'
        return form


# Configuración adicional del admin
admin.site.site_header = "Turbo Speed Reader - Administración de Ejercicios"