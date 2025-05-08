import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from productos.models import (
    Categoria, Marca, Producto, Inventario,
    MovimientoInventario
)
from faker import Faker

fake = Faker()

class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ('name',)

    name = factory.Iterator(['administrador', 'vendedor', 'bodeguero', 'contador'])

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.LazyFunction(lambda: fake.user_name())
    email = factory.LazyFunction(lambda: fake.email())
    first_name = factory.LazyFunction(lambda: fake.first_name())
    last_name = factory.LazyFunction(lambda: fake.last_name())
    is_active = True

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for group in extracted:
                self.groups.add(group)
        elif kwargs.get('rol__nombre'):
            group, _ = Group.objects.get_or_create(name=kwargs['rol__nombre'])
            self.groups.add(group)

class CategoriaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Categoria

    nombre = factory.LazyFunction(lambda: fake.word().title())
    descripcion = factory.LazyFunction(lambda: fake.text())
    activo = True

class MarcaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Marca

    nombre = factory.LazyFunction(lambda: fake.company())
    descripcion = factory.LazyFunction(lambda: fake.text())
    activo = True

class ProductoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Producto

    codigo = factory.Sequence(lambda n: f'PROD{n:04d}')
    nombre = factory.LazyFunction(lambda: fake.word().title())
    descripcion = factory.LazyFunction(lambda: fake.text())
    categoria = factory.SubFactory(CategoriaFactory)
    marca = factory.SubFactory(MarcaFactory)
    precio_base = factory.LazyFunction(lambda: fake.random_number(4))
    activo = True

class SucursalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'sucursales.Sucursal'

    nombre = factory.LazyFunction(lambda: f'Sucursal {fake.city()}')
    direccion = factory.LazyFunction(lambda: fake.address())
    ciudad = factory.LazyFunction(lambda: fake.city())
    region = factory.LazyFunction(lambda: fake.state())

class InventarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Inventario

    producto = factory.SubFactory(ProductoFactory)
    sucursal = factory.SubFactory(SucursalFactory)
    stock_actual = factory.LazyFunction(lambda: fake.random_int(min=0, max=100))
    stock_minimo = 5
    ubicacion_bodega = factory.LazyFunction(lambda: f'Pasillo {fake.random_int(min=1, max=10)}') 