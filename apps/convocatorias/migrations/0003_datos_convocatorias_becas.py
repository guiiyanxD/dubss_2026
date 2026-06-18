from datetime import datetime

from django.db import migrations
from django.utils import timezone

CONVOCATORIAS = [
    {
        "nombre": "Convocatoria de Becas 2026 — Primer Cuatrimestre",
        "apertura": (2026, 3, 1),
        "cierre": (2026, 8, 31),
        "becas": ["Beca Comedor Universitario", "Beca Transporte"],
    },
    {
        "nombre": "Convocatoria de Becas 2026 — Segundo Cuatrimestre",
        "apertura": (2026, 4, 1),
        "cierre": (2026, 9, 30),
        "becas": ["Beca Arancel Completo", "Beca Arancel Parcial 50%"],
    },
    {
        "nombre": "Convocatoria de Becas 2026 — Investigación y Extensión",
        "apertura": (2026, 5, 1),
        "cierre": (2026, 10, 31),
        "becas": ["Beca Materiales de Estudio", "Beca de Investigación"],
    },
]


def crear_convocatorias_becas(apps, schema_editor):
    Convocatoria = apps.get_model("convocatorias", "Convocatoria")
    Beca = apps.get_model("convocatorias", "Beca")

    for datos in CONVOCATORIAS:
        fecha_apertura = timezone.make_aware(datetime(*datos["apertura"]))
        fecha_cierre = timezone.make_aware(datetime(*datos["cierre"], 23, 59, 59))

        convocatoria, _ = Convocatoria.objects.get_or_create(
            nombre=datos["nombre"],
            defaults={
                "fecha_apertura": fecha_apertura,
                "fecha_cierre": fecha_cierre,
                "estado": "PUBLICADA",
            },
        )

        for nombre_beca in datos["becas"]:
            beca, _ = Beca.objects.get_or_create(nombre=nombre_beca)
            convocatoria.becas.add(beca)


def eliminar_convocatorias_becas(apps, schema_editor):
    Convocatoria = apps.get_model("convocatorias", "Convocatoria")
    Beca = apps.get_model("convocatorias", "Beca")

    nombres_convocatorias = [c["nombre"] for c in CONVOCATORIAS]
    nombres_becas = [nombre for c in CONVOCATORIAS for nombre in c["becas"]]

    Convocatoria.objects.filter(nombre__in=nombres_convocatorias).delete()
    Beca.objects.filter(nombre__in=nombres_becas).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("convocatorias", "0002_registrar_tarea_beat"),
    ]

    operations = [
        migrations.RunPython(crear_convocatorias_becas, eliminar_convocatorias_becas),
    ]
