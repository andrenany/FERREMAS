from django.db.models import Q
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import (
    Categoria, Marca, Etiqueta, AtributoProducto,
    Producto, ImagenProducto, MovimientoStock
)
from .serializers import (
    CategoriaSerializer, MarcaSerializer, EtiquetaSerializer,
    AtributoProductoSerializer, ProductoListSerializer,
    ProductoDetailSerializer, ProductoCreateUpdateSerializer,
    ImagenProductoSerializer, MovimientoStockSerializer
)
from .filters import ProductoFilter
from .permissions import EsAdminOVendedor, EsAdminOBodeguero

class CategoriaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar categorías de productos"""
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

    @extend_schema(
        description="Obtiene el árbol completo de categorías",
        responses={200: CategoriaSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Devuelve el árbol completo de categorías"""
        categorias = Categoria.objects.filter(parent=None)
        serializer = self.get_serializer(categorias, many=True)
        return Response(serializer.data)

class MarcaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar marcas"""
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

class EtiquetaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar etiquetas"""
    queryset = Etiqueta.objects.all()
    serializer_class = EtiquetaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

class AtributoProductoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar atributos de productos"""
    queryset = AtributoProducto.objects.all()
    serializer_class = AtributoProductoSerializer
    permission_classes = [IsAuthenticated, EsAdminOVendedor]

class ProductoViewSet(viewsets.ModelViewSet):
    """ViewSet principal para gestionar productos"""
    queryset = Producto.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductoFilter
    search_fields = ['nombre', 'codigo', 'descripcion', 'marca__nombre', 'categoria__nombre']
    ordering_fields = ['nombre', 'precio_venta', 'stock_actual', 'fecha_creacion']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductoListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductoCreateUpdateSerializer
        return ProductoDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), EsAdminOVendedor()]
        return super().get_permissions()

    @extend_schema(
        description="Actualiza el stock de un producto",
        request=MovimientoStockSerializer,
        responses={200: ProductoDetailSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, EsAdminOBodeguero])
    def actualizar_stock(self, request, slug=None):
        """Endpoint para actualizar el stock de un producto"""
        producto = self.get_object()
        serializer = MovimientoStockSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                movimiento = MovimientoStock.objects.create(
                    producto=producto,
                    usuario=request.user,
                    **serializer.validated_data
                )
                return Response(self.get_serializer(producto).data)
            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description="Busca productos por varios criterios",
        parameters=[
            OpenApiParameter(name='q', description='Término de búsqueda', required=False, type=str),
            OpenApiParameter(name='categoria', description='Slug de la categoría', required=False, type=str),
            OpenApiParameter(name='marca', description='Slug de la marca', required=False, type=str),
            OpenApiParameter(name='min_precio', description='Precio mínimo', required=False, type=float),
            OpenApiParameter(name='max_precio', description='Precio máximo', required=False, type=float),
            OpenApiParameter(name='en_stock', description='Solo productos en stock', required=False, type=bool),
        ],
        responses={200: ProductoListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """Endpoint para búsqueda avanzada de productos"""
        queryset = self.get_queryset()
        
        # Término de búsqueda
        q = request.query_params.get('q', '')
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) |
                Q(codigo__icontains=q) |
                Q(descripcion__icontains=q) |
                Q(marca__nombre__icontains=q)
            )
        
        # Filtros
        categoria = request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria__slug=categoria)
        
        marca = request.query_params.get('marca')
        if marca:
            queryset = queryset.filter(marca__slug=marca)
        
        min_precio = request.query_params.get('min_precio')
        if min_precio:
            queryset = queryset.filter(precio_venta__gte=float(min_precio))
        
        max_precio = request.query_params.get('max_precio')
        if max_precio:
            queryset = queryset.filter(precio_venta__lte=float(max_precio))
        
        en_stock = request.query_params.get('en_stock')
        if en_stock and en_stock.lower() == 'true':
            queryset = queryset.filter(stock_actual__gt=0)
        
        serializer = ProductoListSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @extend_schema(
        description="Lista los productos que necesitan reposición",
        responses={200: ProductoListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, EsAdminOBodeguero])
    def necesitan_reposicion(self, request):
        """Lista productos que necesitan reposición"""
        productos = self.get_queryset().filter(
            stock_actual__lte=models.F('stock_minimo')
        )
        serializer = ProductoListSerializer(
            productos,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

class ImagenProductoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar imágenes de productos"""
    queryset = ImagenProducto.objects.all()
    serializer_class = ImagenProductoSerializer
    permission_classes = [IsAuthenticated, EsAdminOVendedor]

    def perform_create(self, serializer):
        """Al crear una imagen, verificar si es la principal"""
        producto = serializer.validated_data['producto']
        es_principal = serializer.validated_data.get('es_principal', False)
        
        if es_principal:
            # Si la nueva imagen es principal, quitar el flag de las demás
            producto.imagenes.filter(es_principal=True).update(es_principal=False)
        
        serializer.save() 