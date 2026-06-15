from django.contrib import admin

from .models import Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ["usuario", "asunto", "estado", "fecha_creacion", "fecha_envio"]
    list_filter = ["estado"]
    search_fields = ["usuario__email", "asunto"]
    readonly_fields = ["fecha_creacion", "fecha_envio", "error_detalle"]
