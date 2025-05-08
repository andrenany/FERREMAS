from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Sucursal
from .serializers import SucursalSerializer
from productos.permissions import EsAdminOVendedor

# Create your views here.

class SucursalViewSet(viewsets.ModelViewSet):
    queryset = Sucursal.objects.all()
    serializer_class = SucursalSerializer
    permission_classes = [IsAuthenticated, EsAdminOVendedor]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ciudad', 'region', 'activo']
    search_fields = ['nombre', 'direccion', 'ciudad', 'region']
    ordering_fields = ['nombre', 'ciudad', 'created_at']
    ordering = ['nombre']

    def perform_destroy(self, instance):
        """Soft delete: marcar como inactivo en lugar de eliminar"""
        instance.activo = False
        instance.save()
