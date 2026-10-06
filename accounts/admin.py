from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("nombre_completo", "email", "rol", "estado")
    ordering = ("email",)
    list_filter = ("rol", "estado")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Datos", {"fields": ("nombre_completo", "rol", "estado")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",),
                             "fields": ("email", "nombre_completo", "rol", "estado", "password1", "password2")}),)
    search_fields = ("email", "nombre_completo")
