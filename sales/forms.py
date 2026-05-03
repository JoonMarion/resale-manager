from django import forms
from django.forms import inlineformset_factory
from .models import Sale, SaleItem
from customers.models import Customer
from products.models import Product


class SaleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.filter(active=True).order_by('name')
        self.fields['customer'].empty_label = 'Selecione um cliente...'
        self.fields['installments'].required = False

    class Meta:
        model = Sale
        fields = ['customer', 'payment_method', 'installments', 'is_paid']
        labels = {
            'customer': 'Cliente',
            'payment_method': 'Forma de Pagamento',
            'installments': 'Parcelas',
            'is_paid': 'Já pago?',
        }


class SaleItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(active=True).order_by('name')
        self.fields['product'].empty_label = 'Selecione um produto...'

    class Meta:
        model = SaleItem
        fields = ['product', 'quantity', 'unit_sale_price']
        labels = {
            'product': 'Produto',
            'quantity': 'Quantidade',
            'unit_sale_price': 'Preço Unitário (R$)',
        }


SaleItemFormSet = inlineformset_factory(
    Sale,
    SaleItem,
    form=SaleItemForm,
    extra=0,
    min_num=1,
    validate_min=True,
    can_delete=False,
)

SaleItemEditFormSet = inlineformset_factory(
    Sale,
    SaleItem,
    form=SaleItemForm,
    extra=0,
    min_num=1,
    validate_min=True,
    can_delete=True,
)
