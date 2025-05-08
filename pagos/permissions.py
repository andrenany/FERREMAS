from rest_framework import permissions

class EsContador(permissions.BasePermission):
    """
    Permiso personalizado para contadores.
    Solo los contadores y administradores pueden acceder.
    """
    
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.es_administrador() or request.user.es_contador())
        )

class PuedeVerFactura(permissions.BasePermission):
    """
    Permiso para ver facturas.
    - Administradores y contadores pueden ver todas las facturas
    - Usuarios normales solo pueden ver sus propias facturas
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        if request.user.es_administrador() or request.user.es_contador():
            return True
            
        return obj.pedido.usuario == request.user 