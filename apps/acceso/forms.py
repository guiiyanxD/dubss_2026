import datetime

from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator


class RegistroEstudianteForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico")
    first_name = forms.CharField(label="Nombre", max_length=150)
    last_name = forms.CharField(label="Apellido", max_length=150)
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)
    nro_registro = forms.CharField(label="Nro. Registro", max_length=20)
    carrera = forms.CharField(label="Carrera", max_length=150)
    anio_ingreso = forms.IntegerField(
        label="Año de ingreso",
        validators=[
            MinValueValidator(2000),
            MaxValueValidator(datetime.date.today().year),
        ],
    )
    fecha_nacimiento = forms.DateField(
        label="Fecha de nacimiento",
        widget=forms.DateInput(attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
    )
    acepta_terminos = forms.BooleanField(
        label="He leído y acepto la política de privacidad y los términos y condiciones.",
        required=True,
        error_messages={
            "required": "Debés aceptar la política de privacidad y los términos y "
            "condiciones para poder registrarte."
        },
    )

    def clean_fecha_nacimiento(self):
        fn = self.cleaned_data["fecha_nacimiento"]
        hoy = datetime.date.today()
        edad = hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))
        if edad < 18:
            raise forms.ValidationError("Debés tener al menos 18 años para registrarte.")
        if edad > 60:
            raise forms.ValidationError("La edad máxima permitida para el registro es de 60 años.")
        return fn
