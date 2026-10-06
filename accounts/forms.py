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
    password = forms.CharField(
        label="Contraseña", required=False, widget=forms.PasswordInput(render_value=False),
        help_text="Al editar, déjala vacía para conservar la actual.")

    class Meta:
        model = Usuario
        fields = ["nombre_completo", "email", "rol", "estado"]
        labels = {"estado": "Activo (puede iniciar sesión)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["password"].required = True

    def clean_password(self):
        clave = self.cleaned_data.get("password")
        if clave:
            validate_password(clave, self.instance)
        return clave

    def save(self, commit=True):
        usuario = super().save(commit=False)
        if self.cleaned_data.get("password"):
            usuario.set_password(self.cleaned_data["password"])
        if commit:
            usuario.save()
        return usuario
