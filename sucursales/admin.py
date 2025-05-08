from django.contrib import admin
from .models import Sucursal

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ciudad', 'region', 'telefono', 'email', 'activo')
    list_filter = ('activo', 'ciudad', 'region')
    search_fields = ('nombre', 'direccion', 'ciudad', 'region', 'telefono', 'email')
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'direccion')
        }),
        ('Ubicación', {
            'fields': ('ciudad', 'region')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )
