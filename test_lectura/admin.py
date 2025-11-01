# test_lectura/admin.py
from django.contrib import admin
from .models import TestLectura, PreguntaTest, OpcionRespuesta, SesionTest, RespuestaUsuario


class OpcionRespuestaInline(admin.TabularInline):
    """
    Inline para opciones de respuesta dentro de preguntas.
    """
    model = OpcionRespuesta
    extra = 4  # 4 opciones por pregunta
    fields = ('texto', 'es_correcta', 'orden')


class PreguntaTestInline(admin.TabularInline):
    """
    Inline para preguntas dentro de tests.
    """
    model = PreguntaTest
    extra = 0
    fields = ('pregunta', 'orden')
    show_change_link = True


@admin.register(TestLectura)
class TestLecturaAdmin(admin.ModelAdmin):
    """
    Admin para tests de lectura.
    """
    list_display = ('nombre', 'titulo', 'dificultad', 'numero_test', 'numero_palabras', 
                    'requiere_password', 'requiere_pro', 'activo')
    list_filter = ('dificultad', 'requiere_password', 'requiere_pro', 'activo', 'fecha_creacion')
    search_fields = ('nombre', 'titulo', 'texto_autor')
    ordering = ('numero_test', 'nombre')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'titulo', 'descripcion', 'instrucciones')
        }),
        ('Contenido del Test', {
            'fields': ('texto_titulo', 'texto_contenido', 'texto_autor', 'numero_palabras'),
            'classes': ('collapse',)
        }),
        ('Configuración', {
            'fields': ('dificultad', 'numero_test')
        }),
        ('Control de Acceso', {
            'fields': ('requiere_password', 'password_acceso', 'requiere_pro', 'activo')
        }),
        ('Prerequisitos', {
            'fields': ('test_previo_requerido', 'bloque_requerido'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [PreguntaTestInline]
    
    # Acciones personalizadas
    actions = ['activar_tests', 'desactivar_tests', 'calcular_palabras']
    
    def activar_tests(self, request, queryset):
        queryset.update(activo=True)
        self.message_user(request, f'{queryset.count()} tests activados')
    activar_tests.short_description = "Activar tests seleccionados"
    
    def desactivar_tests(self, request, queryset):
        queryset.update(activo=False)
        self.message_user(request, f'{queryset.count()} tests desactivados')
    desactivar_tests.short_description = "Desactivar tests seleccionados"
    
    def calcular_palabras(self, request, queryset):
        updated = 0
        for test in queryset:
            if test.texto_contenido:
                test.numero_palabras = len(test.texto_contenido.split())
                test.save()
                updated += 1
        self.message_user(request, f'Número de palabras calculado para {updated} tests')
    calcular_palabras.short_description = "Recalcular número de palabras"


@admin.register(PreguntaTest)
class PreguntaTestAdmin(admin.ModelAdmin):
    """
    Admin para preguntas de tests.
    """
    list_display = ('__str__', 'test', 'orden')
    list_filter = ('test',)
    search_fields = ('pregunta', 'test__nombre')
    ordering = ('test', 'orden')
    
    inlines = [OpcionRespuestaInline]
    
    fieldsets = (
        ('Pregunta', {
            'fields': ('test', 'pregunta', 'orden')
        }),
    )


@admin.register(OpcionRespuesta)
class OpcionRespuestaAdmin(admin.ModelAdmin):
    """
    Admin para opciones de respuesta.
    """
    list_display = ('__str__', 'texto', 'es_correcta', 'orden')
    list_filter = ('es_correcta', 'pregunta__test')
    search_fields = ('texto', 'pregunta__pregunta')
    ordering = ('pregunta', 'orden')


@admin.register(SesionTest)
class SesionTestAdmin(admin.ModelAdmin):
    """
    Admin para sesiones de test.
    """
    list_display = ('usuario', 'test', 'fecha_inicio', 'velocidad_lectura', 
                    'velocidad_memorizacion', 'respuestas_correctas', 'completado')
    list_filter = ('test', 'completado', 'fecha_inicio')
    search_fields = ('usuario__email', 'usuario__nombre', 'test__nombre')
    readonly_fields = ('fecha_inicio', 'velocidad_lectura', 'velocidad_memorizacion')
    ordering = ('-fecha_inicio',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('usuario', 'test', 'completado')
        }),
        ('Tiempos', {
            'fields': ('fecha_inicio', 'fecha_fin', 'tiempo_lectura'),
            'classes': ('collapse',)
        }),
        ('Resultados', {
            'fields': ('respuestas_correctas', 'total_preguntas', 
                      'velocidad_lectura', 'velocidad_memorizacion')
        }),
    )
    
    # Acciones personalizadas
    actions = ['recalcular_velocidades']
    
    def recalcular_velocidades(self, request, queryset):
        updated = 0
        for sesion in queryset:
            if sesion.tiempo_lectura and sesion.test.numero_palabras > 0:
                sesion.calcular_velocidades()
                updated += 1
        self.message_user(request, f'Velocidades recalculadas para {updated} sesiones')
    recalcular_velocidades.short_description = "Recalcular velocidades"


@admin.register(RespuestaUsuario)
class RespuestaUsuarioAdmin(admin.ModelAdmin):
    """
    Admin para respuestas de usuarios.
    """
    list_display = ('sesion', 'pregunta', 'opcion_seleccionada', 'es_correcta')
    list_filter = ('es_correcta', 'sesion__test', 'sesion__usuario')
    search_fields = ('sesion__usuario__email', 'pregunta__pregunta')
    ordering = ('sesion', 'pregunta__orden')
    
    readonly_fields = ('es_correcta',)