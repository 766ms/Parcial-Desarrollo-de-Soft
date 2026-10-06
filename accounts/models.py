from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("El email es obligatorio")
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("rol", Usuario.Rol.ADMIN)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    class Rol(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        USER = "USER", "User"

    id_user = models.AutoField(primary_key=True)
    nombre_completo = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=5, choices=Rol.choices, default=Rol.USER)
    estado = models.BooleanField("Activo", default=True)  # Activo / Inactivo

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre_completo"]
    objects = UsuarioManager()

    # Django usa is_active para impedir el login: aquí lo ligamos a "estado".
    @property
    def is_active(self):
        return self.estado

    @property
    def is_staff(self):
        return self.rol == self.Rol.ADMIN

    @property
    def es_admin(self):
        return self.rol == self.Rol.ADMIN

    def __str__(self):
        return self.nombre_completo
