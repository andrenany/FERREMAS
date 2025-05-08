from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.permissions import AllowAny

urlpatterns = [
    # Redirección de la raíz a Swagger UI
    path('', RedirectView.as_view(url='/api/schema/swagger-ui/', permanent=False), name='api-docs'),
    path('admin/', admin.site.urls),
    # URLs para la documentación del API
    path('api/schema/', SpectacularAPIView.as_view(permission_classes=[AllowAny]), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema', permission_classes=[AllowAny]), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema', permission_classes=[AllowAny]), name='redoc'),
    # Tus otras URLs de API aquí
    path('api/productos/', include('productos.urls')),
    path('api/sucursales/', include('sucursales.urls')),
    path('api/auth/', include('autenticacion.urls')),
    path('api/pedidos/', include('pedidos.urls')),
    path('api/pagos/', include('pagos.urls')),
    path('api/notificaciones/', include('notificaciones.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)