from django import forms
from .models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'address', 'notes']
        labels = {
            'name': 'Nome Completo',
            'phone': 'Telefone',
            'address': 'Endereço',
            'notes': 'Observações',
        }
