from django import forms
from .models import Poliza, Estudiante, Solicitud,TcasDocumentos

class PolizaForm(forms.ModelForm):
        
    class Meta:
        model = Poliza
        fields = ['estudiante', 'numero_poliza', 'estado', 'tipo_cobertura', 'fecha_inicio', 'prima_neta']
        widgets = {'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),'estudiante': forms.Select(attrs={'class': 'form-select'}),}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['numero_poliza'].initial = Poliza.generar_numero_poliza()
            self.fields['numero_poliza'].widget.attrs['readonly'] = True





class SolicitudForm(forms.ModelForm):
    class Meta:
        model = Solicitud
        fields = ['estudiante','tipo_poliza','monto_solicitado','motivo','documento_identidad','telefono','direccion']

    def clean_monto_solicitado(self):
        monto = self.cleaned_data.get('monto_solicitado')
        if monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor a 0")
        return monto





class TcasDocumentosForm(forms.ModelForm):
    class Meta:
        model = TcasDocumentos
        fields = ["doc_descripcion"]
        widgets = {
            "doc_descripcion": forms.Textarea(attrs={"class": "form-control"}),
        }
        labels = {
            "doc_descripcion": "Descripción",
        }

















from django import forms
from django.core.exceptions import ValidationError
from .models import Siniestro, Poliza, Estudiante
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox


class ActivacionPolizaForm(forms.Form):
    """Formulario para reportar evento/siniestro de estudiante UTPL"""
    
    # Datos del siniestro
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


class BeneficiarioLoginForm(forms.Form):
    """Formulario de login para beneficiarios"""
    username = forms.CharField(
        label='Usuario',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600',
            'placeholder': 'Ingresa tu usuario'
        })
    )
    password = forms.CharField(
        label='Contraseña',
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600',
            'placeholder': 'Ingresa tu contraseña'
        })
    )


class GestionSolicitudForm(forms.ModelForm):
    """Formulario para que el administrador gestione una solicitud"""
    
    # Campo para seleccionar estudiante
    estudiante = forms.ModelChoiceField(
        queryset=Estudiante.objects.all().order_by('apellidos', 'nombres'),
        label='Estudiante',
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600'
        })
    )
    
    class Meta:
        model = Siniestro
        fields = ['tipo', 'estado', 'comentarios']
        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600'
            }),
            'estado': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600'
            }),
            'comentarios': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600',
                'rows': 4
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.poliza and self.instance.poliza.estudiante:
            # Pre-seleccionar el estudiante actual si existe
            self.fields['estudiante'].initial = self.instance.poliza.estudiante