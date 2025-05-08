from rest_framework import permissions

class PuedeGestionarPedido(permissions.BasePermission):
    """
    Permiso personalizado para gestionar pedidos:
    - Administradores y vendedores pueden ver todos los pedidos
    - Bodegueros pueden ver y actualizar pedidos en preparación/despacho
    - Usuarios normales solo pueden ver y crear sus propios pedidos
    """
    
    def has_permission(self, request, view):
        # Cualquier usuario autenticado puede listar y crear pedidos
        if not request.user.is_authenticated:
            return False
        
        if view.action in ['create', 'list', 'retrieve']:
            return True
        
        # Solo personal autorizado puede realizar otras acciones
        return (
            request.user.es_administrador() or
            request.user.es_vendedor() or
            request.user.es_bodeguero()
        )
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Los administradores pueden hacer todo
        if user.es_administrador():
            return True
        
        # Los vendedores pueden ver todos los pedidos y actualizar algunos estados
        if user.es_vendedor():
            if view.action == 'actualizar_estado':
                return obj.estado in ['listo_retiro', 'entregado']
            return True
        
        # Los bodegueros pueden actualizar estados relacionados con preparación y despacho
        if user.es_bodeguero():
            if view.action == 'actualizar_estado':
                return obj.estado in ['pagado', 'preparacion', 'en_despacho']
            return obj.estado in ['pagado', 'preparacion', 'en_despacho']
        
        # Los usuarios normales solo pueden ver sus propios pedidos
        return obj.usuario == user 