from django import forms
from .models import StockEntry, StockExit


class StockEntryForm(forms.ModelForm):
    class Meta:
        model = StockEntry
        fields = ['quantity', 'notes']
        labels = {
            'quantity': 'Quantidade de entrada',
            'notes': 'Observações',
        }
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class StockExitForm(forms.ModelForm):
    class Meta:
        model = StockExit
        fields = ['quantity', 'notes']
        labels = {
            'quantity': 'Quantidade de saída',
            'notes': 'Motivo da saída',
        }
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
