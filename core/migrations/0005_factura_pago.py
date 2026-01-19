# RONAL ---- Migración para modelos Factura y Pago
from django.db import migrations, models
import django.db.models.deletion
from django.core.validators import MinValueValidator


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_solicitud_profile"),
    ]

    operations = [
        migrations.CreateModel(
            name="Factura",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("numero_factura", models.CharField(max_length=50, verbose_name="Numero de Factura")),
                ("monto", models.DecimalField(decimal_places=2, max_digits=12, validators=[MinValueValidator(0.01)])),
                ("fecha", models.DateField()),
                (
                    "siniestro",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="factura", to="core.siniestro"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Pago",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("monto_pagado", models.DecimalField(decimal_places=2, max_digits=12, validators=[MinValueValidator(0.01)])),
                ("fecha_pago", models.DateField()),
                (
                    "metodo_pago",
                    models.CharField(
                        choices=[
                            ("transferencia", "Transferencia"),
                            ("cheque", "Cheque"),
                            ("efectivo", "Efectivo"),
                            ("tarjeta", "Tarjeta"),
                            ("otro", "Otro"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "factura",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pagos", to="core.factura"),
                ),
                (
                    "siniestro",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pagos", to="core.siniestro"),
                ),
            ],
        ),
    ]
