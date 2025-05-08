import pytest
from django.urls import reverse
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APIClient
from productos.models import Producto, Categoria, Marca, Inventario
from productos.tests.factories import (
    UserFactory, CategoriaFactory, MarcaFactory,
    ProductoFactory, InventarioFactory
)

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user():
    user = UserFactory(is_staff=True, is_superuser=True)
    return user

@pytest.fixture
def vendedor_group():
    return Group.objects.create(name='vendedor')

@pytest.fixture
def bodeguero_group():
    return Group.objects.create(name='bodeguero')

@pytest.fixture
def vendedor_user(vendedor_group):
    user = UserFactory()
    user.groups.add(vendedor_group)
    return user

@pytest.fixture
def bodeguero_user(bodeguero_group):
    user = UserFactory()
    user.groups.add(bodeguero_group)
    return user

@pytest.fixture
def categoria():
    return CategoriaFactory()

@pytest.fixture
def marca():
    return MarcaFactory()

@pytest.fixture
def producto(categoria, marca):
    return ProductoFactory(categoria=categoria, marca=marca)

@pytest.fixture
def producto_data(categoria, marca):
    return {
        'codigo': 'TEST001',
        'nombre': 'Producto Test',
        'descripcion': 'Descripción del producto test',
        'categoria': categoria.id,
        'marca': marca.id,
        'precio_base': '100.00',
        'peso': '1.5',
        'dimensiones': '10x20x30',
        'activo': True,
        'destacado': False
    }

@pytest.mark.django_db
class TestProductoViewSet:
    def test_list_productos(self, api_client, vendedor_user, producto):
        api_client.force_authenticate(user=vendedor_user)
        url = reverse('producto-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_retrieve_producto(self, api_client, vendedor_user, producto):
        api_client.force_authenticate(user=vendedor_user)
        url = reverse('producto-detail', kwargs={'pk': producto.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['codigo'] == producto.codigo

    def test_create_producto(self, api_client, admin_user, producto_data):
        api_client.force_authenticate(user=admin_user)
        url = reverse('producto-list')
        response = api_client.post(url, producto_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Producto.objects.count() == 1
        assert Producto.objects.first().codigo == producto_data['codigo']

    def test_create_producto_codigo_duplicado(self, api_client, admin_user, producto, producto_data):
        api_client.force_authenticate(user=admin_user)
        producto_data['codigo'] = producto.codigo
        url = reverse('producto-list')
        response = api_client.post(url, producto_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'codigo' in response.data

    def test_create_producto_sin_permisos(self, api_client, vendedor_user, producto_data):
        api_client.force_authenticate(user=vendedor_user)
        url = reverse('producto-list')
        response = api_client.post(url, producto_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_producto(self, api_client, admin_user, producto):
        api_client.force_authenticate(user=admin_user)
        url = reverse('producto-detail', kwargs={'pk': producto.pk})
        data = {
            'nombre': 'Producto Actualizado',
            'precio_base': '150.00'
        }
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['nombre'] == 'Producto Actualizado'
        assert response.data['precio_base'] == '150.00'

    def test_update_producto_sin_permisos(self, api_client, vendedor_user, producto):
        api_client.force_authenticate(user=vendedor_user)
        url = reverse('producto-detail', kwargs={'pk': producto.pk})
        data = {'nombre': 'Producto Actualizado'}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_producto(self, api_client, admin_user, producto):
        api_client.force_authenticate(user=admin_user)
        url = reverse('producto-detail', kwargs={'pk': producto.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        producto.refresh_from_db()
        assert not producto.activo

    def test_delete_producto_sin_permisos(self, api_client, vendedor_user, producto):
        api_client.force_authenticate(user=vendedor_user)
        url = reverse('producto-detail', kwargs={'pk': producto.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_filter_productos_by_categoria(self, api_client, vendedor_user, producto):
        api_client.force_authenticate(user=vendedor_user)
        url = reverse('producto-list')
        response = api_client.get(url, {'categoria': producto.categoria.id})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_filter_productos_by_marca(self, api_client, vendedor_user, producto):
        api_client.force_authenticate(user=vendedor_user)
        url = reverse('producto-list')
        response = api_client.get(url, {'marca': producto.marca.id})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_filter_productos_by_precio(self, api_client, vendedor_user, producto):
        api_client.force_authenticate(user=vendedor_user)
        url = reverse('producto-list')
        response = api_client.get(url, {
            'precio_min': producto.precio_base - 10,
            'precio_max': producto.precio_base + 10
        })
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_search_productos(self, api_client, vendedor_user, producto):
        api_client.force_authenticate(user=vendedor_user)
        url = reverse('producto-list')
        response = api_client.get(url, {'search': producto.nombre[:4]})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

@pytest.mark.django_db
class TestInventarioViewSet:
    def test_registrar_movimiento(self, api_client, bodeguero_user, producto):
        api_client.force_authenticate(user=bodeguero_user)
        inventario = InventarioFactory(producto=producto, stock_actual=10)
        url = reverse('producto-registrar-movimiento', kwargs={'pk': producto.pk})
        data = {
            'inventario': inventario.id,
            'tipo': 'entrada',
            'cantidad': 5,
            'motivo': 'Ingreso de mercadería'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        inventario.refresh_from_db()
        assert inventario.stock_actual == 15

    def test_registrar_movimiento_salida_sin_stock(self, api_client, bodeguero_user, producto):
        api_client.force_authenticate(user=bodeguero_user)
        inventario = InventarioFactory(producto=producto, stock_actual=5)
        url = reverse('producto-registrar-movimiento', kwargs={'pk': producto.pk})
        data = {
            'inventario': inventario.id,
            'tipo': 'salida',
            'cantidad': 10,
            'motivo': 'Venta'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        inventario.refresh_from_db()
        assert inventario.stock_actual == 5

    def test_registrar_movimiento_sin_permisos(self, api_client, vendedor_user, producto):
        api_client.force_authenticate(user=vendedor_user)
        inventario = InventarioFactory(producto=producto, stock_actual=10)
        url = reverse('producto-registrar-movimiento', kwargs={'pk': producto.pk})
        data = {
            'inventario': inventario.id,
            'tipo': 'entrada',
            'cantidad': 5,
            'motivo': 'Ingreso de mercadería'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_registrar_movimiento_cantidad_negativa(self, api_client, bodeguero_user, producto):
        api_client.force_authenticate(user=bodeguero_user)
        inventario = InventarioFactory(producto=producto, stock_actual=10)
        url = reverse('producto-registrar-movimiento', kwargs={'pk': producto.pk})
        data = {
            'inventario': inventario.id,
            'tipo': 'entrada',
            'cantidad': -5,
            'motivo': 'Ingreso de mercadería'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST 