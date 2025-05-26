from django.urls import path, include
from rest_framework.routers import DefaultRouter
from pedidos.views import CarritoViewSet

router = DefaultRouter()
router.register(r'carrito', CarritoViewSet, basename='carrito')
##router.register(r'pedidos', PedidoViewSet, basename='pedidos')

urlpatterns = [
    # New explicit path for the crear_desde_carrito action (moved before include)
    path('carrito/crear-desde-carrito/', CarritoViewSet.as_view({'post': 'crear_desde_carrito'}), name='carrito-crear-pedido'),
    path('', include(router.urls)),
    # Explicit path for the custom add_item action
    path('carrito/add_item/', CarritoViewSet.as_view({'post': 'add_item'}), name='carrito-add-item'),
]
