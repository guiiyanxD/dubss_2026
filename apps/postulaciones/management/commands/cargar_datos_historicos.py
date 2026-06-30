"""
Management command: cargar_datos_historicos

Carga datos sintéticos de convocatorias 2025 ya cerradas, con postulaciones
completamente procesadas (ADJUDICADA / LISTA_ESPERA / NO_ADJUDICADA).

Uso:
    docker compose exec web python manage.py cargar_datos_historicos

Comportamiento:
  - Idempotente: si las convocatorias 2025 ya existen, las omite.
  - Completa los FK de los 83 formularios socioeconómicos (Opción A).
  - NO modifica las 83 postulaciones actuales con estado ENVIADA.
  - NO digitaliza documentos (archivo=None): simula el paso CU20 omitido.
  - Replica la fórmula CU23 localmente (sin importar apps.reportes).
"""

import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from apps.acceso.models import Usuario
from apps.configuracion.models import (
    FormularioSocioeconomico,
    OpcionDependencia,
    OpcionDiscapacidad,
    OpcionOtroBeneficio,
    RangoGrupoFamiliar,
    RangoInfraestructura,
    RangoIngreso,
    TipoOcupacionSosten,
    TipoTenenciaVivienda,
)
from apps.convocatorias.models import Beca, Convocatoria, TipoDocumento
from apps.postulaciones.models import ContadorReferencia, DocumentoPostulacion, Postulacion

# ---------------------------------------------------------------------------
# Constantes de configuración
# ---------------------------------------------------------------------------

CIUDADES_PROCEDENCIA = [
    "Mendoza",
    "San Rafael",
    "San Martín",
    "Rivadavia",
    "Godoy Cruz",
    "Las Heras",
    "Luján de Cuyo",
    "Maipú",
    "Tunuyán",
    "San Carlos",
    "Malargüe",
    "General Alvear",
    "Lavalle",
    "Villa Mercedes",
    "La Rioja",
    "",  # sin procedencia externa (residente local)
    "",
    "",
]

# Distribución de cantidad_familiares: cíclica, sesgada hacia grupos medianos
CICLO_FAMILIARES = [1, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 6, 7, 8, 9]

# Distribución de rango_ingreso: más peso en rangos bajos (índice 0 = menor ingreso)
# Rango 0 → Hasta Bs. 2.500 (valor=100) — 43% de los estudiantes
# Rango 1 → Bs. 2.501–4.000 (valor=75)  — 29%
# Rango 2 → Bs. 4.001–6.000 (valor=50)  — 14%
# Rango 3 → Más de Bs. 6.000 (valor=25)  — 14%
CICLO_INGRESO = [0, 0, 0, 1, 1, 2, 3]

DEFINICION_CONVOCATORIAS = [
    {
        "nombre": "Convocatoria de Becas 2025 — Primer Cuatrimestre",
        "descripcion": (
            "Convocatoria cerrada correspondiente al primer cuatrimestre "
            "del ciclo académico 2025. Proceso de adjudicación finalizado."
        ),
        "fecha_apertura": datetime.datetime(2025, 3, 1, 8, 0, tzinfo=datetime.timezone.utc),
        "fecha_cierre": datetime.datetime(2025, 6, 30, 23, 59, tzinfo=datetime.timezone.utc),
        "becas_cupos": {
            "Beca Comedor Universitario": {"cupo": 10, "espera": 5},
            "Beca Transporte": {"cupo": 10, "espera": 5},
        },
        "offset_estudiantes": 0,
        "n_estudiantes": 65,
    },
    {
        "nombre": "Convocatoria de Becas 2025 — Segundo Cuatrimestre",
        "descripcion": (
            "Convocatoria cerrada correspondiente al segundo cuatrimestre "
            "del ciclo académico 2025. Proceso de adjudicación finalizado."
        ),
        "fecha_apertura": datetime.datetime(2025, 7, 1, 8, 0, tzinfo=datetime.timezone.utc),
        "fecha_cierre": datetime.datetime(2025, 12, 15, 23, 59, tzinfo=datetime.timezone.utc),
        "becas_cupos": {
            "Beca Arancel Completo": {"cupo": 8, "espera": 4},
            "Beca Arancel Parcial 50%": {"cupo": 8, "espera": 4},
        },
        "offset_estudiantes": 15,
        "n_estudiantes": 55,
    },
]


# ---------------------------------------------------------------------------
# Réplica local de la fórmula CU23
# (no se importa apps.reportes para respetar la jerarquía de dependencias)
# ---------------------------------------------------------------------------


def _max_cat(modelo):
    res = modelo.objects.filter(activo=True).aggregate(m=Max("valor_puntaje"))
    return res["m"] or 1


def _lookup_grp(valor):
    rango = (
        RangoGrupoFamiliar.objects.filter(activo=True)
        .filter(cantidad_minima__lte=valor)
        .filter(Q(cantidad_maxima__isnull=True) | Q(cantidad_maxima__gte=valor))
        .first()
    )
    return rango.valor_puntaje if rango else 0


def _lookup_inf(total):
    rango = (
        RangoInfraestructura.objects.filter(activo=True)
        .filter(total_minimo__lte=total)
        .filter(Q(total_maximo__isnull=True) | Q(total_maximo__gte=total))
        .first()
    )
    return rango.valor_puntaje if rango else 0


def _v(fk):
    return fk.valor_puntaje if fk else 0


def _calcular_puntaje(formulario, beca, maximos, ben_si, ben_no, dis_si, dis_no):
    max_dep, max_ocup, max_ing, max_grp, max_ten, max_inf, max_ben, max_dis = maximos

    total_amb = (
        (formulario.dormitorios or 0)
        + (formulario.banos or 0)
        + (formulario.comedores or 0)
        + (formulario.salas or 0)
        + (formulario.patios or 0)
    )

    score_dep = (
        (_v(formulario.dependencia_economica) / max_dep)
        + (_v(formulario.tipo_ocupacion_sosten) / max_ocup)
        + (_v(formulario.rango_ingreso) / max_ing)
    ) / 3

    v_grp = _lookup_grp(formulario.cantidad_familiares)
    v_ten = _v(formulario.tipo_tenencia_vivienda)
    v_inf = _lookup_inf(total_amb)
    v_ben = _v(ben_si if formulario.tiene_beca_previa else ben_no)
    v_dis = _v(dis_si if formulario.tiene_discapacidad else dis_no)
    score_proc = 100 if formulario.lugar_procedencia else 0

    puntaje = (
        score_dep * beca.peso_dependencia_economica
        + (v_grp / max_grp) * beca.peso_grupo_familiar
        + (score_proc / 100) * beca.peso_procedencia
        + (v_ten / max_ten) * beca.peso_tenencia_vivienda
        + (v_inf / max_inf) * beca.peso_infraestructura
        + (v_ben / max_ben) * beca.peso_otro_beneficio
        + (v_dis / max_dis) * beca.peso_discapacidad
    )
    return round(puntaje, 2)


# ---------------------------------------------------------------------------
# Comando
# ---------------------------------------------------------------------------


class Command(BaseCommand):
    help = "Carga datos históricos de convocatorias 2025 cerradas y procesadas."

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write(self.style.MIGRATE_HEADING("\n=== Cargando datos históricos 2025 ===\n"))

            catalogs = self._cargar_catalogos()
            maximos = self._calcular_maximos()
            opciones_binarias = self._cargar_opciones_binarias()
            director = Usuario.objects.filter(email="director@becas.com").first()
            tipos_doc = list(TipoDocumento.objects.all())
            estudiantes, formularios = self._cargar_estudiantes()

            self._completar_formularios(estudiantes, formularios, catalogs)

            total_post = 0
            total_docs = 0
            for defn in DEFINICION_CONVOCATORIAS:
                n_p, n_d = self._procesar_convocatoria(
                    defn=defn,
                    director=director,
                    estudiantes=estudiantes,
                    formularios=formularios,
                    tipos_doc=tipos_doc,
                    maximos=maximos,
                    opciones_binarias=opciones_binarias,
                )
                total_post += n_p
                total_docs += n_d

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ Datos históricos cargados: "
                    f"{total_post} postulaciones, {total_docs} documentos.\n"
                )
            )

    # ------------------------------------------------------------------
    # Helpers de carga inicial
    # ------------------------------------------------------------------

    def _cargar_catalogos(self):
        return {
            "dep": list(OpcionDependencia.objects.filter(activo=True).order_by("pk")),
            "ocup": list(TipoOcupacionSosten.objects.filter(activo=True).order_by("pk")),
            "ing": list(RangoIngreso.objects.filter(activo=True).order_by("valor_puntaje").reverse()),
            "ten": list(TipoTenenciaVivienda.objects.filter(activo=True).order_by("pk")),
        }

    def _calcular_maximos(self):
        return (
            _max_cat(OpcionDependencia),
            _max_cat(TipoOcupacionSosten),
            _max_cat(RangoIngreso),
            _max_cat(RangoGrupoFamiliar),
            _max_cat(TipoTenenciaVivienda),
            _max_cat(RangoInfraestructura),
            _max_cat(OpcionOtroBeneficio),
            _max_cat(OpcionDiscapacidad),
        )

    def _cargar_opciones_binarias(self):
        return {
            "ben_si": OpcionOtroBeneficio.objects.filter(activo=True, nombre="Sí").first(),
            "ben_no": OpcionOtroBeneficio.objects.filter(activo=True, nombre="No").first(),
            "dis_si": OpcionDiscapacidad.objects.filter(activo=True, nombre="Sí").first(),
            "dis_no": OpcionDiscapacidad.objects.filter(activo=True, nombre="No").first(),
        }

    def _cargar_estudiantes(self):
        estudiantes = list(
            Usuario.objects.filter(email__regex=r"^estudiante\d{3}@becas\.com$").order_by("email")
        )
        formularios = {
            f.usuario_id: f
            for f in FormularioSocioeconomico.objects.filter(completado=True)
        }
        self.stdout.write(
            f"  Estudiantes encontrados: {len(estudiantes)} "
            f"| Formularios completos: {len(formularios)}"
        )
        return estudiantes, formularios

    # ------------------------------------------------------------------
    # Opción A: completar FK de formularios
    # ------------------------------------------------------------------

    def _completar_formularios(self, estudiantes, formularios, catalogs):
        actualizados = 0
        for idx, est in enumerate(estudiantes):
            f = formularios.get(est.pk)
            if f is None or f.dependencia_economica_id is not None:
                continue

            ing_idx = CICLO_INGRESO[idx % len(CICLO_INGRESO)]

            f.dependencia_economica = catalogs["dep"][idx % len(catalogs["dep"])]
            f.tipo_ocupacion_sosten = catalogs["ocup"][idx % len(catalogs["ocup"])]
            f.rango_ingreso = catalogs["ing"][ing_idx]
            f.tipo_tenencia_vivienda = catalogs["ten"][idx % len(catalogs["ten"])]
            f.cantidad_familiares = CICLO_FAMILIARES[idx % len(CICLO_FAMILIARES)]
            f.lugar_procedencia = CIUDADES_PROCEDENCIA[idx % len(CIUDADES_PROCEDENCIA)]
            f.dormitorios = (idx % 4) + 1
            f.banos = (idx % 2) + 1
            f.comedores = 1 if idx % 3 != 0 else 0
            f.salas = 1 if idx % 4 != 0 else 0
            f.patios = 1 if idx % 5 != 0 else 0
            f.tiene_beca_previa = idx % 5 == 0       # 20%
            f.tiene_discapacidad = idx % 10 == 0     # 10%
            f.save()
            actualizados += 1

        self.stdout.write(
            self.style.SUCCESS(f"  Formularios actualizados con FK: {actualizados}")
        )

    # ------------------------------------------------------------------
    # Crear convocatoria histórica + postulaciones + documentos + ranking
    # ------------------------------------------------------------------

    def _procesar_convocatoria(
        self, *, defn, director, estudiantes, formularios, tipos_doc, maximos, opciones_binarias
    ):
        nombre = defn["nombre"]

        if Convocatoria.objects.filter(nombre=nombre).exists():
            self.stdout.write(f"\n  [omitida] {nombre}")
            return 0, 0

        conv = Convocatoria.objects.create(
            nombre=nombre,
            descripcion=defn["descripcion"],
            fecha_apertura=defn["fecha_apertura"],
            fecha_cierre=defn["fecha_cierre"],
            estado=Convocatoria.Estado.CERRADA,
            creada_por=director,
        )
        conv.documentos_requeridos.set(tipos_doc)

        becas_config = defn["becas_cupos"]
        becas = {b.nombre: b for b in Beca.objects.filter(nombre__in=becas_config.keys())}
        conv.becas.set(becas.values())

        self.stdout.write(self.style.SUCCESS(f"\n  [creada] {nombre}"))

        offset = defn["offset_estudiantes"]
        n = defn["n_estudiantes"]
        seleccionados = estudiantes[offset : offset + n]

        nombres_becas = list(becas_config.keys())
        total_postulaciones = 0
        total_documentos = 0

        for i_beca, nombre_beca in enumerate(nombres_becas):
            beca = becas[nombre_beca]
            config = becas_config[nombre_beca]
            cupo = config["cupo"]
            espera = config["espera"]

            grupo = [est for j, est in enumerate(seleccionados) if j % len(nombres_becas) == i_beca]

            delta_dias = (defn["fecha_cierre"] - defn["fecha_apertura"]).days
            ventana_envio = int(delta_dias * 0.65)

            postulaciones_beca = []
            documentos_a_crear = []

            for idx_local, est in enumerate(grupo):
                f = formularios.get(est.pk)
                if f is None:
                    continue

                if Postulacion.objects.filter(estudiante=est, convocatoria=conv).exists():
                    continue

                dias_offset = int((idx_local / max(len(grupo) - 1, 1)) * ventana_envio)
                fecha_envio = defn["fecha_apertura"] + datetime.timedelta(days=15 + dias_offset)
                fecha_validacion = fecha_envio + datetime.timedelta(days=7)

                nro_ref = ContadorReferencia.siguiente()

                p = Postulacion(
                    estudiante=est,
                    convocatoria=conv,
                    beca=beca,
                    formulario=f,
                    estado=Postulacion.Estado.APROBADA,
                    fecha_envio=fecha_envio,
                    numero_referencia=nro_ref,
                )
                p.save()

                # Retroactuar fecha_creacion a 2025 (auto_now_add no es editable vía save)
                Postulacion.objects.filter(pk=p.pk).update(fecha_creacion=fecha_envio)

                for tipo_doc in tipos_doc:
                    documentos_a_crear.append(
                        DocumentoPostulacion(
                            postulacion=p,
                            tipo_documento=tipo_doc,
                            validado=True,
                            fecha_validacion=fecha_validacion,
                        )
                    )

                postulaciones_beca.append(p)

            DocumentoPostulacion.objects.bulk_create(documentos_a_crear)
            total_documentos += len(documentos_a_crear)

            # CU23: calcular puntajes
            for p in postulaciones_beca:
                puntaje = _calcular_puntaje(
                    p.formulario,
                    p.beca,
                    maximos,
                    opciones_binarias["ben_si"],
                    opciones_binarias["ben_no"],
                    opciones_binarias["dis_si"],
                    opciones_binarias["dis_no"],
                )
                Postulacion.objects.filter(pk=p.pk).update(
                    puntaje_socioeconomico=Decimal(str(puntaje)),
                    estado=Postulacion.Estado.PROCESADA,
                )
                p.puntaje_socioeconomico = Decimal(str(puntaje))
                p.estado = Postulacion.Estado.PROCESADA

            # CU24: ranking sin disparar señales (datos históricos, no hay notificaciones)
            ordenadas = sorted(
                postulaciones_beca,
                key=lambda p: (-float(p.puntaje_socioeconomico or 0), p.fecha_envio),
            )

            conteo = {
                Postulacion.Estado.ADJUDICADA: 0,
                Postulacion.Estado.LISTA_ESPERA: 0,
                Postulacion.Estado.NO_ADJUDICADA: 0,
            }

            for i, p in enumerate(ordenadas):
                if i < cupo:
                    estado_final = Postulacion.Estado.ADJUDICADA
                elif i < cupo + espera:
                    estado_final = Postulacion.Estado.LISTA_ESPERA
                else:
                    estado_final = Postulacion.Estado.NO_ADJUDICADA
                Postulacion.objects.filter(pk=p.pk).update(estado=estado_final)
                conteo[estado_final] += 1

            self.stdout.write(
                f"    {nombre_beca}: {len(postulaciones_beca)} postulaciones "
                f"→ {conteo[Postulacion.Estado.ADJUDICADA]} ADJUDICADA"
                f" | {conteo[Postulacion.Estado.LISTA_ESPERA]} LISTA_ESPERA"
                f" | {conteo[Postulacion.Estado.NO_ADJUDICADA]} NO_ADJUDICADA"
            )
            total_postulaciones += len(postulaciones_beca)

        self.stdout.write(
            f"  Subtotal: {total_postulaciones} postulaciones, {total_documentos} documentos"
        )
        return total_postulaciones, total_documentos
