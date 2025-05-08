from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Carrito, CarritoItem, Pedido, PedidoItem
from .serializers import (
    CarritoSerializer, CarritoItemSerializer,
    PedidoListSerializer, PedidoDetailSerializer,
    CrearPedidoSerializer, ActualizarEstadoPedidoSerializer
)
from .filters import PedidoFilter
from .permissions import PuedeGestionarPedido

class CarritoViewSet(mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    """ViewSet para gestionar el carrito de compras"""
    serializer_class = CarritoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Carrito.objects.filter(usuario=self.request.user)
    
    def get_object(self):
        """Obtiene o crea el carrito del usuario"""
        carrito, _ = Carrito.objects.get_or_create(usuario=self.request.user)
        return carrito
    
    @extend_schema(
        description="Agrega un producto al carrito",
        request=CarritoItemSerializer,
        responses={201: CarritoSerializer}
    )
    @action(detail=True, methods=['post'])
    def agregar_producto(self, request):
        """Agrega un producto al carrito"""
        carrito = self.get_object()
        serializer = CarritoItemSerializer(data=request.data)
        
        if serializer.is_valid():
            producto_id = serializer.validated_data['producto_id']
            cantidad = serializer.validated_data.get('cantidad', 1)
            
            try:
                item = carrito.agregar_producto(producto_id, cantidad)
                return Response(
                    self.get_serializer(carrito).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        description="Actualiza la cantidad de un producto en el carrito",
        request=CarritoItemSerializer,
        responses={200: CarritoSerializer}
    )
    @action(detail=True, methods=['put'])
    def actualizar_cantidad(self, request):
        """Actualiza la cantidad de un producto en el carrito"""
        carrito = self.get_object()
        serializer = CarritoItemSerializer(data=request.data)
        
        if serializer.is_valid():
            producto_id = serializer.validated_data['producto_id']
            cantidad = serializer.validated_data['cantidad']
            
            try:
                carrito.actualizar_cantidad(producto_id, cantidad)
                return Response(self.get_serializer(carrito).data)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        description="Limpia el carrito",
        responses={204: None}
    )
    @action(detail=True, methods=['post'])
    def limpiar(self, request):
        """Elimina todos los productos del carrito"""
        carrito = self.get_object()
        carrito.limpiar()
        return Response(status=status.HTTP_204_NO_CONTENT)

class PedidoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar pedidos"""
    permission_classes = [IsAuthenticated, PuedeGestionarPedido]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PedidoFilter
    lookup_field = 'numero'
    
    def get_queryset(self):
        user = self.request.user
        if user.es_administrador() or user.es_vendedor():
            return Pedido.objects.all()
        return Pedido.objects.filter(usuario=user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PedidoListSerializer
        elif self.action == 'create':
            return CrearPedidoSerializer
        elif self.action == 'actualizar_estado':
            return ActualizarEstadoPedidoSerializer
        return PedidoDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
    
    @extend_schema(
        description="Actualiza el estado de un pedido",
        request=ActualizarEstadoPedidoSerializer,
        responses={200: PedidoDetailSerializer}
    )
    @action(detail=True, methods=['post'])
    def actualizar_estado(self, request, numero=None):
        """Endpoint para actualizar el estado de un pedido"""
        pedido = self.get_object()
        serializer = self.get_serializer(pedido, data=request.data)
        
        if serializer.is_valid():
            pedido = serializer.save()
            return Response(
                PedidoDetailSerializer(pedido).data
            )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @extend_schema(
        description="Lista los pedidos del usuario actual",
        responses={200: PedidoListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def mis_pedidos(self, request):
        """Lista los pedidos del usuario autenticado"""
        pedidos = Pedido.objects.filter(usuario=request.user)
        page = self.paginate_queryset(pedidos)
        
        if page is not None:
            serializer = PedidoListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PedidoListSerializer(pedidos, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="Lista los pedidos pendientes de preparación",
        responses={200: PedidoListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def pendientes_preparacion(self, request):
        """Lista pedidos pagados pendientes de preparación"""
        if not (request.user.es_administrador() or request.user.es_bodeguero()):
            return Response(
                {'error': 'No tiene permisos para ver esta información'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pedidos = Pedido.objects.filter(estado='pagado')
        serializer = PedidoListSerializer(pedidos, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="Lista los pedidos listos para despacho",
        responses={200: PedidoListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def listos_despacho(self, request):
        """Lista pedidos listos para despacho"""
        if not (request.user.es_administrador() or request.user.es_bodeguero()):
            return Response(
                {'error': 'No tiene permisos para ver esta información'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pedidos = Pedido.objects.filter(
            estado='preparacion',
            tipo_entrega='despacho'
        )
        serializer = PedidoListSerializer(pedidos, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="Lista los pedidos listos para retiro",
        responses={200: PedidoListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def listos_retiro(self, request):
        """Lista pedidos listos para retiro en tienda"""
        if not (request.user.es_administrador() or request.user.es_vendedor()):
            return Response(
                {'error': 'No tiene permisos para ver esta información'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pedidos = Pedido.objects.filter(
            estado='preparacion',
            tipo_entrega='retiro'
        )
        serializer = PedidoListSerializer(pedidos, many=True)
        return Response(serializer.data) 