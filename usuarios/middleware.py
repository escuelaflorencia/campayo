# usuarios/middleware.py
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class PlanAccessMiddleware:
    """
    Middleware que verifica el acceso basado en planes de usuario.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs que requieren plan Pro
        self.pro_required_urls = [
            '/ejercicios/nivel/4/',
            '/ejercicios/nivel/5/',
            '/ejercicios/nivel/6/',
            '/ejercicios/nivel/7/',
            '/ejercicios/nivel/8/',
            '/ejercicios/nivel/9/',
        ]
        
        # URLs que solo pueden acceder gestores
        self.gestor_only_urls = [
            '/usuarios/gestionar/',
            '/usuarios/buscar/',
            '/usuarios/cambiar-plan/',
        ]
    
    def __call__(self, request):
        # Verificar acceso antes de procesar la vista
        response = self.process_request(request)
        if response:
            return response
        
        response = self.get_response(request)
        return response
    
    def process_request(self, request):
        """
        Procesa la petición antes de que llegue a la vista.
        """
        if not request.user.is_authenticated:
            return None
        
        path = request.path
        
        # Verificar URLs que requieren plan Pro
        if any(path.startswith(url) for url in self.pro_required_urls):
            if not request.user.es_pro() and not request.user.es_gestor():
                messages.warning(request, 'Esta funcionalidad requiere un plan Pro.')
                return redirect('usuarios:dashboard')
        
        # Verificar URLs solo para gestores
        if any(path.startswith(url) for url in self.gestor_only_urls):
            if not request.user.es_gestor():
                messages.error(request, 'No tienes permisos para acceder a esta página.')
                return redirect('usuarios:dashboard')
        
        return None


class UserActivityMiddleware:
    """
    Middleware para trackear actividad del usuario.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Registrar actividad después de procesar la vista
        if request.user.is_authenticated and hasattr(request.user, 'ultima_actividad'):
            self.update_last_activity(request.user)
        
        return response
    
    def update_last_activity(self, user):
        """
        Actualiza la última actividad del usuario.
        """
        try:
            from django.utils import timezone
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
        except Exception as e:
            logger.error(f"Error actualizando última actividad para {user.email}: {e}")


class ErrorHandlingMiddleware:
    """
    Middleware para manejo centralizado de errores de usuario.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            return self.handle_exception(request, e)
    
    def handle_exception(self, request, exception):
        """
        Maneja excepciones y redirige apropiadamente.
        """
        logger.error(f"Error en {request.path}: {exception}")
        
        # Para peticiones AJAX/HTMX, devolver error JSON
        if request.headers.get('HX-Request') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({
                'error': 'Ha ocurrido un error. Por favor, intenta de nuevo.',
                'reload': True
            }, status=500)
        
        # Para peticiones normales, redirigir con mensaje
        messages.error(request, 'Ha ocurrido un error inesperado. Por favor, intenta de nuevo.')
        
        if request.user.is_authenticated:
            return redirect('usuarios:dashboard')
        else:
            return redirect('home')


class HTMXMiddleware:
    """
    Middleware para mejorar el manejo de peticiones HTMX.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Agregar flag para identificar peticiones HTMX fácilmente
        request.htmx = bool(request.headers.get('HX-Request'))
        
        response = self.get_response(request)
        
        # Agregar headers HTMX si es necesario
        if request.htmx:
            # Permitir que HTMX maneje redirects
            if response.status_code == 302:
                response['HX-Redirect'] = response['Location']
        
        return response


class SecurityHeadersMiddleware:
    """
    Middleware para agregar headers de seguridad.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Agregar headers de seguridad
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # CSP básico para HTMX
        if not response.get('Content-Security-Policy'):
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
                "img-src 'self' data:; "
                "connect-src 'self';"
            )
        
        return response


class MaintenanceModeMiddleware:
    """
    Middleware para modo de mantenimiento.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        from django.conf import settings
        
        # Verificar si está en modo mantenimiento
        if getattr(settings, 'MAINTENANCE_MODE', False):
            # Permitir acceso a gestores
            if request.user.is_authenticated and request.user.es_gestor():
                response = self.get_response(request)
                response['X-Maintenance-Mode'] = 'Active (Gestor Access)'
                return response
            
            # Mostrar página de mantenimiento para otros usuarios
            from django.template.response import TemplateResponse
            return TemplateResponse(request, 'maintenance.html', status=503)
        
        return self.get_response(request)


class TimezoneMiddleware:
    """
    Middleware para manejar zonas horarias por usuario.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        from django.utils import timezone
        import pytz
        
        # Activar zona horaria española por defecto
        if request.user.is_authenticated:
            # Se puede extender para guardar timezone preferido por usuario
            user_timezone = 'Europe/Madrid'
        else:
            user_timezone = 'Europe/Madrid'
        
        timezone.activate(pytz.timezone(user_timezone))
        
        response = self.get_response(request)
        
        timezone.deactivate()
        return response