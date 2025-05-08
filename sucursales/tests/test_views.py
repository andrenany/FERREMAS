import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from sucursales.models import Sucursal
from productos.tests.factories import UserFactory

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user():
    return UserFactory(is_staff=True)

@pytest.fixture
def sucursal_data():
    return {
        'nombre': 'Sucursal Central',
        'direccion': 'Av. Principal 123',
        'ciudad': 'Ciudad Test',
        'region': 'Región Test',
        'telefono': '123456789',
        'email': 'sucursal@test.com'
    }

@pytest.mark.django_db
class TestSucursalViewSet:
    def test_crear_sucursal(self, api_client, admin_user, sucursal_data):
        api_client.force_authenticate(user=admin_user)
        url = reverse('sucursal-list')
        response = api_client.post(url, sucursal_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Sucursal.objects.count() == 1
        assert Sucursal.objects.first().nombre == sucursal_data['nombre']

    def test_listar_sucursales(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        Sucursal.objects.create(
            nombre='Sucursal Test',
            direccion='Dirección Test',
            ciudad='Ciudad Test',
            region='Región Test'
        )
        url = reverse('sucursal-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_actualizar_sucursal(self, api_client, admin_user, sucursal_data):
        api_client.force_authenticate(user=admin_user)
        sucursal = Sucursal.objects.create(**sucursal_data)
        url = reverse('sucursal-detail', kwargs={'pk': sucursal.pk})
        nuevo_nombre = 'Sucursal Actualizada'
        response = api_client.patch(url, {'nombre': nuevo_nombre})
        assert response.status_code == status.HTTP_200_OK
        sucursal.refresh_from_db()
        assert sucursal.nombre == nuevo_nombre

    def test_eliminar_sucursal(self, api_client, admin_user, sucursal_data):
        api_client.force_authenticate(user=admin_user)
        sucursal = Sucursal.objects.create(**sucursal_data)
        url = reverse('sucursal-detail', kwargs={'pk': sucursal.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        sucursal.refresh_from_db()
        assert not sucursal.activo 