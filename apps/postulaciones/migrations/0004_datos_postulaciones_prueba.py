from django.db import migrations
from django.db.models import Max
from django.utils import timezone

EMAILS_SELECCIONADOS = [f"estudiante{i:03d}@becas.com" for i in range(4, 87)]  # 83 estudiantes

# (beca, convocatoria, cantidad) — cantidades todas distintas, suman 83.
DISTRIBUCION = [
    ("Beca Comedor Universitario", "Convocatoria de Becas 2026 — Primer Cuatrimestre", 17),
    ("Beca Arancel Completo", "Convocatoria de Becas 2026 — Segundo Cuatrimestre", 16),
    ("Beca Materiales de Estudio", "Convocatoria de Becas 2026 — Investigación y Extensión", 14),
    ("Beca de Investigación", "Convocatoria de Becas 2026 — Investigación y Extensión", 13),
    ("Beca Arancel Parcial 50%", "Convocatoria de Becas 2026 — Segundo Cuatrimestre", 12),
    ("Beca Transporte", "Convocatoria de Becas 2026 — Primer Cuatrimestre", 11),
]


def crear_postulaciones_prueba(apps, schema_editor):
    Usuario = apps.get_model("acceso", "Usuario")
    FormularioSocioeconomico = apps.get_model("configuracion", "FormularioSocioeconomico")
    Convocatoria = apps.get_model("convocatorias", "Convocatoria")
    Beca = apps.get_model("convocatorias", "Beca")
    Postulacion = apps.get_model("postulaciones", "Postulacion")
    DocumentoPostulacion = apps.get_model("postulaciones", "DocumentoPostulacion")
    ContadorReferencia = apps.get_model("postulaciones", "ContadorReferencia")

    estudiantes = list(
        Usuario.objects.filter(email__in=EMAILS_SELECCIONADOS).order_by("email")
    )
    if len(estudiantes) != len(EMAILS_SELECCIONADOS):
        return  # datos base (0004 de acceso) no presentes; no hacer nada

    convocatorias_cache = {
        c.nombre: c
        for c in Convocatoria.objects.filter(nombre__in={n for _, n, _ in DISTRIBUCION})
    }
    becas_cache = {
        b.nombre: b for b in Beca.objects.filter(nombre__in={n for n, _, _ in DISTRIBUCION})
    }

    asignaciones = []
    for nombre_beca, nombre_convocatoria, cantidad in DISTRIBUCION:
        for _ in range(cantidad):
            asignaciones.append((nombre_beca, nombre_convocatoria))

    ultimo_numero = (
        Postulacion.objects.aggregate(Max("numero_referencia"))["numero_referencia__max"] or 0
    )
    ahora = timezone.now()

    for i, estudiante in enumerate(estudiantes):
        nombre_beca, nombre_convocatoria = asignaciones[i]

        formulario, _ = FormularioSocioeconomico.objects.update_or_create(
            usuario=estudiante,
            defaults={
                "cantidad_familiares": (i % 6) + 1,
                "tiene_beca_previa": i % 7 == 0,
                "completado": True,
            },
        )

        ultimo_numero += 1
        convocatoria = convocatorias_cache[nombre_convocatoria]
        postulacion = Postulacion.objects.create(
            estudiante=estudiante,
            convocatoria=convocatoria,
            beca=becas_cache[nombre_beca],
            formulario=formulario,
            estado="ENVIADA",
            fecha_envio=ahora,
            numero_referencia=ultimo_numero,
        )
        for tipo_doc in convocatoria.documentos_requeridos.all():
            DocumentoPostulacion.objects.create(
                postulacion=postulacion,
                tipo_documento=tipo_doc,
            )

    contador, _ = ContadorReferencia.objects.get_or_create(pk=1)
    contador.ultimo_numero = max(contador.ultimo_numero, ultimo_numero)
    contador.save(update_fields=["ultimo_numero"])


def eliminar_postulaciones_prueba(apps, schema_editor):
    Usuario = apps.get_model("acceso", "Usuario")
    Postulacion = apps.get_model("postulaciones", "Postulacion")
    FormularioSocioeconomico = apps.get_model("configuracion", "FormularioSocioeconomico")

    estudiantes_ids = list(
        Usuario.objects.filter(email__in=EMAILS_SELECCIONADOS).values_list("id", flat=True)
    )
    Postulacion.objects.filter(estudiante_id__in=estudiantes_ids).delete()
    FormularioSocioeconomico.objects.filter(usuario_id__in=estudiantes_ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("postulaciones", "0003_numero_referencia_contador"),
        ("convocatorias", "0003_datos_convocatorias_becas"),
        ("configuracion", "0005_sync_catalog_fields"),
        ("acceso", "0004_datos_100_estudiantes"),
    ]

    operations = [
        migrations.RunPython(crear_postulaciones_prueba, eliminar_postulaciones_prueba),
    ]
