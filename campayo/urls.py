# campayo/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from usuarios.views import home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('usuarios/', include('usuarios.urls')),
    path('ejercicios/', include('ejercicios.urls')),
    path('tests/', include('test_lectura.urls')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Configuración del admin
admin.site.site_header = "Turbo Speed Reader - Lectura Rápida"
admin.site.site_title = "Campayo Admin"
admin.site.index_title = "Panel de Administración"