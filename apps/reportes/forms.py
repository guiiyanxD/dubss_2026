from django import forms


class GenerarRankingForm(forms.Form):
    cupo = forms.IntegerField(
        label="Cupo a adjudicar",
        min_value=1,
        help_text="Número de postulaciones que serán adjudicadas.",
    )
    cupo_espera = forms.IntegerField(
        label="Cupo lista de espera",
        min_value=0,
        initial=0,
        help_text="Número de postulaciones en lista de espera (0 para ninguna).",
    )
