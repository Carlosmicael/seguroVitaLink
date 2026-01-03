from django import forms
from django.core.exceptions import ValidationError
from siniestros.models import Siniestro, Poliza
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox


class ActivacionPolizaForm(forms.Form):
    """Formulario para reportar evento/siniestro de estudiante UTPL"""
    
    TIPO_EVENTO_CHOICES = [
        ('accidente', 'Accidente'),
        ('enfermedad', 'Enfermedad'),
        ('muerte', 'Muerte'),
        ('invalidez', 'Invalidez'),
        ('otro', 'Otro'),
    ]
    
    # Datos del siniestro
    tipo_evento = forms.ChoiceField(
        choices=TIPO_EVENTO_CHOICES,
        label='Tipo de Evento',
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600'
        })
    )
    
    descripcion = forms.CharField(
        label='Descripción del Evento',
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600',
            'placeholder': 'Describe los detalles del evento...',
            'rows': 5
        })
    )
    
    # Información del beneficiario
    nombre_beneficiario = forms.CharField(
        max_length=150,
        label='Nombre del Beneficiario',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600',
            'placeholder': 'Nombre completo'
        })
    )
    
    relacion_beneficiario = forms.CharField(
        max_length=50,
        label='Relación con el Asegurado',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600',
            'placeholder': 'Ej: Familiar, Heredero, etc.'
        })
    )
    
    # Contacto
    telefono = forms.CharField(
        max_length=20,
        label='Teléfono de Contacto',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600',
            'placeholder': '+593 99 123 4567'
        })
    )
    
    email = forms.EmailField(
        label='Correo Electrónico',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600',
            'placeholder': 'tu@ejemplo.com'
        })
    )
    
    # Documentación
    archivo_documento = forms.FileField(
        label='Documento de Soporte (PDF)',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600',
            'accept': '.pdf,.doc,.docx'
        })
    )
    
    # Consentimiento
    acepta_terminos = forms.BooleanField(
        label='Acepto los términos y condiciones de la póliza',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300'
        })
    )
    
    # Google reCAPTCHA v2 (checkbox)
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)
    
    def clean_archivo_documento(self):
        """Validar tamaño del archivo"""
        archivo = self.cleaned_data.get('archivo_documento')
        if archivo:
            if archivo.size > 5 * 1024 * 1024:  # 5MB máximo
                raise ValidationError('El archivo no debe ser mayor a 5MB.')
        return archivo

    def clean(self):
        return super().clean()
