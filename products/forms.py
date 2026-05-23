from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    initial_stock = forms.IntegerField(label='Estoque', initial=0, required=False)

    class Meta:
        model = Product
        fields = ['name', 'category', 'sku', 'purchase_price', 'sale_price', 'min_stock', 'description', 'image', 'show_in_catalog', 'catalog_categories']
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
            'catalog_categories': forms.MultipleHiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.conf import settings
        if not getattr(settings, 'USE_CATALOG', False):
            if 'show_in_catalog' in self.fields:
                del self.fields['show_in_catalog']
            if 'catalog_categories' in self.fields:
                del self.fields['catalog_categories']

    def clean(self):
        cleaned_data = super().clean()
        from django.conf import settings

        if getattr(settings, 'USE_CATALOG', False):
            show_in_catalog = cleaned_data.get('show_in_catalog')
            catalog_categories = cleaned_data.get('catalog_categories')

            if show_in_catalog and not catalog_categories:
                self.add_error('catalog_categories', 'Selecione ao menos uma categoria do catálogo.')

        return cleaned_data
