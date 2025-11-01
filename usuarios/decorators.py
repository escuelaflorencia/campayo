# usuarios/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)


def usuario_no_autenticado_required(view_func):
    """
    Decorador que redirige al dashboard si el usuario ya está autenticado.
    Usar en vistas de login, registro y landing.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        logger.info(f"DECORATOR: usuario_no_autenticado_required called for {view_func.__name__}")
        logger.info(f"DECORATOR: User authenticated: {request.user.is_authenticated}")
        
        if request.user.is_authenticated:
            logger.info(f"DECORATOR: User is authenticated, redirecting to dashboard")
            logger.info(f"DECORATOR: User: {request.user}")
            redirect_response = redirect('usuarios:dashboard')
            logger.info(f"DECORATOR: Redirect URL: {redirect_response.url}")
            return redirect_response
        
        logger.info(f"DECORATOR: User not authenticated, calling view function")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def gestor_required(view_func):
    """
    Decorador que requiere que el usuario sea un gestor.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
            return redirect('usuarios:login')
        
        if not request.user.es_gestor():
            messages.error(request, 'No tienes permisos para acceder a esta página.')
            return redirect('usuarios:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def gestor_required_ajax(view_func):
    """
    Decorador que requiere que el usuario sea un gestor para vistas AJAX/HTMX.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'No autenticado'}, status=401)
        
        if not request.user.es_gestor():
            return JsonResponse({'error': 'No autorizado'}, status=403)
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def plan_pro_required(view_func):
    """
    Decorador que requiere que el usuario tenga plan Pro.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
            return redirect('usuarios:login')
        
        if not request.user.es_pro() and not request.user.es_gestor():
            messages.warning(request, 'Esta funcionalidad requiere un plan Pro.')
            return redirect('usuarios:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def usuario_regular_required(view_func):
    """
    Decorador que requiere que el usuario NO sea gestor (solo usuarios regulares).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
            return redirect('usuarios:login')
        
        if request.user.es_gestor():
            messages.info(request, 'Esta página es solo para usuarios regulares.')
            return redirect('usuarios:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def ajax_login_required(view_func):
    """
    Decorador para vistas AJAX que requieren autenticación.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'No autenticado', 'redirect': '/usuarios/login/'}, status=401)
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def check_plan_access(nivel_requerido):
    """
    Decorador paramétrico que verifica si el usuario puede acceder a un nivel específico.
    
    Args:
        nivel_requerido: Nivel mínimo requerido (1-9)
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
                return redirect('usuarios:login')
            
            if not request.user.puede_acceder_nivel(nivel_requerido):
                if nivel_requerido > 3:
                    messages.warning(request, f'Este contenido requiere un plan Pro. Nivel {nivel_requerido} no disponible.')
                else:
                    messages.error(request, f'No tienes acceso al nivel {nivel_requerido}.')
                return redirect('usuarios:dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def htmx_required(view_func):
    """
    Decorador que requiere que la petición sea HTMX.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.headers.get('HX-Request'):
            return HttpResponseForbidden('Esta vista solo acepta peticiones HTMX.')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def post_required(view_func):
    """
    Decorador que requiere que la petición sea POST.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.method != 'POST':
            return HttpResponseForbidden('Esta vista solo acepta peticiones POST.')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def combined_decorators(*decorators):
    """
    Combina múltiples decoradores en uno solo.
    
    Uso: @combined_decorators(login_required, gestor_required)
    """
    def decorator(view_func):
        for dec in reversed(decorators):
            view_func = dec(view_func)
        return view_func
    return decorator


# Decoradores combinados comunes
def gestor_ajax_required(view_func):
    """
    Decorador combinado para vistas AJAX que requieren ser gestor.
    """
    return combined_decorators(htmx_required, gestor_required_ajax)(view_func)


def plan_pro_ajax_required(view_func):
    """
    Decorador combinado para vistas AJAX que requieren plan Pro.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'No autenticado'}, status=401)
        
        if not request.user.es_pro() and not request.user.es_gestor():
            return JsonResponse({'error': 'Requiere plan Pro', 'upgrade_needed': True}, status=403)
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view