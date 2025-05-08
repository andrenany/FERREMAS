from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    UserSerializer, ClienteRegistrationSerializer, StaffRegistrationSerializer,
    AdminRegistrationSerializer, UserUpdateSerializer, CustomTokenObtainPairSerializer,
    ChangePasswordSerializer, ResetPasswordSerializer, ResetPasswordConfirmSerializer,
    NewsletterSubscriptionSerializer
)
from .permissions import (
    EsAdministrador, EsAdminOPropietario, EsVendedor, EsBodeguero,
    EsContador, EsCliente
)

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    """Vista personalizada para obtener tokens JWT"""
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            # Actualizar IP de último login
            user = self.serializer_class.get_user(request.data)
            user.last_login_ip = request.META.get('REMOTE_ADDR')
            user.save(update_fields=['last_login_ip'])
        return response

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar usuarios"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, EsAdminOPropietario]

    def get_serializer_class(self):
        if self.action == 'create_cliente':
            return ClienteRegistrationSerializer
        elif self.action == 'create_staff':
            return StaffRegistrationSerializer
        elif self.action == 'create_admin':
            return AdminRegistrationSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return self.serializer_class

    def get_permissions(self):
        if self.action == 'create_cliente':
            return [AllowAny()]
        elif self.action in ['create_staff', 'create_admin', 'list']:
            return [IsAuthenticated(), EsAdministrador()]
        return super().get_permissions()

    @action(detail=False, methods=['post'])
    def create_cliente(self, request):
        """Endpoint para registro de clientes"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user.suscrito_newsletter:
                self._enviar_email_bienvenida_newsletter(user)
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, EsAdministrador])
    def create_staff(self, request):
        """Endpoint para crear usuarios del personal"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            password_temporal = serializer.context.get('password_temporal')
            self._enviar_credenciales_iniciales(user, password_temporal)
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, EsAdministrador])
    def create_admin(self, request):
        """Endpoint para crear usuarios administradores"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            password_temporal = serializer.context.get('password_temporal')
            self._enviar_credenciales_iniciales(user, password_temporal)
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Endpoint para cambiar contraseña"""
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            # Si debe cambiar la contraseña, no validar la contraseña anterior
            if not user.debe_cambiar_password:
                if not user.check_password(serializer.data.get('old_password')):
                    return Response(
                        {'old_password': ['Contraseña incorrecta.']},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            user.set_password(serializer.data.get('new_password'))
            user.debe_cambiar_password = False
            user.ultimo_cambio_password = timezone.now()
            user.save()
            return Response({'status': 'Contraseña actualizada'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def reset_password(self, request):
        """Endpoint para solicitar restablecimiento de contraseña"""
        serializer = ResetPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.data.get('email')
            try:
                user = User.objects.get(email=email)
                token = default_token_generator.make_token(user)
                reset_url = f"{settings.FRONTEND_URL}/reset-password/{user.id}/{token}/"
                
                send_mail(
                    'Restablecimiento de Contraseña - FERREMAS',
                    f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                
                return Response({'status': 'Email de restablecimiento enviado'})
            except User.DoesNotExist:
                pass
            
        return Response({'status': 'Si el email existe, recibirás instrucciones'})

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def reset_password_confirm(self, request):
        """Endpoint para confirmar restablecimiento de contraseña"""
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                user_id = request.data.get('user_id')
                token = serializer.data.get('token')
                user = User.objects.get(id=user_id)
                
                if default_token_generator.check_token(user, token):
                    user.set_password(serializer.data.get('new_password'))
                    user.debe_cambiar_password = False
                    user.ultimo_cambio_password = timezone.now()
                    user.save()
                    return Response({'status': 'Contraseña restablecida'})
                
            except User.DoesNotExist:
                pass
            
        return Response(
            {'error': 'Token inválido o expirado'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Endpoint para obtener información del usuario actual"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_newsletter(self, request, pk=None):
        """Endpoint para suscribirse/desuscribirse del newsletter"""
        user = self.get_object()
        serializer = NewsletterSubscriptionSerializer(data=request.data)
        
        if serializer.is_valid():
            suscrito = serializer.validated_data['suscrito_newsletter']
            user.suscrito_newsletter = suscrito
            user.save()
            
            if suscrito:
                self._enviar_email_bienvenida_newsletter(user)
            
            return Response({
                'status': 'Suscripción actualizada',
                'suscrito_newsletter': suscrito
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _enviar_credenciales_iniciales(self, user, password_temporal):
        """Envía las credenciales iniciales por correo"""
        send_mail(
            'Credenciales de Acceso - FERREMAS',
            f"""
            Bienvenido/a a FERREMAS.
            
            Tus credenciales de acceso son:
            Usuario: {user.username}
            Contraseña temporal: {password_temporal}
            
            Por seguridad, deberás cambiar tu contraseña en el primer inicio de sesión.
            """,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

    def _enviar_email_bienvenida_newsletter(self, user):
        """Envía email de bienvenida al newsletter"""
        send_mail(
            'Bienvenido al Newsletter de FERREMAS',
            """
            ¡Gracias por suscribirte a nuestro newsletter!
            
            Recibirás noticias sobre:
            - Ofertas especiales
            - Descuentos en compras de más de 4 artículos
            - Novedades y promociones
            
            Puedes cancelar tu suscripción en cualquier momento desde tu perfil.
            """,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
