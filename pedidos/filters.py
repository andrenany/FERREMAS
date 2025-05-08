import django_filters
from .models import Pedido

class PedidoFilter(django_filters.FilterSet):
    """Filtros para el modelo Pedido"""
    numero = django_filters.CharFilter(lookup_expr='icontains')
    estado = django_filters.ChoiceFilter(choices=Pedido.ESTADO_CHOICES)
    tipo_entrega = django_filters.ChoiceFilter(choices=Pedido.TIPO_ENTREGA_CHOICES)
    
    fecha_creacion_desde = django_filters.DateTimeFilter(
        field_name='fecha_creacion',
        lookup_expr='gte'
    )
    fecha_creacion_hasta = django_filters.DateTimeFilter(
        field_name='fecha_creacion',
        lookup_expr='lte'
    )
    
    total_min = django_filters.NumberFilter(field_name='total', lookup_expr='gte')
    total_max = django_filters.NumberFilter(field_name='total', lookup_expr='lte')
    
    nombre_contacto = django_filters.CharFilter(lookup_expr='icontains')
    email_contacto = django_filters.CharFilter(lookup_expr='icontains')
    telefono_contacto = django_filters.CharFilter(lookup_expr='icontains')
    
    ciudad_entrega = django_filters.CharFilter(lookup_expr='icontains')
    region_entrega = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Pedido
        fields = [
            'numero', 'estado', 'tipo_entrega',
            'nombre_contacto', 'email_contacto', 'telefono_contacto',
            'ciudad_entrega', 'region_entrega'
        ] 