from django import forms

ROLES_INTERNOS = [
    ("Director", "Director"),
    ("Operador", "Operador"),
]

ROLES_TODOS = [
    ("Director", "Director"),
    ("Operador", "Operador"),
    ("Estudiante", "Estudiante"),
]


class CrearUsuarioForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico")
    first_name = forms.CharField(label="Nombre", max_length=150)
    last_name = forms.CharField(label="Apellido", max_length=150)
    rol = forms.ChoiceField(label="Rol", choices=ROLES_INTERNOS)


class EditarUsuarioForm(forms.Form):
    first_name = forms.CharField(label="Nombre", max_length=150)
    last_name = forms.CharField(label="Apellido", max_length=150)
    rol = forms.ChoiceField(label="Rol", choices=ROLES_TODOS)
