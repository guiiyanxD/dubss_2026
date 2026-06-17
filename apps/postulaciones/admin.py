from django.contrib import admin

from .models import DocumentoPostulacion, Postulacion


class DocumentoPostulacionInline(admin.TabularInline):
    model = DocumentoPostulacion
    extra = 0
    readonly_fields = ["fecha_validacion"]


@admin.register(Postulacion)
class PostulacionAdmin(admin.ModelAdmin):
    list_display = [
        "estudiante",
        "convocatoria",
        "beca",
        "estado",
        "fecha_envio",
        "numero_referencia",
    ]
    list_filter = ["estado", "convocatoria"]
    search_fields = ["estudiante__email", "estudiante__last_name"]
    readonly_fields = ["fecha_creacion", "fecha_envio", "numero_referencia"]
    inlines = [DocumentoPostulacionInline]
