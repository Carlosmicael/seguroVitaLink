from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_factura_pago"),
    ]

    operations = [
        migrations.AddField(
            model_name="aseguradora",
            name="email",
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name="aseguradora",
            name="politicas",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="aseguradora",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="aseguradora",
            name="fecha_creacion",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name="aseguradora",
            name="fecha_actualizacion",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name="aseguradora",
            name="fecha_inactivacion",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="PoliticaAseguradora",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("documento", models.FileField(blank=True, null=True, upload_to="politicas/")),
                ("terminos", models.TextField()),
                ("fecha_version", models.DateField(default=timezone.now)),
                (
                    "aseguradora",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="politicas_versiones", to="core.aseguradora"),
                ),
            ],
            options={
                "ordering": ["-fecha_version", "-id"],
            },
        ),
    ]
