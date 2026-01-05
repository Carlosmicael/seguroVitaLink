from django.contrib import admin
from .models import Aseguradora


@admin.register(Aseguradora)
class AseguradoraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'email', 'activa', 'created_at')
    search_fields = ('nombre', 'email', 'telefono')
    list_filter = ('activa',)
