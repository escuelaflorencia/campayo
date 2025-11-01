# ejercicios/models.py
from django.db import models


class CategoriaEjercicio(models.Model):
    """
    Categorías de ejercicios del método Campayo.
    """
    codigo = models.CharField(max_length=10, unique=True)  # EL, EO, EPM, EVM, EMD
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    orden = models.PositiveSmallIntegerField(default=0)
    activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Categoría de Ejercicio'
        verbose_name_plural = 'Categorías de Ejercicios'
        ordering = ['orden']
    
    def __str__(self):
        return f"{self.codigo}: {self.nombre}"


class Ejercicio(models.Model):
    """
    Modelo simplificado para ejercicios.
    Se gestionan desde Django Admin y se generan con scripts.
    """
    # Identificación
    categoria = models.ForeignKey(CategoriaEjercicio, on_delete=models.CASCADE, related_name='ejercicios')
    codigo = models.CharField(max_length=20, unique=True)  # ej: EL1, EL2, EO1, etc.
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    instrucciones = models.TextField()
    
    # Configuración
    nivel = models.PositiveSmallIntegerField(default=1)  # 1-9
    bloque = models.PositiveSmallIntegerField(default=1)  # 1-3
    orden_en_bloque = models.PositiveSmallIntegerField(default=0)
    
    # Configuración específica (JSON para flexibilidad)
    configuracion = models.JSONField(default=dict, blank=True)
    # Ejemplo de configuración:
    # {
    #     "palabras_por_pantalla": 2,
    #     "columnas": 1,
    #     "tiempo_display": 1000,
    #     "tipo_objeto": "circle",
    #     "posiciones": 9
    # }
    
    # Control
    activo = models.BooleanField(default=True)
    requiere_pro = models.BooleanField(default=False)  # True para niveles 4+
    
    class Meta:
        verbose_name = 'Ejercicio'
        verbose_name_plural = 'Ejercicios'
        ordering = ['bloque', 'categoria__orden', 'orden_en_bloque']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre} (Nivel {self.nivel})"
    
    def save(self, *args, **kwargs):
        # Auto-configurar si requiere pro basado en el nivel
        self.requiere_pro = self.nivel > 3
        super().save(*args, **kwargs)
    
    def puede_acceder(self, usuario, password=None):
        """
        Verifica si un usuario puede acceder a este test.
        LÓGICA DE DESBLOQUEO CORREGIDA
        """
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
        
        # LÓGICA ESPECÍFICA POR TIPO DE TEST
        if self.nombre == 'test_inicial':
            return True, ""
        
        elif self.nombre == 'test_1':
            # Requiere test_inicial + bloque 1 completo
            from usuarios.models import ProgresoTests
            
            if not ProgresoTests.objects.filter(
                usuario=usuario,
                test_nombre='test_inicial',
                completado=True
            ).exists():
                return False, "Debes completar primero el Test Inicial"
            
            if not usuario.bloque_completado(1):
                return False, "Debes completar todos los ejercicios del Bloque 1 (niveles 1, 2 y 3)"
        
        elif self.nombre == 'test_2':
            # Requiere test_1 + bloque 2 completo
            from usuarios.models import ProgresoTests
            
            if not ProgresoTests.objects.filter(
                usuario=usuario,
                test_nombre='test_1',
                completado=True
            ).exists():
                return False, "Debes completar primero el Test 1"
            
            if not usuario.bloque_completado(2):
                return False, "Debes completar todos los ejercicios del Bloque 2 (niveles 4, 5 y 6)"
        
        else:
            # Resto de tests: requieren test_2 + bloque 3 completo
            from usuarios.models import ProgresoTests
            
            if not ProgresoTests.objects.filter(
                usuario=usuario,
                test_nombre='test_2',
                completado=True
            ).exists():
                return False, "Debes completar primero el Test 2"
            
            if not usuario.bloque_completado(3):
                return False, "Debes completar todos los ejercicios del Bloque 3 (niveles 7, 8 y 9)"
        
        return True, ""
    
    def get_requisitos_acceso(self, usuario):
        """
        Devuelve los requisitos no cumplidos para acceder al ejercicio.
        """
        requisitos = []
        
        if not self.activo:
            requisitos.append("Ejercicio no disponible")
        
        if self.requiere_pro and not usuario.es_pro() and not usuario.es_gestor():
            requisitos.append("Requiere plan Pro")
        
        if not usuario.puede_acceder_nivel(self.nivel):
            if self.nivel > 3:
                requisitos.append("Requiere plan Pro")
            else:
                requisitos.append(f"Nivel {self.nivel} no disponible")
        
        return requisitos
    
    def get_requisitos_para_bloque(self):
        """
        Obtiene los requisitos específicos para acceder al bloque de este ejercicio.
        """
        try:
            bloque_previo = BloquePrevio.objects.get(bloque_actual=self.bloque)
            return bloque_previo
        except BloquePrevio.DoesNotExist:
            return None

    def puede_acceder_con_detalles(self, usuario):
        """
        Verifica acceso con detalles específicos de por qué no puede acceder.
        """
        if not self.activo:
            return False, "Ejercicio no disponible"
        
        if usuario.es_gestor():
            return True, ""
        
        if self.requiere_pro and not usuario.es_pro():
            return False, "Requiere plan Pro"
        
        # Verificar requisitos del bloque
        bloque_requisito = self.get_requisitos_para_bloque()
        if bloque_requisito and not bloque_requisito.usuario_cumple_requisitos(usuario):
            # Determinar exactamente qué falta
            if bloque_requisito.test_requerido:
                from usuarios.models import ProgresoTests
                if not ProgresoTests.objects.filter(
                    usuario=usuario,
                    test_nombre=bloque_requisito.test_requerido,
                    completado=True
                ).exists():
                    return False, f"Debes completar el test: {bloque_requisito.test_requerido}"
            
            for bloque_req in bloque_requisito.get_bloques_requeridos_list():
                if not usuario.bloque_completado(bloque_req):
                    return False, f"Debes completar todos los ejercicios del bloque {bloque_req}"
        
        return True, ""

class BloquePrevio(models.Model):
    """
    Define qué bloques deben completarse antes de acceder a otro bloque.
    Simplifica el sistema de prerequisitos.
    """
    bloque_actual = models.PositiveSmallIntegerField(unique=True)
    bloques_requeridos = models.CharField(max_length=50)  # ej: "1,2" para requerir bloques 1 y 2
    test_requerido = models.CharField(max_length=50, blank=True)  # ej: "inicial" o "test_1"
    
    class Meta:
        verbose_name = 'Bloque Previo'
        verbose_name_plural = 'Bloques Previos'
        ordering = ['bloque_actual']
    
    def __str__(self):
        return f"Bloque {self.bloque_actual} - Requiere: {self.bloques_requeridos}"
    
    def get_bloques_requeridos_list(self):
        """Convierte la cadena de bloques requeridos en lista de enteros"""
        if not self.bloques_requeridos:
            return []
        return [int(b.strip()) for b in self.bloques_requeridos.split(',') if b.strip()]
    
    def usuario_cumple_requisitos(self, usuario):
        """
        Verifica si un usuario cumple los requisitos para acceder al bloque.
        """
        # Verificar test requerido
        if self.test_requerido:
            from usuarios.models import ProgresoTests
            if not ProgresoTests.objects.filter(
                usuario=usuario, 
                test_nombre=self.test_requerido,
                completado=True
            ).exists():
                return False
        
        # Verificar bloques completados completamente
        bloques_requeridos = self.get_bloques_requeridos_list()
        for bloque in bloques_requeridos:
            if not usuario.bloque_completado(bloque):
                return False
        
        return True