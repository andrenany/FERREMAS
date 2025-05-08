from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import TransaccionMercadoPago, FacturaElectronica, ConciliacionPago
from .serializers import (
    TransaccionMercadoPagoSerializer, FacturaElectronicaSerializer,
    ConciliacionPagoSerializer
)
from .services import MercadoPagoService, FacturacionService
from .permissions import EsContador

class TransaccionMercadoPagoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar transacciones de Mercado Pago"""
    serializer_class = TransaccionMercadoPagoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['estado', 'pedido__numero']
    
    def get_queryset(self):
        user = self.request.user
        if user.es_administrador() or user.es_contador():
            return TransaccionMercadoPago.objects.all()
        return TransaccionMercadoPago.objects.filter(pedido__usuario=user)
    
    @extend_schema(
        description="Crea una preferencia de pago en Mercado Pago",
        request=TransaccionMercadoPagoSerializer,
        responses={201: TransaccionMercadoPagoSerializer}
    )
    def create(self, request, *args, **kwargs):
        """Crea una preferencia de pago en Mercado Pago"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            mp_service = MercadoPagoService()
            transaccion = mp_service.crear_preferencia(
                serializer.validated_data['pedido']
            )
            return Response(
                self.get_serializer(transaccion).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        description="Procesa webhooks de Mercado Pago"
    )
    @action(detail=False, methods=['post'], permission_classes=[])
    def webhook(self, request):
        """Endpoint para recibir webhooks de Mercado Pago"""
        try:
            mp_service = MercadoPagoService()
            transaccion = mp_service.procesar_webhook(request.data)
            
            if transaccion:
                return Response(
                    self.get_serializer(transaccion).data,
                    status=status.HTTP_200_OK
                )
            return Response(status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class FacturaElectronicaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar facturas electrónicas"""
    serializer_class = FacturaElectronicaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['estado', 'pedido__numero', 'numero_factura']
    
    def get_queryset(self):
        user = self.request.user
        if user.es_administrador() or user.es_contador():
            return FacturaElectronica.objects.all()
        return FacturaElectronica.objects.filter(pedido__usuario=user)
    
    @extend_schema(
        description="Genera y envía una factura al SII",
        responses={200: FacturaElectronicaSerializer}
    )
    @action(detail=True, methods=['post'])
    def generar_y_enviar(self, request, pk=None):
        """Genera el XML y envía la factura al SII"""
        factura = self.get_object()
        facturacion_service = FacturacionService()
        
        try:
            # Generar XML
            facturacion_service.generar_xml(factura)
            
            # Enviar al SII
            facturacion_service.enviar_al_sii(factura)
            
            # Generar PDF
            facturacion_service.generar_pdf(factura)
            
            return Response(
                self.get_serializer(factura).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class ConciliacionPagoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar conciliaciones de pagos"""
    serializer_class = ConciliacionPagoSerializer
    permission_classes = [IsAuthenticated, EsContador]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['estado', 'transaccion__pedido__numero']
    
    def get_queryset(self):
        return ConciliacionPago.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(conciliado_por=self.request.user)
    
    @extend_schema(
        description="Marca una conciliación como completada",
        responses={200: ConciliacionPagoSerializer}
    )
    @action(detail=True, methods=['post'])
    def marcar_conciliado(self, request, pk=None):
        """Marca una conciliación como completada"""
        conciliacion = self.get_object()
        conciliacion.estado = 'conciliado'
        conciliacion.fecha_conciliacion = timezone.now()
        conciliacion.save()
        
        return Response(
            self.get_serializer(conciliacion).data,
            status=status.HTTP_200_OK
        )
