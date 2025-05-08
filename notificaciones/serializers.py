from rest_framework import serializers
from .models import Notificacion, PreferenciasNotificacion, PlantillaNotificacion

class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = [
            'id', 'destinatario', 'plantilla', 'estado',
            'fecha_creacion', 'fecha_envio', 'fecha_lectura',
            'datos_contexto'
        ]
        read_only_fields = fields

class PreferenciasNotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreferenciasNotificacion
        fields = ['email_enabled', 'push_enabled', 'platform_enabled']

class PlantillaNotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantillaNotificacion
        fields = [
            'id', 'nombre', 'tipo', 'asunto_email',
            'contenido_email', 'contenido_push', 'contenido_platform'
        ]
        read_only_fields = fields 