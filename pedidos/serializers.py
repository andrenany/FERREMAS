from rest_framework import serializers
from django.db import transaction
from .models import Carrito, CarritoItem, Pedido, PedidoItem, CambioPedido
from productos.serializers import ProductoListSerializer

class CarritoItemSerializer(serializers.ModelSerializer):
    """Serializer para items del carrito"""
    producto = ProductoListSerializer(read_only=True)
    producto_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = CarritoItem
        fields = ['id', 'producto', 'producto_id', 'cantidad', 'precio_unitario', 'subtotal']
        read_only_fields = ['precio_unitario', 'subtotal']

class CarritoSerializer(serializers.ModelSerializer):
    """Serializer para el carrito de compras"""
    items = CarritoItemSerializer(many=True, read_only=True)
    
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
            'id', 'numero', 'fecha_creacion', 'estado',
            'tipo_entrega', 'total', 'nombre_contacto'
        ]

class PedidoDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalles del pedido"""
    items = PedidoItemSerializer(many=True, read_only=True)
    cambios = CambioPedidoSerializer(many=True, read_only=True)
    usuario = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Pedido
        fields = [
            'id', 'numero', 'usuario', 'fecha_creacion',
            'fecha_actualizacion', 'estado', 'tipo_entrega',
            'nombre_contacto', 'email_contacto', 'telefono_contacto',
            'direccion_entrega', 'ciudad_entrega', 'region_entrega',
            'subtotal', 'costo_envio', 'total', 'metodo_pago',
            'referencia_pago', 'notas', 'fecha_pago',
            'fecha_preparacion', 'fecha_despacho', 'fecha_entrega',
            'items', 'cambios'
        ]
        read_only_fields = [
            'numero', 'usuario', 'fecha_creacion', 'fecha_actualizacion',
            'subtotal', 'total', 'fecha_pago', 'fecha_preparacion',
            'fecha_despacho', 'fecha_entrega'
        ]

class CrearPedidoSerializer(serializers.ModelSerializer):
    """Serializer para crear pedidos desde el carrito"""
    class Meta:
        model = Pedido
        fields = [
            'tipo_entrega', 'nombre_contacto', 'email_contacto',
            'telefono_contacto', 'direccion_entrega', 'ciudad_entrega',
            'region_entrega'
        ]
    
    def validate(self, data):
        """Validación personalizada para la dirección de entrega"""
        tipo_entrega = data.get('tipo_entrega')
        if tipo_entrega == 'despacho':
            if not all([
                data.get('direccion_entrega'),
                data.get('ciudad_entrega'),
                data.get('region_entrega')
            ]):
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
            usuario=usuario,
            subtotal=carrito.total,
            costo_envio=0,  # Aquí se podría calcular según la dirección
            total=carrito.total,
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
    estado = serializers.ChoiceField(choices=Pedido.ESTADO_CHOICES)
    notas = serializers.CharField(required=False, allow_blank=True)
    
    def validate_estado(self, value):
        """Valida que la transición de estado sea válida"""
        pedido = self.instance
        estados_validos = {
            'pendiente': ['pagado', 'cancelado'],
            'pagado': ['preparacion', 'cancelado'],
            'preparacion': ['listo_retiro', 'en_despacho', 'cancelado'],
            'listo_retiro': ['entregado', 'cancelado'],
            'en_despacho': ['entregado', 'cancelado'],
            'entregado': [],
            'cancelado': []
        }
        
        if value not in estados_validos[pedido.estado]:
            raise serializers.ValidationError(
                f'No se puede cambiar de {pedido.estado} a {value}'
            )
        return value
    
    def update(self, instance, validated_data):
        """Actualiza el estado del pedido"""
        instance.actualizar_estado(
            validated_data['estado'],
            notas=validated_data.get('notas', '')
        )
        return instance 