from django.conf import settings
from django.core.mail import send_mail
from django.template import Template, Context
from django.utils import timezone
from firebase_admin import messaging

from .models import Notificacion, PlantillaNotificacion

class NotificacionService:
    @staticmethod
    def crear_notificacion(destinatario, tipo_notificacion, contenido_relacionado=None, **context_data):
        """
        Crea y envía una notificación basada en el tipo y contexto proporcionado.
        """
        plantilla = PlantillaNotificacion.objects.get(tipo=tipo_notificacion, activa=True)
        
        notificacion = Notificacion.objects.create(
            destinatario=destinatario,
            plantilla=plantilla,
            contenido_relacionado=contenido_relacionado,
            datos_contexto=context_data
        )
        
        # Procesar el contexto
        context = Context(context_data)
        
        # Enviar notificaciones según las preferencias del usuario
        preferencias = destinatario.preferenciasnotificacion
        
        if preferencias.email_enabled:
            NotificacionService._enviar_email(notificacion, context)
            
        if preferencias.platform_enabled:
            NotificacionService._enviar_platform(notificacion, context)
            
        if preferencias.push_enabled:
            NotificacionService._enviar_push(notificacion, context)
            
        return notificacion

    @staticmethod
    def _enviar_email(notificacion, context):
        """Envía la notificación por email"""
        plantilla = notificacion.plantilla
        contenido_email = Template(plantilla.contenido_email).render(context)
        asunto = Template(plantilla.asunto_email).render(context)
        
        try:
            send_mail(
                subject=asunto,
                message=contenido_email,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notificacion.destinatario.email],
                html_message=contenido_email
            )
            notificacion.estado = 'enviada'
            notificacion.fecha_envio = timezone.now()
            notificacion.save()
        except Exception as e:
            notificacion.estado = 'fallida'
            notificacion.save()
            raise e

    @staticmethod
    def _enviar_platform(notificacion, context):
        """Guarda la notificación en la base de datos para ser consultada por la plataforma"""
        plantilla = notificacion.plantilla
        contenido = Template(plantilla.contenido_platform).render(context)
        
        notificacion.contenido = contenido
        notificacion.estado = 'pendiente'
        notificacion.fecha_creacion = timezone.now()
        notificacion.save()

    @staticmethod
    def _enviar_push(notificacion, context):
        """Envía push notification usando Firebase Cloud Messaging"""
        plantilla = notificacion.plantilla
        contenido = Template(plantilla.contenido_push).render(context)
        
        # Asumiendo que el token FCM está almacenado en el perfil del usuario
        if hasattr(notificacion.destinatario, 'fcm_token'):
            mensaje = messaging.Message(
                notification=messaging.Notification(
                    title="FERREMAS",
                    body=contenido,
                ),
                token=notificacion.destinatario.fcm_token,
                data={
                    'tipo': plantilla.tipo,
                    'id': str(notificacion.id)
                }
            )
            
            try:
                messaging.send(mensaje)
            except Exception as e:
                # Manejar el error pero no detener el proceso
                print(f"Error enviando push notification: {e}")

    @staticmethod
    def marcar_como_leida(notificacion_id, usuario):
        """Marca una notificación como leída"""
        notificacion = Notificacion.objects.get(id=notificacion_id, destinatario=usuario)
        notificacion.estado = 'leida'
        notificacion.fecha_lectura = timezone.now()
        notificacion.save()
        return notificacion 