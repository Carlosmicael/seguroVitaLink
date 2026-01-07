from django import forms
from .models import Aseguradora

class AseguradoraForm(forms.ModelForm):
    class Meta:
        model = Aseguradora
        fields = ['nombre', 'ruc', 'direccion', 'telefono', 'email', 'politicas', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500'}),
            'ruc': forms.TextInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500'}),
            'direccion': forms.Textarea(attrs={'rows': 3, 'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500'}),
            'telefono': forms.TextInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500'}),
            'politicas': forms.Textarea(attrs={'rows': 4, 'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500'}),
            'activa': forms.CheckboxInput(attrs={'class': 'rounded text-emerald-600 focus:ring-emerald-500 h-5 w-5'}),
        }