from django.db import migrations, models
import django.db.models.deletion


def drop_factura_siniestro_index(apps, schema_editor):
    try:
        schema_editor.execute("DROP INDEX core_factura_siniestro_id_ad8acb0f ON core_factura;")
    except Exception:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_aseguradora_politicas"),
    ]

    operations = [
        migrations.RunPython(drop_factura_siniestro_index, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="factura",
            name="siniestro",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="facturas", to="core.siniestro"),
        ),
        migrations.AddField(
            model_name="factura",
            name="beneficiario",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="factura",
                to="core.beneficiario",
            ),
        ),
        migrations.AlterField(
            model_name="pago",
            name="factura",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pagos", to="core.factura"),
        ),
    ]
