from rest_framework import serializers
from .models import Sucursal

class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = [
            'id', 'nombre', 'direccion', 'ciudad', 'region',
            'telefono', 'email', 'activo', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_email(self, value):
        """Validar que el email sea único"""
        instance = self.instance
        if Sucursal.objects.filter(email=value).exclude(id=instance.id if instance else None).exists():
            raise serializers.ValidationError("Ya existe una sucursal con este email")
        return value 