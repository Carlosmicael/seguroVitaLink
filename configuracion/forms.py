from django import forms
from .models import Aseguradora
from .models import DocumentoPolitica, RequisitoSiniestro

# Forma para Aseguradora ---------- #

class AseguradoraForm(forms.ModelForm):
    class Meta:
        model = Aseguradora
        fields = ['nombre', 'ruc', 'direccion', 'telefono', 'email', 'politicas', 'dias_maximos_reporte', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500'}),
            'ruc': forms.TextInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500'}),
            'direccion': forms.Textarea(attrs={'rows': 3, 'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500'}),
            'telefono': forms.TextInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500'}),
            'politicas': forms.Textarea(attrs={'rows': 4, 'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500'}),
            'activa': forms.CheckboxInput(attrs={'class': 'rounded text-emerald-600 focus:ring-emerald-500 h-5 w-5'}),
            'dias_maximos_reporte': forms.NumberInput(attrs={'class': 'w-1/3 border-gray-300 rounded-md shadow-sm p-2'}),
        }

class RequisitoSiniestroForm(forms.ModelForm):
    class Meta:
        model = RequisitoSiniestro
        fields = ['aseguradora', 'tipo_siniestro', 'nombre_documento', 'obligatorio']
        widgets = {
            'aseguradora': forms.Select(attrs={'class': 'w-full border-gray-300 rounded p-2 focus:ring-blue-500 focus:border-blue-500'}),
            'tipo_siniestro': forms.Select(attrs={'class': 'w-full border-gray-300 rounded p-2 focus:ring-blue-500 focus:border-blue-500'}),
            'nombre_documento': forms.TextInput(attrs={'class': 'w-full border-gray-300 rounded p-2 focus:ring-blue-500 focus:border-blue-500', 'placeholder': 'Ej: Informe Policial Legalizado'}),
            'obligatorio': forms.CheckboxInput(attrs={'class': 'h-5 w-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500'}),
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


class MigracionAseguradoraForm(forms.Form):
    aseguradora_origen = forms.ModelChoiceField(
        queryset=Aseguradora.objects.filter(activa=True),
        label="Aseguradora Actual (Origen)",
        widget=forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm'})
    )
    aseguradora_destino = forms.ModelChoiceField(
        queryset=Aseguradora.objects.filter(activa=True),
        label="Nueva Aseguradora (Destino)",
        widget=forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm'})
    )
    
    confirmacion = forms.BooleanField(
        required=True,
        label="Confirmo que deseo migrar todas las pólizas activas.",
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-yellow-600 focus:ring-yellow-500 border-gray-300 rounded'})
    )

    def clean(self):
        cleaned_data = super().clean()
        origen = cleaned_data.get("aseguradora_origen")
        destino = cleaned_data.get("aseguradora_destino")

        if origen and destino and origen == destino:
            raise forms.ValidationError("La aseguradora de destino debe ser diferente a la de origen.")