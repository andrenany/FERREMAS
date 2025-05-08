from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

class PreferenciasNotificacion(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    email_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    platform_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Preferencia de notificación"
        verbose_name_plural = "Preferencias de notificaciones"

class PlantillaNotificacion(models.Model):
    TIPOS_NOTIFICACION = [
        ('consulta', 'Consulta de Producto'),
        ('pedido', 'Estado de Pedido'),
        ('pago', 'Validación de Pago'),
        ('preparacion', 'Preparación de Pedido'),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPOS_NOTIFICACION)
    asunto_email = models.CharField(max_length=200)
    contenido_email = models.TextField()
    contenido_push = models.CharField(max_length=200)
    contenido_platform = models.TextField()
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Plantilla de notificación"
        verbose_name_plural = "Plantillas de notificaciones"

class Notificacion(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('enviada', 'Enviada'),
        ('leida', 'Leída'),
        ('fallida', 'Fallida'),
    ]

    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    plantilla = models.ForeignKey(PlantillaNotificacion, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    
    # Para referencias genéricas (ej: pedido, pago, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    contenido_relacionado = GenericForeignKey('content_type', 'object_id')
    
    datos_contexto = models.JSONField(default=dict)  # Para almacenar variables de la plantilla

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-fecha_creacion']
