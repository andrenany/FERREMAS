from rest_framework import serializers
from mptt.models import MPTTModel
from .models import (
    Categoria, Marca, Etiqueta, Producto, ImagenProducto,
    AtributoProducto, ValorAtributoProducto,
    Inventario, MovimientoInventario, MovimientoStock
)

class CategoriaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Categoria"""
    children = serializers.SerializerMethodField()

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'slug', 'descripcion', 'parent', 'activo', 'children']

    def get_children(self, obj):
        return CategoriaSerializer(obj.get_children(), many=True).data

class MarcaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Marca"""
    class Meta:
        model = Marca
        fields = ['id', 'nombre', 'slug', 'descripcion', 'logo', 'activo']

class EtiquetaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Etiqueta"""
    class Meta:
        model = Etiqueta
        fields = ['id', 'nombre', 'slug']

class ImagenProductoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo ImagenProducto"""
    class Meta:
        model = ImagenProducto
        fields = ['id', 'imagen', 'es_principal', 'orden']

class ValorAtributoProductoSerializer(serializers.ModelSerializer):
    nombre_atributo = serializers.CharField(source='atributo.nombre', read_only=True)
    tipo_atributo = serializers.CharField(source='atributo.tipo', read_only=True)

    class Meta:
        model = ValorAtributoProducto
        fields = ['id', 'atributo', 'nombre_atributo', 'tipo_atributo', 'valor']

class InventarioSerializer(serializers.ModelSerializer):
    nombre_sucursal = serializers.CharField(source='sucursal.nombre', read_only=True)

    class Meta:
        model = Inventario
        fields = ['id', 'sucursal', 'nombre_sucursal', 'stock_actual', 'stock_minimo', 'ubicacion_bodega']

class MovimientoStockSerializer(serializers.ModelSerializer):
    """Serializer para el modelo MovimientoStock"""
    usuario = serializers.StringRelatedField()
    
    class Meta:
        model = MovimientoStock
        fields = ['id', 'fecha', 'tipo', 'cantidad', 'motivo', 'usuario']

class ProductoListSerializer(serializers.ModelSerializer):
    """Serializer para listar productos"""
    categoria = serializers.StringRelatedField()
    marca = serializers.StringRelatedField()
    imagen_principal = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            'id', 'codigo', 'nombre', 'slug', 'categoria', 'marca',
            'precio_venta', 'stock_actual', 'imagen_principal', 'destacado'
        ]

    def get_imagen_principal(self, obj):
        imagen = obj.imagenes.filter(es_principal=True).first()
        if imagen:
            return self.context['request'].build_absolute_uri(imagen.imagen.url)
        return None

class ProductoDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalles de producto"""
    categoria = CategoriaSerializer()
    marca = MarcaSerializer()
    etiquetas = EtiquetaSerializer(many=True)
    imagenes = ImagenProductoSerializer(many=True)
    valores_atributos = ValorAtributoProductoSerializer(many=True, read_only=True)
    movimientos = MovimientoStockSerializer(many=True, read_only=True, source='movimientostock_set')

    class Meta:
        model = Producto
        fields = [
            'id', 'codigo', 'nombre', 'slug', 'descripcion',
            'categoria', 'marca', 'etiquetas', 'precio_base',
            'precio_venta', 'stock_actual', 'stock_minimo',
            'stock_maximo', 'atributos_json', 'valores_atributos',
            'activo', 'destacado', 'fecha_creacion',
            'fecha_actualizacion', 'imagenes', 'movimientos',
            'necesita_reposicion'
        ]

class ProductoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar productos"""
    imagenes = ImagenProductoSerializer(many=True, required=False)

    class Meta:
        model = Producto
        fields = [
            'codigo', 'nombre', 'slug', 'descripcion', 'categoria',
            'marca', 'etiquetas', 'precio_base', 'precio_venta',
            'stock_actual', 'stock_minimo', 'stock_maximo',
            'atributos_json', 'activo', 'destacado', 'imagenes'
        ]

    def create(self, validated_data):
        imagenes_data = validated_data.pop('imagenes', [])
        etiquetas_data = validated_data.pop('etiquetas', [])
        
        producto = Producto.objects.create(**validated_data)
        producto.etiquetas.set(etiquetas_data)
        
        for imagen_data in imagenes_data:
            ImagenProducto.objects.create(producto=producto, **imagen_data)
        
        return producto

    def update(self, instance, validated_data):
        imagenes_data = validated_data.pop('imagenes', None)
        etiquetas_data = validated_data.pop('etiquetas', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if etiquetas_data is not None:
            instance.etiquetas.set(etiquetas_data)
        
        if imagenes_data is not None:
            instance.imagenes.all().delete()
            for imagen_data in imagenes_data:
                ImagenProducto.objects.create(producto=instance, **imagen_data)
        
        instance.save()
        return instance

class MovimientoInventarioSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)

    class Meta:
        model = MovimientoInventario
        fields = ['id', 'inventario', 'tipo', 'cantidad', 'motivo', 'usuario', 'usuario_nombre', 'created_at']
        read_only_fields = ['usuario']

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)

class AtributoProductoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo AtributoProducto"""
    class Meta:
        model = AtributoProducto
        fields = ['id', 'nombre', 'tipo', 'opciones'] 