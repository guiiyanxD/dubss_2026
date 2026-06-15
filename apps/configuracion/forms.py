from django import forms

from .models import FormularioSocioeconomico


class FormularioSocioeconomicoForm(forms.Form):
    situacion_laboral = forms.ChoiceField(
        label="Situación laboral",
        choices=FormularioSocioeconomico.SituacionLaboral.choices,
    )
    ingreso_mensual_familiar = forms.DecimalField(
        label="Ingreso mensual familiar (ARS)",
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
