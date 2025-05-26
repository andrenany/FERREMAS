# pagos/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from pedidos.models import Pedido

class MetodoPago(models.Model):
    """Modelo para métodos de pago"""
    nombre = models.CharField(max_length=50, unique=True)
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='metodos_pago/', blank=True, null=True)
    requiere_confirmacion_manual = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre

class Pago(models.Model):
    """Modelo principal para pagos"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
        ('rechazado', 'Rechazado'),
        ('reembolsado', 'Reembolsado'),
    ]
    
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='pagos')
    metodo_pago = models.ForeignKey(MetodoPago, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    referencia_transaccion = models.CharField(max_length=100, blank=True, null=True)
    token_webpay = models.CharField(max_length=255, blank=True, null=True)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    datos_adicionales = models.JSONField(default=dict, blank=True, null=True)
    confirmado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagos_confirmados'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pago {self.id} - Pedido {self.pedido.numero_pedido}"

class TransaccionWebpay(models.Model):
    """Modelo para transacciones de Webpay"""
    ESTADO_CHOICES = [
        ('INITIALIZED', 'Inicializada'),
        ('AUTHORIZED', 'Autorizada'),
        ('FAILED', 'Fallida'),
        ('NULLIFIED', 'Anulada'),
        ('CAPTURED', 'Capturada'),
        ('REVERSED', 'Reversada')
    ]
    
    pago = models.OneToOneField(Pago, on_delete=models.CASCADE, related_name='transaccion_webpay')
    token = models.CharField(max_length=255)
    orden_compra = models.CharField(max_length=50)
    session_id = models.CharField(max_length=100)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='INITIALIZED')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    codigo_autorizacion = models.CharField(max_length=50, blank=True, null=True)
    codigo_respuesta = models.CharField(max_length=10, blank=True, null=True)
    tarjeta_ultimos_digitos = models.CharField(max_length=4, blank=True, null=True)
    fecha_transaccion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    respuesta_completa = models.JSONField(default=dict, blank=True, null=True)
    
    def __str__(self):
        return f"Webpay - {self.token[:8]}... - {self.estado}"

class Factura(models.Model):
    """Modelo para facturas electrónicas"""
    # Agregar las opciones de estado
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Emisión'),
        ('emitida', 'Emitida'),
        ('enviada', 'Enviada al SII'),
        ('aceptada', 'Aceptada por SII'),
        ('rechazada', 'Rechazada por SII')
    ]
    
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='factura')
    numero_factura = models.CharField(max_length=20, unique=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    
    # Campos económicos
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    neto = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    iva = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    url_pdf = models.URLField(blank=True, null=True)
    # Añadir el campo faltante que está en el serializer
    pdf_factura = models.FileField(upload_to='facturas/pdf/', blank=True, null=True)
    emitida_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='facturas_emitidas'
    )
    
    # Campo estado
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    # Campos para receptor
    rut_receptor = models.CharField(max_length=20, blank=True, null=True)
    razon_social_receptor = models.CharField(max_length=200, blank=True, null=True)
    giro_receptor = models.CharField(max_length=200, blank=True, null=True)
    direccion_receptor = models.CharField(max_length=200, blank=True, null=True)
    
    # Nuevo campo xml_factura
    xml_factura = models.TextField(blank=True, null=True)
    
    # Datos de tracking
    track_id = models.CharField(max_length=100, blank=True, null=True)
    respuesta_sii = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    # Añadir campo para fecha de actualización para resolver referencia en serializer
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    # Añadir campo para fecha_creacion para resolver referencia en serializer
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    
    # Datos fiscales
    rut_emisor = models.CharField(max_length=20, default=settings.FACTURACION_RUT_EMISOR)
    razon_social_emisor = models.CharField(max_length=200, default=settings.FACTURACION_RAZON_SOCIAL)
    giro_emisor = models.CharField(max_length=200, default=settings.FACTURACION_GIRO)
    direccion_emisor = models.CharField(max_length=200, default=settings.FACTURACION_DIRECCION)

    def __str__(self):
        return f"Factura #{self.numero_factura}"

    def save(self, *args, **kwargs):
        # Asegurarse de que neto y subtotal sean iguales
        if self.subtotal and not self.neto:
            self.neto = self.subtotal
        elif self.neto and not self.subtotal:
            self.subtotal = self.neto
            
        # Si es nueva factura, generar número de factura
        if not self.numero_factura:
            ultima_factura = Factura.objects.order_by('-id').first()
            ultimo_numero = 1
            if ultima_factura and ultima_factura.numero_factura:
                try:
                    ultimo_numero = int(ultima_factura.numero_factura) + 1
                except ValueError:
                    ultimo_numero = 1
            self.numero_factura = f"{ultimo_numero:08d}"
        super().save(*args, **kwargs)

# Modelos adicionales que faltan
class TransaccionMercadoPago(models.Model):
    """Modelo para manejar transacciones de Mercado Pago"""
    ESTADO_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('authorized', 'Autorizado'),
        ('in_process', 'En Proceso'),
        ('in_mediation', 'En Mediación'),
        ('rejected', 'Rechazado'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
        ('charged_back', 'Contracargo')
    ]
    
    pedido = models.ForeignKey(Pedido, on_delete=models.PROTECT, related_name='transacciones_mp')
    preference_id = models.CharField(max_length=100, unique=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    merchant_order_id = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pending')
    monto = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    datos_adicionales = models.JSONField(default=dict, blank=True, null=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Transacción MP {self.preference_id} - Pedido {self.pedido.numero_pedido}"

# Alias para mantener compatibilidad con código que usa FacturaElectronica
FacturaElectronica = Factura

class ConciliacionPago(models.Model):
    """Modelo para manejar la conciliación de pagos"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('conciliado', 'Conciliado'),
        ('discrepancia', 'Con Discrepancia')
    ]
    
    transaccion = models.OneToOneField(TransaccionMercadoPago, on_delete=models.PROTECT)
    factura = models.OneToOneField(Factura, on_delete=models.PROTECT)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_conciliacion = models.DateTimeField(null=True, blank=True)
    notas = models.TextField(blank=True)
    conciliado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='conciliaciones'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Conciliación {self.transaccion.pedido.numero_pedido}"