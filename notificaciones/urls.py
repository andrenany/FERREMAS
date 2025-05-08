from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'notificaciones', views.NotificacionViewSet, basename='notificacion')
router.register(r'preferencias', views.PreferenciasNotificacionViewSet, basename='preferencias')
router.register(r'plantillas', views.PlantillaNotificacionViewSet, basename='plantilla')

urlpatterns = [
    path('', include(router.urls)),
] 