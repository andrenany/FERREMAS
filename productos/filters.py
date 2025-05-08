import django_filters
from .models import Producto
from django.db import models

class ProductoFilter(django_filters.FilterSet):
    """Filtros para el modelo Producto"""
    nombre = django_filters.CharFilter(lookup_expr='icontains')
    codigo = django_filters.CharFilter(lookup_expr='icontains')
    descripcion = django_filters.CharFilter(lookup_expr='icontains')
    categoria = django_filters.CharFilter(field_name='categoria__slug')
    marca = django_filters.CharFilter(field_name='marca__slug')
    etiqueta = django_filters.CharFilter(field_name='etiquetas__slug')
    
    precio_min = django_filters.NumberFilter(field_name='precio_venta', lookup_expr='gte')
    precio_max = django_filters.NumberFilter(field_name='precio_venta', lookup_expr='lte')
    
    en_stock = django_filters.BooleanFilter(method='filter_en_stock')
    necesita_reposicion = django_filters.BooleanFilter(method='filter_necesita_reposicion')
    
    class Meta:
        model = Producto
        fields = [
            'nombre', 'codigo', 'descripcion', 'categoria',
            'marca', 'etiqueta', 'activo', 'destacado'
        ]
    
    def filter_en_stock(self, queryset, name, value):
        """Filtra productos con stock disponible"""
        if value:
            return queryset.filter(stock_actual__gt=0)
        return queryset
    
    def filter_necesita_reposicion(self, queryset, name, value):
        """Filtra productos que necesitan reposición"""
        if value:
            return queryset.filter(stock_actual__lte=models.F('stock_minimo'))
        return queryset 