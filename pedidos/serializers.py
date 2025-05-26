from rest_framework import serializers
from django.db import transaction
from .models import Carrito, CarritoItem, Pedido, PedidoItem, CambioPedido, EstadoPedido
from productos.serializers import ProductoListSerializer
import pdb
import logging

logger = logging.getLogger(__name__)

class CarritoItemSerializer(serializers.ModelSerializer):
    """Serializer para items del carrito"""
    producto = ProductoListSerializer(read_only=True)
    producto_id = serializers.IntegerField(write_only=True)
    
    def to_representation(self, instance):
        
        try:
            representation = super().to_representation(instance)
            return representation
        except Exception as e:
            logger.error(f"Error during serialization of CarritoItem {instance.id if instance else 'N/A'}: {e}", exc_info=True)
            return {
                'id': instance.id if instance else None,
                'error': f'Error serializando CarritoItem: {e}'
            }

    class Meta:
        model = CarritoItem
        fields = ['id', 'producto', 'producto_id', 'cantidad', 'precio_unitario', 'subtotal']
        read_only_fields = ['precio_unitario', 'subtotal']

class CarritoSerializer(serializers.ModelSerializer):
    """Serializer para el carrito de compras"""
    items = CarritoItemSerializer(many=True, read_only=True)
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # ... resto del método ...
        return representation

    class Meta:
        model = Carrito
        fields = ['id', 'usuario', 'items', 'total', 'cantidad_items', 'creado', 'actualizado']
        read_only_fields = ['usuario', 'total', 'cantidad_items']

class PedidoItemSerializer(serializers.ModelSerializer):
    """Serializer para items del pedido"""
    producto = ProductoListSerializer(read_only=True)
    
    class Meta:
        model = PedidoItem
        fields = ['id', 'producto', 'cantidad', 'precio_unitario', 'subtotal']
        read_only_fields = ['precio_unitario', 'subtotal']

class CambioPedidoSerializer(serializers.ModelSerializer):
    """Serializer para cambios de estado en pedidos"""
    class Meta:
        model = CambioPedido
        fields = ['id', 'fecha', 'estado_anterior', 'estado_nuevo', 'notas']
        read_only_fields = ['fecha']

class PedidoListSerializer(serializers.ModelSerializer):
    """Serializer para listar pedidos"""
    class Meta:
        model = Pedido
        fields = [
            'id', 'numero_pedido', 'fecha_pedido', 'estado',
            'tipo_entrega', 'total', 'nombre_contacto'
        ]

class PedidoDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalles del pedido"""
    items = PedidoItemSerializer(many=True, read_only=True)
    cambios = CambioPedidoSerializer(many=True, read_only=True)
    cliente = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Pedido
        fields = [
            'id', 'numero_pedido', 'cliente', 'fecha_pedido',
            'updated_at', 'estado', 'tipo_entrega',
            'nombre_contacto', 'email_contacto', 'telefono_contacto',
            'direccion_entrega', 'fecha_entrega_estimada',
            'subtotal', 'iva', 'descuento', 'total',
            'notas', 'items', 'cambios'
        ]
        read_only_fields = [
            'numero_pedido', 'cliente', 'fecha_pedido', 'updated_at',
            'subtotal', 'total'
        ]

class CrearPedidoSerializer(serializers.ModelSerializer):
    """Serializer para crear pedidos desde el carrito"""
    class Meta:
        model = Pedido
        fields = [
            'tipo_entrega', 'nombre_contacto', 'email_contacto',
            'telefono_contacto', 'direccion_entrega'
        ]
    
    def validate(self, data):
        """Validación personalizada para la dirección de entrega"""
        tipo_entrega = data.get('tipo_entrega')
        if tipo_entrega == 'despacho':
            if not data.get('direccion_entrega'):
                raise serializers.ValidationError(
                    'Para despacho a domicilio se requiere dirección completa'
                )
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        """Crea un pedido a partir del carrito del usuario"""
        usuario = self.context['request'].user
        carrito = Carrito.objects.get(usuario=usuario)
        
        if not carrito.items.exists():
            raise serializers.ValidationError('El carrito está vacío')
        
        # Crear el pedido
        pedido = Pedido.objects.create(
            cliente=usuario,
            subtotal=carrito.total,
            iva=carrito.total * 0.19,  # 19% de IVA (ajustar según necesidad)
            total=carrito.total * 1.19,  # Total con IVA
            **validated_data
        )
        
        # Crear los items del pedido
        for item in carrito.items.all():
            PedidoItem.objects.create(
                pedido=pedido,
                producto=item.producto,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario,
                subtotal=item.subtotal
            )
        
        # Limpiar el carrito
        carrito.limpiar()
        
        return pedido

class ActualizarEstadoPedidoSerializer(serializers.Serializer):
    """Serializer para actualizar el estado de un pedido"""
    # Reemplazamos esta línea:
    # estado = serializers.ChoiceField(choices=Pedido.ESTADO_CHOICES)
    
    # Por esta:
    estado = serializers.PrimaryKeyRelatedField(queryset=EstadoPedido.objects.all())
    notas = serializers.CharField(required=False, allow_blank=True)
    
    def validate_estado(self, value):
        """Valida que la transición de estado sea válida"""
        pedido = self.instance
        estado_actual = pedido.estado.nombre
        nuevo_estado = value.nombre
        
        # Mapeamos los estados válidos según el flujo del negocio
        estados_validos = {
            'pendiente': ['confirmado', 'cancelado'],
            'confirmado': ['en_preparacion', 'cancelado'],
            'en_preparacion': ['listo_para_entrega', 'cancelado'],
            'listo_para_entrega': ['en_transito', 'entregado', 'cancelado'],
            'en_transito': ['entregado', 'cancelado'],
            'entregado': [],
            'cancelado': []
        }
        
        if estado_actual in estados_validos and nuevo_estado not in estados_validos.get(estado_actual, []):
            raise serializers.ValidationError(
                f'No se puede cambiar de {estado_actual} a {nuevo_estado}'
            )
        return value
    
    def update(self, instance, validated_data):
        """Actualiza el estado del pedido"""
        usuario = self.context['request'].user
        instance.actualizar_estado(
            validated_data['estado'],
            usuario=usuario,
            notas=validated_data.get('notas', '')
        )
        return instance