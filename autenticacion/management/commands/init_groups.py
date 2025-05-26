from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Inicializa los grupos de usuarios necesarios'

    def handle(self, *args, **kwargs):
        # Lista de grupos a crear
        grupos = ['administrador', 'vendedor', 'bodeguero', 'contador', 'cliente']
        
        for nombre_grupo in grupos:
            grupo, created = Group.objects.get_or_create(name=nombre_grupo)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Grupo "{nombre_grupo}" creado exitosamente'))
            else:
                self.stdout.write(self.style.WARNING(f'El grupo "{nombre_grupo}" ya existe')) 