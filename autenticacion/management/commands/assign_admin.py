from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from autenticacion.models import User

class Command(BaseCommand):
    help = 'Asigna el usuario administrador al grupo administrador'

    def handle(self, *args, **kwargs):
        try:
            # Obtener el usuario administrador
            admin_user = User.objects.get(email='admin@ferremas.cl')
            
            # Obtener el grupo administrador
            admin_group = Group.objects.get(name='administrador')
            
            # Asignar el usuario al grupo
            admin_user.groups.add(admin_group)
            
            self.stdout.write(self.style.SUCCESS(f'Usuario {admin_user.email} asignado al grupo administrador exitosamente'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('No se encontró el usuario administrador'))
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR('No se encontró el grupo administrador')) 