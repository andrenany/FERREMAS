import logging
logger = logging.getLogger(__name__)

from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Carrito, CarritoItem, Pedido, PedidoItem, EstadoPedido
from .serializers import (
    CarritoSerializer, CarritoItemSerializer,
    PedidoListSerializer, PedidoDetailSerializer,
    CrearPedidoSerializer, ActualizarEstadoPedidoSerializer
)
from .filters import PedidoFilter
from .permissions import PuedeGestionarPedido
from productos.models import Producto as ProductoModel
from django.db import transaction
from decimal import Decimal

class CarritoViewSet(mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    """ViewSet para gestionar el carrito de compras"""
    serializer_class = CarritoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Carrito.objects.none()
        return Carrito.objects.filter(usuario=user)

    def list(self, request, *args, **kwargs):
        """Obtener o crear el carrito del usuario actual"""
        try:
            carrito, created = Carrito.objects.get_or_create(
                usuario=request.user,
                defaults={'total': 0}
            )
            serializer = self.get_serializer(carrito)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        # Temporary test response
        # return Response({"mensaje": "Respuesta de prueba exitosa", "items_test": []}, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Obtener un carrito específico por ID"""
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, methods=['PUT'])
    def actualizar_cantidad(self, request, pk=None):
        """Actualiza la cantidad de un producto en el carrito"""
        carrito = self.get_object()
        producto_id = request.data.get('producto_id')
        cantidad = request.data.get('cantidad')

        if not producto_id:
            return Response(
                {'error': 'producto_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if cantidad == 0:
                # Si la cantidad es 0, eliminar el item
                CarritoItem.objects.filter(
                    carrito=carrito,
                    producto_id=producto_id
                ).delete()
            else:
                # Actualizar o crear el item
                item, created = CarritoItem.objects.get_or_create(
                    carrito=carrito,
                    producto_id=producto_id,
                    defaults={'cantidad': cantidad, 'precio_unitario': 0}
                )
                if not created:
                    item.cantidad = cantidad
                    item.save()

            # Actualizar totales del carrito
            carrito.actualizar_totales()
            
            serializer = self.get_serializer(carrito)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['POST'])
    def add_item(self, request):
        usuario = request.user
        producto_id = request.data.get('producto_id')
        cantidad = int(request.data.get('cantidad', 1))

        if not producto_id:
            return Response({'error': 'Falta producto_id'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            producto = ProductoModel.objects.get(id=producto_id)
        except ProductoModel.DoesNotExist:
            return Response({'error': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        carrito, _ = Carrito.objects.get_or_create(usuario=usuario)

        item, creado = CarritoItem.objects.get_or_create(
            carrito=carrito,
            producto=producto,
            defaults={'cantidad': cantidad, 'precio_unitario': producto.precio_venta}
        )

        if not creado:
            item.cantidad += cantidad
            item.save()
            
        # Actualizar totales del carrito después de agregar/actualizar item
        carrito.actualizar_totales()

        # Serializar el carrito actualizado
        serializer = self.get_serializer(carrito)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['POST'])
    def crear_desde_carrito(self, request):
        """Crea un Pedido a partir del carrito del usuario autenticado"""
        usuario = request.user

        try:
            # 1. Obtener el carrito del usuario
            carrito = Carrito.objects.get(usuario=usuario)
            items_carrito = carrito.items.all()

            if not items_carrito:
                return Response(
                    {'error': 'El carrito está vacío'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Usar una transacción para asegurar la atomicidad
            with transaction.atomic():
                # Calcular subtotal, IVA, descuento y total del pedido
                subtotal_pedido = sum(item.subtotal for item in items_carrito)
                iva_pedido = subtotal_pedido * Decimal('0.19')
                descuento_pedido = 0 # Asumiendo descuento inicial de 0
                total_pedido = subtotal_pedido + iva_pedido - descuento_pedido

                # Obtener el estado inicial (ej. 'Pendiente'). Asegúrate de que este estado exista.
                try:
                    estado_inicial = EstadoPedido.objects.get(nombre='Pendiente') # CAMBIO: Busca tu estado inicial real aquí
                except EstadoPedido.DoesNotExist:
                    # Manejar el caso si el estado inicial no existe
                    raise Exception("Estado inicial 'Pendiente' no encontrado. Asegúrate de crearlo.")

                # 2. Crear el nuevo Pedido
                # CAMBIO: Incluir subtotal, iva, descuento y estado inicial
                pedido = Pedido.objects.create(
                    cliente=usuario,
                    subtotal=subtotal_pedido,
                    iva=iva_pedido,
                    descuento=descuento_pedido,
                    total=total_pedido,
                    estado=estado_inicial,
                    # Asegúrate de copiar otros campos obligatorios del Pedido desde el carrito o request.data si es necesario
                    # como tipo_entrega, direccion_entrega, nombre_contacto, email_contacto, telefono_contacto, sucursal, etc.
                    # Por ahora, solo copiamos los totales.
                    # Es posible que necesites pasar más datos desde el frontend o tener valores por defecto en el modelo Pedido.
                )

                # 3. Crear los PedidoItems a partir de los CarritoItems
                pedido_items = []
                for item_carrito in items_carrito:
                    pedido_item = PedidoItem.objects.create(
                        pedido=pedido,
                        producto=item_carrito.producto,
                        cantidad=item_carrito.cantidad,
                        precio_unitario=item_carrito.precio_unitario
                        # Asumimos que precio_unitario ya está guardado en CarritoItem
                    )
                    pedido_items.append(pedido_item)

                # 4. Vaciar el carrito (opcional pero recomendado)
                carrito.items.all().delete()
                carrito.total = 0
                carrito.save()

            # 5. Serializar y devolver el Pedido creado (puedes usar un serializer de Pedido)
            # Necesitarás un PedidoDetailSerializer o similar. Usaremos uno básico por ahora.
            # Si tienes un PedidoSerializer definido, úsalo aquí.
            # from .serializers import PedidoDetailSerializer # Descomenta si tienes uno
            # serializer = PedidoDetailSerializer(pedido) # Descomenta si tienes uno

            # Si no tienes un PedidoDetailSerializer, puedes devolver una respuesta simple de éxito.
            return Response(
                {'mensaje': 'Pedido creado exitosamente', 'pedido_id': pedido.id},
                status=status.HTTP_201_CREATED
            )

        except Carrito.DoesNotExist:
            return Response(
                {'error': 'Carrito no encontrado para el usuario'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error al crear pedido desde carrito: {e}", exc_info=True)
            return Response(
                {'error': f'Error al procesar tu pedido: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PedidoViewSet(viewsets.ModelViewSet):
    # Add a simple indented line here to ensure a block exists
    pass
