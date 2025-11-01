# test_lectura/urls.py
from django.urls import path
from . import views

app_name = 'test_lectura'

urlpatterns = [
    # Vista principal de tests
    path('', views.lista_tests_view, name='lista_tests'),
    
    # Iniciar un test específico
    path('<int:test_id>/iniciar/', views.iniciar_test_view, name='iniciar'),
    
    # Finalizar fase de lectura (AJAX)
    path('finalizar-lectura/', views.finalizar_lectura_view, name='finalizar_lectura'),
    
    # Finalizar test completo (AJAX)
    path('finalizar-test/', views.finalizar_test_view, name='finalizar_test'),
    
    # Ver resultado de un test
    path('resultado/<int:sesion_id>/', views.resultado_test_view, name='resultado'),
]