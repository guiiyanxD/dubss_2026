from django import forms

from apps.convocatorias.models import Beca


class IniciarPostulacionForm(forms.Form):
    beca = forms.ModelChoiceField(
        label="Beca a la que postulás",
        queryset=Beca.objects.none(),
        empty_label="Seleccioná una beca",
    )

    def __init__(self, *args, convocatoria=None, **kwargs):
        super().__init__(*args, **kwargs)
        if convocatoria:
            self.fields["beca"].queryset = convocatoria.becas.filter(activa=True)


class VerificarIdentidadForm(forms.Form):
    aprobar = forms.ChoiceField(
        label="Resultado",
        choices=[("1", "Aprobar identidad"), ("0", "Rechazar identidad")],
        widget=forms.RadioSelect,
    )
    observaciones = forms.CharField(
        label="Observaciones",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )


class ValidarDocumentoForm(forms.Form):
    aprobar = forms.ChoiceField(
        label="Resultado",
        choices=[("1", "Documento válido"), ("0", "Documento inválido / no presentado")],
        widget=forms.RadioSelect,
    )


class DigitalizarDocumentoForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo digitalizado",
        help_text="PDF, JPG o PNG. Máx. 10 MB.",
    )
