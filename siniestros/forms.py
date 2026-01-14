from django import forms
from django.utils import timezone
from .models import Siniestro

class SiniestroForm(forms.ModelForm):
    class Meta:
        model = Siniestro
        fields = ['tipo', 'fecha_evento', 'descripcion', 'nombre_beneficiario', 'parentesco']
        
        # AQUÍ ESTÁ EL TRUCO VISUAL:
        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            }),
            'fecha_evento': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Describa detalladamente qué sucedió...'
            }),
            'nombre_beneficiario': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            }),
            'parentesco': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_evento = cleaned_data.get('fecha_evento')
        
        if self.instance.poliza_id and fecha_evento:
            aseguradora = self.instance.poliza.aseguradora
            limite_dias = aseguradora.dias_maximos_reporte
            
            delta = timezone.now().date() - fecha_evento
            dias_pasados = delta.days

            if dias_pasados > limite_dias:
                self.add_error('fecha_evento', f"¡Plazo vencido! Han pasado {dias_pasados} días (Máximo permitido: {limite_dias}).")
            
            if dias_pasados < 0:
                self.add_error('fecha_evento', "La fecha no puede ser futura.")

        return cleaned_data