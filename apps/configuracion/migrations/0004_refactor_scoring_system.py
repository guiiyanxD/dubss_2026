"""
Migración de refactorización: reemplaza los campos de TextChoices del formulario
socioeconómico por FKs a modelos catálogo configurables.

Operaciones:
1. Crea los 8 modelos catálogo.
2. Elimina los 3 CharField viejos (dependencia_economica, tipo_ocupacion_sosten,
   tipo_tenencia_vivienda) y los campos obsoletos (situacion_laboral,
   situacion_habitacional, ingreso_mensual_familiar).
3. Agrega los FK correspondientes y rango_ingreso.
4. Inserta seed data en los 8 catálogos.
"""

import django.db.models.deletion
from django.db import migrations, models


def insertar_catalogo_inicial(apps, schema_editor):
    OpcionDependencia = apps.get_model("configuracion", "OpcionDependencia")
    TipoOcupacionSosten = apps.get_model("configuracion", "TipoOcupacionSosten")
    RangoIngreso = apps.get_model("configuracion", "RangoIngreso")
    RangoGrupoFamiliar = apps.get_model("configuracion", "RangoGrupoFamiliar")
    TipoTenenciaVivienda = apps.get_model("configuracion", "TipoTenenciaVivienda")
    RangoInfraestructura = apps.get_model("configuracion", "RangoInfraestructura")
    OpcionOtroBeneficio = apps.get_model("configuracion", "OpcionOtroBeneficio")
    OpcionDiscapacidad = apps.get_model("configuracion", "OpcionDiscapacidad")

    for nombre, puntaje in [
        ("Independiente", 60),
        ("Solo padre/madre", 80),
        ("Ambos padres", 50),
        ("Otro familiar", 70),
        ("De la pareja", 65),
    ]:
        OpcionDependencia.objects.create(nombre=nombre, valor_puntaje=puntaje)

    for nombre, puntaje, doc in [
        ("Asalariado formal", 40, ""),
        ("Asalariado informal", 70, ""),
        ("Comerciante mayorista", 60, ""),
        ("Rentista", 30, ""),
        ("Comerciante minorista", 80, ""),
        ("Agricultor", 90, ""),
    ]:
        TipoOcupacionSosten.objects.create(nombre=nombre, valor_puntaje=puntaje, documento_adjuntar=doc)

    for nombre, puntaje, mn, mx in [
        ("Hasta Bs. 2.500", 100, None, 2500),
        ("Bs. 2.501 – 4.000", 75, 2501, 4000),
        ("Bs. 4.001 – 6.000", 50, 4001, 6000),
        ("Más de Bs. 6.000", 25, 6001, None),
    ]:
        RangoIngreso.objects.create(nombre=nombre, valor_puntaje=puntaje, monto_minimo=mn, monto_maximo=mx)

    for nombre, puntaje, mn, mx in [
        ("1 – 2 personas", 40, 1, 2),
        ("3 – 5 personas", 70, 3, 5),
        ("6 – 8 personas", 90, 6, 8),
        ("9 o más personas", 100, 9, None),
    ]:
        RangoGrupoFamiliar.objects.create(
            nombre=nombre, valor_puntaje=puntaje, cantidad_minima=mn, cantidad_maxima=mx
        )

    for nombre, puntaje, doc in [
        ("Herencia", 40, ""),
        ("De los padres", 60, ""),
        ("Cedida", 90, ""),
        ("Anticrético", 80, ""),
        ("Alquiler", 100, "Contrato de alquiler"),
    ]:
        TipoTenenciaVivienda.objects.create(nombre=nombre, valor_puntaje=puntaje, documento_adjuntar=doc)

    for nombre, puntaje, mn, mx in [
        ("1 – 3 ambientes", 100, 1, 3),
        ("4 – 6 ambientes", 70, 4, 6),
        ("7 – 10 ambientes", 40, 7, 10),
        ("11 o más ambientes", 20, 11, None),
    ]:
        RangoInfraestructura.objects.create(
            nombre=nombre, valor_puntaje=puntaje, total_minimo=mn, total_maximo=mx
        )

    for nombre, puntaje in [("Sí", 0), ("No", 100)]:
        OpcionOtroBeneficio.objects.create(nombre=nombre, valor_puntaje=puntaje)

    for nombre, puntaje in [("Sí", 100), ("No", 0)]:
        OpcionDiscapacidad.objects.create(nombre=nombre, valor_puntaje=puntaje)


class Migration(migrations.Migration):
    dependencies = [
        ("configuracion", "0003_alter_integrantefamiliar_parentesco"),
    ]

    operations = [
        # ── 1. Crear los 8 modelos catálogo ──────────────────────────────────
        migrations.CreateModel(
            name="OpcionDependencia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=100, unique=True, verbose_name="nombre")),
                ("valor_puntaje", models.PositiveSmallIntegerField(verbose_name="valor de puntaje")),
                ("activo", models.BooleanField(default=True, verbose_name="activo")),
            ],
            options={"verbose_name": "opción de dependencia económica", "verbose_name_plural": "opciones de dependencia económica", "ordering": ["nombre"]},
        ),
        migrations.CreateModel(
            name="TipoOcupacionSosten",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=100, unique=True, verbose_name="nombre")),
                ("valor_puntaje", models.PositiveSmallIntegerField(verbose_name="valor de puntaje")),
                ("activo", models.BooleanField(default=True, verbose_name="activo")),
                ("documento_adjuntar", models.CharField(blank=True, max_length=200, verbose_name="documento a adjuntar")),
            ],
            options={"verbose_name": "tipo de ocupación del sostén", "verbose_name_plural": "tipos de ocupación del sostén", "ordering": ["nombre"]},
        ),
        migrations.CreateModel(
            name="RangoIngreso",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=100, unique=True, verbose_name="nombre")),
                ("valor_puntaje", models.PositiveSmallIntegerField(verbose_name="valor de puntaje")),
                ("activo", models.BooleanField(default=True, verbose_name="activo")),
                ("monto_minimo", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name="monto mínimo (inclusive)")),
                ("monto_maximo", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name="monto máximo (inclusive, vacío = sin límite superior)")),
            ],
            options={"verbose_name": "rango de ingreso", "verbose_name_plural": "rangos de ingreso", "ordering": ["monto_minimo"]},
        ),
        migrations.CreateModel(
            name="RangoGrupoFamiliar",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=100, unique=True, verbose_name="nombre")),
                ("valor_puntaje", models.PositiveSmallIntegerField(verbose_name="valor de puntaje")),
                ("activo", models.BooleanField(default=True, verbose_name="activo")),
                ("cantidad_minima", models.PositiveSmallIntegerField(verbose_name="cantidad mínima (inclusive)")),
                ("cantidad_maxima", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="cantidad máxima (inclusive, vacío = sin límite superior)")),
            ],
            options={"verbose_name": "rango de grupo familiar", "verbose_name_plural": "rangos de grupo familiar", "ordering": ["cantidad_minima"]},
        ),
        migrations.CreateModel(
            name="TipoTenenciaVivienda",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=100, unique=True, verbose_name="nombre")),
                ("valor_puntaje", models.PositiveSmallIntegerField(verbose_name="valor de puntaje")),
                ("activo", models.BooleanField(default=True, verbose_name="activo")),
                ("documento_adjuntar", models.CharField(blank=True, max_length=200, verbose_name="documento a adjuntar")),
            ],
            options={"verbose_name": "tipo de tenencia de vivienda", "verbose_name_plural": "tipos de tenencia de vivienda", "ordering": ["nombre"]},
        ),
        migrations.CreateModel(
            name="RangoInfraestructura",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=100, unique=True, verbose_name="nombre")),
                ("valor_puntaje", models.PositiveSmallIntegerField(verbose_name="valor de puntaje")),
                ("activo", models.BooleanField(default=True, verbose_name="activo")),
                ("total_minimo", models.PositiveSmallIntegerField(verbose_name="total mínimo de ambientes (inclusive)")),
                ("total_maximo", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="total máximo de ambientes (inclusive, vacío = sin límite)")),
            ],
            options={"verbose_name": "rango de infraestructura", "verbose_name_plural": "rangos de infraestructura", "ordering": ["total_minimo"]},
        ),
        migrations.CreateModel(
            name="OpcionOtroBeneficio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=100, unique=True, verbose_name="nombre")),
                ("valor_puntaje", models.PositiveSmallIntegerField(verbose_name="valor de puntaje")),
                ("activo", models.BooleanField(default=True, verbose_name="activo")),
            ],
            options={"verbose_name": "opción de otro beneficio", "verbose_name_plural": "opciones de otro beneficio", "ordering": ["nombre"]},
        ),
        migrations.CreateModel(
            name="OpcionDiscapacidad",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=100, unique=True, verbose_name="nombre")),
                ("valor_puntaje", models.PositiveSmallIntegerField(verbose_name="valor de puntaje")),
                ("activo", models.BooleanField(default=True, verbose_name="activo")),
            ],
            options={"verbose_name": "opción de discapacidad", "verbose_name_plural": "opciones de discapacidad", "ordering": ["nombre"]},
        ),
        # ── 2. Eliminar campos obsoletos ──────────────────────────────────────
        migrations.RemoveField(
            model_name="formulariosocioeconomico",
            name="situacion_laboral",
        ),
        migrations.RemoveField(
            model_name="formulariosocioeconomico",
            name="situacion_habitacional",
        ),
        migrations.RemoveField(
            model_name="formulariosocioeconomico",
            name="ingreso_mensual_familiar",
        ),
        # Eliminar los CharField viejos que serán reemplazados por FK
        migrations.RemoveField(
            model_name="formulariosocioeconomico",
            name="dependencia_economica",
        ),
        migrations.RemoveField(
            model_name="formulariosocioeconomico",
            name="tipo_ocupacion_sosten",
        ),
        migrations.RemoveField(
            model_name="formulariosocioeconomico",
            name="tipo_tenencia_vivienda",
        ),
        # ── 3. Agregar los FK nuevos ──────────────────────────────────────────
        migrations.AddField(
            model_name="formulariosocioeconomico",
            name="dependencia_economica",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="formularios",
                to="configuracion.opciondependencia",
                verbose_name="¿de quién depende usted?",
            ),
        ),
        migrations.AddField(
            model_name="formulariosocioeconomico",
            name="tipo_ocupacion_sosten",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="formularios",
                to="configuracion.tipoocupacionsosten",
                verbose_name="ocupación de quien lo sostiene económicamente",
            ),
        ),
        migrations.AddField(
            model_name="formulariosocioeconomico",
            name="rango_ingreso",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="formularios",
                to="configuracion.rangoingreso",
                verbose_name="rango de ingreso mensual familiar",
            ),
        ),
        migrations.AddField(
            model_name="formulariosocioeconomico",
            name="tipo_tenencia_vivienda",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="formularios",
                to="configuracion.tipotenenciavivienda",
                verbose_name="tenencia de la vivienda",
            ),
        ),
        # ── 4. Seed data ──────────────────────────────────────────────────────
        migrations.RunPython(insertar_catalogo_inicial, migrations.RunPython.noop),
    ]
