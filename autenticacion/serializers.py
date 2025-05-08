from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializador base para el modelo de usuario"""
    rol = serializers.CharField(source='get_rol.name', read_only=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'password', 'first_name', 'last_name',
            'telefono', 'direccion', 'ciudad', 'region', 'rut',
            'fecha_nacimiento', 'es_cliente', 'suscrito_newsletter',
            'limite_credito', 'rol', 'is_active', 'debe_cambiar_password',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'is_active', 'debe_cambiar_password',
            'ultimo_cambio_password'
        ]

    def validate_password(self, value):
        if value:
            validate_password(value)
        return value

class ClienteRegistrationSerializer(UserSerializer):
    """Serializador para el registro de clientes"""
    password = serializers.CharField(write_only=True, required=True)

    def create(self, validated_data):
        validated_data['rol'] = 'cliente'
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        user.asignar_rol('cliente')
        return user

class StaffRegistrationSerializer(UserSerializer):
    """Serializador para el registro de personal (vendedores, bodegueros, contadores)"""
    rol = serializers.ChoiceField(
        choices=['vendedor', 'bodeguero', 'contador'],
        write_only=True
    )

    def create(self, validated_data):
        rol = validated_data.pop('rol')
        user = User(**validated_data)
        # Generar credenciales iniciales basadas en nombre y RUT
        user.save()
        user.asignar_rol(rol)
        password = user.generar_credenciales_iniciales()
        user.save()
        
        # Almacenar la contraseña temporal para enviarla por correo
        self.context['password_temporal'] = password
        return user

class AdminRegistrationSerializer(UserSerializer):
    """Serializador para el registro de administradores"""
    def create(self, validated_data):
        user = User(**validated_data)
        user.save()
        user.asignar_rol('administrador')
        password = user.generar_credenciales_iniciales()
        user.save()
        
        # Almacenar la contraseña temporal para enviarla por correo
        self.context['password_temporal'] = password
        return user

class UserUpdateSerializer(UserSerializer):
    """Serializador para actualizar usuarios"""
    current_password = serializers.CharField(write_only=True, required=False)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['current_password']

    def validate(self, attrs):
        # Si se intenta cambiar la contraseña, validar la contraseña actual
        if 'password' in attrs and not self.instance.debe_cambiar_password:
            current_password = attrs.pop('current_password', None)
            if not current_password:
                raise serializers.ValidationError({
                    'current_password': 'Debe proporcionar la contraseña actual'
                })
            if not self.instance.check_password(current_password):
                raise serializers.ValidationError({
                    'current_password': 'Contraseña actual incorrecta'
                })
        return attrs

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
            instance.debe_cambiar_password = False
            instance.save()
        return super().update(instance, validated_data)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializador personalizado para el token JWT"""
    def validate(self, attrs):
        data = super().validate(attrs)
        user_data = UserSerializer(self.user).data
        data['user'] = user_data
        data['debe_cambiar_password'] = self.user.debe_cambiar_password
        return data

class ChangePasswordSerializer(serializers.Serializer):
    """Serializador para cambio de contraseña"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

class ResetPasswordSerializer(serializers.Serializer):
    """Serializador para restablecer contraseña"""
    email = serializers.EmailField(required=True)

class ResetPasswordConfirmSerializer(serializers.Serializer):
    """Serializador para confirmar restablecimiento de contraseña"""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

class NewsletterSubscriptionSerializer(serializers.Serializer):
    """Serializador para suscripción al newsletter"""
    suscrito_newsletter = serializers.BooleanField(required=True) 