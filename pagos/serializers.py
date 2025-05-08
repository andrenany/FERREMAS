from rest_framework import serializers
from .models import TransaccionMercadoPago, FacturaElectronica, ConciliacionPago
from pedidos.serializers import PedidoDetailSerializer
from pedidos.models import Pedido

class TransaccionMercadoPagoSerializer(serializers.ModelSerializer):
    pedido = PedidoDetailSerializer(read_only=True)
    pedido_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = TransaccionMercadoPago
        fields = [
            'id', 'pedido', 'pedido_id', 'preference_id', 'payment_id',
            'merchant_order_id', 'estado', 'monto', 'fecha_creacion',
            'fecha_actualizacion', 'datos_adicionales'
        ]
        read_only_fields = ['preference_id', 'payment_id', 'merchant_order_id', 'estado', 'monto']

    def create(self, validated_data):
        pedido_id = validated_data.pop('pedido_id')
        pedido = Pedido.objects.get(id=pedido_id)
        validated_data['pedido'] = pedido
        validated_data['monto'] = pedido.total
        return super().create(validated_data)

class FacturaElectronicaSerializer(serializers.ModelSerializer):
    pedido = PedidoDetailSerializer(read_only=True)
    pedido_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = FacturaElectronica
        fields = [
            'id', 'pedido', 'pedido_id', 'numero_factura', 'fecha_emision',
            'estado', 'rut_emisor', 'razon_social_emisor', 'giro_emisor',
            'direccion_emisor', 'rut_receptor', 'razon_social_receptor',
            'giro_receptor', 'direccion_receptor', 'neto', 'iva', 'total',
            'xml_factura', 'pdf_factura', 'track_id', 'respuesta_sii',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['numero_factura', 'estado', 'xml_factura', 'pdf_factura', 'track_id', 'respuesta_sii']

class ConciliacionPagoSerializer(serializers.ModelSerializer):
    transaccion = TransaccionMercadoPagoSerializer(read_only=True)
    factura = FacturaElectronicaSerializer(read_only=True)
    transaccion_id = serializers.IntegerField(write_only=True)
    factura_id = serializers.IntegerField(write_only=True)
    conciliado_por = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = ConciliacionPago
        fields = [
            'id', 'transaccion', 'transaccion_id', 'factura', 'factura_id',
            'estado', 'fecha_conciliacion', 'notas', 'conciliado_por',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['estado', 'fecha_conciliacion', 'conciliado_por'] 