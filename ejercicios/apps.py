# ejercicios/apps.py
from django.apps import AppConfig


class EjerciciosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ejercicios'
    verbose_name = 'Ejercicios de Entrenamiento'
    
    def ready(self):
        """
        Importar signals cuando la app esté lista.
        """
        try:
            import ejercicios.signals
        except ImportError:
            pass