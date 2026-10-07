import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from .models import Usuario


class EstiloMixin:
    """Agrega las clases CSS de la VISTA a todos los campos de un formulario."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            w = campo.widget
            w.attrs["class"] = "casilla" if isinstance(w, forms.CheckboxInput) else "entrada"
            if isinstance(w, forms.Textarea):
                w.attrs["rows"] = 3


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "Email", "autocomplete": "email", "autofocus": True}),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Contraseña", "autocomplete": "current-password"}),
    )
    error_messages = {
        "invalid_login": "Email o contraseña incorrectos.",
        "inactive": "Tu usuario está inactivo. Contacta al administrador.",
    }


class UsuarioForm(EstiloMixin, forms.ModelForm):
    nombre_completo = forms.CharField(
        label="Nombre completo",
        max_length=150,
        widget=forms.TextInput(attrs={
            "placeholder": "Ej: Juan Pérez Morales",
            "autocomplete": "name",
            "pattern": r"[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+",
            "title": "Solo letras y espacios permitidos",
        }),
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            "placeholder": "ejemplo@correo.com",
            "autocomplete": "email",
        }),
    )
    password = forms.CharField(
        label="Contraseña",
        required=False,
        widget=forms.PasswordInput(render_value=False, attrs={"placeholder": "Mínimo 8 caracteres"}),
        help_text="Al editar, déjala vacía para conservar la actual.",
    )

    class Meta:
        model = Usuario
        fields = ["nombre_completo", "email", "rol", "estado"]
        labels = {"estado": "Activo (puede iniciar sesión)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["password"].required = True

    def clean_nombre_completo(self):
        nombre = (self.cleaned_data.get("nombre_completo") or "").strip()
        if not nombre:
            raise forms.ValidationError("El nombre completo es obligatorio.")

        # Permitir estrictamente solo letras (con acentos, diéresis, ñ) y espacios
        patron_solo_letras = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$"
        if not re.match(patron_solo_letras, nombre):
            raise forms.ValidationError(
                "El nombre completo solo puede contener letras y espacios. No se permiten números ni caracteres especiales."
            )

        # Normalizar espacios múltiples intermedios
        nombre_limpio = " ".join(nombre.split())
        if len(nombre_limpio) < 3:
            raise forms.ValidationError("Ingresa un nombre completo válido (mínimo 3 letras).")

        return nombre_limpio

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("El correo electrónico es obligatorio.")

        # Validar formato con dominio y extensión (ejemplo@dominio.com)
        patron_email = r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$"
        if not re.match(patron_email, email):
            raise forms.ValidationError("Ingresa una dirección de correo electrónico válida (ej: usuario@empresa.com).")

        # Comprobar unicidad en base de datos
        qs = Usuario.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe un usuario registrado con este correo electrónico.")

        return email

    def clean_password(self):
        clave = self.cleaned_data.get("password")
        if not self.instance.pk and not clave:
            raise forms.ValidationError("La contraseña es obligatoria para nuevos usuarios.")

        if clave:
            if len(clave) < 8:
                raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
            validate_password(clave, self.instance)
        return clave

    def clean_rol(self):
        rol = self.cleaned_data.get("rol")
        if rol not in Usuario.Rol.values:
            raise forms.ValidationError("Selecciona un rol válido (Admin o User).")
        return rol

    def clean_estado(self):
        estado = self.cleaned_data.get("estado")
        return bool(estado)

    def save(self, commit=True):
        usuario = super().save(commit=False)
        if self.cleaned_data.get("password"):
            usuario.set_password(self.cleaned_data["password"])
        if commit:
            usuario.save()
        return usuario

