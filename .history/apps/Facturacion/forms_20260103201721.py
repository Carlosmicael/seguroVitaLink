from django import forms
from .models import DocumentoFacturacion
from apps.siniestros.models import Poliza

class DocumentoFacturacionForm(forms.ModelForm):
    poliza = forms.ModelChoiceField(
        queryset=Poliza.objects.all(),
        empty_label="Seleccione una Póliza",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    documento = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'})
    )
    codigo_documento = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el código del documento'})
    )
    comentarios = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Comentarios sobre el documento'}),
        required=False
    )

    class Meta:
        model = DocumentoFacturacion
        fields = ['poliza', 'documento', 'codigo_documento', 'comentarios']

