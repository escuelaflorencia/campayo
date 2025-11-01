# test_lectura/models.py - VERSIÓN CORREGIDA
from django.db import models
from django.utils import timezone
from usuarios.models import Usuario


class TestLectura(models.Model):
    """
    Modelo simplificado para tests de lectura rápida.
    """
    # Identificación
    nombre = models.CharField(max_length=100, unique=True)  # 'test_inicial', 'test_1', etc.
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    instrucciones = models.TextField()
    
    # Contenido del test
    texto_titulo = models.CharField(max_length=200)
    texto_contenido = models.TextField()
    texto_autor = models.CharField(max_length=100, blank=True)
    numero_palabras = models.PositiveIntegerField(default=0)
    
    # Configuración
    DIFICULTAD_CHOICES = [
        ('inicial', 'Test Inicial'),
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
    ]
    dificultad = models.CharField(max_length=15, choices=DIFICULTAD_CHOICES, default='inicial')
    numero_test = models.PositiveSmallIntegerField(default=1)  # 1, 2, 3, 4...
    
    # Control de acceso
    requiere_password = models.BooleanField(default=False)
    password_acceso = models.CharField(max_length=20, blank=True)
    requiere_pro = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    
    # Prerequisitos - CORREGIDO
    test_previo_requerido = models.CharField(max_length=50, blank=True)  # nombre del test previo
    bloque_requerido = models.PositiveSmallIntegerField(null=True, blank=True)  # bloque que debe completarse
    
    # Fechas
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Test de Lectura'
        verbose_name_plural = 'Tests de Lectura'
        ordering = ['numero_test', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.titulo}"
    
    def save(self, *args, **kwargs):
        # Calcular número de palabras automáticamente
        if self.texto_contenido and not self.numero_palabras:
            self.numero_palabras = len(self.texto_contenido.split())
        super().save(*args, **kwargs)
    
    def puede_acceder(self, usuario, password=None):
        """
        Verifica si un usuario puede acceder a este test.
        LÓGICA DE DESBLOQUEO CORREGIDA:
        - test_inicial: SIEMPRE accesible para cualquier usuario registrado
        - test_1: requiere test_inicial completado Y todos los ejercicios del bloque 1
        - test_2: requiere test_1 completado Y todos los ejercicios del bloque 2
        - Otros tests: requieren test_2 completado Y todos los ejercicios del bloque 3
        """
        # Verificaciones básicas
        if not self.activo:
            return False, "Test no disponible"
        
        if usuario.es_gestor():
            return True, ""
        
        # Verificar plan pro si es requerido
        if self.requiere_pro and not usuario.es_pro():
            return False, "Requiere plan Pro"
        
        # Verificar password si es requerido
        if self.requiere_password:
            if not password or password != self.password_acceso:
                return False, "Password incorrecto"
        
        # LÓGICA DE DESBLOQUEO ESPECÍFICA
        if self.nombre == 'test_inicial':
            # TEST INICIAL: SIEMPRE ACCESIBLE para usuarios registrados
            return True, ""
        
        elif self.nombre == 'test_1':
            # TEST 1: requiere test_inicial completado Y bloque 1 completado
            from usuarios.models import ProgresoTests
            
            # Verificar test_inicial completado
            test_inicial_completado = ProgresoTests.objects.filter(
                usuario=usuario,
                test_nombre='test_inicial',
                completado=True
            ).exists()
            
            if not test_inicial_completado:
                return False, "Debes completar primero el Test Inicial"
            
            # Verificar bloque 1 completado completamente
            if not usuario.bloque_completado(1):
                return False, "Debes completar todos los ejercicios del Bloque 1 (niveles 1, 2 y 3)"
            
            # Si llegamos aquí, puede acceder
            return True, ""
        
        elif self.nombre == 'test_2':
            # TEST 2: requiere test_1 completado Y bloque 2 completado
            from usuarios.models import ProgresoTests
            
            # Verificar test_1 completado
            test_1_completado = ProgresoTests.objects.filter(
                usuario=usuario,
                test_nombre='test_1',
                completado=True
            ).exists()
            
            if not test_1_completado:
                return False, "Debes completar primero el Test 1"
            
            # Verificar bloque 2 completado completamente
            if not usuario.bloque_completado(2):
                return False, "Debes completar todos los ejercicios del Bloque 2 (niveles 4, 5 y 6)"
            
            # Si llegamos aquí, puede acceder
            return True, ""
        
        else:
            # RESTO DE TESTS: requieren test_2 completado Y bloque 3 completado
            from usuarios.models import ProgresoTests
            
            # Verificar test_2 completado
            test_2_completado = ProgresoTests.objects.filter(
                usuario=usuario,
                test_nombre='test_2',
                completado=True
            ).exists()
            
            if not test_2_completado:
                return False, "Debes completar primero el Test 2"
            
            # Verificar bloque 3 completado completamente
            if not usuario.bloque_completado(3):
                return False, "Debes completar todos los ejercicios del Bloque 3 (niveles 7, 8 y 9)"
            
            # Si llegamos aquí, puede acceder
            return True, ""


class PreguntaTest(models.Model):
    """
    Preguntas para los tests de lectura.
    """
    test = models.ForeignKey(TestLectura, on_delete=models.CASCADE, related_name='preguntas')
    pregunta = models.TextField()
    orden = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Pregunta de Test'
        verbose_name_plural = 'Preguntas de Test'
        ordering = ['orden']
    
    def __str__(self):
        return f"{self.test.nombre} - Pregunta {self.orden + 1}"


class OpcionRespuesta(models.Model):
    """
    Opciones de respuesta para las preguntas.
    """
    pregunta = models.ForeignKey(PreguntaTest, on_delete=models.CASCADE, related_name='opciones')
    texto = models.TextField()
    es_correcta = models.BooleanField(default=False)
    orden = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Opción de Respuesta'
        verbose_name_plural = 'Opciones de Respuesta'
        ordering = ['orden']
    
    def __str__(self):
        return f"{self.pregunta} - Opción {self.orden + 1}"


class SesionTest(models.Model):
    """
    Registro de una sesión de test realizada por un usuario.
    Simplificado para guardar solo lo esencial.
    """
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='sesiones_test')
    test = models.ForeignKey(TestLectura, on_delete=models.CASCADE, related_name='sesiones')
    
    # Tiempos
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    tiempo_lectura = models.DurationField(null=True, blank=True)  # Solo tiempo de lectura
    
    # Resultados
    respuestas_correctas = models.PositiveSmallIntegerField(default=0)
    total_preguntas = models.PositiveSmallIntegerField(default=20)
    velocidad_lectura = models.PositiveIntegerField(default=0)  # palabras por minuto
    velocidad_memorizacion = models.PositiveIntegerField(default=0)  # V ajustada
    
    # Estado
    completado = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Sesión de Test'
        verbose_name_plural = 'Sesiones de Test'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"{self.usuario.nombre_completo} - {self.test.nombre} ({self.fecha_inicio.strftime('%d/%m/%Y')})"
    
    def calcular_velocidades(self):
        """
        Calcula las velocidades de lectura y memorización.
        """
        if self.tiempo_lectura and self.test.numero_palabras > 0:
            # Convertir duración a minutos
            minutos = self.tiempo_lectura.total_seconds() / 60
            
            # Calcular velocidad de lectura (palabras por minuto)
            self.velocidad_lectura = int(self.test.numero_palabras / minutos)
            
            # Calcular velocidad de memorización (método Campayo)
            respuestas_ajustadas = max(0, self.respuestas_correctas - 5)
            porcentaje = (respuestas_ajustadas / 15) * 100  # 15 = 20 - 5
            self.velocidad_memorizacion = int(self.velocidad_lectura * (porcentaje / 100))
            
            self.save()
    
    def finalizar_sesion(self):
        """
        Marca la sesión como completada y actualiza el progreso del usuario.
        """
        self.fecha_fin = timezone.now()
        self.completado = True
        self.calcular_velocidades()
        
        # Actualizar o crear progreso en ProgresoTests
        from usuarios.models import ProgresoTests
        progreso, created = ProgresoTests.objects.get_or_create(
            usuario=self.usuario,
            test_nombre=self.test.nombre,
            defaults={
                'tiempo_lectura': self.tiempo_lectura,
                'velocidad_lectura': self.velocidad_lectura,
                'velocidad_memorizacion': self.velocidad_memorizacion,
                'respuestas_correctas': self.respuestas_correctas,
                'total_preguntas': self.total_preguntas,
                'completado': True
            }
        )
        
        if not created:
            # Actualizar si ya existía (mejor resultado)
            if self.velocidad_lectura > progreso.velocidad_lectura:
                progreso.tiempo_lectura = self.tiempo_lectura
                progreso.velocidad_lectura = self.velocidad_lectura
                progreso.velocidad_memorizacion = self.velocidad_memorizacion
                progreso.respuestas_correctas = self.respuestas_correctas
                progreso.total_preguntas = self.total_preguntas
                progreso.fecha_realizacion = self.fecha_fin
                progreso.save()


class RespuestaUsuario(models.Model):
    """
    Respuestas dadas por el usuario en una sesión de test.
    """
    sesion = models.ForeignKey(SesionTest, on_delete=models.CASCADE, related_name='respuestas')
    pregunta = models.ForeignKey(PreguntaTest, on_delete=models.CASCADE)
    opcion_seleccionada = models.ForeignKey(OpcionRespuesta, on_delete=models.CASCADE)
    es_correcta = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Respuesta de Usuario'
        verbose_name_plural = 'Respuestas de Usuario'
        unique_together = ['sesion', 'pregunta']
    
    def __str__(self):
        return f"{self.sesion.usuario.nombre_completo} - {self.pregunta}"
    
    def save(self, *args, **kwargs):
        # Verificar automáticamente si la respuesta es correcta
        self.es_correcta = self.opcion_seleccionada.es_correcta
        super().save(*args, **kwargs)