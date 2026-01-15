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
