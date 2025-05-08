from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CarritoViewSet, PedidoViewSet

router = DefaultRouter()
router.register(r'carrito', CarritoViewSet, basename='carrito')
router.register(r'pedidos', PedidoViewSet, basename='pedido')

urlpatterns = [
    path('', include(router.urls)),
] 