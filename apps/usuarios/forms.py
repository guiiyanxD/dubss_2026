from django import forms

ROLES_INTERNOS = [
    ("Director", "Director"),
    ("Operador", "Operador"),
]


class CrearUsuarioForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico")
    first_name = forms.CharField(label="Nombre", max_length=150)
    last_name = forms.CharField(label="Apellido", max_length=150)
    rol = forms.ChoiceField(label="Rol", choices=ROLES_INTERNOS)
