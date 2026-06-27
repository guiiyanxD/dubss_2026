from django.contrib import admin

from .models import (
    FormularioSocioeconomico,
    IntegranteFamiliar,
    OpcionDependencia,
    OpcionDiscapacidad,
    OpcionOtroBeneficio,
    RangoGrupoFamiliar,
    RangoInfraestructura,
    RangoIngreso,
    TipoOcupacionSosten,
    TipoTenenciaVivienda,
)


@admin.register(OpcionDependencia)
class OpcionDependenciaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "valor_puntaje", "activo"]
    list_editable = ["valor_puntaje", "activo"]
    search_fields = ["nombre"]


@admin.register(TipoOcupacionSosten)
class TipoOcupacionSostenAdmin(admin.ModelAdmin):
    list_display = ["nombre", "documento_adjuntar", "valor_puntaje", "activo"]
    list_editable = ["valor_puntaje", "activo"]
    search_fields = ["nombre"]


@admin.register(RangoIngreso)
class RangoIngresoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "monto_minimo", "monto_maximo", "valor_puntaje", "activo"]
    list_editable = ["valor_puntaje", "activo"]
    search_fields = ["nombre"]


@admin.register(RangoGrupoFamiliar)
class RangoGrupoFamiliarAdmin(admin.ModelAdmin):
    list_display = ["nombre", "cantidad_minima", "cantidad_maxima", "valor_puntaje", "activo"]
    list_editable = ["valor_puntaje", "activo"]
    search_fields = ["nombre"]


@admin.register(TipoTenenciaVivienda)
class TipoTenenciaViviendaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "documento_adjuntar", "valor_puntaje", "activo"]
    list_editable = ["valor_puntaje", "activo"]
    search_fields = ["nombre"]


@admin.register(RangoInfraestructura)
class RangoInfraestructuraAdmin(admin.ModelAdmin):
    list_display = ["nombre", "total_minimo", "total_maximo", "valor_puntaje", "activo"]
    list_editable = ["valor_puntaje", "activo"]
    search_fields = ["nombre"]


@admin.register(OpcionOtroBeneficio)
class OpcionOtroBeneficioAdmin(admin.ModelAdmin):
    list_display = ["nombre", "valor_puntaje", "activo"]
    list_editable = ["valor_puntaje", "activo"]
    search_fields = ["nombre"]


@admin.register(OpcionDiscapacidad)
class OpcionDiscapacidadAdmin(admin.ModelAdmin):
    list_display = ["nombre", "valor_puntaje", "activo"]
    list_editable = ["valor_puntaje", "activo"]
    search_fields = ["nombre"]


class IntegranteFamiliarInline(admin.TabularInline):
    model = IntegranteFamiliar
    extra = 0


@admin.register(FormularioSocioeconomico)
class FormularioSocioeconomicoAdmin(admin.ModelAdmin):
    list_display = [
        "usuario",
        "rango_ingreso",
        "cantidad_familiares",
        "completado",
        "fecha_actualizacion",
    ]
    list_filter = ["completado"]
    search_fields = ["usuario__email", "usuario__last_name"]
    readonly_fields = ["fecha_actualizacion"]
    inlines = [IntegranteFamiliarInline]
