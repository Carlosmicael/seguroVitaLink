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
        fields = ['tipo_poliza', 'monto_solicitado', 'motivo', 'documento_identidad', 'telefono', 'direccion']
        
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







