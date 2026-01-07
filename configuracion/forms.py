from django import forms
from .models import Aseguradora
from .models import DocumentoPolitica

# Forma para Aseguradora ---------- #

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

# Nueva forma para Documentos de Políticas ---------- #

class DocumentoPoliticaForm(forms.ModelForm):
    class Meta:
        model = DocumentoPolitica
        fields = ['aseguradora', 'titulo', 'version', 'fecha_vigencia', 'archivo_pdf', 'terminos_texto', 'activo']
        widgets = {
            'aseguradora': forms.Select(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm p-2'}),
            'titulo': forms.TextInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm p-2'}),
            'version': forms.TextInput(attrs={'class': 'w-1/3 border-gray-300 rounded-md shadow-sm p-2'}),
            'fecha_vigencia': forms.DateInput(attrs={'type': 'date', 'class': 'border-gray-300 rounded-md shadow-sm p-2'}),
            'archivo_pdf': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100'}),
            'terminos_texto': forms.Textarea(attrs={'rows': 5, 'class': 'w-full border-gray-300 rounded-md shadow-sm p-2'}),
            'activo': forms.CheckboxInput(attrs={'class': 'h-5 w-5 text-emerald-600 rounded'}),
        }