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


class ClienteRegistrationSerializer(UserSerializer):
    """Serializador para el registro de clientes"""
    password = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        # Asignar automáticamente el username con el email
        # Asegurarse de que el email exista antes de asignarlo al username
        email = data.get('email')
        if email:
            data['username'] = email
        return data

    def validate_password(self, value):
        if value:
            validate_password(value)
        return value

    def create(self, validated_data):
        # Extraer la contraseña y eliminar campos que no son del modelo directamente
        password = validated_data.pop('password')
        validated_data.pop('rol', None)  # <- Elimina el 'rol' si está presente

        # Asegurarse de que el username esté en validated_data (debería venir de validate)
        # Si por alguna razón no está, asignarlo desde el email (aunque validate debería hacerlo)
        if 'username' not in validated_data or not validated_data['username']:
             validated_data['username'] = validated_data.get('email', '') # Usar get con valor por defecto por seguridad

        user = User(**validated_data)
        user.set_password(password)
        user.save()
        user.asignar_rol('cliente')  # Aquí se asigna el rol por lógica
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
        user.save()
        user.asignar_rol(rol)
        password = user.generar_credenciales_iniciales()
        user.save()
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
        self.context['password_temporal'] = password
        return user


class UserUpdateSerializer(UserSerializer):
    """Serializador para actualizar usuarios"""
    current_password = serializers.CharField(write_only=True, required=False)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['current_password']

    def validate(self, attrs):
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
    username_field = 'email'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            username_field = self.fields.pop('username')
            self.fields['email'] = username_field

    def validate(self, attrs):
        if 'email' in attrs:
            attrs['username'] = attrs.get('email')

        data = super().validate(attrs)
        user_data = UserSerializer(self.user).data
        data['user'] = user_data
        data['debe_cambiar_password'] = self.user.debe_cambiar_password
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=False)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class ResetPasswordConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class NewsletterSubscriptionSerializer(serializers.Serializer):
    suscrito_newsletter = serializers.BooleanField(required=True)
