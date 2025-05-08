import pytest
from django.urls import reverse
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from autenticacion.tests.factories import (
    UserFactory, AdminUserFactory, VendedorUserFactory,
    BodegueroUserFactory, ContadorUserFactory, ClienteUserFactory
)

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user():
    return AdminUserFactory()

@pytest.fixture
def vendedor_user():
    return VendedorUserFactory()

@pytest.fixture
def bodeguero_user():
    return BodegueroUserFactory()

@pytest.fixture
def contador_user():
    return ContadorUserFactory()

@pytest.fixture
def cliente_user():
    return ClienteUserFactory()

@pytest.fixture
def cliente_data():
    return {
        'username': 'testcliente',
        'email': 'cliente@test.com',
        'password': 'TestPass123',
        'first_name': 'Test',
        'last_name': 'Cliente',
        'telefono': '123456789',
        'direccion': 'Test Address',
        'ciudad': 'Test City',
        'region': 'Test Region',
        'rut': '12345678-9',
        'suscrito_newsletter': True
    }

@pytest.fixture
def staff_data():
    return {
        'first_name': 'Test',
        'last_name': 'Vendedor',
        'email': 'vendedor@test.com',
        'telefono': '123456789',
        'rut': '12345678-9',
        'rol': 'vendedor'
    }

@pytest.fixture
def admin_data():
    return {
        'first_name': 'Test',
        'last_name': 'Admin',
        'email': 'admin@test.com',
        'telefono': '123456789',
        'rut': '12345678-9'
    }

@pytest.mark.django_db
class TestAuthViews:
    def test_registro_cliente(self, api_client, cliente_data):
        """Test de registro de cliente"""
        url = reverse('register-cliente')
        response = api_client.post(url, cliente_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == cliente_data['email']
        assert response.data['es_cliente'] is True
        assert response.data['suscrito_newsletter'] is True
        assert 'password' not in response.data

    def test_registro_staff_por_admin(self, api_client, admin_user, staff_data):
        """Test de registro de personal por administrador"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('register-staff')
        response = api_client.post(url, staff_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == staff_data['email']
        assert 'password' not in response.data

    def test_registro_staff_sin_permisos(self, api_client, vendedor_user, staff_data):
        """Test de registro de personal sin permisos"""
        api_client.force_authenticate(user=vendedor_user)
        url = reverse('register-staff')
        response = api_client.post(url, staff_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_registro_admin(self, api_client, admin_user, admin_data):
        """Test de registro de administrador"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('register-admin')
        response = api_client.post(url, admin_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == admin_data['email']
        assert 'password' not in response.data

    def test_login_usuario(self, api_client, cliente_data):
        """Test de login de usuario"""
        # Primero registramos el usuario
        api_client.post(reverse('register-cliente'), cliente_data)
        
        # Intentamos hacer login
        url = reverse('token_obtain_pair')
        response = api_client.post(url, {
            'email': cliente_data['email'],
            'password': cliente_data['password']
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data
        assert 'debe_cambiar_password' in response.data

    def test_refresh_token(self, api_client, cliente_data):
        """Test de refresh token"""
        # Primero registramos y hacemos login
        api_client.post(reverse('register-cliente'), cliente_data)
        response = api_client.post(reverse('token_obtain_pair'), {
            'email': cliente_data['email'],
            'password': cliente_data['password']
        })
        refresh_token = response.data['refresh']
        
        # Intentamos refrescar el token
        url = reverse('token_refresh')
        response = api_client.post(url, {'refresh': refresh_token})
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_cambio_password_primera_vez(self, api_client, admin_user, admin_data):
        """Test de cambio de contraseña en primer login"""
        api_client.force_authenticate(user=admin_user)
        # Crear nuevo admin que debe cambiar contraseña
        url = reverse('register-admin')
        response = api_client.post(url, admin_data)
        new_admin_id = response.data['id']
        
        # Obtener el usuario creado
        new_admin = User.objects.get(id=new_admin_id)
        api_client.force_authenticate(user=new_admin)
        
        # Cambiar contraseña
        url = reverse('user-change-password', args=[new_admin_id])
        response = api_client.post(url, {
            'new_password': 'NewTestPass123'
        })
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar que ya no debe cambiar contraseña
        new_admin.refresh_from_db()
        assert not new_admin.debe_cambiar_password

    def test_cambio_password_normal(self, api_client, cliente_user):
        """Test de cambio de contraseña normal"""
        api_client.force_authenticate(user=cliente_user)
        url = reverse('user-change-password', args=[cliente_user.id])
        response = api_client.post(url, {
            'old_password': 'password123',
            'new_password': 'NewTestPass123'
        })
        assert response.status_code == status.HTTP_200_OK

    def test_reset_password_request(self, api_client, cliente_user):
        """Test de solicitud de reset de contraseña"""
        url = reverse('user-reset-password')
        response = api_client.post(url, {'email': cliente_user.email})
        assert response.status_code == status.HTTP_200_OK

    def test_toggle_newsletter(self, api_client, cliente_user):
        """Test de toggle newsletter"""
        api_client.force_authenticate(user=cliente_user)
        url = reverse('user-toggle-newsletter', args=[cliente_user.id])
        
        # Suscribirse
        response = api_client.post(url, {'suscrito_newsletter': True})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['suscrito_newsletter'] is True
        
        # Desuscribirse
        response = api_client.post(url, {'suscrito_newsletter': False})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['suscrito_newsletter'] is False

    def test_permisos_admin(self, api_client, admin_user):
        """Test de permisos de administrador"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('user-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_permisos_vendedor(self, api_client, vendedor_user):
        """Test de permisos de vendedor"""
        api_client.force_authenticate(user=vendedor_user)
        # Intentar crear staff (no permitido)
        url = reverse('register-staff')
        response = api_client.post(url, {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permisos_cliente(self, api_client, cliente_user):
        """Test de permisos de cliente"""
        api_client.force_authenticate(user=cliente_user)
        url = reverse('user-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_me_endpoint(self, api_client, cliente_user):
        """Test del endpoint me"""
        api_client.force_authenticate(user=cliente_user)
        url = reverse('user-me')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == cliente_user.email 