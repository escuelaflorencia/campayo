# usuarios/managers.py
from django.contrib.auth.models import BaseUserManager
from django.db import models


class UsuarioManager(BaseUserManager):
    """
    Manager personalizado para el modelo Usuario.
    """
    
    def create_user(self, email, nombre, apellidos, password=None, **extra_fields):
        """
        Crea y guarda un usuario regular.
        """
        if not email:
            raise ValueError('El email es obligatorio')
        if not nombre:
            raise ValueError('El nombre es obligatorio')
        if not apellidos:
            raise ValueError('Los apellidos son obligatorios')
        
        email = self.normalize_email(email)
        
        # Generar username único basado en el email
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        
        while self.model.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = self.model(
            email=email,
            username=username,
            nombre=nombre,
            apellidos=apellidos,
            **extra_fields
        )
        
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, nombre, apellidos, password=None, **extra_fields):
        """
        Crea y guarda un superusuario.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('tipo_usuario', 'gestor')
        extra_fields.setdefault('plan', 'pro')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')
        
        return self.create_user(email, nombre, apellidos, password, **extra_fields)
    
    def gestores(self):
        """
        Retorna solo usuarios gestores.
        """
        return self.filter(tipo_usuario='gestor')
    
    def usuarios_regulares(self):
        """
        Retorna solo usuarios regulares (no gestores).
        """
        return self.filter(tipo_usuario='usuario')
    
    def usuarios_pro(self):
        """
        Retorna usuarios con plan pro.
        """
        return self.filter(plan='pro', tipo_usuario='usuario')
    
    def usuarios_gratuitos(self):
        """
        Retorna usuarios con plan gratuito.
        """
        return self.filter(plan='gratuito', tipo_usuario='usuario')
    
    def usuarios_activos(self):
        """
        Retorna usuarios que han completado al menos un test.
        """
        from .models import ProgresoTests
        usuarios_con_progreso = ProgresoTests.objects.filter(
            completado=True
        ).values_list('usuario_id', flat=True).distinct()
        
        return self.filter(id__in=usuarios_con_progreso, tipo_usuario='usuario')
    
    def buscar(self, termino):
        """
        Busca usuarios por nombre, apellidos o email.
        """
        from django.db.models import Q
        
        return self.filter(
            Q(nombre__icontains=termino) |
            Q(apellidos__icontains=termino) |
            Q(email__icontains=termino)
        )
    
    def registrados_en_periodo(self, fecha_inicio, fecha_fin):
        """
        Retorna usuarios registrados en un período específico.
        """
        return self.filter(
            fecha_registro__gte=fecha_inicio,
            fecha_registro__lte=fecha_fin
        )


class ProgresoTestsManager(models.Manager):
    """
    Manager personalizado para ProgresoTests.
    """
    
    def completados(self):
        """
        Retorna solo progresos completados.
        """
        return self.filter(completado=True)
    
    def por_usuario(self, usuario):
        """
        Retorna progresos de un usuario específico.
        """
        return self.filter(usuario=usuario)
    
    def mejores_velocidades(self, limite=10):
        """
        Retorna los mejores registros de velocidad.
        """
        return self.completados().order_by('-velocidad_lectura')[:limite]
    
    def estadisticas_usuario(self, usuario):
        """
        Retorna estadísticas de progreso de un usuario.
        """
        progresos = self.por_usuario(usuario).completados()
        
        if not progresos.exists():
            return {
                'tests_completados': 0,
                'mejor_velocidad_lectura': 0,
                'mejor_velocidad_memorizacion': 0,
                'promedio_velocidad_lectura': 0,
                'ultimo_test': None
            }
        
        velocidades_lectura = [p.velocidad_lectura for p in progresos]
        velocidades_memorizacion = [p.velocidad_memorizacion for p in progresos]
        
        return {
            'tests_completados': progresos.count(),
            'mejor_velocidad_lectura': max(velocidades_lectura),
            'mejor_velocidad_memorizacion': max(velocidades_memorizacion),
            'promedio_velocidad_lectura': sum(velocidades_lectura) // len(velocidades_lectura),
            'ultimo_test': progresos.order_by('-fecha_realizacion').first()
        }
    
    def ranking_velocidad(self, limite=20):
        """
        Retorna ranking de usuarios por mejor velocidad de lectura.
        """
        return self.completados().values(
            'usuario__nombre',
            'usuario__apellidos'
        ).annotate(
            mejor_velocidad=models.Max('velocidad_lectura')
        ).order_by('-mejor_velocidad')[:limite]


class EjercicioRealizadoManager(models.Manager):
    """
    Manager personalizado para EjercicioRealizado.
    """
    
    def por_usuario(self, usuario):
        """
        Retorna ejercicios realizados por un usuario.
        """
        return self.filter(usuario=usuario, realizado=True)
    
    def por_categoria(self, categoria_codigo):
        """
        Retorna ejercicios realizados de una categoría específica.
        """
        return self.filter(
            ejercicio_codigo__startswith=categoria_codigo,
            realizado=True
        )
    
    def estadisticas_usuario(self, usuario):
        """
        Retorna estadísticas de ejercicios de un usuario.
        """
        ejercicios = self.por_usuario(usuario)
        
        return {
            'total_ejercicios': ejercicios.count(),
            'ejercicios_por_categoria': {
                'EL': ejercicios.filter(ejercicio_codigo__startswith='EL').count(),
                'EO': ejercicios.filter(ejercicio_codigo__startswith='EO').count(),
                'EPM': ejercicios.filter(ejercicio_codigo__startswith='EPM').count(),
                'EVM': ejercicios.filter(ejercicio_codigo__startswith='EVM').count(),
                'EMD': ejercicios.filter(ejercicio_codigo__startswith='EMD').count(),
            },
            'ultimo_ejercicio': ejercicios.order_by('-fecha_realizacion').first()
        }
    
    def usuarios_mas_activos(self, limite=10):
        """
        Retorna los usuarios más activos en ejercicios.
        """
        return self.filter(realizado=True).values(
            'usuario__nombre',
            'usuario__apellidos'
        ).annotate(
            total_ejercicios=models.Count('id')
        ).order_by('-total_ejercicios')[:limite]