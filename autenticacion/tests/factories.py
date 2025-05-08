import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from faker import Faker

fake = Faker('es_ES')  # Usamos el locale español

class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ('name',)

    name = factory.Iterator(['administrador', 'vendedor', 'bodeguero', 'contador', 'cliente'])

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.LazyFunction(lambda: fake.user_name())
    email = factory.LazyFunction(lambda: fake.email())
    first_name = factory.LazyFunction(lambda: fake.first_name())
    last_name = factory.LazyFunction(lambda: fake.last_name())
    password = factory.PostGenerationMethodCall('set_password', 'password123')
    is_active = True
    telefono = factory.LazyFunction(lambda: fake.phone_number())
    direccion = factory.LazyFunction(lambda: fake.address())
    ciudad = factory.LazyFunction(lambda: fake.city())
    region = factory.LazyFunction(lambda: fake.state())
    rut = factory.LazyFunction(lambda: f"{fake.random_int(min=1000000, max=25000000)}-{fake.random_int(min=0, max=9)}")
    fecha_nacimiento = factory.LazyFunction(lambda: fake.date_of_birth(minimum_age=18, maximum_age=90))

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for group in extracted:
                self.groups.add(group)
        elif kwargs.get('rol'):
            group, _ = Group.objects.get_or_create(name=kwargs['rol'])
            self.groups.add(group)

class AdminUserFactory(UserFactory):
    """Factory para usuarios administradores"""
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            group, _ = Group.objects.get_or_create(name='administrador')
            self.groups.add(group)

class VendedorUserFactory(UserFactory):
    """Factory para usuarios vendedores"""
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            group, _ = Group.objects.get_or_create(name='vendedor')
            self.groups.add(group)

class BodegueroUserFactory(UserFactory):
    """Factory para usuarios bodegueros"""
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            group, _ = Group.objects.get_or_create(name='bodeguero')
            self.groups.add(group)

class ContadorUserFactory(UserFactory):
    """Factory para usuarios contadores"""
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            group, _ = Group.objects.get_or_create(name='contador')
            self.groups.add(group)

class ClienteUserFactory(UserFactory):
    """Factory para usuarios clientes"""
    es_cliente = True
    limite_credito = factory.LazyFunction(lambda: fake.random_int(min=0, max=1000000))

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            group, _ = Group.objects.get_or_create(name='cliente')
            self.groups.add(group) 