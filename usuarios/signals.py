# usuarios/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from .models import Usuario


@receiver(post_save, sender=Usuario)
def usuario_post_save(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta después de guardar un Usuario.
    """
    if created and instance.tipo_usuario == 'usuario':
        # Enviar email de bienvenida a usuarios nuevos (no gestores)
        enviar_email_bienvenida_signal(instance)


def enviar_email_bienvenida_signal(usuario):
    """
    Envía email de bienvenida cuando se crea un usuario nuevo.
    Función separada para poder ser llamada desde signals.
    """
    asunto = '¡Bienvenido a Turbo Speed Reader - Lectura Rápida!'
    
    # Contexto para el template
    contexto = {
        'usuario': usuario,
        'site_name': 'Campayo',
        'login_url': getattr(settings, 'SITE_URL', 'http://localhost:8000') + reverse('usuarios:login'),
        'dashboard_url': getattr(settings, 'SITE_URL', 'http://localhost:8000') + reverse('usuarios:dashboard'),
    }
    
    # Renderizar templates
    mensaje_html = render_to_string('usuarios/emails/bienvenida.html', contexto)
    mensaje_texto = render_to_string('usuarios/emails/bienvenida.txt', contexto)
    
    try:
        send_mail(
            asunto,
            mensaje_texto,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@campayo.com'),
            [usuario.email],
            html_message=mensaje_html,
            fail_silently=True  # No fallar si hay error de email
        )
        print(f"✓ Email de bienvenida enviado a {usuario.email}")
    except Exception as e:
        print(f"✗ Error enviando email de bienvenida a {usuario.email}: {e}")


@receiver(post_save, sender=Usuario)
def notificar_cambio_plan(sender, instance, created, **kwargs):
    """
    Notifica cuando cambia el plan de un usuario.
    """
    if not created and instance.tipo_usuario == 'usuario':
        # Verificar si cambió el plan
        if hasattr(instance, '_plan_anterior') and instance._plan_anterior != instance.plan:
            enviar_email_cambio_plan_signal(instance, instance._plan_anterior, instance.plan)


def enviar_email_cambio_plan_signal(usuario, plan_anterior, plan_nuevo):
    """
    Envía email cuando cambia el plan de un usuario.
    """
    asunto = f'Tu plan en Campayo ha sido actualizado a {plan_nuevo.title()}'
    
    contexto = {
        'usuario': usuario,
        'plan_anterior': plan_anterior,
        'plan_nuevo': plan_nuevo,
        'site_name': 'Campayo',
        'dashboard_url': getattr(settings, 'SITE_URL', 'http://localhost:8000') + reverse('usuarios:dashboard'),
        'es_upgrade': plan_nuevo == 'pro',
        'es_downgrade': plan_nuevo == 'gratuito',
    }
    
    mensaje_html = render_to_string('usuarios/emails/cambio_plan.html', contexto)
    mensaje_texto = render_to_string('usuarios/emails/cambio_plan.txt', contexto)
    
    try:
        send_mail(
            asunto,
            mensaje_texto,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@campayo.com'),
            [usuario.email],
            html_message=mensaje_html,
            fail_silently=True
        )
        print(f"✓ Email de cambio de plan enviado a {usuario.email}")
    except Exception as e:
        print(f"✗ Error enviando email de cambio de plan a {usuario.email}: {e}")