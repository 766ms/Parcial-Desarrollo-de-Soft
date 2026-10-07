from django.test import TestCase
from accounts.forms import UsuarioForm
from accounts.models import Usuario


class UsuarioFormTestCase(TestCase):
    def test_nombre_completo_valido(self):
        form = UsuarioForm(data={
            "nombre_completo": "María José Nuñez Pérez",
            "email": "maria@ejemplo.com",
            "password": "Password123!",
            "rol": Usuario.Rol.USER,
            "estado": True,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_nombre_completo_con_numeros_invalido(self):
        form = UsuarioForm(data={
            "nombre_completo": "Juan Carlos 123",
            "email": "juan@ejemplo.com",
            "password": "Password123!",
            "rol": Usuario.Rol.USER,
            "estado": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("nombre_completo", form.errors)

    def test_nombre_completo_con_simbolos_invalido(self):
        form = UsuarioForm(data={
            "nombre_completo": "Ana_Gómez #!",
            "email": "ana@ejemplo.com",
            "password": "Password123!",
            "rol": Usuario.Rol.USER,
            "estado": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("nombre_completo", form.errors)

    def test_email_invalido(self):
        form = UsuarioForm(data={
            "nombre_completo": "Carlos Gómez",
            "email": "carlos_sin_dominio_valido",
            "password": "Password123!",
            "rol": Usuario.Rol.USER,
            "estado": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_email_duplicado(self):
        Usuario.objects.create_user(email="duplicado@test.com", password="password123", nombre_completo="Usuario Uno")
        form = UsuarioForm(data={
            "nombre_completo": "Usuario Dos",
            "email": "duplicado@test.com",
            "password": "Password123!",
            "rol": Usuario.Rol.USER,
            "estado": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_password_demasiado_corta(self):
        form = UsuarioForm(data={
            "nombre_completo": "Pedro Picapiedra",
            "email": "pedro@test.com",
            "password": "123",
            "rol": Usuario.Rol.USER,
            "estado": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)
