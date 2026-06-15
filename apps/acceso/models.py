from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UsuarioManager(BaseUserManager):
    """Manager personalizado que usa email como identificador único."""

    def create_user(self, email, password=None, **extra_fields):
        """Crea y guarda un usuario con el email y contraseña dados."""
        if not email:
            raise ValueError("El email es obligatorio.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Crea y guarda un superusuario con el email y contraseña dados."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields.get("is_staff"):
            raise ValueError("El superusuario debe tener is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("El superusuario debe tener is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractUser):
    """Modelo de usuario personalizado. Usa email como identificador de login."""

    username = None
    email = models.EmailField("correo electrónico", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return self.email

    def get_rol(self):
        """Retorna el nombre del primer grupo asignado, o cadena vacía."""
        grupo = self.groups.first()
        return grupo.name if grupo else ""


class PerfilEstudiante(models.Model):
    """Datos académicos del estudiante, complementa al Usuario."""

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="perfil_estudiante",
    )
    legajo = models.CharField("legajo", max_length=20, unique=True)
    carrera = models.CharField("carrera", max_length=150)
    anio_ingreso = models.PositiveSmallIntegerField("año de ingreso")

    class Meta:
        verbose_name = "perfil de estudiante"
        verbose_name_plural = "perfiles de estudiante"

    def __str__(self):
        return f"{self.usuario.email} — {self.legajo}"
