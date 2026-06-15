from django import forms

from .models import Beca, Convocatoria, TipoDocumento  # noqa: F401


class ConvocatoriaForm(forms.Form):
    nombre = forms.CharField(label="Nombre", max_length=200)
    descripcion = forms.CharField(
        label="Descripción", widget=forms.Textarea(attrs={"rows": 3}), required=False
    )
    fecha_apertura = forms.DateTimeField(
        label="Fecha de apertura",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    fecha_cierre = forms.DateTimeField(
        label="Fecha de cierre",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    becas = forms.ModelMultipleChoiceField(
        label="Becas disponibles",
        queryset=Beca.objects.filter(activa=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    documentos_requeridos = forms.ModelMultipleChoiceField(
        label="Documentos requeridos",
        queryset=TipoDocumento.objects.filter(activo=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )


class BecaForm(forms.Form):
    nombre = forms.CharField(label="Nombre", max_length=150)
    descripcion = forms.CharField(
        label="Descripción", widget=forms.Textarea(attrs={"rows": 2}), required=False
    )
    activa = forms.BooleanField(label="Activa", required=False, initial=True)


class TipoDocumentoForm(forms.Form):
    nombre = forms.CharField(label="Nombre", max_length=150)
    descripcion = forms.CharField(
        label="Descripción", widget=forms.Textarea(attrs={"rows": 2}), required=False
    )
    activo = forms.BooleanField(label="Activo", required=False, initial=True)


def convocatoria_a_form_inicial(convocatoria):
    """Devuelve los valores iniciales del form a partir de una instancia existente."""
    return {
        "nombre": convocatoria.nombre,
        "descripcion": convocatoria.descripcion,
        "fecha_apertura": convocatoria.fecha_apertura.strftime("%Y-%m-%dT%H:%M"),
        "fecha_cierre": convocatoria.fecha_cierre.strftime("%Y-%m-%dT%H:%M"),
        "becas": convocatoria.becas.values_list("pk", flat=True),
        "documentos_requeridos": convocatoria.documentos_requeridos.values_list("pk", flat=True),
    }
