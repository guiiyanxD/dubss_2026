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

    # CU15 — Ponderación configurable. Los initial reproducen la fórmula original.
    peso_ingreso = forms.IntegerField(
        label="Peso: ingreso familiar (%)", min_value=0, max_value=100, initial=40
    )
    peso_desempleo = forms.IntegerField(
        label="Peso: desempleo (%)", min_value=0, max_value=100, initial=20
    )
    peso_familiares = forms.IntegerField(
        label="Peso: cantidad de familiares (%)", min_value=0, max_value=100, initial=20
    )
    peso_no_propietario = forms.IntegerField(
        label="Peso: no propietario de vivienda (%)", min_value=0, max_value=100, initial=10
    )
    peso_sin_beca_previa = forms.IntegerField(
        label="Peso: sin beca previa (%)", min_value=0, max_value=100, initial=10
    )

    def clean(self):
        cleaned_data = super().clean()
        campos_peso = [
            "peso_ingreso",
            "peso_desempleo",
            "peso_familiares",
            "peso_no_propietario",
            "peso_sin_beca_previa",
        ]
        if all(campo in cleaned_data for campo in campos_peso):
            suma = sum(cleaned_data[campo] for campo in campos_peso)
            if suma != 100:
                raise forms.ValidationError(
                    f"La suma de los pesos de ponderación debe ser 100 (actual: {suma})."
                )
        return cleaned_data


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
