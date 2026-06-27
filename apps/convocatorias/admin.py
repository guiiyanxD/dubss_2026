from django.contrib import admin

from .models import Beca, Convocatoria, TipoDocumento


@admin.register(Beca)
class BecaAdmin(admin.ModelAdmin):
    list_display = [
        "nombre",
        "activa",
        "peso_dependencia_economica",
        "peso_grupo_familiar",
        "peso_procedencia",
        "peso_tenencia_vivienda",
        "peso_infraestructura",
        "peso_otro_beneficio",
        "peso_discapacidad",
    ]
    list_filter = ["activa"]
    search_fields = ["nombre"]


@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "activo"]
    list_filter = ["activo"]
    search_fields = ["nombre"]


@admin.register(Convocatoria)
class ConvocatoriaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "estado", "fecha_apertura", "fecha_cierre", "creada_por"]
    list_filter = ["estado"]
    search_fields = ["nombre"]
    filter_horizontal = ["becas", "documentos_requeridos"]
    readonly_fields = ["creada_por"]
