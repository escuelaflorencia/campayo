# usuarios/utils.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import json
import random
import os

import logging

logger = logging.getLogger(__name__)


def enviar_email_template(usuario, asunto, template_name, contexto_extra=None, fail_silently=True):
    """
    Función genérica para enviar emails usando templates HTML y texto.
    
    Args:
        usuario: Instancia del modelo Usuario
        asunto: Asunto del email
        template_name: Nombre base del template (sin extensión)
        contexto_extra: Contexto adicional para el template
        fail_silently: Si True, no lanza excepción en caso de error
    """
    # Contexto base
    contexto = {
        'usuario': usuario,
        'site_name': getattr(settings, 'SITE_NAME', 'Campayo'),
        'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        'support_email': getattr(settings, 'SUPPORT_EMAIL', 'soporte@campayo.com'),
    }
    
    # Agregar contexto extra si se proporciona
    if contexto_extra:
        contexto.update(contexto_extra)
    
    try:
        # Renderizar templates
        mensaje_html = render_to_string(f'usuarios/emails/{template_name}.html', contexto)
        mensaje_texto = render_to_string(f'usuarios/emails/{template_name}.txt', contexto)
        
        # Enviar email
        send_mail(
            asunto,
            mensaje_texto,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@campayo.com'),
            [usuario.email],
            html_message=mensaje_html,
            fail_silently=fail_silently
        )
        
        logger.info(f"Email '{asunto}' enviado exitosamente a {usuario.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando email '{asunto}' a {usuario.email}: {e}")
        if not fail_silently:
            raise
        return False


def generar_link_recuperacion(usuario, request):
    """
    Genera un link de recuperación de contraseña para un usuario.
    
    Args:
        usuario: Instancia del modelo Usuario
        request: HttpRequest object
        
    Returns:
        str: URL completa para recuperación de contraseña
    """
    token = default_token_generator.make_token(usuario)
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    
    reset_url = request.build_absolute_uri(
        reverse('usuarios:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    )
    
    return reset_url


def validar_fuerza_password(password):
    """
    Valida la fuerza de una contraseña.
    
    Args:
        password: String de la contraseña
        
    Returns:
        tuple: (es_valida, lista_errores)
    """
    errores = []
    
    if len(password) < 8:
        errores.append('La contraseña debe tener al menos 8 caracteres.')
    
    if not any(c.isupper() for c in password):
        errores.append('La contraseña debe contener al menos una letra mayúscula.')
    
    if not any(c.islower() for c in password):
        errores.append('La contraseña debe contener al menos una letra minúscula.')
    
    if not any(c.isdigit() for c in password):
        errores.append('La contraseña debe contener al menos un número.')
    
    # Contraseñas comunes (puedes expandir esta lista)
    contraseñas_comunes = [
        'password', '123456', '123456789', 'qwerty', 'abc123',
        'password123', 'admin', 'letmein', 'welcome', 'monkey'
    ]
    
    if password.lower() in contraseñas_comunes:
        errores.append('Esta contraseña es demasiado común.')
    
    return len(errores) == 0, errores


def obtener_estadisticas_usuario(usuario):
    """
    Obtiene estadísticas resumidas de un usuario.
    
    Args:
        usuario: Instancia del modelo Usuario
        
    Returns:
        dict: Diccionario con estadísticas del usuario
    """
    from .models import ProgresoTests, EjercicioRealizado
    
    # Tests completados
    tests_completados = ProgresoTests.objects.filter(
        usuario=usuario, 
        completado=True
    ).count()
    
    # Mejor velocidad de lectura
    mejor_velocidad = 0
    progresos = ProgresoTests.objects.filter(usuario=usuario, completado=True)
    if progresos.exists():
        mejor_velocidad = max([p.velocidad_lectura for p in progresos])
    
    # Ejercicios realizados
    ejercicios_realizados = EjercicioRealizado.objects.filter(
        usuario=usuario,
        realizado=True
    ).count()
    
    # Último test realizado
    ultimo_test = ProgresoTests.objects.filter(
        usuario=usuario,
        completado=True
    ).order_by('-fecha_realizacion').first()
    
    return {
        'tests_completados': tests_completados,
        'mejor_velocidad_lectura': mejor_velocidad,
        'ejercicios_realizados': ejercicios_realizados,
        'ultimo_test': ultimo_test,
        'plan_actual': usuario.get_plan_display(),
        'es_pro': usuario.es_pro(),
        'es_gestor': usuario.es_gestor(),
    }


def filtrar_usuarios_para_gestor(queryset, filtros):
    """
    Aplica filtros a un queryset de usuarios para gestores.
    
    Args:
        queryset: QuerySet de usuarios
        filtros: Diccionario con filtros a aplicar
        
    Returns:
        QuerySet filtrado
    """
    from django.db.models import Q
    
    # Filtro por búsqueda de texto
    if filtros.get('busqueda'):
        busqueda = filtros['busqueda']
        queryset = queryset.filter(
            Q(nombre__icontains=busqueda) |
            Q(apellidos__icontains=busqueda) |
            Q(email__icontains=busqueda)
        )
    
    # Filtro por plan
    if filtros.get('plan'):
        queryset = queryset.filter(plan=filtros['plan'])
    
    # Filtro por fecha de registro
    if filtros.get('fecha_desde'):
        queryset = queryset.filter(fecha_registro__gte=filtros['fecha_desde'])
    
    if filtros.get('fecha_hasta'):
        queryset = queryset.filter(fecha_registro__lte=filtros['fecha_hasta'])
    
    # Filtro por actividad (usuarios que han completado al menos un test)
    if filtros.get('solo_activos'):
        from .models import ProgresoTests
        usuarios_activos = ProgresoTests.objects.filter(
            completado=True
        ).values_list('usuario_id', flat=True).distinct()
        queryset = queryset.filter(id__in=usuarios_activos)
    
    return queryset


def obtener_resumen_sistema():
    """
    Obtiene un resumen estadístico del sistema para gestores.
    
    Returns:
        dict: Estadísticas generales del sistema
    """
    from .models import Usuario, ProgresoTests, EjercicioRealizado
    from django.utils import timezone
    from datetime import timedelta
    
    # Usuarios
    total_usuarios = Usuario.objects.filter(tipo_usuario='usuario').count()
    usuarios_pro = Usuario.objects.filter(tipo_usuario='usuario', plan='pro').count()
    usuarios_gratuitos = Usuario.objects.filter(tipo_usuario='usuario', plan='gratuito').count()
    
    # Usuarios registrados esta semana
    hace_una_semana = timezone.now() - timedelta(days=7)
    usuarios_esta_semana = Usuario.objects.filter(
        tipo_usuario='usuario',
        fecha_registro__gte=hace_una_semana
    ).count()
    
    # Tests completados
    total_tests = ProgresoTests.objects.filter(completado=True).count()
    tests_esta_semana = ProgresoTests.objects.filter(
        completado=True,
        fecha_realizacion__gte=hace_una_semana
    ).count()
    
    # Ejercicios realizados
    total_ejercicios = EjercicioRealizado.objects.count()
    
    return {
        'total_usuarios': total_usuarios,
        'usuarios_pro': usuarios_pro,
        'usuarios_gratuitos': usuarios_gratuitos,
        'porcentaje_pro': round((usuarios_pro / total_usuarios * 100), 1) if total_usuarios > 0 else 0,
        'usuarios_esta_semana': usuarios_esta_semana,
        'total_tests_completados': total_tests,
        'tests_esta_semana': tests_esta_semana,
        'total_ejercicios_realizados': total_ejercicios,
    }


class EmailTemplates:
    """
    Clase con constantes para nombres de templates de email.
    """
    BIENVENIDA = 'bienvenida'
    CAMBIO_PLAN = 'cambio_plan'
    RECUPERAR_PASSWORD = 'recuperar_password'
    NOTIFICACION_PROGRESO = 'notificacion_progreso'
    
    @classmethod
    def get_asunto(cls, template_name, **kwargs):
        """
        Obtiene el asunto predefinido para cada tipo de email.
        """
        asuntos = {
            cls.BIENVENIDA: '¡Bienvenido a Campayo!',
            cls.CAMBIO_PLAN: f'Tu plan ha sido actualizado a {kwargs.get("plan_nuevo", "").title()}',
            cls.RECUPERAR_PASSWORD: 'Recuperar contraseña - Campayo',
            cls.NOTIFICACION_PROGRESO: '¡Felicidades por tu progreso en Campayo!',
        }
        return asuntos.get(template_name, 'Notificación de Campayo')
    
def cargar_frases():
    """
    Carga las frases desde el archivo JSON.
    """
    try:
        frases_path = os.path.join(settings.STATIC_ROOT or settings.STATICFILES_DIRS[0], 'frases', 'frases.json')
        with open(frases_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get('frases', [])
    except (FileNotFoundError, json.JSONDecodeError, IndexError):
        # Frases de respaldo en caso de error
        return [
            "La velocidad importa, pero la comprensión es el verdadero poder.",
            "Hoy es un buen día para superar tu récord personal, {nombre}.",
            "La constancia es la clave del progreso real.",
            "Tu cerebro es capaz de mucho más de lo que imaginas, {nombre}.",
            "¡Vamos {nombre}! Hoy puede ser el día en que superes tu mejor marca."
        ]


def personalizar_frase(frase, nombre_usuario):
    """
    Personaliza una frase reemplazando {nombre} con el nombre del usuario.
    
    Args:
        frase (str): La frase con marcadores de personalización
        nombre_usuario (str): El nombre del usuario
    
    Returns:
        str: La frase personalizada
    """
    return frase.replace('{nombre}', nombre_usuario)


def obtener_frase_aleatoria(nombre_usuario):
    """
    Obtiene una frase aleatoria personalizada para el usuario.
    
    Args:
        nombre_usuario (str): El nombre del usuario
    
    Returns:
        str: Una frase personalizada y aleatoria
    """
    frases = cargar_frases()
    frase_aleatoria = random.choice(frases)
    return personalizar_frase(frase_aleatoria, nombre_usuario)


def obtener_frases_personalizadas(nombre_usuario, cantidad=5):
    """
    Obtiene múltiples frases personalizadas para el usuario.
    
    Args:
        nombre_usuario (str): El nombre del usuario
        cantidad (int): Cantidad de frases a obtener
    
    Returns:
        list: Lista de frases personalizadas
    """
    frases = cargar_frases()
    frases_seleccionadas = random.sample(frases, min(cantidad, len(frases)))
    return [personalizar_frase(frase, nombre_usuario) for frase in frases_seleccionadas]