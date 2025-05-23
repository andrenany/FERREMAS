# Generated by Django 5.2.1 on 2025-05-07 21:43

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('pedidos', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FacturaElectronica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_factura', models.CharField(max_length=50, unique=True)),
                ('fecha_emision', models.DateTimeField()),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente de Emisión'), ('emitida', 'Emitida'), ('enviada', 'Enviada al SII'), ('aceptada', 'Aceptada por SII'), ('rechazada', 'Rechazada por SII')], default='pendiente', max_length=20)),
                ('rut_emisor', models.CharField(max_length=20)),
                ('razon_social_emisor', models.CharField(max_length=200)),
                ('giro_emisor', models.CharField(max_length=200)),
                ('direccion_emisor', models.CharField(max_length=200)),
                ('rut_receptor', models.CharField(max_length=20)),
                ('razon_social_receptor', models.CharField(max_length=200)),
                ('giro_receptor', models.CharField(blank=True, max_length=200)),
                ('direccion_receptor', models.CharField(max_length=200)),
                ('neto', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('iva', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('total', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('xml_factura', models.TextField(blank=True)),
                ('pdf_factura', models.FileField(blank=True, null=True, upload_to='facturas/')),
                ('track_id', models.CharField(blank=True, max_length=100)),
                ('respuesta_sii', models.TextField(blank=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('pedido', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='factura', to='pedidos.pedido')),
            ],
            options={
                'ordering': ['-fecha_emision'],
            },
        ),
        migrations.CreateModel(
            name='TransaccionMercadoPago',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preference_id', models.CharField(max_length=100, unique=True)),
                ('payment_id', models.CharField(blank=True, max_length=100, null=True)),
                ('merchant_order_id', models.CharField(blank=True, max_length=100, null=True)),
                ('estado', models.CharField(choices=[('pending', 'Pendiente'), ('approved', 'Aprobado'), ('authorized', 'Autorizado'), ('in_process', 'En Proceso'), ('in_mediation', 'En Mediación'), ('rejected', 'Rechazado'), ('cancelled', 'Cancelado'), ('refunded', 'Reembolsado'), ('charged_back', 'Contracargo')], default='pending', max_length=20)),
                ('monto', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('datos_adicionales', models.JSONField(default=dict)),
                ('pedido', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transacciones_mp', to='pedidos.pedido')),
            ],
            options={
                'ordering': ['-fecha_creacion'],
            },
        ),
        migrations.CreateModel(
            name='ConciliacionPago',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('conciliado', 'Conciliado'), ('discrepancia', 'Con Discrepancia')], default='pendiente', max_length=20)),
                ('fecha_conciliacion', models.DateTimeField(blank=True, null=True)),
                ('notas', models.TextField(blank=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('conciliado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='conciliaciones', to=settings.AUTH_USER_MODEL)),
                ('factura', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='pagos.facturaelectronica')),
                ('transaccion', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='pagos.transaccionmercadopago')),
            ],
            options={
                'ordering': ['-fecha_creacion'],
            },
        ),
    ]
