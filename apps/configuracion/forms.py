from django import forms

from .models import FormularioSocioeconomico


class FormularioSocioeconomicoForm(forms.Form):
    
    situacion_laboral = forms.ChoiceField(
        label="Situación laboral",
        choices=FormularioSocioeconomico.SituacionLaboral.choices,
    )
    ingreso_mensual_familiar = forms.DecimalField(
        label="Ingreso mensual familiar (Bs.)",
        min_value=0,
        max_digits=12,
        decimal_places=2,
    )
    cantidad_familiares = forms.IntegerField(
        label="Cantidad de miembros del grupo familiar",
        min_value=1,
        max_value=20,
    )
    situacion_habitacional = forms.ChoiceField(
        label="Situación habitacional",
        choices=FormularioSocioeconomico.SituacionHabitacional.choices,
    )
    tiene_beca_previa = forms.BooleanField(
        label="¿Posee otra beca actualmente?",
        required=False,
    )
    observaciones = forms.CharField(
        label="Observaciones adicionales",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )

    # 1° Datos del postulante
    numero_celular = forms.CharField(label="Número de celular", max_length=20, required=False)
    telefono_referencia = forms.CharField(
        label="Teléfono de referencia", max_length=20, required=False
    )

    # 2° Dependencia económica del postulante
    dependencia_economica = forms.ChoiceField(
        label="¿De quién depende usted?",
        choices=FormularioSocioeconomico.DependenciaEconomica.choices,
        required=False,
    )
    tipo_ocupacion_sosten = forms.ChoiceField(
        label="Ocupación de quien lo sostiene económicamente",
        choices=FormularioSocioeconomico.TipoOcupacionSosten.choices,
        required=False,
    )

    # 3° Grupo familiar
    tiene_hijos = forms.BooleanField(label="¿Tiene hijos?", required=False)
    cantidad_hijos = forms.IntegerField(
        label="Cantidad de hijos", min_value=0, max_value=20, required=False
    )

    # 4° Procedencia
    lugar_procedencia = forms.CharField(
        label="Lugar de procedencia (si es de otra ciudad o provincia)",
        max_length=150,
        required=False,
    )

    # 5° Residencia
    residencia_lugar = forms.CharField(label="Lugar de residencia", max_length=150, required=False)
    residencia_provincia = forms.CharField(label="Provincia", max_length=100, required=False)
    residencia_zona_anillo = forms.CharField(label="Zona o anillo", max_length=100, required=False)
    residencia_barrio = forms.CharField(label="Barrio", max_length=100, required=False)
    residencia_calle = forms.CharField(label="Calle", max_length=150, required=False)

    # 6° Tenencia de vivienda
    tipo_tenencia_vivienda = forms.ChoiceField(
        label="Tenencia de la vivienda",
        choices=FormularioSocioeconomico.TipoTenenciaVivienda.choices,
        required=False,
    )

    # 7° Infraestructura de la vivienda
    dormitorios = forms.IntegerField(label="Dormitorios", min_value=0, required=False)
    banos = forms.IntegerField(label="Baños", min_value=0, required=False)
    comedores = forms.IntegerField(label="Comedores", min_value=0, required=False)
    salas = forms.IntegerField(label="Salas", min_value=0, required=False)
    patios = forms.IntegerField(label="Patios", min_value=0, required=False)

    # 8° Otro beneficio dentro de la universidad
    detalle_otro_beneficio = forms.CharField(
        label="¿Cuál otro beneficio?", max_length=200, required=False
    )

    # 9° Discapacidad
    tiene_discapacidad = forms.BooleanField(
        label="¿Tiene algún tipo de discapacidad?", required=False
    )
    detalle_discapacidad = forms.CharField(
        label="Tipo y grado de discapacidad", max_length=200, required=False
    )


class IntegranteFamiliarForm(forms.Form):
    nombre_completo = forms.CharField(label="Nombre completo", max_length=200, required=False)
    parentesco = forms.ChoiceField(
        label="Parentesco",
        choices=FormularioSocioeconomico.ParentescoIntegrante.choices,
        required=True
    )
    edad = forms.IntegerField(label="Edad", min_value=0, max_value=120, required=False)
    ocupacion = forms.CharField(label="Ocupación", max_length=100, required=False)
    observacion = forms.CharField(label="Observación", max_length=200, required=False)

    def tiene_datos(self):
        """True si la fila tiene al menos nombre y parentesco completos."""
        return bool(
            self.cleaned_data.get("nombre_completo") and self.cleaned_data.get("parentesco")
        )


IntegranteFamiliarFormSet = forms.formset_factory(IntegranteFamiliarForm, extra=1, max_num=10)
