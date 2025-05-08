from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Modelo personalizado de usuario para FERREMAS"""
    email = models.EmailField(_('email address'), unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    rut = models.CharField(max_length=12, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    # Campos específicos para clientes
    es_cliente = models.BooleanField(default=False)
    suscrito_newsletter = models.BooleanField(default=False)
    limite_credito = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text='Límite de crédito para compras a plazo'
    )
    
    # Campos de seguridad y auditoría
    debe_cambiar_password = models.BooleanField(default=False)
    ultimo_cambio_password = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        """Retorna el nombre completo del usuario"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email

    def get_rol(self):
        """Obtiene el rol principal del usuario"""
        return self.groups.first()

    def asignar_rol(self, nombre_rol):
        """Asigna un rol al usuario"""
        rol, _ = Group.objects.get_or_create(name=nombre_rol)
        self.groups.clear()  # Un usuario solo puede tener un rol
        self.groups.add(rol)
        
        # Configuración específica según el rol
        if nombre_rol == 'cliente':
            self.es_cliente = True
        elif nombre_rol in ['administrador', 'vendedor', 'bodeguero', 'contador']:
            self.es_cliente = False
            if nombre_rol == 'administrador':
                self.debe_cambiar_password = True

    def es_administrador(self):
        return self.groups.filter(name='administrador').exists()

    def es_vendedor(self):
        return self.groups.filter(name='vendedor').exists()

    def es_bodeguero(self):
        return self.groups.filter(name='bodeguero').exists()

    def es_contador(self):
        return self.groups.filter(name='contador').exists()

    def generar_credenciales_iniciales(self):
        """Genera credenciales iniciales basadas en nombre y RUT"""
        if self.rut:
            # Usuario: primera letra del nombre + apellido en minúsculas
            nombre_usuario = f"{self.first_name[0]}{self.last_name}".lower()
            self.username = nombre_usuario
            
            # Contraseña: RUT sin puntos ni guión
            password = self.rut.replace('.', '').replace('-', '')
            self.set_password(password)
            
            # Marcar para cambio obligatorio
            self.debe_cambiar_password = True
            
            return password
        return None

    def __str__(self):
        return f'{self.get_full_name()} ({self.email})'
