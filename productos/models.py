from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField

User = get_user_model()

class Categoria(MPTTModel):
    """Modelo para manejar categorías jerárquicas de productos"""
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField(blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ['nombre']

    def __str__(self):
        return self.nombre

class Marca(models.Model):
    """Modelo para manejar marcas de productos"""
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField(blank=True)
    logo = models.ImageField(upload_to='marcas/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

class Etiqueta(models.Model):
    """Modelo para etiquetar productos"""
    nombre = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    
    def __str__(self):
        return self.nombre

class Producto(models.Model):
    """Modelo principal de productos"""
    # Campos básicos
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField()
    
    # Organización
    categoria = TreeForeignKey(Categoria, on_delete=models.PROTECT)
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT)
    etiquetas = models.ManyToManyField(Etiqueta, blank=True)
    
    # Precios y stock
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5)
    stock_maximo = models.IntegerField(default=100)
    
    # Atributos dinámicos
    atributos_json = models.JSONField(default=dict)
    
    # Estado
    activo = models.BooleanField(default=True)
    destacado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def actualizar_stock(self, cantidad, tipo_movimiento):
        """Actualiza el stock del producto"""
        if tipo_movimiento == 'entrada':
            self.stock_actual += cantidad
        elif tipo_movimiento == 'salida':
            if self.stock_actual >= cantidad:
                self.stock_actual -= cantidad
            else:
                raise ValueError("Stock insuficiente")
        self.save()
    
    @property
    def necesita_reposicion(self):
        """Indica si el producto necesita reposición"""
        return self.stock_actual <= self.stock_minimo

class ImagenProducto(models.Model):
    """Modelo para manejar múltiples imágenes por producto"""
    producto = models.ForeignKey(Producto, related_name='imagenes', on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='productos/')
    es_principal = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['orden']
    
    def __str__(self):
        return f"Imagen de {self.producto.nombre}"

class AtributoProducto(models.Model):
    """Modelo para definir atributos dinámicos de productos"""
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=[
        ('texto', 'Texto'),
        ('numero', 'Número'),
        ('booleano', 'Booleano'),
        ('seleccion', 'Selección')
    ])
    opciones = models.TextField(blank=True, help_text='Opciones separadas por comas para tipo selección')
    
    def __str__(self):
        return self.nombre

class ValorAtributoProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='valores_atributos')
    atributo = models.ForeignKey(AtributoProducto, on_delete=models.CASCADE)
    valor = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('producto', 'atributo')

    def __str__(self):
        return f"{self.atributo.nombre}: {self.valor}"

class Inventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='inventarios')
    sucursal = models.ForeignKey('sucursales.Sucursal', on_delete=models.CASCADE)
    stock_actual = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5)
    ubicacion_bodega = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('producto', 'sucursal')

    def __str__(self):
        return f"{self.producto.nombre} - {self.sucursal.nombre}"

class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste')
    ]

    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO)
    cantidad = models.IntegerField()
    motivo = models.TextField()
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} - {self.inventario.producto.nombre}"

class MovimientoStock(models.Model):
    """Modelo para registrar movimientos de stock"""
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=20, choices=[
        ('entrada', 'Entrada'),
        ('salida', 'Salida')
    ])
    cantidad = models.IntegerField()
    motivo = models.CharField(max_length=100)
    usuario = models.ForeignKey('autenticacion.User', on_delete=models.PROTECT)
    
    def __str__(self):
        return f"{self.tipo} de {self.cantidad} unidades de {self.producto.nombre}"
    
    def save(self, *args, **kwargs):
        """Sobrescribe el método save para actualizar el stock del producto"""
        super().save(*args, **kwargs)
        self.producto.actualizar_stock(self.cantidad, self.tipo) 