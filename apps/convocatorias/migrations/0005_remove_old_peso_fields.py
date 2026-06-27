from django.db import migrations


class Migration(migrations.Migration):
    """Elimina los campos de peso anteriores al refactor del scoring.

    Los campos nuevos (peso_dependencia_economica, etc.) fueron agregados en 0004.
    Los campos viejos (peso_ingreso, peso_desempleo, etc.) existían en la BD por el
    contenido original de 0004 antes del refactor y se eliminan aquí.
    """

    dependencies = [
        ("convocatorias", "0004_beca_peso_desempleo_beca_peso_familiares_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE convocatorias_beca DROP COLUMN IF EXISTS peso_desempleo",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="ALTER TABLE convocatorias_beca DROP COLUMN IF EXISTS peso_familiares",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="ALTER TABLE convocatorias_beca DROP COLUMN IF EXISTS peso_ingreso",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="ALTER TABLE convocatorias_beca DROP COLUMN IF EXISTS peso_no_propietario",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="ALTER TABLE convocatorias_beca DROP COLUMN IF EXISTS peso_sin_beca_previa",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
