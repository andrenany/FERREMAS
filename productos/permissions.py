from rest_framework import permissions

class EsAdminOVendedor(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.rol.nombre in ['administrador', 'vendedor']

class EsAdminOBodeguero(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.rol.nombre in ['administrador', 'bodeguero'] 