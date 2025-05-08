from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoriaViewSet, MarcaViewSet, EtiquetaViewSet,
    AtributoProductoViewSet, ProductoViewSet, ImagenProductoViewSet
)

router = DefaultRouter()
router.register(r'categorias', CategoriaViewSet)
router.register(r'marcas', MarcaViewSet)
router.register(r'etiquetas', EtiquetaViewSet)
router.register(r'atributos', AtributoProductoViewSet)
router.register(r'productos', ProductoViewSet)
router.register(r'imagenes', ImagenProductoViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 