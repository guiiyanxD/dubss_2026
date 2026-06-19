from django.contrib import admin

from .models import Conversacion, MensajeChat, ResumenIA


@admin.register(ResumenIA)
class ResumenIAAdmin(admin.ModelAdmin):
    list_display = ("id", "convocatoria", "usuario", "estado", "fecha_creacion", "fecha_completado")
    list_filter = ("estado",)
    readonly_fields = ("resultado", "error_detalle", "fecha_creacion", "fecha_completado")


class MensajeChatInline(admin.TabularInline):
    model = MensajeChat
    extra = 0
    readonly_fields = ("rol", "contenido", "tools_usadas", "fecha_creacion")


@admin.register(Conversacion)
class ConversacionAdmin(admin.ModelAdmin):
    list_display = ("id", "titulo", "usuario", "fecha_creacion", "fecha_actualizacion")
    inlines = [MensajeChatInline]
