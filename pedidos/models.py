from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from productos.models import Producto
from django.utils import timezone

class Carrito(models.Model):
    """Modelo para manejar el carrito de compras"""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def cantidad_items(self):
        return self.items.count()
    
    def agregar_producto(self, producto, cantidad=1):
        """Agrega un producto al carrito o actualiza su cantidad"""
        item, created = CarritoItem.objects.get_or_create(
            carrito=self,
            producto=producto,
            defaults={'cantidad': cantidad}
        )
        if not created:
            item.cantidad += cantidad
            item.save()
        return item
    
    def actualizar_cantidad(self, producto, cantidad):
        """Actualiza la cantidad de un producto en el carrito"""
        try:
            item = self.items.get(producto=producto)
            if cantidad > 0:
                item.cantidad = cantidad
                item.save()
            else:
                item.delete()
        except CarritoItem.DoesNotExist:
            if cantidad > 0:
                self.agregar_producto(producto, cantidad)
    
    def limpiar(self):
        """Elimina todos los items del carrito"""
        self.items.all().delete()

class CarritoItem(models.Model):
    """Modelo para items en el carrito"""
    carrito = models.ForeignKey(Carrito, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ('carrito', 'producto')
    
    def save(self, *args, **kwargs):
        if not self.precio_unitario:
            self.precio_unitario = self.producto.precio_venta
        super().save(*args, **kwargs)
    
    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

class Pedido(models.Model):
    """Modelo principal para pedidos"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Pago'),
        ('pagado', 'Pagado'),
        ('preparacion', 'En Preparación'),
        ('listo_retiro', 'Listo para Retiro'),
        ('en_despacho', 'En Despacho'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado')
    ]
    
    TIPO_ENTREGA_CHOICES = [
        ('retiro', 'Retiro en Tienda'),
        ('despacho', 'Despacho a Domicilio')
    ]
    
    # Información básica
    numero = models.CharField(max_length=50, unique=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Estado y tipo de entrega
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    tipo_entrega = models.CharField(max_length=20, choices=TIPO_ENTREGA_CHOICES)
    
    # Información de contacto y entrega
    nombre_contacto = models.CharField(max_length=100)
    email_contacto = models.EmailField()
    telefono_contacto = models.CharField(max_length=20)
    direccion_entrega = models.TextField(blank=True, null=True)
    ciudad_entrega = models.CharField(max_length=100, blank=True, null=True)
    region_entrega = models.CharField(max_length=100, blank=True, null=True)
    
    # Información de pago
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    metodo_pago = models.CharField(max_length=50, blank=True)
    referencia_pago = models.CharField(max_length=100, blank=True)
    
    # Seguimiento
    notas = models.TextField(blank=True)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    fecha_preparacion = models.DateTimeField(null=True, blank=True)
    fecha_despacho = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Pedido {self.numero}"
    
    def clean(self):
        """Validaciones personalizadas"""
        if self.tipo_entrega == 'despacho' and not all([
            self.direccion_entrega,
            self.ciudad_entrega,
            self.region_entrega
        ]):
            raise ValidationError({
                'tipo_entrega': _('Para despacho a domicilio se requiere dirección completa')
            })
    
    def save(self, *args, **kwargs):
        """Sobrescribe el método save para realizar validaciones y cálculos"""
        if not self.numero:
            # Generar número de pedido único
            ultimo_pedido = Pedido.objects.order_by('-id').first()
            numero = 1 if not ultimo_pedido else int(ultimo_pedido.numero) + 1
            self.numero = f"{numero:08d}"
        
        # Calcular total
        self.total = self.subtotal + self.costo_envio
        
        super().save(*args, **kwargs)
    
    def actualizar_estado(self, nuevo_estado):
        """Actualiza el estado del pedido y registra la fecha correspondiente"""
        if nuevo_estado not in dict(self.ESTADO_CHOICES):
            raise ValidationError(f"Estado inválido: {nuevo_estado}")
        
        self.estado = nuevo_estado
        
        # Actualizar fechas según el estado
        if nuevo_estado == 'pagado':
            self.fecha_pago = timezone.now()
        elif nuevo_estado == 'preparacion':
            self.fecha_preparacion = timezone.now()
        elif nuevo_estado == 'en_despacho':
            self.fecha_despacho = timezone.now()
        elif nuevo_estado == 'entregado':
            self.fecha_entrega = timezone.now()
        
        self.save()

class PedidoItem(models.Model):
    """Modelo para items en un pedido"""
    pedido = models.ForeignKey(Pedido, related_name='items', on_delete=models.PROTECT)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        """Calcula el subtotal antes de guardar"""
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

class CambioPedido(models.Model):
    """Modelo para registrar cambios en el estado de los pedidos"""
    pedido = models.ForeignKey(Pedido, related_name='cambios', on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    estado_anterior = models.CharField(max_length=20, choices=Pedido.ESTADO_CHOICES)
    estado_nuevo = models.CharField(max_length=20, choices=Pedido.ESTADO_CHOICES)
    notas = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.pedido.numero}: {self.estado_anterior} -> {self.estado_nuevo}" 