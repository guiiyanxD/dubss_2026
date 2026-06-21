from django import forms

from apps.convocatorias.models import Beca, Convocatoria


class GenerarRankingForm(forms.Form):
    """CU24 — el ranking se genera por Beca (CU15: pesos no comparables entre becas)."""

    beca = forms.ModelChoiceField(
        label="Beca",
        queryset=Beca.objects.none(),
        help_text="Cada beca de la convocatoria se rankea por separado.",
    )
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

    def __init__(self, *args, convocatoria=None, **kwargs):
        super().__init__(*args, **kwargs)
        if convocatoria is not None:
            self.fields["beca"].queryset = convocatoria.becas.all()


class FiltroDashboardForm(forms.Form):
    """Filtros del dashboard de KPIs (CU26): convocatoria y rango de fechas."""

    convocatoria = forms.ModelChoiceField(
        label="Convocatoria",
        queryset=Convocatoria.objects.order_by("-fecha_apertura"),
        required=False,
        empty_label="Todas las convocatorias",
    )
    fecha_desde = forms.DateField(
        label="Desde",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    fecha_hasta = forms.DateField(
        label="Hasta",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
