from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    initial_stock = forms.IntegerField(label='Estoque', initial=0, required=False)

    class Meta:
        model = Product
        fields = ['name', 'category', 'sku', 'purchase_price', 'sale_price', 'min_stock', 'description', 'image']
        labels = {
            'name': 'Nome',
            'category': 'Categoria',
            'sku': 'SKU',
            'purchase_price': 'Preço de compra',
            'sale_price': 'Preço de venda',
            'min_stock': 'Estoque mínimo',
            'description': 'Descrição',
            'image': 'Imagem',
        }
        widgets = {
            'image': forms.FileInput(),
        }
