# pedidos/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from productos.models import Producto
from sucursales.models import Sucursal

class Carrito(models.Model):
    """Modelo para manejar el carrito de compras"""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    @property
    def cantidad_items(self):
        return self.items.count()
    
    def agregar_producto(self, producto, cantidad=1):
        """Agrega un producto al carrito o actualiza su cantidad"""
        item, created = CarritoItem.objects.get_or_create(
            carrito=self,
            producto=producto,
            defaults={'cantidad': cantidad, 'precio_unitario': producto.precio_venta}
        )
        if not created:
            item.cantidad += cantidad
            item.save()
        self.actualizar_totales()
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
            self.actualizar_totales()
        except CarritoItem.DoesNotExist:
            if cantidad > 0:
                self.agregar_producto(producto, cantidad)
    
    def limpiar(self):
        """Elimina todos los items del carrito"""
        self.items.all().delete()
        self.actualizar_totales()
    
    def actualizar_totales(self):
        """Calcula y actualiza el total del carrito"""
        self.total = sum(item.subtotal for item in self.items.all())
        self.save()
    
    def __str__(self):
        return f"Carrito de {self.usuario.email}"

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
    
    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"

class EstadoPedido(models.Model):
    """Modelo para estados de pedidos"""
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#000000")
    orden = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return self.nombre

class Pedido(models.Model):
    """Modelo principal para pedidos"""
    TIPO_ENTREGA_CHOICES = [
        ('retiro', 'Retiro en Tienda'),
        ('despacho', 'Despacho a Domicilio')
    ]
    
    # Información básica
    numero_pedido = models.CharField(max_length=10, unique=True, editable=False)
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pedidos')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='pedidos')
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='pedidos_vendedor'
    )
    estado = models.ForeignKey(EstadoPedido, on_delete=models.CASCADE)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    
    # Datos de entrega
    tipo_entrega = models.CharField(max_length=10, choices=TIPO_ENTREGA_CHOICES)
    direccion_entrega = models.TextField(null=True, blank=True)
    fecha_entrega_estimada = models.DateField(null=True, blank=True)
    
    # Información de contacto
    nombre_contacto = models.CharField(max_length=100)
    email_contacto = models.EmailField()
    telefono_contacto = models.CharField(max_length=20)
    
    # Información económica
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    iva = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Datos adicionales
    notas = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_pedido']

    def __str__(self):
        return f"Pedido #{self.numero_pedido} - {self.cliente.get_full_name()}"
    
    def save(self, *args, **kwargs):
        # Generar número de pedido si es nuevo
        if not self.numero_pedido:
            ultimo_pedido = Pedido.objects.order_by('-id').first()
            ultimo_numero = 1
            if ultimo_pedido and ultimo_pedido.numero_pedido:
                try:
                    ultimo_numero = int(ultimo_pedido.numero_pedido) + 1
                except ValueError:
                    ultimo_numero = 1
            self.numero_pedido = f"{ultimo_numero:08d}"
        super().save(*args, **kwargs)

    def actualizar_estado(self, nuevo_estado, usuario, notas=""):
        """Actualiza el estado del pedido y registra el cambio"""
        estado_anterior = self.estado
        
        # Obtener el nuevo objeto EstadoPedido
        if isinstance(nuevo_estado, str):
            nuevo_estado_obj = EstadoPedido.objects.get(nombre=nuevo_estado)
        else:
            nuevo_estado_obj = nuevo_estado
            
        # Actualizar el estado
        self.estado = nuevo_estado_obj
        self.save()
        
        # Registrar el cambio
        CambioPedido.objects.create(
            pedido=self,
            estado_anterior=estado_anterior.nombre,
            estado_nuevo=nuevo_estado_obj.nombre,
            usuario=usuario,
            notas=notas
        )
        
        return True

class DetallePedido(models.Model):
    """Modelo para items en un pedido"""
    pedido = models.ForeignKey(Pedido, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    notas = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        """Calcula el subtotal antes de guardar"""
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.pedido.numero_pedido} - {self.producto.nombre} x {self.cantidad}"

# Agregar esta clase para mantener la compatibilidad con el código existente
class PedidoItem(models.Model):
    """Modelo para items en un pedido"""
    pedido = models.ForeignKey(Pedido, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    notas = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        """Calcula el subtotal antes de guardar"""
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.pedido.numero_pedido} - {self.producto.nombre} x {self.cantidad}"

class CambioPedido(models.Model):
    """Modelo para registrar cambios en el estado de los pedidos"""
    pedido = models.ForeignKey(Pedido, related_name='cambios', on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    estado_anterior = models.CharField(max_length=50)
    estado_nuevo = models.CharField(max_length=50)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notas = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.pedido.numero_pedido}: {self.estado_anterior} -> {self.estado_nuevo}"