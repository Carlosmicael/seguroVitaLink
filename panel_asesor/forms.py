from django import forms
from .models import Beneficiario
from .models import Estudiante

class BeneficiarioForm(forms.ModelForm):
    class Meta:
        model = Beneficiario
        fields = [
            'cedula',
            'telefono',
            'relacion',
            'cuenta_bancaria'
        ]
class BeneficiarioEditForm(forms.ModelForm):
    # Campos del User
    first_name = forms.CharField(max_length=150, required=True, label="Nombre")
    last_name = forms.CharField(max_length=150, required=True, label="Apellido")
    email = forms.EmailField(required=True, label="Correo electrónico")
    username = forms.CharField(max_length=150, required=True, label="Usuario")

    class Meta:
        model = Beneficiario
        fields = [
            'cedula',
            'telefono',
            'relacion',
            'cuenta_bancaria',
        ]
class EstudianteForm(forms.ModelForm):
    class Meta:
        model = Estudiante
        fields = [
            'cedula',
            'nombres',
            'apellidos',
            'correo',
            'modalidad',
            'nivel',
            'carrera',
            'periodo_academico',
        ]

        widgets = {
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'modalidad': forms.Select(attrs={'class': 'form-control'}),
            'nivel': forms.Select(attrs={'class': 'form-control'}),
            'carrera': forms.TextInput(attrs={'class': 'form-control'}),
            'periodo_academico': forms.Select(attrs={'class': 'form-control'}),
        }
class ImportarEstudiantesForm(forms.Form):
    archivo = forms.FileField(
        label='Selecciona un archivo Excel',
        widget=forms.ClearableFileInput(attrs={'accept': '.xlsx,.csv'})
    )
