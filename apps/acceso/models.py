from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UsuarioManager(BaseUserManager):
    """Manager personalizado que usa email como identificador único."""

    def create_user(self, email, password=None, **extra_fields):
        """Crea y guarda un usuario con el email y contraseña dados."""
        if not email:
            raise ValueError('El email es obligatorio.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Crea y guarda un superusuario con el email y contraseña dados."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if not extra_fields.get('is_staff'):
            raise ValueError('El superusuario debe tener is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('El superusuario debe tener is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado. Usa email como identificador de login.

    El campo username de AbstractUser se elimina; el email es el USERNAME_FIELD.
    Los campos de perfil de negocio (legajo, carrera, etc.) se agregan en
    Iteración 1 al implementar CU01–CU03.
    """

    username = None
    email = models.EmailField('correo electrónico', unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'

    def __str__(self):
        return self.email
