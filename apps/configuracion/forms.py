from django import forms

from .models import (
    FormularioSocioeconomico,
    OpcionDependencia,
    OpcionDiscapacidad,
    OpcionOtroBeneficio,
    RangoGrupoFamiliar,
    RangoIngreso,
    RangoInfraestructura,
    TipoOcupacionSosten,
    TipoTenenciaVivienda,
)

# ---------------------------------------------------------------------------
# Forms para edición de catálogos socioeconómicos (Director)
# ---------------------------------------------------------------------------

_W_TEXT = {"class": "form-control form-control-sm"}
_W_NUM = {"class": "form-control form-control-sm text-end"}
_W_CHECK = {"class": "form-check-input"}


class OpcionDependenciaForm(forms.ModelForm):
    class Meta:
        model = OpcionDependencia
        fields = ["nombre", "valor_puntaje", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs=_W_TEXT),
            "valor_puntaje": forms.NumberInput(attrs=_W_NUM),
            "activo": forms.CheckboxInput(attrs=_W_CHECK),
        }


class TipoOcupacionSostenForm(forms.ModelForm):
    class Meta:
        model = TipoOcupacionSosten
        fields = ["nombre", "documento_adjuntar", "valor_puntaje", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs=_W_TEXT),
            "documento_adjuntar": forms.TextInput(attrs=_W_TEXT),
            "valor_puntaje": forms.NumberInput(attrs=_W_NUM),
            "activo": forms.CheckboxInput(attrs=_W_CHECK),
        }


class RangoIngresoForm(forms.ModelForm):
    class Meta:
        model = RangoIngreso
        fields = ["nombre", "monto_minimo", "monto_maximo", "valor_puntaje", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs=_W_TEXT),
            "monto_minimo": forms.NumberInput(attrs=_W_NUM),
            "monto_maximo": forms.NumberInput(attrs=_W_NUM),
            "valor_puntaje": forms.NumberInput(attrs=_W_NUM),
            "activo": forms.CheckboxInput(attrs=_W_CHECK),
        }


class RangoGrupoFamiliarForm(forms.ModelForm):
    class Meta:
        model = RangoGrupoFamiliar
        fields = ["nombre", "cantidad_minima", "cantidad_maxima", "valor_puntaje", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs=_W_TEXT),
            "cantidad_minima": forms.NumberInput(attrs=_W_NUM),
            "cantidad_maxima": forms.NumberInput(attrs=_W_NUM),
            "valor_puntaje": forms.NumberInput(attrs=_W_NUM),
            "activo": forms.CheckboxInput(attrs=_W_CHECK),
        }


class TipoTenenciaViviendaForm(forms.ModelForm):
    class Meta:
        model = TipoTenenciaVivienda
        fields = ["nombre", "documento_adjuntar", "valor_puntaje", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs=_W_TEXT),
            "documento_adjuntar": forms.TextInput(attrs=_W_TEXT),
            "valor_puntaje": forms.NumberInput(attrs=_W_NUM),
            "activo": forms.CheckboxInput(attrs=_W_CHECK),
        }


class RangoInfraestructuraForm(forms.ModelForm):
    class Meta:
        model = RangoInfraestructura
        fields = ["nombre", "total_minimo", "total_maximo", "valor_puntaje", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs=_W_TEXT),
            "total_minimo": forms.NumberInput(attrs=_W_NUM),
            "total_maximo": forms.NumberInput(attrs=_W_NUM),
            "valor_puntaje": forms.NumberInput(attrs=_W_NUM),
            "activo": forms.CheckboxInput(attrs=_W_CHECK),
        }


class OpcionOtroBeneficioForm(forms.ModelForm):
    class Meta:
        model = OpcionOtroBeneficio
        fields = ["nombre", "valor_puntaje", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs=_W_TEXT),
            "valor_puntaje": forms.NumberInput(attrs=_W_NUM),
            "activo": forms.CheckboxInput(attrs=_W_CHECK),
        }


class OpcionDiscapacidadForm(forms.ModelForm):
    class Meta:
        model = OpcionDiscapacidad
        fields = ["nombre", "valor_puntaje", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs=_W_TEXT),
            "valor_puntaje": forms.NumberInput(attrs=_W_NUM),
            "activo": forms.CheckboxInput(attrs=_W_CHECK),
        }


class FormularioSocioeconomicoForm(forms.Form):

    cantidad_familiares = forms.IntegerField(
        label="Cantidad de miembros del grupo familiar",
        min_value=1,
        max_value=20,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    tiene_beca_previa = forms.BooleanField(
        label="¿Posee otra beca actualmente?",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    observaciones = forms.CharField(
        label="Aclaración o comentario personal",
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        required=False,
    )

    # 1° Datos del postulante
    numero_celular = forms.CharField(
        label="Número de celular",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    telefono_referencia = forms.CharField(
        label="Teléfono de referencia",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    # 2° Dependencia económica del postulante
    dependencia_economica = forms.ModelChoiceField(
        label="¿De quién depende usted?",
        queryset=OpcionDependencia.objects.filter(activo=True),
        required=False,
        empty_label="— Seleccione —",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    tipo_ocupacion_sosten = forms.ModelChoiceField(
        label="Ocupación de quien lo sostiene económicamente",
        queryset=TipoOcupacionSosten.objects.filter(activo=True),
        required=False,
        empty_label="— Seleccione —",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    rango_ingreso = forms.ModelChoiceField(
        label="Rango de ingreso mensual familiar (Bs.)",
        queryset=RangoIngreso.objects.filter(activo=True),
        required=False,
        empty_label="— Seleccione —",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    # 3° Grupo familiar
    tiene_hijos = forms.BooleanField(
        label="¿Tiene hijos?",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    cantidad_hijos = forms.IntegerField(
        label="Cantidad de hijos",
        min_value=0,
        max_value=20,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    # 4° Procedencia
    lugar_procedencia = forms.CharField(
        label="Lugar de procedencia",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Solo si su procedencia es otra ciudad o provincia",
        }),
    )

    # 5° Residencia
    residencia_lugar = forms.CharField(
        label="Lugar",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    residencia_provincia = forms.CharField(
        label="Provincia",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    residencia_zona_anillo = forms.CharField(
        label="Zona o Anillo",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    residencia_barrio = forms.CharField(
        label="Barrio",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    residencia_calle = forms.CharField(
        label="Calle",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    # 6° Tenencia de vivienda
    tipo_tenencia_vivienda = forms.ModelChoiceField(
        label="Tenencia de la vivienda",
        queryset=TipoTenenciaVivienda.objects.filter(activo=True),
        required=False,
        empty_label="— Seleccione —",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    # 7° Infraestructura de la vivienda
    dormitorios = forms.IntegerField(
        label="Dormitorios",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control text-center"}),
    )
    banos = forms.IntegerField(
        label="Baños",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control text-center"}),
    )
    comedores = forms.IntegerField(
        label="Comedores",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control text-center"}),
    )
    salas = forms.IntegerField(
        label="Salas",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control text-center"}),
    )
    patios = forms.IntegerField(
        label="Patios",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control text-center"}),
    )

    # 8° Otro beneficio
    detalle_otro_beneficio = forms.CharField(
        label="¿Cuál otro beneficio?",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    # 9° Discapacidad
    tiene_discapacidad = forms.BooleanField(
        label="¿Tiene algún tipo de discapacidad?",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    detalle_discapacidad = forms.CharField(
        label="Tipo y grado de discapacidad",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )


class IntegranteFamiliarForm(forms.Form):
    nombre_completo = forms.CharField(
        label="Nombre completo",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-sm",
            "placeholder": "Nombre completo",
        }),
    )
    parentesco = forms.ChoiceField(
        label="Parentesco",
        choices=FormularioSocioeconomico.ParentescoIntegrante.choices,
        required=True,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    edad = forms.IntegerField(
        label="Edad",
        min_value=0,
        max_value=120,
        required=False,
        widget=forms.NumberInput(attrs={
            "class": "form-control form-control-sm",
            "placeholder": "Edad",
        }),
    )
    ocupacion = forms.CharField(
        label="Ocupación",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-sm",
            "placeholder": "Ocupación",
        }),
    )
    observacion = forms.CharField(
        label="Observación",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-sm",
            "placeholder": "Observación",
        }),
    )

    def tiene_datos(self):
        """True si la fila tiene al menos nombre y parentesco completos."""
        return bool(
            self.cleaned_data.get("nombre_completo") and self.cleaned_data.get("parentesco")
        )


class _IntegranteFamiliarBaseFormSet(forms.BaseFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.fields["DELETE"].widget = forms.HiddenInput(
            attrs={"class": "campo-delete-integrante"}
        )


IntegranteFamiliarFormSet = forms.formset_factory(
    IntegranteFamiliarForm,
    formset=_IntegranteFamiliarBaseFormSet,
    extra=1,
    max_num=10,
    can_delete=True,
)
