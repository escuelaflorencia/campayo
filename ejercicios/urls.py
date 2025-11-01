# ejercicios/urls.py
from django.urls import path
from . import views

app_name = 'ejercicios'

urlpatterns = [
    path('', views.lista_ejercicios_view, name='lista'),
    path('<int:ejercicio_id>/', views.detalle_ejercicio_view, name='detalle'),
    path('completar/', views.completar_ejercicio_view, name='completar'),
    path('progreso/', views.mi_progreso_view, name='mi_progreso'),
]