import mercadopago
from django.conf import settings
from django.utils import timezone
from .models import TransaccionMercadoPago, FacturaElectronica

class MercadoPagoService:
    """Servicio para integración con Mercado Pago"""
    
    def __init__(self, sdk=None):
        self.sdk = sdk or mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    
    def crear_preferencia(self, pedido):
        """Crea una preferencia de pago en Mercado Pago"""
        preference_data = {
            "items": [
                {
                    "title": f"Pedido #{pedido.numero}",
                    "quantity": 1,
                    "currency_id": "CLP",
                    "unit_price": float(pedido.total)
                }
            ],
            "external_reference": str(pedido.numero),
            "back_urls": {
                "success": f"{settings.SITE_URL}/pagos/success",
                "failure": f"{settings.SITE_URL}/pagos/failure",
                "pending": f"{settings.SITE_URL}/pagos/pending"
            },
            "auto_return": "approved",
            "notification_url": f"{settings.SITE_URL}/api/pagos/webhook/"
        }
        
        try:
            preference_response = self.sdk.preference().create(preference_data)
            
            if preference_response.get("status") == 201 and preference_response.get("response", {}).get("id"):
                # Crear registro de transacción
                transaccion = TransaccionMercadoPago.objects.create(
                    pedido=pedido,
                    preference_id=preference_response["response"]["id"],
                    monto=pedido.total,
                    estado='pending'  # Estado inicial
                )
                return transaccion
            else:
                raise Exception(f"Error al crear preferencia: {preference_response}")
        except Exception as e:
            raise Exception(f"Error al crear preferencia en Mercado Pago: {str(e)}")
    
    def procesar_webhook(self, data):
        """Procesa webhooks de Mercado Pago"""
        if data["type"] == "payment":
            payment = self.sdk.payment().get(data["data"]["id"])
            
            if payment.get("status") == 200 and payment.get("response"):
                payment_info = payment["response"]
                
                try:
                    transaccion = TransaccionMercadoPago.objects.get(
                        preference_id=payment_info["preference_id"]
                    )
                    
                    transaccion.payment_id = str(payment_info["id"])
                    transaccion.merchant_order_id = payment_info["order"]["id"]
                    transaccion.estado = payment_info["status"]
                    transaccion.datos_adicionales = payment_info
                    transaccion.save()
                    
                    # Si el pago fue aprobado, actualizar el estado del pedido
                    if payment_info["status"] == "approved":
                        transaccion.pedido.actualizar_estado('pagado')
                        
                        # Generar factura electrónica
                        self._generar_factura(transaccion.pedido)
                    
                    return transaccion
                    
                except TransaccionMercadoPago.DoesNotExist:
                    raise Exception("Transacción no encontrada")
        
        return None
    
    def _generar_factura(self, pedido):
        """Genera una factura electrónica para un pedido pagado"""
        # Aquí iría la integración con el servicio de facturación electrónica
        factura = FacturaElectronica.objects.create(
            pedido=pedido,
            numero_factura=f"F{pedido.numero}",
            fecha_emision=timezone.now(),
            rut_emisor=settings.FACTURACION_RUT_EMISOR,
            razon_social_emisor=settings.FACTURACION_RAZON_SOCIAL,
            giro_emisor=settings.FACTURACION_GIRO,
            direccion_emisor=settings.FACTURACION_DIRECCION,
            rut_receptor=pedido.usuario.rut,
            razon_social_receptor=pedido.usuario.get_full_name(),
            direccion_receptor=pedido.direccion_entrega or 'Retiro en tienda',
            neto=pedido.total / 1.19,  # Asumiendo IVA de 19%
            iva=pedido.total - (pedido.total / 1.19),
            total=pedido.total
        )
        return factura

class FacturacionService:
    """Servicio para generación y envío de facturas electrónicas"""
    
    def generar_xml(self, factura):
        """Genera el XML de la factura electrónica"""
        # Aquí iría la lógica de generación del XML según el formato del SII
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <DTE version="1.0">
            <Documento>
                <Encabezado>
                    <IdDoc>
                        <TipoDTE>33</TipoDTE>
                        <Folio>{factura.numero_factura}</Folio>
                        <FchEmis>{factura.fecha_emision.strftime('%Y-%m-%d')}</FchEmis>
                    </IdDoc>
                    <Emisor>
                        <RUTEmisor>{factura.rut_emisor}</RUTEmisor>
                        <RznSoc>{factura.razon_social_emisor}</RznSoc>
                        <GiroEmis>{factura.giro_emisor}</GiroEmis>
                        <DirOrigen>{factura.direccion_emisor}</DirOrigen>
                    </Emisor>
                    <Receptor>
                        <RUTRecep>{factura.rut_receptor}</RUTRecep>
                        <RznSocRecep>{factura.razon_social_receptor}</RznSocRecep>
                        <DirRecep>{factura.direccion_receptor}</DirRecep>
                    </Receptor>
                    <Totales>
                        <MntNeto>{factura.neto}</MntNeto>
                        <IVA>{factura.iva}</IVA>
                        <MntTotal>{factura.total}</MntTotal>
                    </Totales>
                </Encabezado>
                <Detalle>
                    <!-- Aquí irían los detalles de los productos -->
                </Detalle>
            </Documento>
        </DTE>"""
        
        factura.xml_factura = xml
        factura.save()
        return xml
    
    def enviar_al_sii(self, factura):
        """Envía la factura al SII"""
        # Aquí iría la integración con el webservice del SII
        # Por ahora solo simulamos el envío
        factura.estado = 'enviada'
        factura.track_id = f"T{factura.numero_factura}"
        factura.save()
        return factura.track_id
    
    def generar_pdf(self, factura):
        """Genera el PDF de la factura"""
        # Aquí iría la lógica de generación del PDF
        # Por ahora solo simulamos la generación
        from django.core.files.base import ContentFile
        
        # Simular contenido del PDF
        pdf_content = b"Contenido del PDF"
        filename = f"factura_{factura.numero_factura}.pdf"
        
        factura.pdf_factura.save(filename, ContentFile(pdf_content), save=True)
        return factura.pdf_factura 