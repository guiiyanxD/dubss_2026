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

    # CU15 — Ponderación por sección del formulario socioeconómico. Los initial suman 100.
    peso_dependencia_economica = forms.IntegerField(
        label="Peso: dependencia económica (%)", min_value=0, max_value=100, initial=30
    )
    peso_grupo_familiar = forms.IntegerField(
        label="Peso: grupo familiar (%)", min_value=0, max_value=100, initial=20
    )
    peso_procedencia = forms.IntegerField(
        label="Peso: procedencia (%)", min_value=0, max_value=100, initial=5
    )
    peso_tenencia_vivienda = forms.IntegerField(
        label="Peso: tenencia de vivienda (%)", min_value=0, max_value=100, initial=15
    )
    peso_infraestructura = forms.IntegerField(
        label="Peso: infraestructura (%)", min_value=0, max_value=100, initial=15
    )
    peso_otro_beneficio = forms.IntegerField(
        label="Peso: otro beneficio (%)", min_value=0, max_value=100, initial=10
    )
    peso_discapacidad = forms.IntegerField(
        label="Peso: discapacidad (%)", min_value=0, max_value=100, initial=5
    )

    def clean(self):
        cleaned_data = super().clean()
        campos_peso = [
            "peso_dependencia_economica",
            "peso_grupo_familiar",
            "peso_procedencia",
            "peso_tenencia_vivienda",
            "peso_infraestructura",
            "peso_otro_beneficio",
            "peso_discapacidad",
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
