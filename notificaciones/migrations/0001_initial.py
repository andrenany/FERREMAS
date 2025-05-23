# Generated by Django 5.2.1 on 2025-05-07 23:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlantillaNotificacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('tipo', models.CharField(choices=[('consulta', 'Consulta de Producto'), ('pedido', 'Estado de Pedido'), ('pago', 'Validación de Pago'), ('preparacion', 'Preparación de Pedido')], max_length=20)),
                ('asunto_email', models.CharField(max_length=200)),
                ('contenido_email', models.TextField()),
                ('contenido_push', models.CharField(max_length=200)),
                ('contenido_platform', models.TextField()),
                ('activa', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Plantilla de notificación',
                'verbose_name_plural': 'Plantillas de notificaciones',
            },
        ),
        migrations.CreateModel(
            name='Notificacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('enviada', 'Enviada'), ('leida', 'Leída'), ('fallida', 'Fallida')], default='pendiente', max_length=20)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_envio', models.DateTimeField(blank=True, null=True)),
                ('fecha_lectura', models.DateTimeField(blank=True, null=True)),
                ('object_id', models.PositiveIntegerField()),
                ('datos_contexto', models.JSONField(default=dict)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('destinatario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notificaciones', to=settings.AUTH_USER_MODEL)),
                ('plantilla', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='notificaciones.plantillanotificacion')),
            ],
            options={
                'verbose_name': 'Notificación',
                'verbose_name_plural': 'Notificaciones',
                'ordering': ['-fecha_creacion'],
            },
        ),
        migrations.CreateModel(
            name='PreferenciasNotificacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_enabled', models.BooleanField(default=True)),
                ('push_enabled', models.BooleanField(default=True)),
                ('platform_enabled', models.BooleanField(default=True)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Preferencia de notificación',
                'verbose_name_plural': 'Preferencias de notificaciones',
            },
        ),
    ]
