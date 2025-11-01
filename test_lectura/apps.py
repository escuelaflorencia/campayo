# test_lectura/apps.py
from django.apps import AppConfig


class TestLecturaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'test_lectura'
    verbose_name = 'Tests de Lectura Rápida'
    
    def ready(self):
        """
        Importar signals cuando la app esté lista.
        """
        try:
            import test_lectura.signals
        except ImportError:
            pass