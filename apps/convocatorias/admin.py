from django.contrib import admin

from .models import Beca, Convocatoria, TipoDocumento


@admin.register(Beca)
class BecaAdmin(admin.ModelAdmin):
    list_display = [
        "nombre",
        "activa",
        "peso_ingreso",
        "peso_desempleo",
        "peso_familiares",
        "peso_no_propietario",
        "peso_sin_beca_previa",
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
