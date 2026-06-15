import datetime

from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator


class RegistroEstudianteForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico")
    first_name = forms.CharField(label="Nombre", max_length=150)
    last_name = forms.CharField(label="Apellido", max_length=150)
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)
    legajo = forms.CharField(label="Legajo", max_length=20)
    carrera = forms.CharField(label="Carrera", max_length=150)
    anio_ingreso = forms.IntegerField(
        label="Año de ingreso",
        validators=[
            MinValueValidator(2000),
            MaxValueValidator(datetime.date.today().year),
        ],
    )
