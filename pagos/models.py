from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from pedidos.models import Pedido

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
    datos_adicionales = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Transacción MP {self.preference_id} - Pedido {self.pedido.numero}"

class FacturaElectronica(models.Model):
    """Modelo para manejar facturas electrónicas"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Emisión'),
        ('emitida', 'Emitida'),
        ('enviada', 'Enviada al SII'),
        ('aceptada', 'Aceptada por SII'),
        ('rechazada', 'Rechazada por SII')
    ]
    
    pedido = models.OneToOneField(Pedido, on_delete=models.PROTECT, related_name='factura')
    numero_factura = models.CharField(max_length=50, unique=True)
    fecha_emision = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    # Datos del emisor (FERREMAS)
    rut_emisor = models.CharField(max_length=20)
    razon_social_emisor = models.CharField(max_length=200)
    giro_emisor = models.CharField(max_length=200)
    direccion_emisor = models.CharField(max_length=200)
    
    # Datos del receptor (cliente)
    rut_receptor = models.CharField(max_length=20)
    razon_social_receptor = models.CharField(max_length=200)
    giro_receptor = models.CharField(max_length=200, blank=True)
    direccion_receptor = models.CharField(max_length=200)
    
    # Montos
    neto = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    iva = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Datos técnicos
    xml_factura = models.TextField(blank=True)
    pdf_factura = models.FileField(upload_to='facturas/', null=True, blank=True)
    track_id = models.CharField(max_length=100, blank=True)
    respuesta_sii = models.TextField(blank=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_emision']
    
    def __str__(self):
        return f"Factura {self.numero_factura} - Pedido {self.pedido.numero}"

class ConciliacionPago(models.Model):
    """Modelo para manejar la conciliación de pagos"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('conciliado', 'Conciliado'),
        ('discrepancia', 'Con Discrepancia')
    ]
    
    transaccion = models.OneToOneField(TransaccionMercadoPago, on_delete=models.PROTECT)
    factura = models.OneToOneField(FacturaElectronica, on_delete=models.PROTECT)
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
        return f"Conciliación {self.transaccion.pedido.numero}"
    
    def clean(self):
        """Validaciones personalizadas del modelo"""
        if self.estado == 'conciliado':
            if not self.conciliado_por:
                raise ValueError("Se requiere un contador para marcar como conciliado")
            if not self.fecha_conciliacion:
                raise ValueError("Se requiere fecha de conciliación al marcar como conciliado")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
