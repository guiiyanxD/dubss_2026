from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("acceso", "0005_datos_director_operador_superuser"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="cargo",
            field=models.CharField(blank=True, max_length=100, verbose_name="cargo"),
        ),
        migrations.AddField(
            model_name="usuario",
            name="departamento",
            field=models.CharField(blank=True, max_length=100, verbose_name="departamento"),
        ),
    ]
