from django.contrib import admin

from .models import FormularioSocioeconomico


@admin.register(FormularioSocioeconomico)
class FormularioSocioeconomicoAdmin(admin.ModelAdmin):
    list_display = [
        "usuario",
        "situacion_laboral",
        "ingreso_mensual_familiar",
        "completado",
        "fecha_actualizacion",
    ]
    list_filter = ["completado", "situacion_laboral", "situacion_habitacional"]
    search_fields = ["usuario__email", "usuario__last_name"]
    readonly_fields = ["fecha_actualizacion"]
