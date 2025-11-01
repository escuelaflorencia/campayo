# usuarios/models.py (VERSIÓN ACTUALIZADA)
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from .managers import UsuarioManager, ProgresoTestsManager, EjercicioRealizadoManager


class Usuario(AbstractUser):
    """
    Modelo de usuario simplificado.
    Solo campos esenciales: nombre, apellidos, email.
    """
    # Campos personalizados
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    
    # Tipo de usuario
    TIPO_USUARIO = [
        ('usuario', 'Usuario'),
        ('gestor', 'Gestor'),
    ]
    tipo_usuario = models.CharField(
        max_length=10, 
        choices=TIPO_USUARIO, 
        default='usuario'
    )
    
    # Plan de suscripción
    PLAN = [
        ('gratuito', 'Gratuito'),
        ('pro', 'Pro'),
    ]
    plan = models.CharField(
        max_length=10, 
        choices=PLAN, 
        default='gratuito'
    )
    
    # Fechas
    fecha_registro = models.DateTimeField(default=timezone.now)
    
    # Configuración de autenticación
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellidos']
    
    # Manager personalizado
    objects = UsuarioManager()
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.nombre} {self.apellidos} ({self.email})"
    
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellidos}"
    
    def es_gestor(self):
        """Verifica si el usuario es un gestor"""
        return self.tipo_usuario == 'gestor'
    
    def es_pro(self):
        """Verifica si el usuario tiene plan pro"""
        return self.plan == 'pro'
    
    def get_plan_display(self):
        return "Pro" if self.plan == 'pro' else "Gratuito"
    
    def puede_acceder_nivel(self, nivel):
        """
        Determina si el usuario puede acceder a un nivel específico.
        - Gratuito: niveles 1-3
        - Pro: todos los niveles
        - Gestor: todos los niveles
        """
        if self.es_gestor() or self.es_pro():
            return True
        return nivel <= 3
    
    def bloque_completado(self, bloque_numero):
        """
        Verifica si el usuario ha completado todos los ejercicios de un bloque.
        """
        from ejercicios.models import Ejercicio
        
        # Obtener todos los ejercicios activos del bloque
        ejercicios_bloque = Ejercicio.objects.filter(bloque=bloque_numero, activo=True)
        total_ejercicios = ejercicios_bloque.count()
        
        if total_ejercicios == 0:
            return True  # Si no hay ejercicios, consideramos el bloque completado
        
        # Contar ejercicios realizados por el usuario
        ejercicios_realizados = EjercicioRealizado.objects.filter(
            usuario=self,
            ejercicio_codigo__in=[e.codigo for e in ejercicios_bloque],
            realizado=True
        ).count()
        
        return ejercicios_realizados >= total_ejercicios
    
    def save(self, *args, **kwargs):
        # Guardar plan anterior para detectar cambios
        if self.pk:
            try:
                original = Usuario.objects.get(pk=self.pk)
                self._plan_anterior = original.plan
            except Usuario.DoesNotExist:
                self._plan_anterior = None
        
        super().save(*args, **kwargs)


class ProgresoTests(models.Model):
    """
    Modelo simplificado para el progreso en tests de lectura.
    Solo guarda el progreso de tests, no de ejercicios.
    """
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='progresos')
    test_nombre = models.CharField(max_length=100)  # 'inicial', 'test_1', 'test_2', etc.
    
    # Resultados del test
    velocidad_lectura = models.PositiveIntegerField(default=0)  # palabras por minuto
    velocidad_memorizacion = models.PositiveIntegerField(default=0)  # velocidad ajustada
    respuestas_correctas = models.PositiveSmallIntegerField(default=0)
    total_preguntas = models.PositiveSmallIntegerField(default=20)
    
    # Tiempos
    tiempo_lectura = models.DurationField()  # tiempo real de lectura
    fecha_realizacion = models.DateTimeField(default=timezone.now)
    completado = models.BooleanField(default=False)
    
    # Manager personalizado
    objects = ProgresoTestsManager()
    
    class Meta:
        verbose_name = 'Progreso en Test'
        verbose_name_plural = 'Progresos en Tests'
        unique_together = ['usuario', 'test_nombre']
    
    def __str__(self):
        return f"{self.usuario.nombre_completo} - {self.test_nombre}"
    
    def calcular_velocidad_memorizacion(self):
        """
        Calcula Vm según la fórmula del método Campayo:
        Se descuentan las 5 primeras respuestas y se ajusta el porcentaje
        """
        respuestas_ajustadas = max(0, self.respuestas_correctas - 5)
        porcentaje = (respuestas_ajustadas / 15) * 100  # 15 = 20 - 5
        vm = int(self.velocidad_lectura * (porcentaje / 100))
        return vm
    
    def save(self, *args, **kwargs):
        # Calcular automáticamente la velocidad de memorización
        if self.velocidad_lectura > 0:
            self.velocidad_memorizacion = self.calcular_velocidad_memorizacion()
        super().save(*args, **kwargs)


class EjercicioRealizado(models.Model):
    """
    Modelo simple para trackear qué ejercicios ha realizado cada usuario.
    Solo importa si lo ha hecho o no, no guarda métricas detalladas.
    """
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='ejercicios_realizados')
    ejercicio_codigo = models.CharField(max_length=20)  # ej: 'EL1', 'EO2', etc.
    realizado = models.BooleanField(default=True)
    fecha_realizacion = models.DateTimeField(default=timezone.now)
    
    # Manager personalizado
    objects = EjercicioRealizadoManager()
    
    class Meta:
        verbose_name = 'Ejercicio Realizado'
        verbose_name_plural = 'Ejercicios Realizados'
        unique_together = ['usuario', 'ejercicio_codigo']
    
    def __str__(self):
        return f"{self.usuario.nombre_completo} - {self.ejercicio_codigo}"

class SolicitudCambioPlan(models.Model):
    """
    Modelo para trackear solicitudes de cambio de plan de usuarios.
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesada', 'Procesada'),
        ('cancelada', 'Cancelada'),
    ]
    
    TIPO_SOLICITUD = [
        ('solicitar_pro', 'Solicitar Pro'),
        ('volver_gratuito', 'Volver a Gratuito'),
    ]
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='solicitudes_cambio_plan')
    tipo_solicitud = models.CharField(max_length=20, choices=TIPO_SOLICITUD)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    fecha_solicitud = models.DateTimeField(default=timezone.now)
    fecha_procesada = models.DateTimeField(null=True, blank=True)
    procesada_por = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='solicitudes_procesadas'
    )
    notas = models.TextField(blank=True, help_text="Notas internas para gestores")
    
    class Meta:
        verbose_name = 'Solicitud de Cambio de Plan'
        verbose_name_plural = 'Solicitudes de Cambio de Plan'
        ordering = ['-fecha_solicitud']
        # ELIMINAMOS unique_together que causaba el problema
        indexes = [
            models.Index(fields=['estado', 'fecha_solicitud']),
            models.Index(fields=['tipo_solicitud', 'estado']),
            models.Index(fields=['usuario', 'estado']),
        ]
    
    def __str__(self):
        return f"{self.usuario.nombre_completo} - {self.get_tipo_solicitud_display()} ({self.estado})"
    
    def save(self, *args, **kwargs):
        # Si se marca como procesada o cancelada, guardar fecha
        if self.estado in ['procesada', 'cancelada'] and not self.fecha_procesada:
            self.fecha_procesada = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def dias_pendiente(self):
        """Calcula cuántos días lleva pendiente la solicitud"""
        if self.estado != 'pendiente':
            return 0
        return (timezone.now() - self.fecha_solicitud).days
    
    @staticmethod
    def puede_usuario_solicitar_cambio(usuario):
        """Verifica si un usuario puede hacer una nueva solicitud"""
        return not SolicitudCambioPlan.objects.filter(
            usuario=usuario, 
            estado='pendiente'
        ).exists()
