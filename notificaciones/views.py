from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Notificacion, PreferenciasNotificacion, PlantillaNotificacion
from .serializers import (
    NotificacionSerializer,
    PreferenciasNotificacionSerializer,
    PlantillaNotificacionSerializer
)
from .services import NotificacionService

# Create your views here.

class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notificacion.objects.filter(destinatario=self.request.user)

    @action(detail=True, methods=['post'])
    def marcar_leida(self, request, pk=None):
        notificacion = NotificacionService.marcar_como_leida(pk, request.user)
        return Response(self.get_serializer(notificacion).data)

    @action(detail=False, methods=['get'])
    def no_leidas(self, request):
        notificaciones = self.get_queryset().filter(estado='pendiente')
        return Response(self.get_serializer(notificaciones, many=True).data)

class PreferenciasNotificacionViewSet(viewsets.ModelViewSet):
    serializer_class = PreferenciasNotificacionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PreferenciasNotificacion.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class PlantillaNotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PlantillaNotificacion.objects.filter(activa=True)
    serializer_class = PlantillaNotificacionSerializer
    permission_classes = [IsAuthenticated]
