# usuarios/views.py
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.utils import timezone
import json

from .models import Usuario, ProgresoTests, SolicitudCambioPlan
from .forms import (
    RegistroForm, LoginForm, EditarPerfilForm, CambiarPasswordForm,
    RecuperarPasswordForm, BuscarUsuarioForm, CambiarPlanForm
)
from .decorators import usuario_no_autenticado_required
from .utils import obtener_frase_aleatoria

logger = logging.getLogger(__name__)

@usuario_no_autenticado_required
def home_view(request):
    """
    Vista de bienvenida principal.
    Redirige según el estado de autenticación del usuario.
    """
    return render(request, 'home.html')


@usuario_no_autenticado_required
def registro_view(request):
    """
    Vista de registro de usuarios.
    """
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Enviar email de bienvenida
            enviar_email_bienvenida(user)
            
            # Hacer login automático
            login(request, user)
            messages.success(request, f'¡Bienvenido {user.nombre}! Tu cuenta ha sido creada exitosamente.')
            return redirect('usuarios:dashboard')
    else:
        form = RegistroForm()
    
    return render(request, 'usuarios/registro.html', {'form': form})


@usuario_no_autenticado_required
def login_view(request):
    """
    Vista de login personalizada.
    """
    logger.info("=" * 80)
    logger.info("LOGIN VIEW CALLED")
    logger.info(f"Request method: {request.method}")
    logger.info(f"User authenticated: {request.user.is_authenticated}")
    logger.info(f"User: {request.user}")
    
    if request.method == 'POST':
        logger.info("POST request received")
        logger.info(f"POST data: {request.POST}")
        
        form = LoginForm(request, data=request.POST)
        logger.info(f"Form created")
        
        if form.is_valid():
            logger.info("Form is VALID!")
            
            # Obtener el usuario autenticado del formulario
            user = form.get_user()
            logger.info(f"User from form: {user}")
            logger.info(f"User username: {user.username}")
            logger.info(f"User email: {user.email}")
            logger.info(f"User tipo: {user.tipo_usuario}")
            logger.info(f"User es_gestor: {user.es_gestor()}")
            
            # Hacer login
            logger.info("Calling login()")
            login(request, user)
            logger.info(f"Login successful. User is now authenticated: {request.user.is_authenticated}")
            
            messages.success(request, f'¡Bienvenido de nuevo, {user.nombre}!')
            
            # Manejar redirección después del login
            next_url = request.GET.get('next')
            logger.info(f"Next URL from GET: {next_url}")
            
            if next_url:
                logger.info(f"Redirecting to next_url: {next_url}")
                return redirect(next_url)
            else:
                logger.info("Redirecting to usuarios:dashboard")
                redirect_response = redirect('usuarios:dashboard')
                logger.info(f"Redirect response: {redirect_response}")
                logger.info(f"Redirect URL: {redirect_response.url}")
                logger.info(f"Redirect status code: {redirect_response.status_code}")
                return redirect_response
        else:
            logger.warning(f"Form is NOT valid. Errors: {form.errors}")
            logger.warning(f"Form errors as HTML: {form.errors.as_ul()}")
    else:
        logger.info("GET request - rendering empty form")
        form = LoginForm(request)
    
    logger.info("Returning render with login.html")
    logger.info("=" * 80)
    return render(request, 'usuarios/login.html', {'form': form})


def logout_view(request):
    """
    Vista de logout.
    """
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('home')


@login_required
def dashboard_view(request):
    """
    Dashboard principal para usuarios autenticados.
    Diferente vista para gestores vs usuarios normales.
    """
    logger.info("=" * 80)
    logger.info("DASHBOARD VIEW CALLED")
    logger.info(f"User: {request.user}")
    logger.info(f"User authenticated: {request.user.is_authenticated}")
    logger.info(f"User tipo: {request.user.tipo_usuario}")
    logger.info(f"User es_gestor: {request.user.es_gestor()}")
    
    usuario = request.user
    
    if usuario.es_gestor():
        logger.info("Rendering GESTOR dashboard")
        # Dashboard para gestores
        total_usuarios = Usuario.objects.filter(tipo_usuario='usuario').count()
        usuarios_pro = Usuario.objects.filter(tipo_usuario='usuario', plan='pro').count()
        usuarios_gratuitos = Usuario.objects.filter(tipo_usuario='usuario', plan='gratuito').count()
        
        # Contar solicitudes pendientes
        solicitudes_pendientes = SolicitudCambioPlan.objects.filter(estado='pendiente').count()
        
        # Usuarios recientes (iniciales - se cargan con HTMX después)
        usuarios_recientes = Usuario.objects.filter(
            tipo_usuario='usuario'
        ).order_by('-fecha_registro')[:10]
        
        context = {
            'es_gestor': True,
            'total_usuarios': total_usuarios,
            'usuarios_pro': usuarios_pro,
            'usuarios_gratuitos': usuarios_gratuitos,
            'usuarios': usuarios_recientes,  # Para la carga inicial
            'busqueda': '',
            'solicitudes_pendientes': solicitudes_pendientes,
        }
        logger.info(f"Context for gestor: {context}")
    else:
        logger.info("Rendering USUARIO dashboard")
        # Dashboard para usuarios normales
        # Obtener progreso del usuario
        progresos = ProgresoTests.objects.filter(
            usuario=usuario
        ).order_by('-fecha_realizacion')
        
        # Estadísticas básicas
        tests_completados = progresos.filter(completado=True).count()
        mejor_velocidad = 0
        if progresos.filter(completado=True).exists():
            mejor_velocidad = max([
                p.velocidad_lectura for p in progresos.filter(completado=True) 
                if p.velocidad_lectura
            ], default=0)
        
        # Verificar si tiene solicitud pendiente
        tiene_solicitud_pendiente = SolicitudCambioPlan.objects.filter(
            usuario=usuario,
            estado='pendiente'
        ).exists()
        
        context = {
            'es_gestor': False,
            'tests_completados': tests_completados,
            'mejor_velocidad': mejor_velocidad,
            'progresos_recientes': progresos[:3],
            'plan_actual': usuario.get_plan_display(),
            'puede_acceder_pro': usuario.es_pro(),
            'tiene_solicitud_pendiente': tiene_solicitud_pendiente,
            'frase_motivacional': obtener_frase_aleatoria(usuario.nombre),
        }
        logger.info(f"Context for usuario: {context}")
    
    logger.info("Rendering template usuarios/dashboard.html")
    logger.info("=" * 80)
    return render(request, 'usuarios/dashboard.html', context)


@login_required
def solicitar_cambio_plan_view(request):
    """
    Vista para que usuarios soliciten cambio de plan.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    usuario = request.user
    
    # Verificar que el usuario no sea gestor
    if usuario.es_gestor():
        return JsonResponse({'error': 'Los gestores no pueden solicitar cambios de plan'}, status=403)
    
    # Verificar que no tenga una solicitud pendiente
    if not SolicitudCambioPlan.puede_usuario_solicitar_cambio(usuario):
        return JsonResponse({'error': 'Ya tienes una solicitud pendiente'}, status=400)
    
    # Determinar tipo de solicitud
    tipo_solicitud = 'solicitar_pro' if usuario.plan == 'gratuito' else 'volver_gratuito'
    
    # Crear solicitud
    solicitud = SolicitudCambioPlan.objects.create(
        usuario=usuario,
        tipo_solicitud=tipo_solicitud
    )
    
    # Enviar email a gestores
    enviar_email_nueva_solicitud_gestor(solicitud)
    
    # Respuesta exitosa
    return JsonResponse({
        'success': True,
        'mensaje': 'Solicitud enviada correctamente. Será procesada por un administrador.',
        'tipo_solicitud': solicitud.get_tipo_solicitud_display(),
        'tiene_solicitud_pendiente': True
    })


@login_required
def cancelar_solicitud_plan_view(request):
    """
    Vista para que usuarios cancelen su solicitud pendiente.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Buscar la solicitud pendiente del usuario
        solicitud = SolicitudCambioPlan.objects.get(
            usuario=request.user,
            estado='pendiente'
        )
        
        # En lugar de cambiar el estado, simplemente marcar como cancelada
        # y actualizar la fecha de procesada
        solicitud.estado = 'cancelada'
        solicitud.fecha_procesada = timezone.now()
        solicitud.procesada_por = request.user  # El usuario se cancela a sí mismo
        solicitud.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Solicitud cancelada correctamente.',
            'tiene_solicitud_pendiente': False
        })
        
    except SolicitudCambioPlan.DoesNotExist:
        return JsonResponse({'error': 'No tienes solicitudes pendientes'}, status=404)
    
    except Exception as e:
        logger.error(f"Error cancelando solicitud: {e}")
        return JsonResponse({'error': 'Error procesando la cancelación'}, status=500)


@login_required
def procesar_solicitud_plan_view(request):
    """
    Vista para que gestores procesen solicitudes de cambio de plan.
    """
    if not request.user.es_gestor():
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        solicitud_id = request.POST.get('solicitud_id')
        accion = request.POST.get('accion')  # 'aprobar' o 'rechazar'
        
        solicitud = SolicitudCambioPlan.objects.get(
            id=solicitud_id,
            estado='pendiente'
        )
        
        if accion == 'aprobar':
            # Cambiar plan del usuario
            usuario = solicitud.usuario
            if solicitud.tipo_solicitud == 'solicitar_pro':
                usuario.plan = 'pro'
            else:  # volver_gratuito
                usuario.plan = 'gratuito'
            usuario.save()
            
            # Marcar solicitud como procesada
            solicitud.estado = 'procesada'
            solicitud.procesada_por = request.user
            solicitud.save()
            
            # Enviar email al usuario sobre aprobación
            enviar_email_resultado_solicitud_usuario(solicitud, aprobada=True)
            
            mensaje = f'Plan cambiado a {usuario.get_plan_display()} para {usuario.nombre_completo}'
            
        elif accion == 'rechazar':
            solicitud.estado = 'cancelada'
            solicitud.procesada_por = request.user
            solicitud.save()
            
            # Enviar email al usuario sobre rechazo
            enviar_email_resultado_solicitud_usuario(solicitud, aprobada=False)
            
            mensaje = f'Solicitud rechazada para {solicitud.usuario.nombre_completo}'
        
        else:
            return JsonResponse({'error': 'Acción no válida'}, status=400)
        
        return JsonResponse({
            'success': True,
            'mensaje': mensaje
        })
        
    except SolicitudCambioPlan.DoesNotExist:
        return JsonResponse({'error': 'Solicitud no encontrada'}, status=404)
    except Exception as e:
        logger.error(f"Error procesando solicitud: {e}")
        return JsonResponse({'error': 'Error procesando solicitud'}, status=500)


@login_required 
def gestionar_solicitudes_view(request):
    """
    Vista para que gestores vean y filtren solicitudes de cambio de plan.
    """
    if not request.user.es_gestor():
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('usuarios:dashboard')
    
    # Filtros
    filtro_estado = request.GET.get('estado', 'pendiente')
    filtro_tipo = request.GET.get('tipo', '')
    busqueda = request.GET.get('busqueda', '')
    
    # Query base
    solicitudes = SolicitudCambioPlan.objects.select_related('usuario', 'procesada_por')
    
    # Aplicar filtros
    if filtro_estado:
        solicitudes = solicitudes.filter(estado=filtro_estado)
    
    if filtro_tipo:
        solicitudes = solicitudes.filter(tipo_solicitud=filtro_tipo)
    
    if busqueda:
        solicitudes = solicitudes.filter(
            Q(usuario__nombre__icontains=busqueda) |
            Q(usuario__apellidos__icontains=busqueda) |
            Q(usuario__email__icontains=busqueda)
        )
    
    # Ordenar por fecha
    solicitudes = solicitudes.order_by('-fecha_solicitud')
    
    # Paginación
    paginator = Paginator(solicitudes, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas rápidas
    stats = {
        'pendientes': SolicitudCambioPlan.objects.filter(estado='pendiente').count(),
        'procesadas_hoy': SolicitudCambioPlan.objects.filter(
            estado='procesada',
            fecha_procesada__date=timezone.now().date()
        ).count(),
    }
    
    context = {
        'page_obj': page_obj,
        'filtro_estado': filtro_estado,
        'filtro_tipo': filtro_tipo,
        'busqueda': busqueda,
        'stats': stats,
        'estados': SolicitudCambioPlan.ESTADO_CHOICES,
        'tipos': SolicitudCambioPlan.TIPO_SOLICITUD,
    }
    
    return render(request, 'usuarios/gestionar_solicitudes.html', context)


@login_required
def editar_perfil_view(request):
    """
    Vista para editar información personal del usuario.
    """
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu información ha sido actualizada correctamente.')
            return redirect('usuarios:dashboard')
    else:
        form = EditarPerfilForm(instance=request.user)
    
    return render(request, 'usuarios/editar_perfil.html', {'form': form})


@login_required
def cambiar_password_view(request):
    """
    Vista para cambiar contraseña.
    """
    if request.method == 'POST':
        form = CambiarPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Actualizar la sesión para mantener al usuario logueado
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            messages.success(request, 'Tu contraseña ha sido cambiada correctamente.')
            return redirect('usuarios:dashboard')
    else:
        form = CambiarPasswordForm(request.user)
    
    return render(request, 'usuarios/cambiar_password.html', {'form': form})


@require_POST
@login_required
def buscar_usuarios_view(request):
    """
    Vista HTMX para búsqueda dinámica de usuarios.
    Solo accesible para gestores.
    """
    if not request.user.es_gestor():
        return HttpResponse('No autorizado', status=403)
    
    busqueda = request.POST.get('busqueda', '').strip()
    
    if len(busqueda) < 2:
        # Sin búsqueda, mostrar usuarios recientes
        usuarios = Usuario.objects.filter(
            tipo_usuario='usuario'
        ).order_by('-fecha_registro')[:10]
    else:
        # Búsqueda activa
        usuarios = Usuario.objects.filter(
            tipo_usuario='usuario'
        ).filter(
            Q(nombre__icontains=busqueda) |
            Q(apellidos__icontains=busqueda) |
            Q(email__icontains=busqueda)
        ).order_by('-fecha_registro')[:20]
    
    return render(request, 'usuarios/partials/lista_usuarios.html', {
        'usuarios': usuarios,
        'busqueda': busqueda
    })

@login_required
def cambiar_plan_usuario_view(request):
    """
    Endpoint HTMX para cambiar el plan de un usuario.
    """
    if not request.user.es_gestor():
        return JsonResponse({'error': 'No autorizado'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        usuario_id = request.POST.get('usuario_id')
        nuevo_plan = request.POST.get('nuevo_plan')
        
        if not usuario_id or not nuevo_plan:
            return JsonResponse({'error': 'Datos incompletos'}, status=400)
        
        usuario = Usuario.objects.get(id=usuario_id, tipo_usuario='usuario')
        plan_anterior = usuario.plan
        usuario.plan = nuevo_plan
        usuario.save()
        
        # Enviar email de cambio de plan
        enviar_email_cambio_plan(usuario, plan_anterior, nuevo_plan)
        
        # Renderizar solo la tarjeta actualizada
        html = render_to_string('usuarios/partials/user_card.html', {
            'usuario': usuario
        })
        
        return HttpResponse(html)
        
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        logger.error(f"Error cambiando plan de usuario: {e}")
        return JsonResponse({'error': 'Error al cambiar plan'}, status=500)


@login_required
def gestionar_usuarios_view(request):
    """
    Vista completa para gestión de usuarios (solo gestores).
    """
    if not request.user.es_gestor():
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('usuarios:dashboard')
    
    # Obtener usuarios con paginación
    usuarios = Usuario.objects.filter(tipo_usuario='usuario').order_by('-fecha_registro')
    paginator = Paginator(usuarios, 20)  # 20 usuarios por página
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form_buscar': BuscarUsuarioForm(),
        'total_usuarios': usuarios.count(),
        'usuarios_pro': usuarios.filter(plan='pro').count(),
        'usuarios_gratuitos': usuarios.filter(plan='gratuito').count()
    }
    
    return render(request, 'usuarios/gestionar_usuarios.html', context)


# ============================================================================
# FUNCIONES AUXILIARES PARA EMAILS
# ============================================================================

def enviar_email_bienvenida(usuario):
    """
    Envía email de bienvenida a nuevo usuario.
    """
    asunto = f'¡Bienvenido a Campayo, {usuario.nombre}!'
    mensaje_html = render_to_string('usuarios/emails/bienvenida.html', {
        'usuario': usuario,
        'login_url': getattr(settings, 'SITE_URL', 'http://localhost:8000') + reverse('usuarios:login'),
        'dashboard_url': getattr(settings, 'SITE_URL', 'http://localhost:8000') + reverse('usuarios:dashboard'),
    })
    mensaje_texto = render_to_string('usuarios/emails/bienvenida.txt', {
        'usuario': usuario,
        'dashboard_url': getattr(settings, 'SITE_URL', 'http://localhost:8000') + reverse('usuarios:dashboard'),
    })
    
    try:
        send_mail(
            asunto,
            mensaje_texto,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@campayo.com'),
            [usuario.email],
            html_message=mensaje_html,
            fail_silently=True
        )
        logger.info(f"✓ Email de bienvenida enviado a {usuario.email}")
    except Exception as e:
        logger.error(f"✗ Error enviando email de bienvenida a {usuario.email}: {e}")


def enviar_email_nueva_solicitud_gestor(solicitud):
    """
    Envía email a todos los gestores cuando hay una nueva solicitud.
    """
    # Obtener todos los gestores
    gestores = Usuario.objects.filter(tipo_usuario='gestor', is_active=True)
    
    if not gestores.exists():
        logger.warning("No hay gestores activos para notificar la nueva solicitud")
        return
    
    emails_gestores = [gestor.email for gestor in gestores]
    
    asunto = f'Nueva solicitud de {solicitud.get_tipo_solicitud_display().lower()} - {solicitud.usuario.nombre_completo}'
    
    contexto = {
        'solicitud': solicitud,
        'gestionar_url': getattr(settings, 'SITE_URL', 'http://localhost:8000') + reverse('usuarios:gestionar_solicitudes'),
    }
    
    mensaje_html = render_to_string('usuarios/emails/nueva_solicitud_gestor.html', contexto)
    mensaje_texto = render_to_string('usuarios/emails/nueva_solicitud_gestor.txt', contexto)
    
    try:
        send_mail(
            asunto,
            mensaje_texto,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@campayo.com'),
            emails_gestores,
            html_message=mensaje_html,
            fail_silently=True
        )
        logger.info(f"✓ Email de nueva solicitud enviado a {len(emails_gestores)} gestores")
    except Exception as e:
        logger.error(f"✗ Error enviando email de nueva solicitud a gestores: {e}")


def enviar_email_resultado_solicitud_usuario(solicitud, aprobada):
    """
    Envía email al usuario notificando el resultado de su solicitud.
    """
    usuario = solicitud.usuario
    
    if aprobada:
        asunto = f'¡Tu plan ha sido actualizado a {usuario.get_plan_display()}! - Campayo'
    else:
        asunto = 'Solicitud de cambio de plan procesada - Campayo'
    
    contexto = {
        'usuario': usuario,
        'solicitud': solicitud,
        'aprobada': aprobada,
        'dashboard_url': getattr(settings, 'SITE_URL', 'http://localhost:8000') + reverse('usuarios:dashboard'),
    }
    
    mensaje_html = render_to_string('usuarios/emails/resultado_solicitud_usuario.html', contexto)
    mensaje_texto = render_to_string('usuarios/emails/resultado_solicitud_usuario.txt', contexto)
    
    try:
        send_mail(
            asunto,
            mensaje_texto,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@campayo.com'),
            [usuario.email],
            html_message=mensaje_html,
            fail_silently=True
        )
        status = "aprobada" if aprobada else "rechazada"
        logger.info(f"✓ Email de solicitud {status} enviado a {usuario.email}")
    except Exception as e:
        logger.error(f"✗ Error enviando email de resultado a {usuario.email}: {e}")


def enviar_email_cambio_plan(usuario, plan_anterior, plan_nuevo):
    """
    Envía email de notificación de cambio de plan directo por gestor.
    """
    asunto = f'Tu plan ha sido actualizado a {plan_nuevo.title()} - Campayo'
    
    contexto = {
        'usuario': usuario,
        'plan_anterior': plan_anterior,
        'plan_nuevo': plan_nuevo,
        'dashboard_url': getattr(settings, 'SITE_URL', 'http://localhost:8000') + reverse('usuarios:dashboard'),
    }
    
    mensaje_html = render_to_string('usuarios/emails/resultado_solicitud_usuario.html', {
        **contexto,
        'aprobada': True,
        'solicitud': None,
    })
    mensaje_texto = render_to_string('usuarios/emails/resultado_solicitud_usuario.txt', {
        **contexto,
        'aprobada': True,
        'solicitud': None,
    })
    
    try:
        send_mail(
            asunto,
            mensaje_texto,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@campayo.com'),
            [usuario.email],
            html_message=mensaje_html,
            fail_silently=True
        )
        logger.info(f"✓ Email de cambio de plan enviado a {usuario.email}")
    except Exception as e:
        logger.error(f"✗ Error enviando email de cambio de plan a {usuario.email}: {e}")


# ============================================================================
# VISTAS DE RESET DE CONTRASEÑA (Django built-in con personalización)
# ============================================================================

class CustomPasswordResetView(PasswordResetView):
    """
    Vista personalizada para reset de contraseña.
    """
    template_name = 'usuarios/password_reset_form.html'
    email_template_name = 'usuarios/emails/password_reset_email.html'
    success_url = reverse_lazy('usuarios:password_reset_done')
    
    def get_form_class(self):
        return RecuperarPasswordForm


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Vista personalizada para confirmar reset de contraseña.
    """
    template_name = 'usuarios/password_reset_confirm.html'
    success_url = reverse_lazy('usuarios:password_reset_complete')