from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.utils import timezone

from pedidos.models import Pedido
from .models import TransaccionMercadoPago, FacturaElectronica, ConciliacionPago
from .services import MercadoPagoService, FacturacionService

User = get_user_model()

# Configuración de prueba
TEST_SETTINGS = {
    'MERCADOPAGO_ACCESS_TOKEN': 'TEST-0123456789abcdef0123456789abcdef',
    'SITE_URL': 'http://localhost:8000',
    'FACTURACION_RUT_EMISOR': '76.123.456-7',
    'FACTURACION_RAZON_SOCIAL': 'FERREMAS SpA',
    'FACTURACION_GIRO': 'Venta al por menor de artículos de ferretería',
    'FACTURACION_DIRECCION': 'Av. Principal 123, Santiago'
}

class MercadoPagoServiceTest(TestCase):
    """Tests para el servicio de Mercado Pago"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com',
            rut='12.345.678-9'
        )
        self.pedido = Pedido.objects.create(
            usuario=self.user,
            numero='00000001',
            tipo_entrega='retiro',
            nombre_contacto='Test User',
            email_contacto='test@example.com',
            telefono_contacto='123456789',
            subtotal=Decimal('1000.00'),
            total=Decimal('1000.00')
        )

    @patch('mercadopago.sdk.SDK')
    def test_flujo_pago_completo_exitoso(self, mock_sdk_class):
        """Test del flujo completo de pago exitoso desde la creación hasta la conciliación"""
        
        # Configurar mock del SDK
        mock_sdk = MagicMock()
        mock_sdk_class.return_value = mock_sdk
        
        # Mock de preference
        mock_preference = MagicMock()
        mock_preference.create.return_value = {
            "status": 201,
            "response": {
                "id": "test_preference_id",
                "init_point": "https://www.mercadopago.com/checkout/v1/redirect?pref_id=test_preference_id",
                "items": [
                    {
                        "title": f"Pedido #{self.pedido.numero}",
                        "quantity": 1,
                        "currency_id": "CLP",
                        "unit_price": float(self.pedido.total)
                    }
                ]
            }
        }
        mock_sdk.preference.return_value = mock_preference
        
        # Crear servicio con mock
        mp_service = MercadoPagoService(sdk=mock_sdk)
        
        # Crear preferencia
        transaccion = mp_service.crear_preferencia(self.pedido)
        
        # Verificar preferencia creada
        self.assertEqual(transaccion.pedido, self.pedido)
        self.assertEqual(transaccion.preference_id, "test_preference_id")
        self.assertEqual(transaccion.monto, self.pedido.total)
        self.assertEqual(transaccion.estado, "pending")
        
        # Mock de payment
        mock_payment = MagicMock()
        mock_payment.get.return_value = {
            "status": 200,
            "response": {
                "id": "test_payment_id",
                "preference_id": "test_preference_id",
                "order": {"id": "test_order_id"},
                "status": "approved",
                "transaction_amount": float(self.pedido.total),
                "payment_method_id": "visa",
                "payment_type_id": "credit_card",
                "date_approved": "2024-03-20T15:30:00.000-04:00"
            }
        }
        mock_sdk.payment.return_value = mock_payment
        
        # Procesar webhook
        webhook_data = {
            "type": "payment",
            "data": {"id": "test_payment_id"}
        }
        
        updated_transaccion = mp_service.procesar_webhook(webhook_data)
        
        # Verificar actualización de transacción
        self.assertEqual(updated_transaccion.payment_id, "test_payment_id")
        self.assertEqual(updated_transaccion.estado, "approved")
        self.assertEqual(updated_transaccion.merchant_order_id, "test_order_id")
        
        # Verificar que el pedido fue actualizado
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, "pagado")
        
        # Verificar generación de factura
        factura = FacturaElectronica.objects.get(pedido=self.pedido)
        self.assertIsNotNone(factura)
        self.assertEqual(factura.estado, "pendiente")
        self.assertEqual(factura.total, self.pedido.total)

    @patch('mercadopago.sdk.SDK')
    def test_flujo_pago_rechazado(self, mock_sdk_class):
        """Test del flujo de pago cuando es rechazado"""
        
        # Configurar mock del SDK
        mock_sdk = MagicMock()
        mock_sdk_class.return_value = mock_sdk
        
        # Mock de preference
        mock_preference = MagicMock()
        mock_preference.create.return_value = {
            "status": 201,
            "response": {
                "id": "test_preference_id",
                "init_point": "https://www.mercadopago.com/checkout/v1/redirect?pref_id=test_preference_id"
            }
        }
        mock_sdk.preference.return_value = mock_preference
        
        # Crear servicio con mock
        mp_service = MercadoPagoService(sdk=mock_sdk)
        
        # Crear preferencia
        transaccion = mp_service.crear_preferencia(self.pedido)
        
        # Mock de payment rechazado
        mock_payment = MagicMock()
        mock_payment.get.return_value = {
            "status": 200,
            "response": {
                "id": "test_payment_id",
                "preference_id": "test_preference_id",
                "order": {"id": "test_order_id"},
                "status": "rejected",
                "transaction_amount": float(self.pedido.total),
                "payment_method_id": "visa",
                "payment_type_id": "credit_card"
            }
        }
        mock_sdk.payment.return_value = mock_payment
        
        # Procesar webhook
        webhook_data = {
            "type": "payment",
            "data": {"id": "test_payment_id"}
        }
        
        updated_transaccion = mp_service.procesar_webhook(webhook_data)
        
        # Verificar que la transacción fue actualizada
        self.assertEqual(updated_transaccion.payment_id, "test_payment_id")
        self.assertEqual(updated_transaccion.estado, "rejected")
        
        # Verificar que el pedido mantiene su estado original
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, "pendiente")
        
        # Verificar que no se generó factura
        self.assertFalse(FacturaElectronica.objects.filter(pedido=self.pedido).exists())

    @patch('mercadopago.sdk.SDK')
    def test_flujo_pago_webhook_invalido(self, mock_sdk_class):
        """Test del manejo de webhooks inválidos"""
        
        # Configurar mock del SDK
        mock_sdk = MagicMock()
        mock_sdk_class.return_value = mock_sdk
        
        # Mock de preference
        mock_preference = MagicMock()
        mock_preference.create.return_value = {
            "status": 201,
            "response": {
                "id": "test_preference_id",
                "init_point": "https://www.mercadopago.com/checkout/v1/redirect?pref_id=test_preference_id"
            }
        }
        mock_sdk.preference.return_value = mock_preference
        
        # Crear servicio con mock
        mp_service = MercadoPagoService(sdk=mock_sdk)
        
        # Crear preferencia
        transaccion = mp_service.crear_preferencia(self.pedido)
        
        # Mock de payment inválido
        mock_payment = MagicMock()
        mock_payment.get.return_value = {
            "status": 404,
            "response": {
                "message": "Payment not found"
            }
        }
        mock_sdk.payment.return_value = mock_payment
        
        # Procesar webhook
        webhook_data = {
            "type": "payment",
            "data": {"id": "invalid_payment_id"}
        }
        
        with self.assertRaises(Exception) as context:
            mp_service.procesar_webhook(webhook_data)
        
        # Verificar que la transacción mantiene su estado original
        transaccion.refresh_from_db()
        self.assertEqual(transaccion.estado, "pending")
        
        # Verificar que el pedido mantiene su estado original
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, "pendiente")

class FacturacionServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com'
        )
        self.pedido = Pedido.objects.create(
            usuario=self.user,
            numero='00000001',
            tipo_entrega='retiro',
            nombre_contacto='Test User',
            email_contacto='test@example.com',
            telefono_contacto='123456789',
            subtotal=Decimal('1000.00'),
            total=Decimal('1000.00')
        )
        self.factura = FacturaElectronica.objects.create(
            pedido=self.pedido,
            numero_factura='F00000001',
            fecha_emision=timezone.datetime(2024, 3, 20, tzinfo=timezone.get_current_timezone()),
            rut_emisor='76.123.456-7',
            razon_social_emisor='FERREMAS SpA',
            giro_emisor='Ferretería',
            direccion_emisor='Dirección 123',
            rut_receptor='12.345.678-9',
            razon_social_receptor='Test User',
            direccion_receptor='Dirección Cliente 123',
            neto=Decimal('840.34'),
            iva=Decimal('159.66'),
            total=Decimal('1000.00')
        )
        self.facturacion_service = FacturacionService()
    
    def test_generar_xml(self):
        xml = self.facturacion_service.generar_xml(self.factura)
        self.assertIn(self.factura.numero_factura, xml)
        self.assertIn(self.factura.rut_emisor, xml)
        self.assertIn(self.factura.rut_receptor, xml)
    
    def test_enviar_al_sii(self):
        track_id = self.facturacion_service.enviar_al_sii(self.factura)
        self.assertTrue(track_id.startswith('T'))
        self.assertEqual(self.factura.estado, 'enviada')
    
    def test_generar_pdf(self):
        pdf = self.facturacion_service.generar_pdf(self.factura)
        self.assertTrue(pdf.name.endswith('.pdf'))

class TransaccionMercadoPagoViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com'
        )
        self.admin = User.objects.create_user(
            username='admin',
            password='adminpass',
            email='admin@example.com',
            is_staff=True,
            is_superuser=True
        )
        self.pedido = Pedido.objects.create(
            usuario=self.user,
            numero='00000001',
            tipo_entrega='retiro',
            nombre_contacto='Test User',
            email_contacto='test@example.com',
            telefono_contacto='123456789',
            subtotal=Decimal('1000.00'),
            total=Decimal('1000.00')
        )
    
    def test_crear_transaccion(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('transaccion-list')
        data = {'pedido_id': self.pedido.id}
        
        with patch('pagos.services.MercadoPagoService.crear_preferencia') as mock_crear:
            mock_crear.return_value = TransaccionMercadoPago.objects.create(
                pedido=self.pedido,
                preference_id='test_preference_id',
                monto=self.pedido.total
            )
            
            response = self.client.post(url, data)
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['preference_id'], 'test_preference_id')
    
    def test_webhook(self):
        url = reverse('transaccion-webhook')
        data = {
            "type": "payment",
            "data": {"id": "test_payment_id"}
        }
        
        with patch('pagos.services.MercadoPagoService.procesar_webhook') as mock_webhook:
            mock_webhook.return_value = None
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

class ConciliacionPagoViewSetTest(APITestCase):
    def setUp(self):
        self.contador = User.objects.create_user(
            username='contador',
            password='contadorpass',
            email='contador@example.com'
        )
        self.pedido = Pedido.objects.create(
            usuario=User.objects.create_user(
                username='cliente',
                password='clientepass'
            ),
            numero='00000001',
            tipo_entrega='retiro',
            nombre_contacto='Cliente Test',
            email_contacto='cliente@example.com',
            telefono_contacto='123456789',
            subtotal=Decimal('1000.00'),
            total=Decimal('1000.00')
        )
        self.transaccion = TransaccionMercadoPago.objects.create(
            pedido=self.pedido,
            preference_id='test_preference_id',
            monto=self.pedido.total
        )
        self.factura = FacturaElectronica.objects.create(
            pedido=self.pedido,
            numero_factura='F00000001',
            fecha_emision='2024-03-20',
            rut_emisor='76.123.456-7',
            razon_social_emisor='FERREMAS SpA',
            giro_emisor='Ferretería',
            direccion_emisor='Dirección 123',
            rut_receptor='12.345.678-9',
            razon_social_receptor='Cliente Test',
            direccion_receptor='Dirección Cliente 123',
            neto=Decimal('840.34'),
            iva=Decimal('159.66'),
            total=Decimal('1000.00')
        )
    
    def test_crear_conciliacion(self):
        self.client.force_authenticate(user=self.contador)
        url = reverse('conciliacion-list')
        data = {
            'transaccion_id': self.transaccion.id,
            'factura_id': self.factura.id
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['estado'], 'pendiente')
    
    def test_marcar_conciliado(self):
        conciliacion = ConciliacionPago.objects.create(
            transaccion=self.transaccion,
            factura=self.factura,
            conciliado_por=self.contador
        )
        
        self.client.force_authenticate(user=self.contador)
        url = reverse('conciliacion-marcar-conciliado', args=[conciliacion.id])
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'conciliado')

@override_settings(**TEST_SETTINGS)
class FlujoPagoCompletoTest(TestCase):
    """Test que simula el flujo completo de pago"""
    
    def setUp(self):
        # Crear usuario cliente
        self.cliente = User.objects.create_user(
            username='cliente',
            password='clientepass',
            email='cliente@test.com',
            rut='12.345.678-9'
        )
        
        # Crear usuario contador
        self.contador = User.objects.create_user(
            username='contador',
            password='contadorpass',
            email='contador@test.com',
            is_staff=True
        )
        
        # Crear pedido
        self.pedido = Pedido.objects.create(
            usuario=self.cliente,
            numero='00000001',
            tipo_entrega='retiro',
            nombre_contacto='Cliente Test',
            email_contacto='cliente@test.com',
            telefono_contacto='123456789',
            subtotal=Decimal('10000.00'),
            total=Decimal('10000.00')
        )
        
        self.mp_service = MercadoPagoService()

    @patch('mercadopago.sdk.SDK')
    def test_flujo_pago_completo_exitoso(self, mock_sdk_class):
        """Test del flujo completo de pago exitoso desde la creación hasta la conciliación"""
        
        # Configurar mock del SDK
        mock_sdk = MagicMock()
        mock_sdk_class.return_value = mock_sdk
        
        # Mock de preference
        mock_preference = MagicMock()
        mock_preference.create.return_value = {
            "status": 201,
            "response": {
                "id": "test_preference_id",
                "init_point": "https://www.mercadopago.com/checkout/v1/redirect?pref_id=test_preference_id",
                "items": [
                    {
                        "title": f"Pedido #{self.pedido.numero}",
                        "quantity": 1,
                        "currency_id": "CLP",
                        "unit_price": float(self.pedido.total)
                    }
                ]
            }
        }
        mock_sdk.preference.return_value = mock_preference
        
        transaccion = self.mp_service.crear_preferencia(self.pedido)
        
        self.assertEqual(transaccion.pedido, self.pedido)
        self.assertEqual(transaccion.preference_id, "test_preference_id")
        self.assertEqual(transaccion.monto, self.pedido.total)
        self.assertEqual(transaccion.estado, "pending")
        
        # Mock de payment
        mock_payment = MagicMock()
        mock_payment.get.return_value = {
            "status": 200,
            "response": {
                "id": "test_payment_id",
                "preference_id": "test_preference_id",
                "order": {"id": "test_order_id"},
                "status": "approved",
                "transaction_amount": float(self.pedido.total),
                "payment_method_id": "visa",
                "payment_type_id": "credit_card",
                "date_approved": "2024-03-20T15:30:00.000-04:00"
            }
        }
        mock_sdk.payment.return_value = mock_payment
        
        webhook_data = {
            "type": "payment",
            "data": {"id": "test_payment_id"}
        }
        
        updated_transaccion = self.mp_service.procesar_webhook(webhook_data)
        
        # Verificar actualización de transacción
        self.assertEqual(updated_transaccion.payment_id, "test_payment_id")
        self.assertEqual(updated_transaccion.estado, "approved")
        self.assertEqual(updated_transaccion.merchant_order_id, "test_order_id")
        
        # Verificar que el pedido fue actualizado
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, "pagado")
        
        # 3. Verificar generación de factura
        factura = FacturaElectronica.objects.get(pedido=self.pedido)
        self.assertIsNotNone(factura)
        self.assertEqual(factura.estado, "pendiente")
        self.assertEqual(factura.total, self.pedido.total)
        
        # 4. Simular conciliación del pago
        conciliacion = ConciliacionPago.objects.create(
            transaccion=updated_transaccion,
            factura=factura,
            conciliado_por=self.contador,
            estado='pendiente'
        )
        
        # Marcar como conciliado
        conciliacion.estado = 'conciliado'
        conciliacion.fecha_conciliacion = timezone.now()
        conciliacion.save()
        
        self.assertEqual(conciliacion.estado, 'conciliado')
        self.assertIsNotNone(conciliacion.fecha_conciliacion)

    @patch('mercadopago.SDK')
    def test_flujo_pago_rechazado(self, mock_sdk):
        """Test del flujo de pago cuando es rechazado"""
        
        # 1. Crear preferencia de pago
        mock_preference = MagicMock()
        mock_preference.create.return_value = {
            "status": 201,
            "response": {
                "id": "test_preference_id",
                "init_point": "https://www.mercadopago.com/checkout/v1/redirect?pref_id=test_preference_id"
            }
        }
        mock_sdk.return_value.preference.return_value = mock_preference
        
        transaccion = self.mp_service.crear_preferencia(self.pedido)
        
        # 2. Simular webhook de pago rechazado
        mock_payment = MagicMock()
        mock_payment.get.return_value = {
            "status": 200,
            "response": {
                "id": "test_payment_id",
                "preference_id": "test_preference_id",
                "order": {"id": "test_order_id"},
                "status": "rejected",
                "transaction_amount": 10000.00,
                "payment_method_id": "visa",
                "payment_type_id": "credit_card"
            }
        }
        mock_sdk.return_value.payment.return_value = mock_payment
        
        webhook_data = {
            "type": "payment",
            "data": {"id": "test_payment_id"}
        }
        
        updated_transaccion = self.mp_service.procesar_webhook(webhook_data)
        
        # Verificar actualización de transacción
        self.assertEqual(updated_transaccion.payment_id, "test_payment_id")
        self.assertEqual(updated_transaccion.estado, "rejected")
        
        # Verificar que el pedido mantiene su estado original
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, "pendiente")
        
        # Verificar que no se generó factura
        self.assertFalse(FacturaElectronica.objects.filter(pedido=self.pedido).exists())

    @patch('mercadopago.SDK')
    def test_flujo_pago_con_error_preference(self, mock_sdk):
        """Test del flujo cuando hay error al crear la preferencia"""
        
        # Simular error al crear preferencia
        mock_preference = MagicMock()
        mock_preference.create.return_value = {
            "status": 400,
            "response": {
                "message": "Error creating preference",
                "error": "invalid_request"
            }
        }
        mock_sdk.return_value.preference.return_value = mock_preference
        
        with self.assertRaises(Exception) as context:
            self.mp_service.crear_preferencia(self.pedido)
        
        self.assertTrue("Error al crear preferencia en Mercado Pago" in str(context.exception))
        
        # Verificar que no se creó la transacción
        self.assertFalse(TransaccionMercadoPago.objects.filter(pedido=self.pedido).exists())

    @patch('mercadopago.SDK')
    def test_flujo_pago_webhook_invalido(self, mock_sdk):
        """Test del manejo de webhooks inválidos"""
        
        # 1. Crear preferencia inicial
        mock_preference = MagicMock()
        mock_preference.create.return_value = {
            "status": 201,
            "response": {
                "id": "test_preference_id"
            }
        }
        mock_sdk.return_value.preference.return_value = mock_preference
        
        transaccion = self.mp_service.crear_preferencia(self.pedido)
        
        # 2. Simular webhook con datos inválidos
        webhook_data = {
            "type": "payment",
            "data": {"id": "invalid_payment_id"}
        }
        
        mock_payment = MagicMock()
        mock_payment.get.return_value = {
            "status": 404,
            "response": {
                "message": "Payment not found"
            }
        }
        mock_sdk.return_value.payment.return_value = mock_payment
        
        with self.assertRaises(Exception) as context:
            self.mp_service.procesar_webhook(webhook_data)
        
        # Verificar que la transacción mantiene su estado original
        transaccion.refresh_from_db()
        self.assertEqual(transaccion.estado, "pending")
        
        # Verificar que el pedido mantiene su estado original
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, "pendiente")

    def test_validaciones_conciliacion(self):
        """Test de las validaciones en el proceso de conciliación"""
        
        # Crear transacción y factura para pruebas
        transaccion = TransaccionMercadoPago.objects.create(
            pedido=self.pedido,
            preference_id="test_preference_id",
            payment_id="test_payment_id",
            estado="approved",
            monto=self.pedido.total
        )
        
        factura = FacturaElectronica.objects.create(
            pedido=self.pedido,
            numero_factura="F00000001",
            fecha_emision=timezone.now(),
            rut_emisor="76.123.456-7",
            razon_social_emisor="FERREMAS SpA",
            giro_emisor="Ferretería",
            direccion_emisor="Dirección 123",
            rut_receptor=self.cliente.rut,
            razon_social_receptor=self.cliente.get_full_name(),
            direccion_receptor="Dirección Cliente 123",
            neto=Decimal('8403.36'),
            iva=Decimal('1596.64'),
            total=self.pedido.total
        )
        
        # Intentar crear conciliación sin contador
        with self.assertRaises(ValueError):
            ConciliacionPago.objects.create(
                transaccion=transaccion,
                factura=factura,
                estado='conciliado'
            )
        
        # Crear conciliación correctamente
        conciliacion = ConciliacionPago.objects.create(
            transaccion=transaccion,
            factura=factura,
            conciliado_por=self.contador,
            estado='pendiente'
        )
        
        # Verificar que no se puede marcar como conciliado sin fecha
        with self.assertRaises(ValueError):
            conciliacion.estado = 'conciliado'
            conciliacion.save()
        
        # Marcar como conciliado correctamente
        conciliacion.estado = 'conciliado'
        conciliacion.fecha_conciliacion = timezone.now()
        conciliacion.save()
        
        self.assertEqual(conciliacion.estado, 'conciliado')
        self.assertIsNotNone(conciliacion.fecha_conciliacion)

@override_settings(**TEST_SETTINGS)
class FlujoPagoAPITest(APITestCase):
    """Test que simula el flujo completo de pago a través de la API"""
    
    def setUp(self):
        # Crear usuario cliente
        self.cliente = User.objects.create_user(
            username='cliente',
            password='clientepass',
            email='cliente@test.com',
            rut='12.345.678-9'
        )
        
        # Crear pedido
        self.pedido = Pedido.objects.create(
            usuario=self.cliente,
            numero='00000001',
            tipo_entrega='retiro',
            nombre_contacto='Cliente Test',
            email_contacto='cliente@test.com',
            telefono_contacto='123456789',
            subtotal=Decimal('10000.00'),
            total=Decimal('10000.00')
        )

    def test_flujo_pago_api(self):
        """Test del flujo completo de pago usando los endpoints de la API"""
        
        # 1. Cliente crea preferencia de pago
        self.client.force_authenticate(user=self.cliente)
        url_crear_preferencia = reverse('transaccion-list')
        data = {'pedido_id': self.pedido.id}
        
        with patch('pagos.services.MercadoPagoService.crear_preferencia') as mock_crear:
            transaccion = TransaccionMercadoPago.objects.create(
                pedido=self.pedido,
                preference_id='test_preference_id',
                monto=self.pedido.total,
                estado='pending'
            )
            mock_crear.return_value = transaccion
            
            response = self.client.post(url_crear_preferencia, data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['preference_id'], 'test_preference_id')
        
        # 2. Simular webhook de pago
        url_webhook = reverse('transaccion-webhook')
        webhook_data = {
            "type": "payment",
            "data": {"id": "test_payment_id"}
        }
        
        with patch('pagos.services.MercadoPagoService.procesar_webhook') as mock_webhook:
            transaccion = TransaccionMercadoPago.objects.get(preference_id='test_preference_id')
            transaccion.payment_id = 'test_payment_id'
            transaccion.estado = 'approved'
            transaccion.save()
            mock_webhook.return_value = transaccion
            
            response = self.client.post(url_webhook, webhook_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. Contador accede a la factura
        self.client.force_authenticate(user=self.contador)
        url_facturas = reverse('factura-list')
        response = self.client.get(url_facturas)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # 4. Contador crea y marca conciliación
        url_conciliaciones = reverse('conciliacion-list')
        factura = FacturaElectronica.objects.get(pedido=self.pedido)
        data_conciliacion = {
            'transaccion': transaccion.id,
            'factura': factura.id,
            'estado': 'pendiente'
        }
        
        response = self.client.post(url_conciliaciones, data_conciliacion)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        conciliacion_id = response.data['id']
        
        # Marcar como conciliado
        url_marcar_conciliado = reverse('conciliacion-marcar-conciliado', args=[conciliacion_id])
        response = self.client.post(url_marcar_conciliado)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'conciliado')
