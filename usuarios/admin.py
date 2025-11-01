# usuarios/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, ProgresoTests, EjercicioRealizado


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """
    Admin simplificado para el modelo Usuario.
    """
    list_display = ('email', 'nombre', 'apellidos', 'tipo_usuario', 'plan', 'fecha_registro')
    list_filter = ('tipo_usuario', 'plan', 'fecha_registro')
    search_fields = ('email', 'nombre', 'apellidos')
    ordering = ('email',)
    
    # Definir fieldsets para el formulario de edición
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        ('Información Personal', {
            'fields': ('nombre', 'apellidos')
        }),
        ('Configuración de Usuario', {
            'fields': ('tipo_usuario', 'plan')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'fecha_registro'),
            'classes': ('collapse',)
        }),
    )
    
    # Para crear usuarios
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'apellidos', 'password1', 'password2', 'tipo_usuario', 'plan'),
        }),
    )
    
    # Acciones personalizadas
    actions = ['hacer_pro', 'hacer_gratuito', 'hacer_gestor']
    
    def hacer_pro(self, request, queryset):
        queryset.update(plan='pro')
        self.message_user(request, f'{queryset.count()} usuarios cambiados a Plan Pro')
    hacer_pro.short_description = "Cambiar a Plan Pro"
    
    def hacer_gratuito(self, request, queryset):
        queryset.update(plan='gratuito')
        self.message_user(request, f'{queryset.count()} usuarios cambiados a Plan Gratuito')
    hacer_gratuito.short_description = "Cambiar a Plan Gratuito"
    
    def hacer_gestor(self, request, queryset):
        queryset.update(tipo_usuario='gestor')
        self.message_user(request, f'{queryset.count()} usuarios cambiados a Gestor')
    hacer_gestor.short_description = "Cambiar a Gestor"


@admin.register(ProgresoTests)
class ProgresoTestsAdmin(admin.ModelAdmin):
    """
    Admin para el progreso en tests.
    """
    list_display = ('usuario', 'test_nombre', 'velocidad_lectura', 'velocidad_memorizacion', 
                    'respuestas_correctas', 'total_preguntas', 'completado', 'fecha_realizacion')
    list_filter = ('test_nombre', 'completado', 'fecha_realizacion')
    search_fields = ('usuario__email', 'usuario__nombre', 'usuario__apellidos')
    readonly_fields = ('velocidad_memorizacion', 'fecha_realizacion')
    ordering = ('-fecha_realizacion',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('usuario', 'test_nombre', 'completado')
        }),
        ('Resultados', {
            'fields': ('respuestas_correctas', 'total_preguntas', 'tiempo_lectura')
        }),
        ('Velocidades (calculadas automáticamente)', {
            'fields': ('velocidad_lectura', 'velocidad_memorizacion'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_realizacion',),
            'classes': ('collapse',)
        }),
    )


@admin.register(EjercicioRealizado)
class EjercicioRealizadoAdmin(admin.ModelAdmin):
    """
    Admin para tracking de ejercicios realizados.
    """
    list_display = ('usuario', 'ejercicio_codigo', 'realizado', 'fecha_realizacion')
    list_filter = ('realizado', 'ejercicio_codigo', 'fecha_realizacion')
    search_fields = ('usuario__email', 'usuario__nombre', 'ejercicio_codigo')
    ordering = ('-fecha_realizacion',)
    
    # Acciones personalizadas
    actions = ['marcar_realizado', 'marcar_no_realizado']
    
    def marcar_realizado(self, request, queryset):
        queryset.update(realizado=True)
        self.message_user(request, f'{queryset.count()} ejercicios marcados como realizados')
    marcar_realizado.short_description = "Marcar como realizado"
    
    def marcar_no_realizado(self, request, queryset):
        queryset.update(realizado=False)
        self.message_user(request, f'{queryset.count()} ejercicios marcados como no realizados')
    marcar_no_realizado.short_description = "Marcar como no realizado"