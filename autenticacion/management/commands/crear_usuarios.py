from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea los usuarios del sistema con sus respectivos roles'

    def handle(self, *args, **kwargs):
        # Crear grupos si no existen
        roles = ['administrador', 'vendedor', 'bodeguero', 'contador', 'cliente']
        for rol in roles:
            Group.objects.get_or_create(name=rol)
            self.stdout.write(self.style.SUCCESS(f'Grupo {rol} creado o ya existente'))

        # Crear usuarios del sistema
        usuarios = [
            {
                'email': 'admin@ferremas.cl',
                'username': 'admin',
                'password': 'admin12345',
                'first_name': 'Carlos',
                'last_name': 'Administrador',
                'rol': 'administrador',
                'telefono': '+56955555555',
                'direccion': 'Avenida Administrativa 1',
                'ciudad': 'Santiago',
                'region': 'Metropolitana',
                'rut': '11111111-1'
            },
            {
                'email': 'vendedor@ferremas.cl',
                'username': 'vendedor',
                'password': 'vendedor123',
                'first_name': 'Juan',
                'last_name': 'Vendedor',
                'rol': 'vendedor',
                'telefono': '+56912345678',
                'direccion': 'Calle Principal 123',
                'ciudad': 'Santiago',
                'region': 'Metropolitana',
                'rut': '12345678-9'
            },
            {
                'email': 'bodeguero@ferremas.cl',
                'username': 'bodeguero',
                'password': 'bodeguero123',
                'first_name': 'Pedro',
                'last_name': 'Bodeguero',
                'rol': 'bodeguero',
                'telefono': '+56987654321',
                'direccion': 'Avenida Central 456',
                'ciudad': 'Santiago',
                'region': 'Metropolitana',
                'rut': '87654321-0'
            },
            {
                'email': 'contador@ferremas.cl',
                'username': 'contador',
                'password': 'contador123',
                'first_name': 'María',
                'last_name': 'Contador',
                'rol': 'contador',
                'telefono': '+56923456789',
                'direccion': 'Plaza Mayor 789',
                'ciudad': 'Santiago',
                'region': 'Metropolitana',
                'rut': '23456789-1'
            }
        ]

        for usuario_data in usuarios:
            # Crear usuario si no existe
            user, created = User.objects.get_or_create(
                email=usuario_data['email'],
                defaults={
                    'username': usuario_data['username'],
                    'first_name': usuario_data['first_name'],
                    'last_name': usuario_data['last_name'],
                    'telefono': usuario_data['telefono'],
                    'direccion': usuario_data['direccion'],
                    'ciudad': usuario_data['ciudad'],
                    'region': usuario_data['region'],
                    'rut': usuario_data['rut'],
                    'is_active': True
                }
            )
            
            if created:
                # Establecer contraseña
                user.set_password(usuario_data['password'])
                user.save()
                
                # Asignar rol
                rol = Group.objects.get(name=usuario_data['rol'])
                user.groups.add(rol)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Usuario {usuario_data["username"]} creado exitosamente')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'El usuario {usuario_data["username"]} ya existe')
                ) 