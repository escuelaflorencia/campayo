# usuarios/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'usuarios'

urlpatterns = [
    # ============================================================================
    # AUTENTICACIÓN BÁSICA
    # ============================================================================
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # ============================================================================
    # DASHBOARD Y PERFIL
    # ============================================================================
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('editar-perfil/', views.editar_perfil_view, name='editar_perfil'),
    path('cambiar-password/', views.cambiar_password_view, name='cambiar_password'),
    
    # ============================================================================
    # SOLICITUDES DE CAMBIO DE PLAN
    # ============================================================================
    path('solicitar-cambio-plan/', views.solicitar_cambio_plan_view, name='solicitar_cambio_plan'),
    path('cancelar-solicitud-plan/', views.cancelar_solicitud_plan_view, name='cancelar_solicitud_plan'),
    path('procesar-solicitud-plan/', views.procesar_solicitud_plan_view, name='procesar_solicitud_plan'),
    path('gestionar-solicitudes/', views.gestionar_solicitudes_view, name='gestionar_solicitudes'),
    
    # ============================================================================
    # RECUPERACIÓN DE CONTRASEÑA
    # ============================================================================
    
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='usuarios/password_reset_form.html',
             email_template_name='usuarios/emails/password_reset_email.html',
             subject_template_name='usuarios/emails/password_reset_subject.txt',
             success_url='/usuarios/password-reset-done/'
         ), 
         name='password_reset'),
    
    path('password-reset-done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='usuarios/password_reset_done.html'
         ),
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='usuarios/password_reset_confirm.html',
             success_url='/usuarios/password-reset-complete/'
         ),
         name='password_reset_confirm'),
    
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='usuarios/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    
    # ============================================================================
    # GESTIÓN DE USUARIOS (SOLO GESTORES)
    # ============================================================================
    path('gestionar/', views.gestionar_usuarios_view, name='gestionar_usuarios'),
    
    # ============================================================================
    # ENDPOINTS HTMX Y AJAX
    # ============================================================================
    path('api/buscar/', views.buscar_usuarios_view, name='buscar_usuarios'),
    path('api/cambiar-plan/', views.cambiar_plan_usuario_view, name='cambiar_plan_usuario'),
]