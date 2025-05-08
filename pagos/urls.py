from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TransaccionMercadoPagoViewSet,
    FacturaElectronicaViewSet,
    ConciliacionPagoViewSet
)

router = DefaultRouter()
router.register(r'transacciones', TransaccionMercadoPagoViewSet, basename='transaccion')
router.register(r'facturas', FacturaElectronicaViewSet, basename='factura')
router.register(r'conciliaciones', ConciliacionPagoViewSet, basename='conciliacion')

urlpatterns = [
    path('', include(router.urls)),
] 