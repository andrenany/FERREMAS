from rest_framework import permissions

class EsAdministrador(permissions.BasePermission):
    """Permiso para administradores"""
    def has_permission(self, request, view):
        return request.user and request.user.es_administrador()

class EsVendedor(permissions.BasePermission):
    """Permiso para vendedores"""
    def has_permission(self, request, view):
        return request.user and request.user.es_vendedor()

class EsBodeguero(permissions.BasePermission):
    """Permiso para bodegueros"""
    def has_permission(self, request, view):
        return request.user and request.user.es_bodeguero()

class EsContador(permissions.BasePermission):
    """Permiso para contadores"""
    def has_permission(self, request, view):
        return request.user and request.user.es_contador()

class EsCliente(permissions.BasePermission):
    """Permiso para clientes"""
    def has_permission(self, request, view):
        return request.user and request.user.es_cliente

class EsAdminOPropietario(permissions.BasePermission):
    """Permiso para administradores o el propietario del recurso"""
    def has_object_permission(self, request, view, obj):
        return bool(
            request.user.es_administrador() or
            obj.id == request.user.id
        ) 