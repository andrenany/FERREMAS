import django_filters
from .models import Pedido, EstadoPedido

class PedidoFilter(django_filters.FilterSet):
    """Filtros para el modelo Pedido"""
    numero_pedido = django_filters.CharFilter(lookup_expr='icontains')
    
    # Reemplazar estado con ModelChoiceFilter
    estado = django_filters.ModelChoiceFilter(
        queryset=EstadoPedido.objects.all(),
        field_name='estado',
        to_field_name='id'
    )
    
    # Mantener tipo_entrega pero usando directamente la referencia a las opciones
    tipo_entrega = django_filters.ChoiceFilter(choices=Pedido.TIPO_ENTREGA_CHOICES)
    
    fecha_pedido_desde = django_filters.DateTimeFilter(
        field_name='fecha_pedido',
        lookup_expr='gte'
    )
    fecha_pedido_hasta = django_filters.DateTimeFilter(
        field_name='fecha_pedido',
        lookup_expr='lte'
    )
    
    total_min = django_filters.NumberFilter(field_name='total', lookup_expr='gte')
    total_max = django_filters.NumberFilter(field_name='total', lookup_expr='lte')
    
    nombre_contacto = django_filters.CharFilter(lookup_expr='icontains')
    email_contacto = django_filters.CharFilter(lookup_expr='icontains')
    telefono_contacto = django_filters.CharFilter(lookup_expr='icontains')
    
    # He quitado estos campos si no existen en tu modelo actual
    # ciudad_entrega = django_filters.CharFilter(lookup_expr='icontains')
    # region_entrega = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Pedido
        fields = [
            'numero_pedido', 'estado', 'tipo_entrega',
            'nombre_contacto', 'email_contacto', 'telefono_contacto',
            # 'ciudad_entrega', 'region_entrega'
        ]